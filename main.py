from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, validator
import os
import sys
import logging
import re
from typing import Dict, Any, List, Optional
import secrets
import time
from datetime import datetime

# Set Playwright browsers path if not already set
PLAYWRIGHT_BROWSERS_PATH = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
if not PLAYWRIGHT_BROWSERS_PATH:
    PLAYWRIGHT_BROWSERS_PATH = "/opt/render/project/browsers"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = PLAYWRIGHT_BROWSERS_PATH
    print(f"Setting PLAYWRIGHT_BROWSERS_PATH to {PLAYWRIGHT_BROWSERS_PATH}")
else:
    print(f"Using existing PLAYWRIGHT_BROWSERS_PATH: {PLAYWRIGHT_BROWSERS_PATH}")

# Set Playwright browsers path without running tests
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/render/project/browsers")

# Run minimal Chrome setup
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("chrome_setup_minimal", "chrome_setup_minimal.py")
    chrome_setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chrome_setup)
    chrome_setup.main()
except Exception as e:
    print(f"Error running Chrome setup: {e}")

# Import job storage module
from job_storage import save_job, load_job, list_jobs

# Import job monitor module
from job_monitor import check_for_stalled_jobs

# System check module removed to streamline application

# Add parent directory to path to import scraper modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import scraper modules
from scraper_wrapper import run_scraper, run_uploader

# Import custom logging configuration
from logging_config import configure_logging, get_logger, get_recent_error_logs, get_recent_supabase_logs

# Configure logging with more detailed settings
configure_logging(console_level=logging.INFO, file_level=logging.DEBUG, enable_json=True)

# Get a logger with extra context
logger = get_logger("api", {"component": "api_server"})

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="College Portal Scraper API",
    description="API for scraping college portal data and uploading to Supabase",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nrenx.github.io",  # GitHub Pages domain
        "http://localhost:3000",    # Local development
        "*"                         # Allow all origins for testing
    ],
    allow_credentials=False,  # Changed to False since we're using Basic Auth
    allow_methods=["*"],      # Allow all methods
    allow_headers=["*"],      # Allow all headers
    expose_headers=["*"]      # Expose all headers
)

# Basic authentication
security = HTTPBasic()

# Define request models
class ScrapeRequest(BaseModel):
    username: str
    password: str
    academic_year: str
    scrape_attendance: bool = True
    scrape_mid_marks: bool = True
    scrape_personal_details: bool = True
    upload_to_supabase: bool = True
    force_update: bool = False

    @validator('username')
    def username_must_not_be_default(cls, v):
        if v == "string" or not v.strip():
            raise ValueError('username must not be the default value "string" or empty')
        return v

    @validator('password')
    def password_must_not_be_default(cls, v):
        if v == "string" or not v.strip():
            raise ValueError('password must not be the default value "string" or empty')
        return v

    @validator('academic_year')
    def academic_year_must_be_valid(cls, v):
        if v == "string" or not v.strip():
            raise ValueError('academic_year must not be the default value "string" or empty')
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError('academic_year must be in the format "YYYY-YY" (e.g., "2022-23")')
        return v

# Define response models
class ScrapeResponse(BaseModel):
    status: str
    message: str
    job_id: str
    file_urls: Optional[List[str]] = None

class JobStatusResponse(BaseModel):
    status: str
    message: str
    progress: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

# Store job status
job_status = {}

# Load any saved jobs from storage
try:
    saved_jobs = list_jobs()
    if saved_jobs:
        logger.info(f"Loaded {len(saved_jobs)} saved jobs from storage")
        job_status.update(saved_jobs)
except Exception as e:
    logger.error(f"Error loading saved jobs: {str(e)}")

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Validate API credentials"""
    correct_username = os.getenv("API_USERNAME", "admin")
    correct_password = os.getenv("API_PASSWORD", "password")

    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "College Portal Scraper API"}

@app.get("/health")
def health_check():
    """Health check endpoint for Render"""
    logger.info("Health check endpoint accessed")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.options("/cors-test")
def cors_test_preflight():
    """Test endpoint for CORS preflight requests"""
    logger.info("CORS preflight test endpoint accessed")
    return {}

@app.get("/cors-test")
def cors_test():
    """Test endpoint for CORS"""
    logger.info("CORS test endpoint accessed")
    return {
        "status": "success",
        "message": "CORS is working correctly",
        "timestamp": datetime.now().isoformat()
    }

# Debug endpoint removed to streamline application

# Debug endpoint removed to streamline application

# Debug endpoint removed to streamline application

# Debug endpoint removed to streamline application

# Debug endpoint removed to streamline application

# Debug endpoint removed to streamline application

# Debug endpoint removed to streamline application

# Debug endpoint removed to streamline application

# Debug endpoint removed to streamline application

# Debug endpoint removed to streamline application

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_data(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    username: str = Depends(get_current_username)
):
    """
    Scrape data from college portal and optionally upload to Supabase
    """
    logger.info(f"Scrape endpoint accessed by {username}")
    logger.info(f"Request data: username={request.username}, academic_year={request.academic_year}, "
                f"scrape_attendance={request.scrape_attendance}, scrape_mid_marks={request.scrape_mid_marks}, "
                f"scrape_personal_details={request.scrape_personal_details}, upload_to_supabase={request.upload_to_supabase}")

    # Generate a unique job ID
    job_id = f"job_{int(time.time())}_{secrets.token_hex(4)}"
    logger.info(f"Generated job ID: {job_id}")

    # Initialize job status
    job_status[job_id] = {
        "status": "queued",
        "message": "Job queued for processing",
        "start_time": datetime.now().isoformat(),
        "progress": 0.0,
        "details": {
            "username": request.username,
            "academic_year": request.academic_year,
            "scrape_attendance": request.scrape_attendance,
            "scrape_mid_marks": request.scrape_mid_marks,
            "scrape_personal_details": request.scrape_personal_details,
            "upload_to_supabase": request.upload_to_supabase,
            "force_update": request.force_update
        }
    }

    # Save job to persistent storage
    save_job(job_id, job_status[job_id])

    # Add job to background tasks
    background_tasks.add_task(
        process_scrape_job,
        job_id,
        request.username,
        request.password,
        request.academic_year,
        request.scrape_attendance,
        request.scrape_mid_marks,
        request.scrape_personal_details,
        request.upload_to_supabase,
        request.force_update
    )

    logger.info(f"Job {job_id} queued for processing")

    return {
        "status": "queued",
        "message": "Scraping job started",
        "job_id": job_id
    }

@app.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, username: str = Depends(get_current_username)):
    """
    Get the status of a scraping job
    """
    logger.info(f"Job status endpoint accessed for job_id={job_id} by {username}")

    # Check for stalled jobs before returning status
    # This ensures we don't keep showing "running" for jobs that have stalled
    try:
        stalled_jobs = check_for_stalled_jobs()
        if stalled_jobs:
            logger.info(f"Found and marked {len(stalled_jobs)} stalled jobs")
    except Exception as e:
        logger.error(f"Error checking for stalled jobs: {str(e)}")

    # Check if job is in memory
    if job_id not in job_status:
        # Try to load from persistent storage
        logger.info(f"Job {job_id} not found in memory, trying to load from storage")
        stored_job = load_job(job_id)

        if stored_job:
            # Add to in-memory cache
            job_status[job_id] = stored_job
            logger.info(f"Loaded job {job_id} from storage")
        else:
            logger.warning(f"Job {job_id} not found in storage")
            # Log all available job IDs for debugging
            available_jobs = list(job_status.keys())
            logger.info(f"Available job IDs in memory: {available_jobs}")
            raise HTTPException(status_code=404, detail="Job not found")

    logger.info(f"Returning status for job {job_id}: {job_status[job_id]['status']}")
    return job_status[job_id]

async def process_scrape_job(
    job_id: str,
    username: str,
    password: str,
    academic_year: str,
    scrape_attendance: bool,
    scrape_mid_marks: bool,
    scrape_personal_details: bool,
    upload_to_supabase: bool,
    force_update: bool = False
):
    """
    Process a scraping job in the background
    """
    # Initialize job status if it doesn't exist (in case of worker restart)
    if job_id not in job_status:
        job_status[job_id] = {
            "status": "queued",
            "message": "Job queued for processing",
            "start_time": datetime.now().isoformat(),
            "progress": 0.0,
            "details": {
                "username": username,
                "academic_year": academic_year,
                "scrape_attendance": scrape_attendance,
                "scrape_mid_marks": scrape_mid_marks,
                "scrape_personal_details": scrape_personal_details,
                "upload_to_supabase": upload_to_supabase,
                "force_update": force_update
            }
        }
    try:
        # Update job status
        job_status[job_id]["status"] = "running"
        job_status[job_id]["message"] = "Scraping in progress"

        # Save updated status to storage
        save_job(job_id, job_status[job_id])

        # Run scrapers
        scrape_results = {}

        if scrape_attendance:
            job_status[job_id]["message"] = "Scraping attendance data"
            job_status[job_id]["progress"] = 0.1
            attendance_result = run_scraper(
                "attendance",
                username,
                password,
                academic_year,
                workers=1,  # Reduced to 1 worker to minimize resource usage on Render
                worker_mode="thread"
            )
            scrape_results["attendance"] = attendance_result
            job_status[job_id]["progress"] = 0.3

            # Check if scraper failed due to authentication error or any other error
            if not attendance_result["success"]:
                error_message = attendance_result.get("stderr", "") or ""
                stdout_message = attendance_result.get("stdout", "") or ""

                # Check for various authentication failure indicators
                if ("Login failed" in error_message or "Authentication failed" in error_message or
                    "Invalid credentials" in error_message or "Login failed" in stdout_message or
                    "Authentication failed" in stdout_message or "exit status 1" in error_message):
                    job_status[job_id]["status"] = "failed"
                    job_status[job_id]["message"] = "Authentication failed: Invalid username or password"
                    job_status[job_id]["details"]["results"] = scrape_results
                    job_status[job_id]["end_time"] = datetime.now().isoformat()
                    return

                # Stop processing if any scraper fails
                job_status[job_id]["status"] = "failed"
                job_status[job_id]["message"] = "Attendance scraper failed. Please check credentials and try again."
                job_status[job_id]["details"]["results"] = scrape_results
                job_status[job_id]["end_time"] = datetime.now().isoformat()
                return

        if scrape_mid_marks:
            job_status[job_id]["message"] = "Scraping mid marks data"
            mid_marks_result = run_scraper(
                "mid_marks",
                username,
                password,
                academic_year,
                workers=1,  # Reduced to 1 worker to minimize resource usage on Render
                worker_mode="thread"
            )
            scrape_results["mid_marks"] = mid_marks_result
            job_status[job_id]["progress"] = 0.5

            # Check if scraper failed due to authentication error or any other error
            if not mid_marks_result["success"]:
                error_message = mid_marks_result.get("stderr", "") or ""
                stdout_message = mid_marks_result.get("stdout", "") or ""

                # Check for various authentication failure indicators
                if ("Login failed" in error_message or "Authentication failed" in error_message or
                    "Invalid credentials" in error_message or "Login failed" in stdout_message or
                    "Authentication failed" in stdout_message or "exit status 1" in error_message):
                    job_status[job_id]["status"] = "failed"
                    job_status[job_id]["message"] = "Authentication failed: Invalid username or password"
                    job_status[job_id]["details"]["results"] = scrape_results
                    job_status[job_id]["end_time"] = datetime.now().isoformat()
                    return

                # Stop processing if any scraper fails
                job_status[job_id]["status"] = "failed"
                job_status[job_id]["message"] = "Mid marks scraper failed. Please check credentials and try again."
                job_status[job_id]["details"]["results"] = scrape_results
                job_status[job_id]["end_time"] = datetime.now().isoformat()
                return

        if scrape_personal_details:
            job_status[job_id]["message"] = "Scraping personal details"
            personal_details_result = run_scraper(
                "personal_details",
                username,
                password,
                academic_year,
                workers=1,  # Reduced to 1 worker to minimize resource usage on Render
                worker_mode="thread"
            )
            scrape_results["personal_details"] = personal_details_result
            job_status[job_id]["progress"] = 0.7

            # Check if scraper failed due to authentication error or any other error
            if not personal_details_result["success"]:
                error_message = personal_details_result.get("stderr", "") or ""
                stdout_message = personal_details_result.get("stdout", "") or ""

                # Check for various authentication failure indicators
                if ("Login failed" in error_message or "Authentication failed" in error_message or
                    "Invalid credentials" in error_message or "Login failed" in stdout_message or
                    "Authentication failed" in stdout_message or "exit status 1" in error_message):
                    job_status[job_id]["status"] = "failed"
                    job_status[job_id]["message"] = "Authentication failed: Invalid username or password"
                    job_status[job_id]["details"]["results"] = scrape_results
                    job_status[job_id]["end_time"] = datetime.now().isoformat()
                    return

                # Stop processing if any scraper fails
                job_status[job_id]["status"] = "failed"
                job_status[job_id]["message"] = "Personal details scraper failed. Please check credentials and try again."
                job_status[job_id]["details"]["results"] = scrape_results
                job_status[job_id]["end_time"] = datetime.now().isoformat()
                return

        # Upload to Supabase if requested and at least one scraper was successful
        if upload_to_supabase and any(result.get("success", False) for result in scrape_results.values()):
            job_status[job_id]["message"] = "Uploading data to Supabase"
            upload_result = run_uploader(force_update=force_update)
            scrape_results["upload"] = upload_result
            job_status[job_id]["progress"] = 0.9
        elif upload_to_supabase:
            # Skip upload if all scrapers failed
            job_status[job_id]["message"] = "Skipping upload as all scrapers failed"
            scrape_results["upload"] = {
                "success": False,
                "message": "Upload skipped because all scrapers failed"
            }
            job_status[job_id]["progress"] = 0.9

        # Update job status based on scraper results
        job_status[job_id]["progress"] = 1.0
        job_status[job_id]["details"]["results"] = scrape_results
        job_status[job_id]["end_time"] = datetime.now().isoformat()

        # Check for authentication failures
        auth_failure = False
        for result in scrape_results.values():
            if not result.get("success", False) and "Authentication failed" in result.get("message", ""):
                auth_failure = True
                break

        if auth_failure:
            # Special handling for authentication failures
            job_status[job_id]["status"] = "failed"
            job_status[job_id]["message"] = "Authentication failed. Please check your credentials."
            logger.warning(f"Job {job_id} failed due to authentication error")
        # Check if any scraper was successful
        elif any(result.get("success", False) for result in scrape_results.values()):
            job_status[job_id]["status"] = "completed"

            # Count successful and failed scrapers
            successful_scrapers = sum(1 for result in scrape_results.values() if result.get("success", False))
            total_scrapers = len(scrape_results)

            if successful_scrapers == total_scrapers:
                job_status[job_id]["message"] = "All scraping tasks completed successfully"
            else:
                job_status[job_id]["message"] = f"{successful_scrapers} of {total_scrapers} scraping tasks completed successfully"
        else:
            job_status[job_id]["status"] = "failed"
            job_status[job_id]["message"] = "All scraping tasks failed"

        # Save final job status to storage
        save_job(job_id, job_status[job_id])

    except Exception as e:
        import traceback
        error_message = f"Error processing job {job_id}: {str(e)}"
        logger.error(error_message)

        # Get the full traceback for debugging
        tb = traceback.format_exc()
        logger.error(f"Traceback:\n{tb}")

        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = f"Error: {str(e)}"
        job_status[job_id]["end_time"] = datetime.now().isoformat()

        # Save error status to storage
        save_job(job_id, job_status[job_id])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
