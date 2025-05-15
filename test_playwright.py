#!/usr/bin/env python3
"""
Test script for Playwright.
This script tests if Playwright is working correctly.
"""

import os
import sys
import logging
import json
import subprocess
from pathlib import Path

# Set Playwright browsers path if not already set
PLAYWRIGHT_BROWSERS_PATH = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
if not PLAYWRIGHT_BROWSERS_PATH:
    PLAYWRIGHT_BROWSERS_PATH = "/opt/render/project/browsers"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = PLAYWRIGHT_BROWSERS_PATH
    print(f"Setting PLAYWRIGHT_BROWSERS_PATH to {PLAYWRIGHT_BROWSERS_PATH}")
else:
    print(f"Using existing PLAYWRIGHT_BROWSERS_PATH: {PLAYWRIGHT_BROWSERS_PATH}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("test_playwright")

def test_playwright_installation():
    """
    Test if Playwright is installed correctly.

    Returns:
        dict: Test results
    """
    logger.info("Testing Playwright installation...")

    try:
        from playwright.sync_api import sync_playwright
        import subprocess
        import sys

        # Check Playwright version
        try:
            result = subprocess.run([sys.executable, "-m", "playwright", "--version"],
                                   capture_output=True, text=True)
            playwright_version = result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
            logger.info(f"Playwright version: {playwright_version}")
        except Exception as e:
            playwright_version = f"Error getting version: {str(e)}"
            logger.error(f"Error getting Playwright version: {e}")

        # Check installed browsers
        try:
            result = subprocess.run([sys.executable, "-m", "playwright", "install", "--help"],
                                   capture_output=True, text=True)
            install_help = result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
            logger.info(f"Playwright install help available: {len(install_help) > 0}")
        except Exception as e:
            install_help = f"Error getting install help: {str(e)}"
            logger.error(f"Error getting Playwright install help: {e}")

        # Check browser installation paths
        try:
            cache_dir = os.path.expanduser("~/.cache/ms-playwright")
            if not os.path.exists(cache_dir):
                cache_dir = "/opt/render/.cache/ms-playwright"

            browser_paths = []
            if os.path.exists(cache_dir):
                browser_paths = [os.path.join(cache_dir, d) for d in os.listdir(cache_dir)
                               if os.path.isdir(os.path.join(cache_dir, d))]

            logger.info(f"Browser paths: {browser_paths}")
        except Exception as e:
            browser_paths = f"Error getting browser paths: {str(e)}"
            logger.error(f"Error getting browser paths: {e}")

        # Start Playwright
        with sync_playwright() as playwright:
            # Check if browsers are available
            browsers = {
                "chromium": hasattr(playwright, "chromium"),
                "firefox": hasattr(playwright, "firefox"),
                "webkit": hasattr(playwright, "webkit")
            }

            logger.info(f"Playwright browsers: {browsers}")

            # Try to launch Chromium
            chromium_launch_success = False
            chromium_error = None
            if browsers["chromium"]:
                try:
                    browser = playwright.chromium.launch()
                    browser.close()
                    chromium_launch_success = True
                    logger.info("Successfully launched Chromium")
                except Exception as e:
                    chromium_error = str(e)
                    logger.error(f"Error launching Chromium: {e}")

            return {
                "installed": True,
                "browsers": browsers,
                "chromium_launch_success": chromium_launch_success,
                "chromium_error": chromium_error,
                "playwright_version": playwright_version,
                "browser_paths": browser_paths,
                "cache_dir_exists": os.path.exists(cache_dir),
                "cache_dir": cache_dir
            }

    except ImportError:
        logger.error("Playwright is not installed")
        return {
            "installed": False,
            "error": "Playwright is not installed"
        }
    except Exception as e:
        logger.error(f"Error testing Playwright installation: {e}")
        return {
            "installed": True,
            "error": str(e)
        }

def test_playwright_navigation():
    """
    Test if Playwright can navigate to a website.

    Returns:
        dict: Test results
    """
    logger.info("Testing Playwright navigation...")

    try:
        from playwright.sync_api import sync_playwright

        # Start Playwright
        with sync_playwright() as playwright:
            # Launch browser
            browser = playwright.chromium.launch()

            # Create a new page
            page = browser.new_page()

            # Navigate to a website
            page.goto("https://example.com")

            # Get the title
            title = page.title()
            logger.info(f"Page title: {title}")

            # Take a screenshot
            screenshot_path = "playwright_screenshot.png"
            page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")

            # Get the content
            content = page.content()
            content_length = len(content)
            logger.info(f"Page content length: {content_length}")

            # Close the browser
            browser.close()

            return {
                "success": True,
                "title": title,
                "screenshot_path": screenshot_path,
                "content_length": content_length
            }

    except Exception as e:
        logger.error(f"Error testing Playwright navigation: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def run_tests():
    """
    Run all Playwright tests.

    Returns:
        dict: Test results
    """
    logger.info("Running Playwright tests...")

    results = {
        "installation": test_playwright_installation(),
        "navigation": test_playwright_navigation()
    }

    return results

if __name__ == "__main__":
    # Run tests
    results = run_tests()

    # Print results
    print(json.dumps(results, indent=2))

    # Save results to file
    with open("playwright_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Exit with appropriate code
    if (results["installation"].get("installed", False) and
        not results["installation"].get("error") and
        results["navigation"].get("success", False)):
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)
