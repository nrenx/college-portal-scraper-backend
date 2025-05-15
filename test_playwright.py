#!/usr/bin/env python3
"""
Test script for Playwright.
This script tests if Playwright is working correctly.
"""

import os
import sys
import logging
import json
from pathlib import Path

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
                "chromium_error": chromium_error
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
