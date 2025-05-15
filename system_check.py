"""
System check module for verifying the environment and dependencies.
"""

import os
import sys
import platform
import logging
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("system_check")

def check_python_version() -> Dict[str, Any]:
    """Check Python version"""
    logger.info("Checking Python version")
    return {
        "version": sys.version,
        "version_info": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro,
        },
        "executable": sys.executable,
        "platform": platform.platform()
    }

def check_environment_variables() -> Dict[str, Any]:
    """Check environment variables"""
    logger.info("Checking environment variables")
    
    # List of required environment variables
    required_vars = [
        "API_USERNAME",
        "API_PASSWORD",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_BUCKET"
    ]
    
    # Check if each variable is set
    env_vars = {}
    for var in required_vars:
        value = os.environ.get(var)
        env_vars[var] = {
            "set": value is not None,
            # Don't log the actual values for security
            "value_preview": f"{value[:3]}...{value[-3:]}" if value and len(value) > 10 else "(not set or too short)"
        }
    
    return env_vars

def check_dependencies() -> Dict[str, Any]:
    """Check Python dependencies"""
    logger.info("Checking Python dependencies")
    
    # List of required packages
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-dotenv",
        "requests",
        "beautifulsoup4",
        "lxml",
        "aiohttp",
        "supabase",
        "tqdm",
        "selenium",
        "pandas"
    ]
    
    # Check if each package is installed
    packages = {}
    for package in required_packages:
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "unknown")
            packages[package] = {
                "installed": True,
                "version": version
            }
        except ImportError:
            packages[package] = {
                "installed": False,
                "version": None
            }
    
    return packages

def check_chrome_installation() -> Dict[str, Any]:
    """Check Chrome installation"""
    logger.info("Checking Chrome installation")
    
    chrome_paths = [
        # Linux paths
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        # macOS paths
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        # Windows paths
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    chrome_found = False
    chrome_path = None
    chrome_version = None
    
    # Check if Chrome is in PATH
    chrome_in_path = shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("chrome")
    if chrome_in_path:
        chrome_found = True
        chrome_path = chrome_in_path
    else:
        # Check common locations
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_found = True
                chrome_path = path
                break
    
    # Try to get Chrome version
    if chrome_found and chrome_path:
        try:
            result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                chrome_version = result.stdout.strip()
        except Exception as e:
            logger.error(f"Error getting Chrome version: {e}")
    
    return {
        "installed": chrome_found,
        "path": chrome_path,
        "version": chrome_version
    }

def check_chromedriver_installation() -> Dict[str, Any]:
    """Check ChromeDriver installation"""
    logger.info("Checking ChromeDriver installation")
    
    chromedriver_found = False
    chromedriver_path = None
    chromedriver_version = None
    
    # Check if ChromeDriver is in PATH
    chromedriver_in_path = shutil.which("chromedriver")
    if chromedriver_in_path:
        chromedriver_found = True
        chromedriver_path = chromedriver_in_path
    
    # Try to get ChromeDriver version
    if chromedriver_found and chromedriver_path:
        try:
            result = subprocess.run([chromedriver_path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                chromedriver_version = result.stdout.strip()
        except Exception as e:
            logger.error(f"Error getting ChromeDriver version: {e}")
    
    return {
        "installed": chromedriver_found,
        "path": chromedriver_path,
        "version": chromedriver_version
    }

def check_file_permissions() -> Dict[str, Any]:
    """Check file permissions for key files"""
    logger.info("Checking file permissions")
    
    # List of important files to check
    files_to_check = [
        "main.py",
        "scraper_wrapper.py",
        "job_storage.py",
        "job_monitor.py",
        "system_check.py"
    ]
    
    file_permissions = {}
    for file in files_to_check:
        file_path = Path(file)
        if file_path.exists():
            try:
                # Get file stats
                stats = file_path.stat()
                file_permissions[file] = {
                    "exists": True,
                    "readable": os.access(file_path, os.R_OK),
                    "writable": os.access(file_path, os.W_OK),
                    "executable": os.access(file_path, os.X_OK),
                    "size": stats.st_size,
                    "mode": oct(stats.st_mode)[-3:]  # Last 3 digits of octal mode
                }
            except Exception as e:
                file_permissions[file] = {
                    "exists": True,
                    "error": str(e)
                }
        else:
            file_permissions[file] = {
                "exists": False
            }
    
    return file_permissions

def run_system_check() -> Dict[str, Any]:
    """Run all system checks"""
    logger.info("Running system check")
    
    try:
        results = {
            "python": check_python_version(),
            "environment_variables": check_environment_variables(),
            "dependencies": check_dependencies(),
            "chrome": check_chrome_installation(),
            "chromedriver": check_chromedriver_installation(),
            "file_permissions": check_file_permissions(),
            "success": True
        }
        
        logger.info("System check completed successfully")
        return results
    except Exception as e:
        logger.error(f"Error running system check: {e}")
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    # Run the system check
    results = run_system_check()
    print(json.dumps(results, indent=2))
