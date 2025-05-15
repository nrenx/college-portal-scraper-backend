"""
Job monitoring module for detecting and handling stalled jobs.
"""

import os
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import job storage module
from job_storage import load_job, save_job, list_jobs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("job_monitor")

# Maximum job runtime in seconds (15 minutes)
MAX_JOB_RUNTIME = 15 * 60

def check_for_stalled_jobs() -> List[str]:
    """
    Check for jobs that have been running for too long and mark them as failed.
    
    Returns:
        List of job IDs that were marked as stalled
    """
    logger.info("Checking for stalled jobs")
    
    # Get all jobs
    jobs = list_jobs()
    stalled_jobs = []
    
    # Current time
    now = datetime.now()
    
    for job_id, job_data in jobs.items():
        # Skip jobs that are not in running state
        if job_data.get("status") != "running":
            continue
        
        # Check if the job has a start time
        start_time_str = job_data.get("start_time")
        if not start_time_str:
            continue
        
        try:
            # Parse the start time
            start_time = datetime.fromisoformat(start_time_str)
            
            # Calculate the job runtime
            runtime = now - start_time
            
            # Check if the job has been running for too long
            if runtime.total_seconds() > MAX_JOB_RUNTIME:
                logger.warning(f"Job {job_id} has been running for {runtime.total_seconds()} seconds, marking as stalled")
                
                # Mark the job as failed
                job_data["status"] = "failed"
                job_data["message"] = f"Job timed out after {int(runtime.total_seconds())} seconds"
                job_data["end_time"] = now.isoformat()
                
                # Save the updated job status
                save_job(job_id, job_data)
                
                stalled_jobs.append(job_id)
        except Exception as e:
            logger.error(f"Error checking job {job_id}: {str(e)}")
    
    if stalled_jobs:
        logger.info(f"Marked {len(stalled_jobs)} jobs as stalled: {stalled_jobs}")
    else:
        logger.info("No stalled jobs found")
    
    return stalled_jobs

def run_job_monitor():
    """
    Run the job monitor once to check for stalled jobs.
    """
    try:
        stalled_jobs = check_for_stalled_jobs()
        return {
            "success": True,
            "stalled_jobs": stalled_jobs,
            "count": len(stalled_jobs)
        }
    except Exception as e:
        logger.error(f"Error running job monitor: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Run the job monitor
    result = run_job_monitor()
    print(json.dumps(result, indent=2))
