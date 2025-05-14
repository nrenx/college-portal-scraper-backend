from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, validator
import os
import sys
import logging
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import secrets
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("api")

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
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]  # Expose all headers
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
    return {"message": "College Portal Scraper API"}

@app.get("/health")
def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_data(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    username: str = Depends(get_current_username)
):
    """
    Scrape data from college portal and optionally upload to Supabase
    """
    # Generate a unique job ID
    job_id = f"job_{int(time.time())}_{secrets.token_hex(4)}"

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
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")

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
    try:
        # Update job status
        job_status[job_id]["status"] = "running"
        job_status[job_id]["message"] = "Scraping in progress"
        job_status[job_id]["progress"] = 0.1

        # Simulate scraping (without actually running the scrapers)
        time.sleep(2)  # Simulate work
        
        # Update job status
        job_status[job_id]["status"] = "completed"
        job_status[job_id]["message"] = "Scraping completed successfully (simulated)"
        job_status[job_id]["progress"] = 1.0
        job_status[job_id]["end_time"] = datetime.now().isoformat()
        job_status[job_id]["details"]["results"] = {
            "attendance": {"success": True, "message": "Simulated attendance scraping"},
            "mid_marks": {"success": True, "message": "Simulated mid marks scraping"},
            "personal_details": {"success": True, "message": "Simulated personal details scraping"},
            "upload": {"success": True, "message": "Simulated upload to Supabase"}
        }

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = f"Error: {str(e)}"
        job_status[job_id]["end_time"] = datetime.now().isoformat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
