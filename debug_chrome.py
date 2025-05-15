#!/usr/bin/env python3
"""
Debug script to check Chrome and ChromeDriver installation.
This script can be run directly to test Chrome and ChromeDriver.
"""

import os
import sys
import logging
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("debug_chrome")

def get_chrome_path() -> Optional[str]:
    """
    Get the path to the Chrome binary.
    
    Returns:
        str or None: Path to Chrome binary if found, None otherwise
    """
    # Check environment variable first
    chrome_path = os.environ.get("CHROME_PATH")
    if chrome_path and os.path.exists(chrome_path):
        logger.info(f"Using Chrome path from environment variable: {chrome_path}")
        return chrome_path
    
    # Common Chrome paths
    chrome_paths = [
        # Linux paths
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        # Render-specific paths
        "/opt/render/chrome/chrome",
        "/opt/google/chrome/chrome",
        # macOS paths
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        # Windows paths
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    # Check if Chrome is in PATH
    chrome_in_path = shutil.which("google-chrome-stable") or shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("chromium")
    if chrome_in_path:
        logger.info(f"Found Chrome in PATH: {chrome_in_path}")
        return chrome_in_path
    
    # Check common locations
    for path in chrome_paths:
        if os.path.exists(path):
            logger.info(f"Found Chrome at: {path}")
            return path
    
    logger.warning("Chrome binary not found in any standard location")
    return None

def get_chromedriver_path() -> Optional[str]:
    """
    Get the path to the ChromeDriver binary.
    
    Returns:
        str or None: Path to ChromeDriver binary if found, None otherwise
    """
    # Check environment variable first
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    if chromedriver_path and os.path.exists(chromedriver_path):
        logger.info(f"Using ChromeDriver path from environment variable: {chromedriver_path}")
        return chromedriver_path
    
    # Check if ChromeDriver is in PATH
    chromedriver_in_path = shutil.which("chromedriver")
    if chromedriver_in_path:
        logger.info(f"Found ChromeDriver in PATH: {chromedriver_in_path}")
        return chromedriver_in_path
    
    logger.warning("ChromeDriver binary not found")
    return None

def test_chrome_version(chrome_path: str) -> Dict[str, Any]:
    """
    Test Chrome version.
    
    Args:
        chrome_path: Path to Chrome binary
        
    Returns:
        dict: Test results
    """
    logger.info(f"Testing Chrome version using: {chrome_path}")
    
    try:
        result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"Chrome version: {version}")
            return {
                "success": True,
                "version": version,
                "error": None
            }
        else:
            logger.error(f"Error getting Chrome version: {result.stderr}")
            return {
                "success": False,
                "version": None,
                "error": result.stderr
            }
    except Exception as e:
        logger.error(f"Exception getting Chrome version: {e}")
        return {
            "success": False,
            "version": None,
            "error": str(e)
        }

def test_chromedriver_version(chromedriver_path: str) -> Dict[str, Any]:
    """
    Test ChromeDriver version.
    
    Args:
        chromedriver_path: Path to ChromeDriver binary
        
    Returns:
        dict: Test results
    """
    logger.info(f"Testing ChromeDriver version using: {chromedriver_path}")
    
    try:
        result = subprocess.run([chromedriver_path, "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"ChromeDriver version: {version}")
            return {
                "success": True,
                "version": version,
                "error": None
            }
        else:
            logger.error(f"Error getting ChromeDriver version: {result.stderr}")
            return {
                "success": False,
                "version": None,
                "error": result.stderr
            }
    except Exception as e:
        logger.error(f"Exception getting ChromeDriver version: {e}")
        return {
            "success": False,
            "version": None,
            "error": str(e)
        }

def run_debug_tests() -> Dict[str, Any]:
    """
    Run all debug tests.
    
    Returns:
        dict: Test results
    """
    logger.info("Running Chrome debug tests")
    
    results = {
        "chrome": {
            "found": False,
            "path": None,
            "version_test": None
        },
        "chromedriver": {
            "found": False,
            "path": None,
            "version_test": None
        },
        "environment": {
            "CHROME_PATH": os.environ.get("CHROME_PATH"),
            "CHROMEDRIVER_PATH": os.environ.get("CHROMEDRIVER_PATH"),
            "PATH": os.environ.get("PATH")
        }
    }
    
    # Test Chrome
    chrome_path = get_chrome_path()
    if chrome_path:
        results["chrome"]["found"] = True
        results["chrome"]["path"] = chrome_path
        results["chrome"]["version_test"] = test_chrome_version(chrome_path)
    
    # Test ChromeDriver
    chromedriver_path = get_chromedriver_path()
    if chromedriver_path:
        results["chromedriver"]["found"] = True
        results["chromedriver"]["path"] = chromedriver_path
        results["chromedriver"]["version_test"] = test_chromedriver_version(chromedriver_path)
    
    return results

if __name__ == "__main__":
    # Run the debug tests
    results = run_debug_tests()
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    chrome_success = results["chrome"]["found"] and (results["chrome"]["version_test"] or {}).get("success", False)
    chromedriver_success = results["chromedriver"]["found"] and (results["chromedriver"]["version_test"] or {}).get("success", False)
    
    if chrome_success and chromedriver_success:
        print("SUCCESS: Chrome and ChromeDriver are working correctly")
        sys.exit(0)
    elif chrome_success:
        print("PARTIAL SUCCESS: Chrome is working but ChromeDriver is not")
        sys.exit(1)
    elif chromedriver_success:
        print("PARTIAL SUCCESS: ChromeDriver is working but Chrome is not")
        sys.exit(1)
    else:
        print("FAILURE: Neither Chrome nor ChromeDriver are working")
        sys.exit(2)
