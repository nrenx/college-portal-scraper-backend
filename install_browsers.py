#!/usr/bin/env python3
"""
Script to install Playwright browsers at runtime.
This script is used to install Playwright browsers when the application starts.
"""

import os
import sys
import logging
import subprocess
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("install_browsers")

def set_browsers_path():
    """Set the Playwright browsers path environment variable."""
    # Set Playwright browsers path if not already set
    playwright_browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not playwright_browsers_path:
        playwright_browsers_path = "/opt/render/project/browsers"
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = playwright_browsers_path
        logger.info(f"Setting PLAYWRIGHT_BROWSERS_PATH to {playwright_browsers_path}")
    else:
        logger.info(f"Using existing PLAYWRIGHT_BROWSERS_PATH: {playwright_browsers_path}")
    
    return playwright_browsers_path

def create_browsers_directory(path):
    """Create the browsers directory if it doesn't exist."""
    try:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Created browsers directory at {path}")
        
        # Make sure the directory is writable
        os.chmod(path, 0o777)
        logger.info(f"Set permissions on {path}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating browsers directory: {e}")
        return False

def install_browsers():
    """Install Playwright browsers."""
    try:
        logger.info("Installing Playwright browsers...")
        
        # Run the playwright install command
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"],
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

def verify_installation(browsers_path):
    """Verify that the browsers were installed correctly."""
    try:
        logger.info(f"Verifying installation in {browsers_path}...")
        
        # Check if the browsers directory exists
        if not os.path.exists(browsers_path):
            logger.error(f"Browsers directory {browsers_path} does not exist")
            return False
        
        # List the contents of the browsers directory
        contents = os.listdir(browsers_path)
        logger.info(f"Contents of {browsers_path}: {contents}")
        
        # Check if there are any browser directories
        if not contents:
            logger.error(f"No browsers found in {browsers_path}")
            return False
        
        # Try to launch a browser
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                browser.close()
                logger.info("Successfully launched Chromium")
                return True
        except Exception as e:
            logger.error(f"Error launching browser: {e}")
            return False
    except Exception as e:
        logger.error(f"Error verifying installation: {e}")
        return False

def run_installation():
    """Run the browser installation process."""
    logger.info("Starting Playwright browsers installation...")
    
    # Set the browsers path
    browsers_path = set_browsers_path()
    
    # Create the browsers directory
    if not create_browsers_directory(browsers_path):
        logger.error("Failed to create browsers directory")
        return False
    
    # Install the browsers
    if not install_browsers():
        logger.error("Failed to install browsers")
        return False
    
    # Verify the installation
    if not verify_installation(browsers_path):
        logger.error("Failed to verify installation")
        return False
    
    logger.info("Playwright browsers installation completed successfully")
    return True

if __name__ == "__main__":
    # Run the installation
    success = run_installation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
