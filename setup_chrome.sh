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

# Run the Python Chrome setup script
echo "Running Chrome setup script..."
python chrome_setup_minimal.py

# Verify Chrome and ChromeDriver are available
echo "Verifying Chrome and ChromeDriver setup..."
if [ -f "/opt/render/project/browsers/chrome" ]; then
  echo "Chrome is available at /opt/render/project/browsers/chrome"
else
  echo "WARNING: Chrome not found at expected location"
  # Find Chrome in Playwright directory
  find /opt/render/project/browsers -name "chrome*" -type f -executable
fi

if [ -f "/opt/render/project/browsers/chromedriver" ]; then
  echo "ChromeDriver is available at /opt/render/project/browsers/chromedriver"
else
  echo "WARNING: ChromeDriver not found at expected location"
  # Find ChromeDriver in Playwright directory
  find /opt/render/project/browsers -name "chromedriver*" -type f -executable
fi

# Set environment variables
export CHROME_PATH=/opt/render/project/browsers/chrome
export CHROMEDRIVER_PATH=/opt/render/project/browsers/chromedriver

echo "Chrome and Playwright setup completed successfully!"
