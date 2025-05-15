#!/usr/bin/env python3
"""
Minimal Chrome setup script for Render deployment.
This script sets up the environment for Chrome and Playwright without unnecessary overhead.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("chrome_setup")

# Set Playwright browsers path
PLAYWRIGHT_BROWSERS_PATH = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
if not PLAYWRIGHT_BROWSERS_PATH:
    PLAYWRIGHT_BROWSERS_PATH = "/opt/render/project/browsers"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = PLAYWRIGHT_BROWSERS_PATH
    logger.info(f"Setting PLAYWRIGHT_BROWSERS_PATH to {PLAYWRIGHT_BROWSERS_PATH}")
else:
    logger.info(f"Using existing PLAYWRIGHT_BROWSERS_PATH: {PLAYWRIGHT_BROWSERS_PATH}")

def create_browsers_directory():
    """Create the browsers directory if it doesn't exist."""
    try:
        os.makedirs(PLAYWRIGHT_BROWSERS_PATH, exist_ok=True)
        logger.info(f"Created browsers directory at {PLAYWRIGHT_BROWSERS_PATH}")
        
        # Make sure the directory is writable
        os.chmod(PLAYWRIGHT_BROWSERS_PATH, 0o777)
        logger.info(f"Set permissions on {PLAYWRIGHT_BROWSERS_PATH}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating browsers directory: {e}")
        return False

def install_playwright_browsers():
    """Install Playwright browsers."""
    try:
        logger.info("Installing Playwright browsers...")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("Successfully installed Playwright browsers")
            logger.info(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"Failed to install Playwright browsers: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error installing Playwright browsers: {e}")
        return False

def main():
    """Main function."""
    logger.info("Starting minimal Chrome setup...")
    
    # Create browsers directory
    create_browsers_directory()
    
    # Install Playwright browsers
    install_playwright_browsers()
    
    logger.info("Chrome setup completed")

if __name__ == "__main__":
    main()
