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

# Import Chrome configuration
try:
    from chrome_config import get_chrome_path, get_chromedriver_path, get_chrome_config
except ImportError:
    # Define fallback functions if the module is not available
    def get_chrome_path():
        return None
    def get_chromedriver_path():
        return None
    def get_chrome_config():
        return {"chrome_found": False, "chromedriver_found": False}

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

    # Use the chrome_config module to get Chrome information
    chrome_config = get_chrome_config()

    return {
        "installed": chrome_config.get("chrome_found", False),
        "path": chrome_config.get("chrome_path"),
        "version": chrome_config.get("chrome_version"),
        "config": chrome_config
    }

def check_chromedriver_installation() -> Dict[str, Any]:
    """Check ChromeDriver installation"""
    logger.info("Checking ChromeDriver installation")

    # Use the chrome_config module to get ChromeDriver information
    chrome_config = get_chrome_config()

    return {
        "installed": chrome_config.get("chromedriver_found", False),
        "path": chrome_config.get("chromedriver_path"),
        "version": chrome_config.get("chromedriver_version")
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
