#!/usr/bin/env python3
"""
Script to download and set up Chromium directly.
This script downloads a pre-built Chromium binary and sets it up for use with Playwright.
"""

import os
import sys
import logging
import subprocess
import tempfile
import shutil
import zipfile
import tarfile
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("download_chromium")

# Set Playwright browsers path
PLAYWRIGHT_BROWSERS_PATH = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
if not PLAYWRIGHT_BROWSERS_PATH:
    PLAYWRIGHT_BROWSERS_PATH = "/opt/render/project/browsers"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = PLAYWRIGHT_BROWSERS_PATH
    logger.info(f"Setting PLAYWRIGHT_BROWSERS_PATH to {PLAYWRIGHT_BROWSERS_PATH}")
else:
    logger.info(f"Using existing PLAYWRIGHT_BROWSERS_PATH: {PLAYWRIGHT_BROWSERS_PATH}")

# Chromium download URLs
CHROMIUM_DOWNLOAD_URLS = {
    "linux": "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1097615/chrome-linux.zip",
    "darwin": "https://storage.googleapis.com/chromium-browser-snapshots/Mac/1097615/chrome-mac.zip",
    "win32": "https://storage.googleapis.com/chromium-browser-snapshots/Win/1097615/chrome-win.zip"
}

def get_platform():
    """Get the current platform."""
    if sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform.startswith("darwin"):
        return "darwin"
    elif sys.platform.startswith("win"):
        return "win32"
    else:
        logger.error(f"Unsupported platform: {sys.platform}")
        return None

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

def download_file(url, dest_path):
    """Download a file from a URL to a destination path."""
    try:
        logger.info(f"Downloading {url} to {dest_path}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded {url} to {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False

def extract_zip(zip_path, extract_path):
    """Extract a zip file to a destination path."""
    try:
        logger.info(f"Extracting {zip_path} to {extract_path}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        
        logger.info(f"Extracted {zip_path} to {extract_path}")
        return True
    except Exception as e:
        logger.error(f"Error extracting {zip_path}: {e}")
        return False

def extract_tar(tar_path, extract_path):
    """Extract a tar file to a destination path."""
    try:
        logger.info(f"Extracting {tar_path} to {extract_path}")
        with tarfile.open(tar_path, "r:*") as tar_ref:
            tar_ref.extractall(extract_path)
        
        logger.info(f"Extracted {tar_path} to {extract_path}")
        return True
    except Exception as e:
        logger.error(f"Error extracting {tar_path}: {e}")
        return False

def download_and_setup_chromium():
    """Download and set up Chromium."""
    try:
        # Create browsers directory
        if not create_browsers_directory():
            return False
        
        # Get platform
        platform = get_platform()
        if not platform:
            return False
        
        # Get download URL
        download_url = CHROMIUM_DOWNLOAD_URLS.get(platform)
        if not download_url:
            logger.error(f"No download URL for platform {platform}")
            return False
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download Chromium
            download_path = os.path.join(temp_dir, "chromium.zip")
            if not download_file(download_url, download_path):
                return False
            
            # Extract Chromium
            extract_path = os.path.join(temp_dir, "chromium")
            if not extract_zip(download_path, extract_path):
                return False
            
            # Set up Chromium in browsers directory
            chromium_dir = os.path.join(PLAYWRIGHT_BROWSERS_PATH, "chromium")
            os.makedirs(chromium_dir, exist_ok=True)
            
            # Copy Chromium files
            if platform == "linux":
                chrome_linux_dir = os.path.join(extract_path, "chrome-linux")
                if os.path.exists(chrome_linux_dir):
                    # Copy to browsers directory
                    shutil.copytree(chrome_linux_dir, os.path.join(chromium_dir, "chrome-linux"), dirs_exist_ok=True)
                    
                    # Make executable
                    chrome_binary = os.path.join(chromium_dir, "chrome-linux", "chrome")
                    if os.path.exists(chrome_binary):
                        os.chmod(chrome_binary, 0o755)
                        logger.info(f"Made {chrome_binary} executable")
                        
                        # Create symlink for Playwright
                        headless_shell_dir = os.path.join(PLAYWRIGHT_BROWSERS_PATH, "chromium_headless_shell-1169")
                        os.makedirs(os.path.join(headless_shell_dir, "chrome-linux"), exist_ok=True)
                        headless_shell = os.path.join(headless_shell_dir, "chrome-linux", "headless_shell")
                        if not os.path.exists(headless_shell):
                            os.symlink(chrome_binary, headless_shell)
                            logger.info(f"Created symlink from {chrome_binary} to {headless_shell}")
                        
                        return True
                    else:
                        logger.error(f"Chrome binary not found at {chrome_binary}")
                else:
                    logger.error(f"Chrome Linux directory not found at {chrome_linux_dir}")
            else:
                logger.error(f"Platform {platform} not supported yet")
        
        return False
    except Exception as e:
        logger.error(f"Error downloading and setting up Chromium: {e}")
        return False

def verify_installation():
    """Verify that Chromium is installed correctly."""
    try:
        # Check if the Chromium binary exists
        headless_shell = os.path.join(PLAYWRIGHT_BROWSERS_PATH, "chromium_headless_shell-1169", "chrome-linux", "headless_shell")
        if os.path.exists(headless_shell):
            logger.info(f"Chromium binary found at {headless_shell}")
            
            # Check if it's executable
            if os.access(headless_shell, os.X_OK):
                logger.info(f"Chromium binary is executable")
                return True
            else:
                logger.error(f"Chromium binary is not executable")
                return False
        else:
            logger.error(f"Chromium binary not found at {headless_shell}")
            return False
    except Exception as e:
        logger.error(f"Error verifying Chromium installation: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Chromium download and setup...")
    
    if download_and_setup_chromium():
        logger.info("Chromium download and setup successful")
        
        if verify_installation():
            logger.info("Chromium installation verified")
            sys.exit(0)
        else:
            logger.error("Chromium installation verification failed")
            sys.exit(1)
    else:
        logger.error("Chromium download and setup failed")
        sys.exit(1)
