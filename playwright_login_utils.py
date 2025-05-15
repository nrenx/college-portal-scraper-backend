#!/usr/bin/env python3
"""
Playwright-based login utilities for the college website scraper.
This module handles authentication to the college portal using Playwright.
"""

import os
import sys
import time
import logging
import asyncio
from typing import Dict, Optional, Tuple, Any, Union
from pathlib import Path

# Import configuration
from config import USERNAME, PASSWORD, ATTENDANCE_PORTAL_URL, MID_MARKS_PORTAL_URL, DEFAULT_SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("playwright_login_utils")

# Portal URLs
BASE_URL = "http://103.203.175.90:94"
LOGIN_URL = ATTENDANCE_PORTAL_URL  # This will redirect to login page if not authenticated
ATTENDANCE_LOGIN_URL = f"{BASE_URL}/attendance/attendanceLogin.php"
MID_MARKS_URL = MID_MARKS_PORTAL_URL

# Check if Playwright is available
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
    logger.info("Playwright is available")
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright is not available. Install with 'pip install playwright' and 'playwright install'")

def is_playwright_available() -> bool:
    """
    Check if Playwright is available.

    Returns:
        bool: True if Playwright is available, False otherwise
    """
    return PLAYWRIGHT_AVAILABLE

def create_browser(headless: bool = True) -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
    """
    Create a Playwright browser instance.

    Args:
        headless: Whether to run in headless mode

    Returns:
        Tuple of (playwright, browser, context) or (None, None, None) if Playwright is not available
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright is not available. Cannot create browser.")
        return None, None, None

    try:
        logger.info("Creating Playwright browser...")
        playwright = sync_playwright().start()

        # Check if browsers are installed
        try:
            # Launch Chromium browser
            browser = playwright.chromium.launch(headless=headless)
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                logger.error("Playwright browsers are not installed. Attempting to install...")
                try:
                    import subprocess
                    import sys

                    # Try to install browsers
                    result = subprocess.run(
                        [sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"],
                        capture_output=True,
                        text=True
                    )

                    if result.returncode == 0:
                        logger.info("Successfully installed Playwright browsers")
                        # Try launching again
                        browser = playwright.chromium.launch(headless=headless)
                    else:
                        logger.error(f"Failed to install Playwright browsers: {result.stderr}")
                        playwright.stop()
                        return None, None, None
                except Exception as install_error:
                    logger.error(f"Error installing Playwright browsers: {install_error}")
                    playwright.stop()
                    return None, None, None
            else:
                logger.error(f"Error launching Playwright browser: {e}")
                playwright.stop()
                return None, None, None

        # Create a new browser context
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        logger.info("Playwright browser created successfully")
        return playwright, browser, context

    except Exception as e:
        logger.error(f"Error creating Playwright browser: {str(e)}")
        return None, None, None

def close_browser(playwright: Any, browser: Any) -> None:
    """
    Close the Playwright browser.

    Args:
        playwright: Playwright instance
        browser: Browser instance
    """
    if browser:
        try:
            browser.close()
            logger.info("Playwright browser closed")
        except Exception as e:
            logger.error(f"Error closing Playwright browser: {str(e)}")

    if playwright:
        try:
            playwright.stop()
            logger.info("Playwright stopped")
        except Exception as e:
            logger.error(f"Error stopping Playwright: {str(e)}")

def playwright_login(context: Any, username: str = USERNAME, password: str = PASSWORD) -> Tuple[bool, str, Optional[Any]]:
    """
    Log in to the college website using Playwright.

    Args:
        context: BrowserContext instance
        username: Login username
        password: Login password

    Returns:
        Tuple of (success status, error message if any, page if successful)
    """
    if not context:
        return False, "Browser context is not available", None

    page = None
    try:
        # Create a new page
        page = context.new_page()

        # Navigate to the login page
        logger.info(f"Navigating to login page: {LOGIN_URL}")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        # Wait for the login form to load
        logger.info("Waiting for login form...")
        page.wait_for_selector('input[name="username"]', state="visible", timeout=10000)

        # Fill in the login form
        logger.info("Filling in login form...")
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)

        # Find and click the submit button
        submit_button = page.locator('input[type="submit"]')
        submit_button.click()

        # Wait for navigation to complete
        page.wait_for_load_state("networkidle")

        # Check if login was successful
        current_url = page.url
        if "login" not in current_url.lower():
            logger.info("Login successful")
            return True, "", page
        else:
            logger.warning("Login failed - incorrect credentials or form fields")
            return False, "Login failed - please check your credentials", page

    except Exception as e:
        error_msg = f"Error during login: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, page

def playwright_login_to_attendance(context: Any, username: str = USERNAME, password: str = PASSWORD) -> Tuple[bool, str, Optional[Any]]:
    """
    Log in to the attendance section of the college website using Playwright.

    Args:
        context: BrowserContext instance
        username: Login username
        password: Login password

    Returns:
        Tuple of (success status, error message if any, page if successful)
    """
    if not context:
        return False, "Browser context is not available", None

    page = None
    try:
        # Create a new page
        page = context.new_page()

        # Navigate to the attendance login page
        logger.info(f"Navigating to attendance login page: {ATTENDANCE_LOGIN_URL}")
        page.goto(ATTENDANCE_LOGIN_URL, wait_until="domcontentloaded")

        # Wait for the login form to load
        logger.info("Waiting for attendance login form...")
        page.wait_for_selector('input[name="username"]', state="visible", timeout=10000)

        # Fill in the login form
        logger.info("Filling in attendance login form...")
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)

        # Find and click the submit button
        submit_button = page.locator('input[type="submit"]')
        submit_button.click()

        # Wait for navigation to complete
        page.wait_for_load_state("networkidle")

        # Check if login was successful
        current_url = page.url
        if "login" not in current_url.lower():
            logger.info("Attendance login successful")
            return True, "", page
        else:
            logger.warning("Attendance login failed - incorrect credentials or form fields")
            return False, "Attendance login failed - please check your credentials", page

    except Exception as e:
        error_msg = f"Error during attendance login: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, page

def is_playwright_logged_in(page: Any) -> bool:
    """
    Check if the Playwright page is logged in.

    Args:
        page: Playwright Page instance

    Returns:
        Boolean indicating login status
    """
    if not page:
        return False

    try:
        # Try to access a page that requires authentication
        page.goto(ATTENDANCE_PORTAL_URL, wait_until="domcontentloaded")

        # Wait briefly for the page to load
        page.wait_for_load_state("networkidle")

        # Check if we're redirected to the login page
        current_url = page.url
        if "login" in current_url.lower():
            return False

        # Check for indicators of being logged in
        return True

    except Exception as e:
        logger.error(f"Error checking login status: {str(e)}")
        return False

# Simple test function to verify Playwright is working
def test_playwright():
    """Test Playwright functionality"""
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright is not available. Cannot run test.")
        return False

    playwright, browser, context = None, None, None
    try:
        playwright, browser, context = create_browser(headless=True)
        if not browser or not context:
            logger.error("Failed to create browser or context")
            return False

        page = context.new_page()
        page.goto("https://example.com")
        title = page.title()
        logger.info(f"Page title: {title}")

        return title == "Example Domain"

    except Exception as e:
        logger.error(f"Error testing Playwright: {str(e)}")
        return False

    finally:
        if browser:
            browser.close()
        if playwright:
            playwright.stop()

if __name__ == "__main__":
    # Test Playwright functionality
    if test_playwright():
        print("Playwright test successful")
    else:
        print("Playwright test failed")
