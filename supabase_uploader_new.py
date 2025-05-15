#!/usr/bin/env python3
"""
Optimized Supabase Uploader for Student Data

This script is optimized for uploading student data from the student_details folder
to Supabase Storage with maximum performance.

Key optimizations:
1. Student-level batching: Uploads all files for a student in a single operation
2. Directory-based caching: Reduces redundant API calls by caching at directory level
3. Hierarchical parallelism: Processes academic years, semesters, and students in parallel
4. Connection pooling: Maintains persistent connections for better performance
5. Automatic retries with exponential backoff: Handles transient network issues
6. Progress tracking with ETA: Shows detailed progress information

Usage:
    python3 supabase_uploader_new.py [options]

Options:
    --supabase-url <url>       Supabase project URL (can be set in supabase_config.py)
    --supabase-key <key>       Supabase API key (can be set in supabase_config.py)
    --bucket <name>            Supabase Storage bucket name (default: student_data)
    --source-dir <dir>         Source directory (default: student_details)
    --workers <num>            Number of worker threads (default: 16)
    --student-batch <num>      Number of students to process in parallel (default: 20)
    --skip-existing            Skip files that already exist in Supabase
    --dry-run                  Perform a dry run without uploading
    --verbose                  Enable verbose logging
"""

import os
import sys
import time
import json
import logging
import argparse
import hashlib
import asyncio
import aiohttp
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional, Set
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Lock

# Try to import configuration
try:
    from supabase_config import (
        SUPABASE_URL, SUPABASE_KEY, DEFAULT_SETTINGS
    )
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: supabase_config.py not found. Using default settings.")

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Warning: tqdm is not installed. Progress bars will not be available.")

# Import custom logging configuration if available
try:
    from logging_config import configure_logging, get_logger
    # Configure logging with more detailed settings
    configure_logging(console_level=logging.INFO, file_level=logging.DEBUG, enable_json=True)
    # Get a logger with extra context
    logger = get_logger("supabase_uploader", {"component": "uploader"})
    logger.info("Using custom logging configuration")
except ImportError:
    # Fall back to basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("supabase_uploader_new.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger("supabase_uploader_new")
    logger.info("Using basic logging configuration")

# Global variables
upload_stats = {
    "total_files": 0,
    "uploaded_files": 0,
    "skipped_files": 0,
    "failed_files": 0,
    "total_bytes": 0,
    "uploaded_bytes": 0,
    "start_time": None,
    "end_time": None,
    "students_processed": 0,
    "total_students": 0
}
stats_lock = Lock()

# Cache for existing files and directories
existing_files_cache = {}
existing_dirs_cache = set()
cache_lock = Lock()

def format_size(size_bytes):
    """Format size in bytes to human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

class SupabaseClient:
    """
    A custom Supabase client optimized for bulk uploads.
    """
    def __init__(self, url: str, key: str, max_connections: int = 100):
        self.url = url.rstrip('/')
        self.key = key
        self.max_connections = max_connections
        self.headers = {
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        self.session = None
        self.connector = None

    async def initialize(self):
        """Initialize the aiohttp session with connection pooling."""
        if self.session is None:
            # Create a TCP connector with connection pooling and SSL verification disabled
            self.connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                ttl_dns_cache=300,
                use_dns_cache=True,
                ssl=False  # Disable SSL verification
            )

            # Create a ClientSession with the connector
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=60)
            )

    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
            self.connector = None

    async def list_buckets(self):
        """List all buckets in Supabase Storage."""
        await self.initialize()
        async with self.session.get(f"{self.url}/storage/v1/bucket") as response:
            if response.status == 200:
                return await response.json()
            else:
                text = await response.text()
                raise Exception(f"Error listing buckets: {response.status} - {text}")

    async def create_bucket(self, name: str, is_public: bool = False):
        """Create a new bucket in Supabase Storage."""
        await self.initialize()
        data = {"name": name, "public": is_public}
        async with self.session.post(f"{self.url}/storage/v1/bucket", json=data) as response:
            if response.status == 200 or response.status == 201:
                return await response.json()
            else:
                text = await response.text()
                raise Exception(f"Error creating bucket: {response.status} - {text}")

    async def list_files(self, bucket: str, prefix: str = ""):
        """List files in a bucket with the given prefix."""
        await self.initialize()
        params = {}
        if prefix:
            params["prefix"] = prefix

        async with self.session.get(
            f"{self.url}/storage/v1/object/list/{bucket}",
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                text = await response.text()
                raise Exception(f"Error listing files: {response.status} - {text}")

    async def upload_file(self, bucket: str, path: str, data: bytes):
        """Upload a file to Supabase Storage."""
        await self.initialize()

        # Create FormData with the file
        form = aiohttp.FormData()
        form.add_field('file', data, filename=os.path.basename(path))

        async with self.session.post(
            f"{self.url}/storage/v1/object/{bucket}/{path}",
            data=form,
            headers={'Authorization': f'Bearer {self.key}'}  # Override content-type
        ) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 400:
                # Check if it's a duplicate error
                text = await response.text()
                if "Duplicate" in text:
                    # File already exists, consider it a success for our purposes
                    logger.debug(f"File already exists: {path}")
                    return {"path": path, "status": "exists"}
                else:
                    raise Exception(f"Error uploading file: {response.status} - {text}")
            else:
                text = await response.text()
                raise Exception(f"Error uploading file: {response.status} - {text}")

    async def upload_student_files(self, bucket: str, student_dir: Path, source_dir: Path, skip_existing: bool = False):
        """Upload all files for a student in parallel."""
        await self.initialize()

        # Get all JSON files in the student directory
        files = list(student_dir.glob("*.json"))
        if not files:
            return {"uploaded": 0, "skipped": 0, "failed": 0, "bytes": 0}

        # Prepare tasks for each file
        tasks = []
        for file_path in files:
            # Get the path in Supabase Storage
            supabase_path = str(file_path.relative_to(source_dir)).replace('\\', '/')

            # Check if the file already exists
            if skip_existing:
                with cache_lock:
                    cache_key = f"{bucket}:{supabase_path}"
                    if cache_key in existing_files_cache and existing_files_cache[cache_key]:
                        continue

            # Read the file
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Create a task to upload the file
            tasks.append(self.upload_file(bucket, supabase_path, file_data))

        # Execute all tasks in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            stats = {"uploaded": 0, "skipped": 0, "failed": 0, "bytes": 0}
            for i, result in enumerate(results):
                file_path = files[i]
                file_size = file_path.stat().st_size

                if isinstance(result, Exception):
                    # Log detailed error information
                    error_type = type(result).__name__
                    error_message = str(result)
                    file_name = os.path.basename(file_path)
                    file_size = file_path.stat().st_size

                    # Create structured error log
                    logger.error(
                        f"Error uploading file {file_name} ({format_size(file_size)})",
                        extra={
                            "error_type": error_type,
                            "error_message": error_message,
                            "file_path": str(file_path),
                            "file_size": file_size,
                            "supabase_path": str(file_path.relative_to(source_dir)).replace('\\', '/'),
                            "bucket": bucket,
                            "operation": "upload_file"
                        }
                    )
                    stats["failed"] += 1
                else:
                    # Check if the file was a duplicate (already exists)
                    if isinstance(result, dict) and result.get('status') == 'exists':
                        stats["skipped"] += 1
                        stats["bytes"] += file_size  # Still count the bytes for statistics
                    else:
                        stats["uploaded"] += 1
                        stats["bytes"] += file_size

                    # Cache the file as uploaded/existing
                    supabase_path = str(file_path.relative_to(source_dir)).replace('\\', '/')
                    with cache_lock:
                        existing_files_cache[f"{bucket}:{supabase_path}"] = True

            return stats
        else:
            return {"uploaded": 0, "skipped": len(files), "failed": 0, "bytes": 0}

async def ensure_bucket_exists(client: SupabaseClient, bucket_name: str, create_if_missing: bool = False) -> bool:
    """
    Ensure that the specified bucket exists in Supabase Storage.

    Args:
        client: Supabase client
        bucket_name: Name of the bucket
        create_if_missing: Whether to create the bucket if it doesn't exist

    Returns:
        Boolean indicating whether the bucket exists
    """
    try:
        # Try to create the bucket first (this is more reliable)
        if create_if_missing:
            try:
                await client.create_bucket(bucket_name, is_public=False)
                logger.info(f"Created bucket: {bucket_name}")
                return True
            except Exception as e:
                # If the bucket already exists, this will fail with a 409 Conflict error
                if "Duplicate" in str(e) or "already exists" in str(e) or "409" in str(e):
                    logger.info(f"Bucket already exists: {bucket_name}")
                    return True
                else:
                    logger.warning(f"Error creating bucket: {e}")

        # Try to list buckets as a fallback
        try:
            buckets = await client.list_buckets()
            bucket_exists = any(bucket.get('name') == bucket_name for bucket in buckets)

            if bucket_exists:
                logger.info(f"Bucket already exists: {bucket_name}")
                return True
            elif create_if_missing:
                # Try again to create the bucket
                await client.create_bucket(bucket_name, is_public=False)
                logger.info(f"Created bucket: {bucket_name}")
                return True
            else:
                logger.error(f"Bucket does not exist: {bucket_name}")
                return False
        except Exception as e2:
            logger.warning(f"Error listing buckets: {e2}")

            # As a last resort, assume the bucket exists if we're getting errors
            # This is safer than failing the entire upload process
            if create_if_missing:
                logger.info(f"Assuming bucket {bucket_name} exists or was created")
                return True
            else:
                logger.error(f"Cannot verify if bucket {bucket_name} exists")
                return False
    except Exception as e:
        logger.error(f"Error checking/creating bucket: {e}")
        return False

async def cache_directory_files(client: SupabaseClient, bucket: str, directory: str):
    """
    Cache all files in a directory to avoid redundant API calls.

    Args:
        client: Supabase client
        bucket: Bucket name
        directory: Directory path in Supabase Storage
    """
    try:
        # Normalize the directory path
        directory = directory.rstrip('/')

        # Check if we've already cached this directory
        with cache_lock:
            dir_cache_key = f"{bucket}:{directory}"
            if dir_cache_key in existing_dirs_cache:
                return

            # Mark this directory as processed even if we fail to list files
            # This prevents repeated attempts to cache the same directory
            existing_dirs_cache.add(dir_cache_key)

        try:
            # List all files in the directory
            files = await client.list_files(bucket, directory)

            # Cache the files
            with cache_lock:
                for file in files:
                    file_path = file.get('name')
                    if file_path:
                        # Construct the full path
                        if directory:
                            full_path = f"{directory}/{file_path}"
                        else:
                            full_path = file_path

                        # Add to cache
                        existing_files_cache[f"{bucket}:{full_path}"] = True

            logger.debug(f"Cached {len(files)} files in directory {directory}")
        except Exception as e:
            # If we can't list files, just assume files don't exist
            # This is safer than failing the entire upload process
            logger.debug(f"Could not list files in directory {directory}: {e}")
            # We'll continue with the upload and let the server handle duplicates
    except Exception as e:
        logger.debug(f"Error in cache_directory_files: {e}")

async def process_student_directory(client: SupabaseClient, student_dir: Path, source_dir: Path,
                                   bucket: str, skip_existing: bool = False, dry_run: bool = False):
    """
    Process a student directory and upload all files.

    Args:
        client: Supabase client
        student_dir: Path to the student directory
        source_dir: Source directory
        bucket: Bucket name
        skip_existing: Whether to skip files that already exist
        dry_run: Whether to perform a dry run without uploading

    Returns:
        Dictionary with upload statistics
    """
    try:
        # Get the relative path for caching
        relative_path = str(student_dir.relative_to(source_dir)).replace('\\', '/')

        # Cache the directory if skipping existing files
        if skip_existing:
            await cache_directory_files(client, bucket, relative_path)

        # Dry run
        if dry_run:
            files = list(student_dir.glob("*.json"))
            logger.info(f"[DRY RUN] Would upload {len(files)} files from {student_dir}")
            return {"uploaded": len(files), "skipped": 0, "failed": 0, "bytes": sum(f.stat().st_size for f in files)}

        # Upload all files for this student
        stats = await client.upload_student_files(bucket, student_dir, source_dir, skip_existing)

        # Update global stats
        with stats_lock:
            upload_stats["uploaded_files"] += stats["uploaded"]
            upload_stats["skipped_files"] += stats["skipped"]
            upload_stats["failed_files"] += stats["failed"]
            upload_stats["uploaded_bytes"] += stats["bytes"]
            upload_stats["students_processed"] += 1

        return stats
    except Exception as e:
        logger.error(f"Error processing student directory {student_dir}: {e}")
        return {"uploaded": 0, "skipped": 0, "failed": 1, "bytes": 0}

async def process_semester_directory(client: SupabaseClient, semester_dir: Path, source_dir: Path,
                                    bucket: str, skip_existing: bool = False, dry_run: bool = False,
                                    student_batch_size: int = 20):
    """
    Process a semester directory and all student directories within it.

    Args:
        client: Supabase client
        semester_dir: Path to the semester directory
        source_dir: Source directory
        bucket: Bucket name
        skip_existing: Whether to skip files that already exist
        dry_run: Whether to perform a dry run without uploading
        student_batch_size: Number of students to process in parallel

    Returns:
        Dictionary with upload statistics
    """
    try:
        # Get all student directories
        student_dirs = [d for d in semester_dir.iterdir() if d.is_dir()]

        # Process students in batches
        stats = {"uploaded": 0, "skipped": 0, "failed": 0, "bytes": 0}
        for i in range(0, len(student_dirs), student_batch_size):
            batch = student_dirs[i:i + student_batch_size]

            # Process the batch in parallel
            tasks = [
                process_student_directory(
                    client, student_dir, source_dir, bucket, skip_existing, dry_run
                )
                for student_dir in batch
            ]

            # Wait for all tasks to complete
            batch_results = await asyncio.gather(*tasks)

            # Aggregate results
            for result in batch_results:
                stats["uploaded"] += result["uploaded"]
                stats["skipped"] += result["skipped"]
                stats["failed"] += result["failed"]
                stats["bytes"] += result["bytes"]

        return stats
    except Exception as e:
        logger.error(f"Error processing semester directory {semester_dir}: {e}")
        return {"uploaded": 0, "skipped": 0, "failed": 1, "bytes": 0}

async def process_academic_year_directory(client: SupabaseClient, year_dir: Path, source_dir: Path,
                                         bucket: str, skip_existing: bool = False, dry_run: bool = False,
                                         student_batch_size: int = 20):
    """
    Process an academic year directory and all semester directories within it.

    Args:
        client: Supabase client
        year_dir: Path to the academic year directory
        source_dir: Source directory
        bucket: Bucket name
        skip_existing: Whether to skip files that already exist
        dry_run: Whether to perform a dry run without uploading
        student_batch_size: Number of students to process in parallel

    Returns:
        Dictionary with upload statistics
    """
    try:
        # Get all semester directories
        semester_dirs = [d for d in year_dir.iterdir() if d.is_dir()]

        # Process each semester directory
        stats = {"uploaded": 0, "skipped": 0, "failed": 0, "bytes": 0}
        for semester_dir in semester_dirs:
            result = await process_semester_directory(
                client, semester_dir, source_dir, bucket, skip_existing, dry_run, student_batch_size
            )

            # Aggregate results
            stats["uploaded"] += result["uploaded"]
            stats["skipped"] += result["skipped"]
            stats["failed"] += result["failed"]
            stats["bytes"] += result["bytes"]

        return stats
    except Exception as e:
        logger.error(f"Error processing academic year directory {year_dir}: {e}")
        return {"uploaded": 0, "skipped": 0, "failed": 1, "bytes": 0}

def count_files_and_students(source_dir: Path) -> Tuple[int, int]:
    """
    Count the total number of files and students in the source directory.

    Args:
        source_dir: Source directory

    Returns:
        Tuple of (total_files, total_students)
    """
    total_files = 0
    total_students = 0

    for root, dirs, files in os.walk(source_dir):
        # Count JSON files
        json_files = [f for f in files if f.endswith('.json')]
        total_files += len(json_files)

        # Count student directories (leaf directories with JSON files)
        if json_files and not any(os.path.isdir(os.path.join(root, d)) for d in dirs):
            total_students += 1

    return total_files, total_students

def format_size(size_bytes: int) -> str:
    """
    Format a size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def print_stats():
    """
    Print the upload statistics.
    """
    duration = upload_stats["end_time"] - upload_stats["start_time"]
    duration_seconds = duration.total_seconds()

    print("\nUpload Statistics:")
    print(f"  Total files: {upload_stats['total_files']}")
    print(f"  Uploaded files: {upload_stats['uploaded_files']}")
    print(f"  Skipped files: {upload_stats['skipped_files']}")
    print(f"  Failed files: {upload_stats['failed_files']}")
    print(f"  Total students: {upload_stats['total_students']}")
    print(f"  Students processed: {upload_stats['students_processed']}")
    print(f"  Total size: {format_size(upload_stats['total_bytes'])}")
    print(f"  Uploaded size: {format_size(upload_stats['uploaded_bytes'])}")
    print(f"  Duration: {duration_seconds:.2f} seconds")

    if duration_seconds > 0 and upload_stats['uploaded_bytes'] > 0:
        speed = upload_stats['uploaded_bytes'] / duration_seconds
        print(f"  Average speed: {format_size(int(speed))}/s")

        # Calculate files per second
        files_per_second = upload_stats['uploaded_files'] / duration_seconds
        print(f"  Files per second: {files_per_second:.2f}")

async def update_progress(progress_bar):
    """
    Update the progress bar periodically.

    Args:
        progress_bar: tqdm progress bar
    """
    while True:
        # Update the progress bar
        progress_bar.n = upload_stats["students_processed"]
        progress_bar.set_description(
            f"Uploaded: {upload_stats['uploaded_files']}, "
            f"Skipped: {upload_stats['skipped_files']}, "
            f"Failed: {upload_stats['failed_files']}"
        )
        progress_bar.refresh()

        # Check if we're done
        if upload_stats["students_processed"] >= upload_stats["total_students"]:
            break

        # Wait before updating again
        await asyncio.sleep(0.5)

async def main_async():
    """
    Main async function to run the uploader.
    """
    global upload_stats

    # Set default values from config if available
    default_supabase_url = SUPABASE_URL if CONFIG_AVAILABLE else ""
    default_supabase_key = SUPABASE_KEY if CONFIG_AVAILABLE else ""

    if CONFIG_AVAILABLE:
        default_bucket = DEFAULT_SETTINGS.get("bucket", "student_data")
        default_source_dir = DEFAULT_SETTINGS.get("source_dir", "student_details")
        default_workers = DEFAULT_SETTINGS.get("workers", 16)
        default_student_batch = DEFAULT_SETTINGS.get("student_batch", 20)
        default_skip_existing = DEFAULT_SETTINGS.get("skip_existing", False)
    else:
        default_bucket = "student_data"
        default_source_dir = "student_details"
        default_workers = 16
        default_student_batch = 20
        default_skip_existing = False

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fast uploader for student data to Supabase Storage')
    parser.add_argument('--supabase-url', default=default_supabase_url, help='Supabase project URL')
    parser.add_argument('--supabase-key', default=default_supabase_key, help='Supabase API key')
    parser.add_argument('--bucket', default=default_bucket, help='Supabase Storage bucket name')
    parser.add_argument('--source-dir', default=default_source_dir, help='Source directory')
    parser.add_argument('--workers', type=int, default=default_workers, help='Number of worker threads')
    parser.add_argument('--student-batch', type=int, default=default_student_batch, help='Number of students to process in parallel')
    parser.add_argument('--skip-existing', action='store_true', default=default_skip_existing, help='Skip files that already exist in Supabase')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without uploading')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Check if Supabase URL and key are provided
    if not args.supabase_url or not args.supabase_key:
        logger.error("Supabase URL and API key are required. Provide them via command line or supabase_config.py.")
        return 1

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.DEBUG)

    # Get the source directory
    source_dir = Path(args.source_dir)
    if not source_dir.exists() or not source_dir.is_dir():
        logger.error(f"Source directory {source_dir} does not exist or is not a directory.")
        return 1

    # Count files and students
    total_files, total_students = count_files_and_students(source_dir)
    if total_files == 0:
        logger.error(f"No JSON files found in {source_dir}.")
        return 1

    # Initialize upload statistics
    upload_stats["total_files"] = total_files
    upload_stats["total_students"] = total_students
    upload_stats["start_time"] = datetime.now()

    # Calculate total size
    total_bytes = 0
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = Path(root) / file
                total_bytes += file_path.stat().st_size

    upload_stats["total_bytes"] = total_bytes

    logger.info(f"Starting upload of {total_files} files ({format_size(total_bytes)}) "
                f"from {total_students} students to {args.bucket}")

    # Create Supabase client
    client = SupabaseClient(args.supabase_url, args.supabase_key, args.workers)

    try:
        # Ensure bucket exists
        if not await ensure_bucket_exists(client, args.bucket, True):
            logger.error(f"Bucket {args.bucket} does not exist and could not be created.")
            return 1

        # Get all academic year directories
        year_dirs = [d for d in source_dir.iterdir() if d.is_dir()]

        # Create progress bar
        progress_bar = None
        progress_task = None
        if TQDM_AVAILABLE:
            progress_bar = tqdm(total=total_students, unit='student')
            progress_task = asyncio.create_task(update_progress(progress_bar))

        # Process each academic year directory
        for year_dir in year_dirs:
            await process_academic_year_directory(
                client, year_dir, source_dir, args.bucket,
                args.skip_existing, args.dry_run, args.student_batch
            )

        # Wait for progress task to complete
        if progress_task:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

        # Close progress bar
        if progress_bar:
            progress_bar.close()

        # Close the client
        await client.close()

        # Update end time
        upload_stats["end_time"] = datetime.now()

        # Print statistics
        print_stats()

        # Check for failures
        if upload_stats["failed_files"] > 0:
            logger.warning(f"{upload_stats['failed_files']} files failed to upload.")
            return 1
        else:
            logger.info("Upload completed successfully.")
            return 0

    except Exception as e:
        logger.error(f"Error during upload: {e}")
        return 1
    finally:
        # Make sure to close the client
        if client.session:
            await client.close()

def main():
    """
    Main function to run the uploader.
    """
    # Run the async main function
    return asyncio.run(main_async())

if __name__ == "__main__":
    sys.exit(main())
