"""
Chrome configuration module for setting up Chrome and ChromeDriver paths.
"""

import os
import sys
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("chrome_config")

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
    chrome_in_path = shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("chrome")
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

def get_chrome_config() -> Dict[str, Any]:
    """
    Get Chrome configuration.
    
    Returns:
        dict: Chrome configuration
    """
    chrome_path = get_chrome_path()
    chromedriver_path = get_chromedriver_path()
    
    config = {
        "chrome_path": chrome_path,
        "chromedriver_path": chromedriver_path,
        "chrome_found": chrome_path is not None,
        "chromedriver_found": chromedriver_path is not None
    }
    
    # Try to get Chrome version
    if chrome_path:
        try:
            result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                config["chrome_version"] = result.stdout.strip()
        except Exception as e:
            logger.error(f"Error getting Chrome version: {e}")
    
    # Try to get ChromeDriver version
    if chromedriver_path:
        try:
            result = subprocess.run([chromedriver_path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                config["chromedriver_version"] = result.stdout.strip()
        except Exception as e:
            logger.error(f"Error getting ChromeDriver version: {e}")
    
    return config

if __name__ == "__main__":
    # Print Chrome configuration
    config = get_chrome_config()
    import json
    print(json.dumps(config, indent=2))
