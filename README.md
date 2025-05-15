# College Portal Scraper API

This is the backend API for the College Portal Scraper application. It provides endpoints for scraping college portal data and uploading it to Supabase.

## Features

- Scrape attendance data
- Scrape mid marks data
- Scrape personal details
- Upload data to Supabase
- Background job processing
- Job status tracking

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example` and fill in your credentials
4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### GET /

Returns a simple message to confirm the API is running.

### GET /health

Health check endpoint for monitoring. Returns a status and timestamp.

### POST /scrape

Starts a scraping job with the specified parameters.

**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password",
  "academic_year": "2022-23",
  "scrape_attendance": true,
  "scrape_mid_marks": true,
  "scrape_personal_details": true,
  "upload_to_supabase": true
}
```

**Response:**
```json
{
  "status": "queued",
  "message": "Scraping job started",
  "job_id": "job_1234567890_abcd"
}
```

### GET /job/{job_id}

Returns the status of a scraping job.

**Response:**
```json
{
  "status": "running",
  "message": "Scraping in progress",
  "progress": 0.5,
  "details": {
    "username": "your_username",
    "academic_year": "2022-23",
    "scrape_attendance": true,
    "scrape_mid_marks": true,
    "scrape_personal_details": true,
    "upload_to_supabase": true
  }
}
```

## Deployment

### Render.com with Docker

This repository includes a `render.yaml` file and `Dockerfile` for automatic deployment to Render.com using Docker.

1. Push this backend folder to a GitHub repository
2. In Render.com, click "New" and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file and set up the service as a Docker container
5. Add the following environment variables:
   - `API_USERNAME`: Your API username
   - `API_PASSWORD`: Your API password
   - `SUPABASE_URL`: Your Supabase URL
   - `SUPABASE_KEY`: Your Supabase key
6. Deploy

Alternatively, you can manually set up a Web Service:

1. Create a new Web Service
2. Connect your GitHub repository
3. Select "Docker" as the environment
4. Set the following:
   - Docker Build Context: `.`
   - Dockerfile Path: `./Dockerfile`
5. Add environment variables from your `.env` file
6. Deploy

### Local Development with Docker

To run the application locally using Docker:

1. Make sure Docker and Docker Compose are installed on your machine
2. Create a `.env` file with your environment variables
3. Run the following command:
   ```bash
   docker-compose up --build
   ```
4. The API will be available at http://localhost:8000

### Environment Variables

Make sure to set the following environment variables in your deployment:

- `API_USERNAME`: Username for API authentication
- `API_PASSWORD`: Password for API authentication
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase service role key
- `SUPABASE_BUCKET`: Supabase storage bucket name (default: "demo-usingfastapi")
