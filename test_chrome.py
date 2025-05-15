#!/usr/bin/env python3
"""
Test script to verify Chrome and Selenium are working correctly.
This script attempts to open a browser and navigate to a test page.
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("test_chrome")

# Try to import Chrome configuration
try:
    from chrome_config import get_chrome_path, get_chromedriver_path
except ImportError:
    logger.warning("chrome_config module not found, using default paths")
    
    def get_chrome_path():
        return os.environ.get("CHROME_PATH")
    
    def get_chromedriver_path():
        return os.environ.get("CHROMEDRIVER_PATH")

def test_selenium_basic():
    """
    Test basic Selenium functionality with Chrome.
    
    Returns:
        dict: Test results
    """
    logger.info("Testing basic Selenium functionality with Chrome")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # Get Chrome and ChromeDriver paths
        chrome_path = get_chrome_path()
        chromedriver_path = get_chromedriver_path()
        
        logger.info(f"Using Chrome path: {chrome_path}")
        logger.info(f"Using ChromeDriver path: {chromedriver_path}")
        
        # Configure Chrome options
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if chrome_path:
            options.binary_location = chrome_path
        
        # Create a new Chrome driver
        if chromedriver_path:
            from selenium.webdriver.chrome.service import Service
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        
        logger.info("Chrome driver created successfully")
        
        # Navigate to a test page
        driver.get("https://www.example.com")
        logger.info(f"Page title: {driver.title}")
        
        # Take a screenshot
        screenshot_path = "chrome_test_screenshot.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")
        
        # Get page source
        page_source = driver.page_source
        logger.info(f"Page source length: {len(page_source)} characters")
        
        # Close the driver
        driver.quit()
        logger.info("Chrome driver closed successfully")
        
        return {
            "success": True,
            "page_title": driver.title,
            "screenshot_path": screenshot_path,
            "page_source_length": len(page_source),
            "error": None
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Error testing Selenium: {e}")
        logger.error(traceback.format_exc())
        
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def test_undetected_chromedriver():
    """
    Test undetected-chromedriver functionality.
    
    Returns:
        dict: Test results
    """
    logger.info("Testing undetected-chromedriver functionality")
    
    try:
        import undetected_chromedriver as uc
        
        # Get Chrome path
        chrome_path = get_chrome_path()
        logger.info(f"Using Chrome path: {chrome_path}")
        
        # Configure Chrome options
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if chrome_path:
            options.binary_location = chrome_path
        
        # Create a new Chrome driver
        driver = uc.Chrome(options=options)
        logger.info("Undetected Chrome driver created successfully")
        
        # Navigate to a test page
        driver.get("https://www.example.com")
        logger.info(f"Page title: {driver.title}")
        
        # Take a screenshot
        screenshot_path = "undetected_chrome_test_screenshot.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")
        
        # Get page source
        page_source = driver.page_source
        logger.info(f"Page source length: {len(page_source)} characters")
        
        # Close the driver
        driver.quit()
        logger.info("Undetected Chrome driver closed successfully")
        
        return {
            "success": True,
            "page_title": driver.title,
            "screenshot_path": screenshot_path,
            "page_source_length": len(page_source),
            "error": None
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Error testing undetected-chromedriver: {e}")
        logger.error(traceback.format_exc())
        
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def run_all_tests():
    """
    Run all Chrome tests.
    
    Returns:
        dict: Test results
    """
    logger.info("Running all Chrome tests")
    
    results = {
        "selenium_basic": test_selenium_basic(),
        "undetected_chromedriver": test_undetected_chromedriver(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return results

if __name__ == "__main__":
    # Run all tests
    results = run_all_tests()
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    selenium_success = results["selenium_basic"]["success"]
    undetected_success = results["undetected_chromedriver"]["success"]
    
    if selenium_success and undetected_success:
        print("SUCCESS: Both Selenium and undetected-chromedriver are working correctly")
        sys.exit(0)
    elif selenium_success:
        print("PARTIAL SUCCESS: Selenium is working but undetected-chromedriver is not")
        sys.exit(1)
    elif undetected_success:
        print("PARTIAL SUCCESS: undetected-chromedriver is working but Selenium is not")
        sys.exit(1)
    else:
        print("FAILURE: Neither Selenium nor undetected-chromedriver are working")
        sys.exit(2)
