"""
Job storage module for persisting job status between server restarts.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Import custom logging configuration if available
try:
    from logging_config import configure_logging, get_logger
    # Get a logger with extra context
    logger = get_logger("job_storage", {"component": "job_storage"})
except ImportError:
    # Fall back to basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger = logging.getLogger("job_storage")

# Define the storage directory
STORAGE_DIR = Path("job_storage")

def ensure_storage_dir():
    """Ensure the storage directory exists"""
    if not STORAGE_DIR.exists():
        STORAGE_DIR.mkdir(parents=True)
        logger.info(f"Created job storage directory: {STORAGE_DIR}")

def save_job(job_id: str, job_data: Dict[str, Any]) -> bool:
    """
    Save job data to a file

    Args:
        job_id: The job ID
        job_data: The job data to save

    Returns:
        bool: True if successful, False otherwise
    """
    ensure_storage_dir()

    try:
        file_path = STORAGE_DIR / f"{job_id}.json"
        with open(file_path, 'w') as f:
            json.dump(job_data, f, indent=2)
        logger.info(f"Saved job {job_id} to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving job {job_id}: {str(e)}")
        return False

def load_job(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Load job data from a file

    Args:
        job_id: The job ID

    Returns:
        Dict or None: The job data if found, None otherwise
    """
    ensure_storage_dir()

    file_path = STORAGE_DIR / f"{job_id}.json"
    if not file_path.exists():
        logger.warning(f"Job file not found: {file_path}")
        return None

    try:
        with open(file_path, 'r') as f:
            job_data = json.load(f)
        logger.info(f"Loaded job {job_id} from {file_path}")
        return job_data
    except Exception as e:
        logger.error(f"Error loading job {job_id}: {str(e)}")
        return None

def list_jobs() -> Dict[str, Dict[str, Any]]:
    """
    List all saved jobs

    Returns:
        Dict: A dictionary of job_id -> job_data
    """
    ensure_storage_dir()

    jobs = {}
    for file_path in STORAGE_DIR.glob("*.json"):
        job_id = file_path.stem
        job_data = load_job(job_id)
        if job_data:
            jobs[job_id] = job_data

    logger.info(f"Listed {len(jobs)} jobs")
    return jobs

def delete_job(job_id: str) -> bool:
    """
    Delete a job file

    Args:
        job_id: The job ID

    Returns:
        bool: True if successful, False otherwise
    """
    ensure_storage_dir()

    file_path = STORAGE_DIR / f"{job_id}.json"
    if not file_path.exists():
        logger.warning(f"Job file not found for deletion: {file_path}")
        return False

    try:
        file_path.unlink()
        logger.info(f"Deleted job {job_id} from {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        return False
