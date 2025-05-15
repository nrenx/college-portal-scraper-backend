#!/usr/bin/env python3
"""
Simple browser test script for Playwright.
This script attempts to launch a browser without requiring root privileges.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("simple_browser_test")

# Set Playwright browsers path if not already set
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

def test_browser():
    """Test launching a browser."""
    try:
        logger.info("Importing Playwright...")
        from playwright.sync_api import sync_playwright
        
        logger.info("Creating browsers directory...")
        create_browsers_directory()
        
        logger.info("Starting Playwright...")
        with sync_playwright() as p:
            logger.info("Launching browser...")
            try:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--no-first-run",
                        "--no-zygote",
                        "--single-process",
                        "--disable-gpu"
                    ]
                )
                
                logger.info("Creating page...")
                page = browser.new_page()
                
                logger.info("Navigating to example.com...")
                page.goto("https://example.com")
                
                logger.info(f"Page title: {page.title()}")
                
                logger.info("Taking screenshot...")
                screenshot_path = "browser_test_screenshot.png"
                page.screenshot(path=screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
                
                logger.info("Closing browser...")
                browser.close()
                
                return {
                    "success": True,
                    "title": page.title(),
                    "screenshot": screenshot_path
                }
            except Exception as e:
                logger.error(f"Error launching browser: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
    except ImportError:
        logger.error("Playwright not installed")
        return {
            "success": False,
            "error": "Playwright not installed"
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    logger.info("Starting simple browser test...")
    result = test_browser()
    
    if result["success"]:
        logger.info("Browser test successful!")
        logger.info(f"Page title: {result['title']}")
        logger.info(f"Screenshot saved to: {result['screenshot']}")
        sys.exit(0)
    else:
        logger.error(f"Browser test failed: {result['error']}")
        sys.exit(1)
