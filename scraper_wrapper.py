"""
Wrapper module for running the college portal scrapers and Supabase uploader.
This module provides functions to run the scrapers and uploader from the API.
"""

import os
import sys
import subprocess
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper_wrapper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("scraper_wrapper")

# Add parent directory to path to import scraper modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_scraper(
    scraper_type: str,
    username: str,
    password: str,
    academic_year: str,
    headless: bool = True,
    workers: int = 16,
    worker_mode: str = "thread",
    delay: float = 1.0,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Run a scraper with the specified parameters.

    Args:
        scraper_type: Type of scraper to run ('attendance', 'mid_marks', or 'personal_details')
        username: Login username
        password: Login password
        academic_year: Academic year to scrape
        headless: Whether to run in headless mode
        workers: Number of worker threads/processes
        worker_mode: Worker mode ('thread' or 'process')
        delay: Delay between requests
        max_retries: Maximum number of retries for failed requests

    Returns:
        Dictionary with scraper results
    """
    logger.info(f"Running {scraper_type} scraper for academic year {academic_year}")

    # Determine the script to run
    if scraper_type == "attendance":
        script_name = "attendance_scraper.py"
    elif scraper_type == "mid_marks":
        script_name = "mid_marks_scraper.py"
    elif scraper_type == "personal_details":
        script_name = "personal_details_scraper.py"
    else:
        raise ValueError(f"Invalid scraper type: {scraper_type}")

    # Get the script path - look in the current directory first, then try the parent directory
    script_path = Path(os.path.dirname(os.path.abspath(__file__))) / script_name
    if not script_path.exists():
        # Try the parent directory as fallback
        script_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Scraper script not found: {script_path}")

    # Build the command
    if scraper_type == "personal_details":
        # Use modified command for personal_details_scraper (without --max-retries)
        cmd = [
            sys.executable,
            str(script_path),
            "--username", username,
            "--password", password,
            "--academic-year", academic_year,
            "--workers", str(workers),
            "--worker-mode", worker_mode,
            "--delay", str(delay),
            "--no-csv"  # Disable CSV generation to save time
        ]
    else:
        # Use full command for other scrapers
        cmd = [
            sys.executable,
            str(script_path),
            "--username", username,
            "--password", password,
            "--academic-year", academic_year,
            "--workers", str(workers),
            "--worker-mode", worker_mode,
            "--delay", str(delay),
            "--max-retries", str(max_retries),
            "--no-csv"  # Disable CSV generation to save time
        ]

    if headless:
        cmd.append("--headless")

    # Run the command
    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        logger.info(f"{scraper_type} scraper completed successfully")

        # Parse the output to extract relevant information
        output_lines = result.stdout.splitlines()

        # Extract statistics from the output
        stats = {}
        for line in output_lines:
            if "Processed" in line and "students" in line:
                stats["processed"] = line
            elif "Combinations with data" in line:
                stats["combinations"] = line
            elif "Summary: Processed" in line and "students across" in line:
                stats["summary"] = line
            elif "Total success:" in line:
                stats["success_details"] = line
            elif "PERSONAL DETAILS SCRAPING COMPLETED SUCCESSFULLY" in line:
                stats["personal_details_success"] = True
            elif "scraping completed successfully" in line:
                stats["scraping_success"] = True

        return {
            "success": True,
            "message": f"{scraper_type} scraper completed successfully",
            "stats": stats,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.CalledProcessError as e:
        error_message = f"Error running {scraper_type} scraper: {e}"

        # Check for common error patterns in the output
        stderr = e.stderr or ""
        stdout = e.stdout or ""

        # Special handling for personal_details scraper
        # Even if it returns a non-zero exit code, check if it completed successfully
        if scraper_type == "personal_details" and (
            "PERSONAL DETAILS SCRAPING COMPLETED SUCCESSFULLY" in stdout or
            "Personal details scraping completed successfully" in stdout or
            "Personal details scraping completed with no data found" in stdout
        ):
            logger.info(f"Personal details scraper completed successfully despite non-zero exit code")

            # Parse the output to extract relevant information
            output_lines = stdout.splitlines()

            # Extract statistics from the output
            stats = {}
            for line in output_lines:
                if "Processed" in line and "students" in line:
                    stats["processed"] = line
                elif "Summary: Processed" in line and "students across" in line:
                    stats["summary"] = line
                elif "Total success:" in line:
                    stats["success_details"] = line
                elif "PERSONAL DETAILS SCRAPING COMPLETED SUCCESSFULLY" in line:
                    stats["personal_details_success"] = True

            return {
                "success": True,
                "message": "Personal details scraper completed successfully",
                "stats": stats,
                "stdout": stdout,
                "stderr": stderr
            }

        # Normal error handling for other scrapers
        if "exit status 1" in stderr:
            if "Login failed" in stderr or "Authentication failed" in stderr or "Login failed" in stdout or "Authentication failed" in stdout:
                error_message = f"Authentication failed for {scraper_type} scraper. Please check your credentials."
            elif "Connection refused" in stderr or "Failed to establish a new connection" in stderr:
                error_message = f"Connection error in {scraper_type} scraper. The college portal may be down or unreachable."
            elif "Timeout" in stderr:
                error_message = f"Timeout error in {scraper_type} scraper. The college portal is responding slowly."

        logger.error(error_message)
        return {
            "success": False,
            "message": error_message,
            "stdout": e.stdout,
            "stderr": e.stderr
        }
    except Exception as e:
        logger.error(f"Unexpected error running {scraper_type} scraper: {e}")
        return {
            "success": False,
            "message": f"Unexpected error running {scraper_type} scraper: {e}"
        }

def run_uploader(
    workers: int = 32,
    force_update: bool = False
) -> Dict[str, Any]:
    """
    Run the Supabase uploader with the specified parameters.

    Args:
        workers: Number of worker threads
        force_update: Whether to force update existing files

    Returns:
        Dictionary with uploader results
    """
    logger.info("Running Supabase uploader")

    # Get the script path - look in the current directory first, then try the parent directory
    script_path = Path(os.path.dirname(os.path.abspath(__file__))) / "upload_folder_to_supabase.py"
    if not script_path.exists():
        # Try the parent directory as fallback
        script_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "upload_folder_to_supabase.py"

    if not script_path.exists():
        # Try the alternative uploader if the primary one doesn't exist
        alt_script_path = Path(os.path.dirname(os.path.abspath(__file__))) / "supabase_uploader_new.py"
        if not alt_script_path.exists():
            # Try the parent directory as fallback
            alt_script_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "supabase_uploader_new.py"
        if alt_script_path.exists():
            script_path = alt_script_path
            logger.info(f"Using alternative uploader: {script_path}")
        else:
            raise FileNotFoundError(f"Uploader script not found: {script_path} or {alt_script_path}")

    # Get bucket name from environment variable
    bucket_name = os.getenv("SUPABASE_BUCKET", "demo-usingfastapi")

    # Create a temporary supabase_config.py file with the correct settings
    config_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "supabase_config.py"
    with open(config_path, 'w') as f:
        f.write(f"""#!/usr/bin/env python3
\"\"\"
Supabase Configuration for Fast Uploader

This file contains configuration settings for the Supabase uploader.
\"\"\"

# Supabase credentials
SUPABASE_URL = "{os.getenv('SUPABASE_URL')}"
SUPABASE_KEY = "{os.getenv('SUPABASE_KEY')}"

# Default settings
DEFAULT_SETTINGS = {{
    # Storage settings
    "bucket": "{bucket_name}",
    "source_dir": "student_details",

    # Performance settings
    "workers": {workers},

    # Feature settings
    "skip_existing": {not force_update},
}}
""")

    # Build the command
    cmd = [
        sys.executable,
        str(script_path)
    ]

    # Run the command
    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        logger.info("Supabase uploader completed successfully")

        # Parse the output to extract relevant information
        output_lines = result.stdout.splitlines()

        # Extract statistics from the output
        stats = {}
        for line in output_lines:
            if "Uploaded" in line and "files" in line:
                stats["uploaded"] = line
            elif "Skipped" in line and "files" in line:
                stats["skipped"] = line
            elif "Total" in line and "bytes" in line:
                stats["total_bytes"] = line

        return {
            "success": True,
            "message": "Supabase uploader completed successfully",
            "stats": stats,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Supabase uploader: {e}")
        return {
            "success": False,
            "message": f"Error running Supabase uploader: {e}",
            "stdout": e.stdout,
            "stderr": e.stderr
        }
    except Exception as e:
        logger.error(f"Unexpected error running Supabase uploader: {e}")
        return {
            "success": False,
            "message": f"Unexpected error running Supabase uploader: {e}"
        }
