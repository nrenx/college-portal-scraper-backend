#!/usr/bin/env python3
"""
Script to find Chrome and ChromeDriver binaries on the system.
This script searches for Chrome and ChromeDriver in common locations
and reports detailed information about what it finds.
"""

import os
import sys
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
logger = logging.getLogger("find_chrome")

def find_executables(name: str) -> List[str]:
    """
    Find executables with the given name in PATH.
    
    Args:
        name: Name of the executable to find
        
    Returns:
        List of paths to the executable
    """
    paths = []
    
    # Use 'which' command to find the executable
    try:
        result = subprocess.run(['which', '-a', name], capture_output=True, text=True)
        if result.returncode == 0:
            paths.extend([p.strip() for p in result.stdout.splitlines() if p.strip()])
    except Exception as e:
        logger.error(f"Error running 'which' command: {e}")
    
    return paths

def find_chrome_binaries() -> Dict[str, Any]:
    """
    Find Chrome binaries on the system.
    
    Returns:
        Dict with information about Chrome binaries
    """
    logger.info("Searching for Chrome binaries...")
    
    # Common Chrome binary names
    chrome_names = [
        "google-chrome-stable",
        "google-chrome",
        "chromium-browser",
        "chromium",
        "chrome"
    ]
    
    # Common Chrome binary paths
    chrome_paths = [
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/opt/google/chrome/chrome",
        "/opt/render/chrome/chrome"
    ]
    
    results = {
        "which_results": {},
        "path_checks": {},
        "environment": {
            "CHROME_PATH": os.environ.get("CHROME_PATH"),
            "PATH": os.environ.get("PATH")
        }
    }
    
    # Check using 'which' command
    for name in chrome_names:
        paths = find_executables(name)
        results["which_results"][name] = paths
        if paths:
            logger.info(f"Found {name} using 'which': {paths}")
    
    # Check specific paths
    for path in chrome_paths:
        exists = os.path.exists(path)
        is_file = os.path.isfile(path) if exists else False
        is_executable = os.access(path, os.X_OK) if exists else False
        
        results["path_checks"][path] = {
            "exists": exists,
            "is_file": is_file,
            "is_executable": is_executable
        }
        
        if exists:
            logger.info(f"Found Chrome at {path}")
            if is_executable:
                try:
                    # Try to get version
                    result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        results["path_checks"][path]["version"] = version
                        logger.info(f"Chrome version at {path}: {version}")
                except Exception as e:
                    logger.error(f"Error getting Chrome version at {path}: {e}")
                    results["path_checks"][path]["version_error"] = str(e)
    
    return results

def find_chromedriver_binaries() -> Dict[str, Any]:
    """
    Find ChromeDriver binaries on the system.
    
    Returns:
        Dict with information about ChromeDriver binaries
    """
    logger.info("Searching for ChromeDriver binaries...")
    
    # Common ChromeDriver binary paths
    chromedriver_paths = [
        "/usr/local/bin/chromedriver",
        "/usr/bin/chromedriver"
    ]
    
    results = {
        "which_results": find_executables("chromedriver"),
        "path_checks": {},
        "environment": {
            "CHROMEDRIVER_PATH": os.environ.get("CHROMEDRIVER_PATH")
        }
    }
    
    # Log which results
    if results["which_results"]:
        logger.info(f"Found chromedriver using 'which': {results['which_results']}")
    
    # Check specific paths
    for path in chromedriver_paths:
        exists = os.path.exists(path)
        is_file = os.path.isfile(path) if exists else False
        is_executable = os.access(path, os.X_OK) if exists else False
        
        results["path_checks"][path] = {
            "exists": exists,
            "is_file": is_file,
            "is_executable": is_executable
        }
        
        if exists:
            logger.info(f"Found ChromeDriver at {path}")
            if is_executable:
                try:
                    # Try to get version
                    result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        results["path_checks"][path]["version"] = version
                        logger.info(f"ChromeDriver version at {path}: {version}")
                except Exception as e:
                    logger.error(f"Error getting ChromeDriver version at {path}: {e}")
                    results["path_checks"][path]["version_error"] = str(e)
    
    return results

def check_system_packages() -> Dict[str, Any]:
    """
    Check if Chrome is installed as a system package.
    
    Returns:
        Dict with information about Chrome packages
    """
    logger.info("Checking system packages...")
    
    results = {
        "dpkg": {},
        "apt": {}
    }
    
    # Check using dpkg
    try:
        result = subprocess.run(['dpkg', '-l', '*chrome*'], capture_output=True, text=True)
        results["dpkg"]["chrome"] = result.stdout.strip()
        
        result = subprocess.run(['dpkg', '-l', '*chromium*'], capture_output=True, text=True)
        results["dpkg"]["chromium"] = result.stdout.strip()
    except Exception as e:
        logger.error(f"Error checking dpkg packages: {e}")
        results["dpkg"]["error"] = str(e)
    
    # Check using apt
    try:
        result = subprocess.run(['apt', 'list', '--installed', '*chrome*'], capture_output=True, text=True)
        results["apt"]["chrome"] = result.stdout.strip()
        
        result = subprocess.run(['apt', 'list', '--installed', '*chromium*'], capture_output=True, text=True)
        results["apt"]["chromium"] = result.stdout.strip()
    except Exception as e:
        logger.error(f"Error checking apt packages: {e}")
        results["apt"]["error"] = str(e)
    
    return results

def run_find_chrome() -> Dict[str, Any]:
    """
    Run all Chrome finding functions.
    
    Returns:
        Dict with all results
    """
    logger.info("Running Chrome finder...")
    
    results = {
        "chrome": find_chrome_binaries(),
        "chromedriver": find_chromedriver_binaries(),
        "system_packages": check_system_packages(),
        "environment": {
            "PATH": os.environ.get("PATH"),
            "CHROME_PATH": os.environ.get("CHROME_PATH"),
            "CHROMEDRIVER_PATH": os.environ.get("CHROMEDRIVER_PATH")
        }
    }
    
    return results

if __name__ == "__main__":
    # Run the Chrome finder
    results = run_find_chrome()
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Save results to file
    with open("chrome_finder_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Results saved to chrome_finder_results.json")
