#!/usr/bin/env python3
"""
Minimal Chrome setup script for Render deployment.
This script sets up the environment for Chrome and Playwright without unnecessary overhead.
It also installs ChromeDriver for Selenium compatibility.
"""

import os
import sys
import logging
import subprocess
import shutil
import tempfile
import zipfile
import requests
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

# Set ChromeDriver path
CHROMEDRIVER_PATH = os.path.join(PLAYWRIGHT_BROWSERS_PATH, "chromedriver")
os.environ["CHROMEDRIVER_PATH"] = CHROMEDRIVER_PATH
logger.info(f"Setting CHROMEDRIVER_PATH to {CHROMEDRIVER_PATH}")

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

def install_chromedriver():
    """Install ChromeDriver for Selenium compatibility."""
    try:
        logger.info("Installing ChromeDriver...")

        # Use webdriver-manager to install ChromeDriver
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType

        # Install ChromeDriver
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver installed at: {driver_path}")

        # Copy ChromeDriver to our browsers directory
        shutil.copy(driver_path, CHROMEDRIVER_PATH)
        os.chmod(CHROMEDRIVER_PATH, 0o755)  # Make executable
        logger.info(f"ChromeDriver copied to: {CHROMEDRIVER_PATH}")

        # Create a symlink to Chrome from Playwright's Chromium
        chrome_path = os.path.join(PLAYWRIGHT_BROWSERS_PATH, "chrome")
        chromium_path = None

        # Find Chromium executable in Playwright directory
        for root, dirs, files in os.walk(PLAYWRIGHT_BROWSERS_PATH):
            for file in files:
                if file == "chrome" or file == "chromium":
                    chromium_path = os.path.join(root, file)
                    break
            if chromium_path:
                break

        if chromium_path:
            # Create symlink if not exists
            if not os.path.exists(chrome_path):
                os.symlink(chromium_path, chrome_path)
                logger.info(f"Created symlink from {chromium_path} to {chrome_path}")

            # Set environment variable
            os.environ["CHROME_PATH"] = chrome_path
            logger.info(f"Set CHROME_PATH to {chrome_path}")
        else:
            logger.warning("Could not find Chromium executable in Playwright directory")

        return True
    except Exception as e:
        logger.error(f"Error installing ChromeDriver: {e}")
        return False

def main():
    """Main function."""
    logger.info("Starting Chrome and ChromeDriver setup...")

    # Create browsers directory
    create_browsers_directory()

    # Install Playwright browsers
    install_playwright_browsers()

    # Install ChromeDriver
    install_chromedriver()

    logger.info("Chrome and ChromeDriver setup completed")

if __name__ == "__main__":
    main()
