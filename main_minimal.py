from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
from datetime import datetime

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

@app.get("/")
def read_root():
    return {"message": "College Portal Scraper API"}

@app.get("/health")
def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/scrape")
async def scrape_data():
    """
    Simulate scraping data from college portal
    """
    # Generate a unique job ID
    job_id = f"job_{int(time.time())}"

    return {
        "status": "queued",
        "message": "Scraping job started (simulated)",
        "job_id": job_id
    }

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a scraping job (simulated)
    """
    return {
        "status": "completed",
        "message": "Scraping completed successfully (simulated)",
        "progress": 1.0,
        "details": {
            "results": {
                "attendance": {"success": True, "message": "Simulated attendance scraping"},
                "mid_marks": {"success": True, "message": "Simulated mid marks scraping"},
                "personal_details": {"success": True, "message": "Simulated personal details scraping"},
                "upload": {"success": True, "message": "Simulated upload to Supabase"}
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
