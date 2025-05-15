#!/bin/bash
# Setup Chrome and Playwright for Render deployment

echo "Setting up Chrome and Playwright for Render deployment..."

# Create necessary directories
mkdir -p /opt/render/project/browsers
chmod -R 777 /opt/render/project/browsers
mkdir -p logs
mkdir -p job_storage
mkdir -p student_details

# Install Playwright browsers
python -m playwright install chromium

echo "Chrome and Playwright setup completed successfully!"
