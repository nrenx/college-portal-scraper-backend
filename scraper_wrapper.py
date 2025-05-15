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
    workers: int = 3,  # Increased to 3 workers as requested
    worker_mode: str = "thread",
    delay: float = 2.0,  # Keeping increased delay to reduce load
    max_retries: int = None  # Removed max retries as requested
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
    # Base command for all scrapers
    cmd = [
        sys.executable,
        str(script_path),
        "--username", username,
        "--password", password,
        "--academic-year", academic_year,
        "--workers", str(workers),
        "--worker-mode", worker_mode,
        "--delay", str(delay),
        "--no-csv",  # Disable CSV generation to save time
        "--headless"  # Always use headless mode on Render
    ]

    # Add max-retries parameter only if it's specified
    if max_retries is not None and scraper_type != "personal_details":
        cmd.extend(["--max-retries", str(max_retries)])

    # Log the full command for debugging
    logger.info(f"Built command for {scraper_type} scraper with {workers} workers and delay={delay}")
    # Log a sanitized version of the command (without password)
    sanitized_cmd = cmd.copy()
    password_index = sanitized_cmd.index("--password") + 1
    sanitized_cmd[password_index] = "********"
    logger.info(f"Running command: {' '.join(sanitized_cmd)}")

    try:
        # Use a shorter timeout to prevent hanging processes on Render free tier
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=180  # 3 minute timeout (reduced from 5 minutes)
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

    except subprocess.TimeoutExpired as e:
        error_message = f"Timeout running {scraper_type} scraper: Process took too long and was terminated after {180} seconds"
        logger.error(error_message)

        # Log any available output
        stdout = e.stdout.decode('utf-8', errors='replace') if hasattr(e, 'stdout') and e.stdout else ""
        stderr = e.stderr.decode('utf-8', errors='replace') if hasattr(e, 'stderr') and e.stderr else ""

        if stdout:
            logger.error(f"Last stdout output before timeout:\n{stdout[-1000:] if len(stdout) > 1000 else stdout}")
        if stderr:
            logger.error(f"Last stderr output before timeout:\n{stderr[-1000:] if len(stderr) > 1000 else stderr}")

        return {
            "success": False,
            "message": error_message,
            "stdout": stdout,
            "stderr": stderr
        }
    except subprocess.CalledProcessError as e:
        error_message = f"Error running {scraper_type} scraper: {e}"
        logger.error(error_message)

        # Convert bytes to string with error handling
        stderr = e.stderr.decode('utf-8', errors='replace') if e.stderr else ""
        stdout = e.stdout.decode('utf-8', errors='replace') if e.stdout else ""

        # Log the output for debugging
        if stdout:
            logger.error(f"Process stdout:\n{stdout[-1000:] if len(stdout) > 1000 else stdout}")
        if stderr:
            logger.error(f"Process stderr:\n{stderr[-1000:] if len(stderr) > 1000 else stderr}")

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

        # Check for specific error patterns
        error_details = ""

        # Check for Selenium/ChromeDriver errors
        if "selenium.common.exceptions" in stderr or "selenium.common.exceptions" in stdout:
            if "WebDriverException" in stderr or "WebDriverException" in stdout:
                error_details = "WebDriver error. Chrome or ChromeDriver might not be installed correctly."
            elif "NoSuchElementException" in stderr or "NoSuchElementException" in stdout:
                error_details = "Element not found on page. The college portal structure might have changed."
            elif "TimeoutException" in stderr or "TimeoutException" in stdout:
                error_details = "Timeout waiting for element. The college portal is responding slowly."

        # Check for authentication errors
        elif "Login failed" in stderr or "Authentication failed" in stderr or "Login failed" in stdout or "Authentication failed" in stdout:
            error_details = "Authentication failed. Please check your credentials."

        # Check for connection errors
        elif "Connection refused" in stderr or "Failed to establish a new connection" in stderr:
            error_details = "Connection error. The college portal may be down or unreachable."

        # Check for timeout errors
        elif "Timeout" in stderr or "timed out" in stderr:
            error_details = "Timeout error. The college portal is responding slowly."

        # Check for file not found errors
        elif "No such file or directory" in stderr:
            error_details = "File not found error. Required files might be missing."

        # Check for permission errors
        elif "Permission denied" in stderr:
            error_details = "Permission denied. Check file permissions."

        # Update error message with details if available
        if error_details:
            error_message = f"{error_message} - {error_details}"

        logger.error(f"Final error diagnosis: {error_message}")
        return {
            "success": False,
            "message": error_message,
            "stdout": stdout,
            "stderr": stderr
        }
    except Exception as e:
        import traceback
        error_message = f"Unexpected error running {scraper_type} scraper: {e}"
        logger.error(error_message)

        # Get the full traceback for debugging
        tb = traceback.format_exc()
        logger.error(f"Traceback:\n{tb}")

        # Try to provide more specific error information
        if "chrome not reachable" in str(e).lower():
            error_message = f"{error_message} - Chrome browser crashed or is not available. Check Chrome installation."
        elif "chromedriver" in str(e).lower():
            error_message = f"{error_message} - ChromeDriver issue. Check if ChromeDriver is installed and compatible with Chrome."
        elif "selenium" in str(e).lower():
            error_message = f"{error_message} - Selenium issue. Check Selenium installation."
        elif "permission" in str(e).lower():
            error_message = f"{error_message} - Permission issue. Check file permissions."
        elif "file" in str(e).lower() and "not found" in str(e).lower():
            error_message = f"{error_message} - File not found. Check if required files exist."

        return {
            "success": False,
            "message": error_message,
            "traceback": tb
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
            check=True,
            timeout=300  # 5 minute timeout
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

    except subprocess.TimeoutExpired as e:
        error_message = f"Timeout running Supabase uploader: Process took too long and was terminated after {300} seconds"
        logger.error(error_message)

        # Log any available output
        stdout = e.stdout.decode('utf-8', errors='replace') if hasattr(e, 'stdout') and e.stdout else ""
        stderr = e.stderr.decode('utf-8', errors='replace') if hasattr(e, 'stderr') and e.stderr else ""

        if stdout:
            logger.error(f"Last stdout output before timeout:\n{stdout[-1000:] if len(stdout) > 1000 else stdout}")
        if stderr:
            logger.error(f"Last stderr output before timeout:\n{stderr[-1000:] if len(stderr) > 1000 else stderr}")

        return {
            "success": False,
            "message": error_message,
            "stdout": stdout,
            "stderr": stderr
        }
    except subprocess.CalledProcessError as e:
        error_message = f"Error running Supabase uploader: {e}"
        logger.error(error_message)

        # Convert bytes to string with error handling
        stderr = e.stderr.decode('utf-8', errors='replace') if e.stderr else ""
        stdout = e.stdout.decode('utf-8', errors='replace') if e.stdout else ""

        # Log the output for debugging
        if stdout:
            logger.error(f"Process stdout:\n{stdout[-1000:] if len(stdout) > 1000 else stdout}")
        if stderr:
            logger.error(f"Process stderr:\n{stderr[-1000:] if len(stderr) > 1000 else stderr}")

        # Check for specific error patterns
        error_details = ""

        if "supabase" in stderr.lower() and "auth" in stderr.lower():
            error_details = "Supabase authentication error. Check your Supabase URL and API key."
        elif "bucket" in stderr.lower() and "not found" in stderr.lower():
            error_details = "Supabase bucket not found. Check if the bucket exists."
        elif "permission" in stderr.lower() or "access" in stderr.lower():
            error_details = "Permission denied. Check your Supabase permissions."
        elif "network" in stderr.lower() or "connection" in stderr.lower():
            error_details = "Network error. Check your internet connection."

        # Update error message with details if available
        if error_details:
            error_message = f"{error_message} - {error_details}"

        logger.error(f"Final error diagnosis: {error_message}")

        return {
            "success": False,
            "message": error_message,
            "stdout": stdout,
            "stderr": stderr
        }
    except Exception as e:
        import traceback
        error_message = f"Unexpected error running Supabase uploader: {e}"
        logger.error(error_message)

        # Get the full traceback for debugging
        tb = traceback.format_exc()
        logger.error(f"Traceback:\n{tb}")

        # Try to provide more specific error information
        if "supabase" in str(e).lower():
            error_message = f"{error_message} - Supabase client error. Check Supabase configuration."
        elif "permission" in str(e).lower():
            error_message = f"{error_message} - Permission issue. Check file permissions."
        elif "file" in str(e).lower() and "not found" in str(e).lower():
            error_message = f"{error_message} - File not found. Check if required files exist."
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            error_message = f"{error_message} - Network error. Check your internet connection."

        return {
            "success": False,
            "message": error_message,
            "traceback": tb
        }
