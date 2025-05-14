#!/usr/bin/env python3
"""
Selenium-based login utilities for the college website scraper.
This module handles authentication to the college portal using Selenium.
"""

import os
import sys
import time
import logging
import tempfile
from typing import Dict, Optional, Tuple, Any
from pathlib import Path

# Import Selenium and undetected-chromedriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc

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
logger = logging.getLogger("selenium_login_utils")

# Portal URLs
BASE_URL = "http://103.203.175.90:94"
LOGIN_URL = ATTENDANCE_PORTAL_URL  # This will redirect to login page if not authenticated
ATTENDANCE_LOGIN_URL = f"{BASE_URL}/attendance/attendanceLogin.php"
MID_MARKS_URL = MID_MARKS_PORTAL_URL

def create_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Create a Selenium WebDriver instance with undetected-chromedriver.
    
    Args:
        headless: Whether to run in headless mode
        
    Returns:
        webdriver.Chrome instance
    """
    try:
        # Create a temporary directory for Chrome user data
        user_data_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary user data directory: {user_data_dir}")
        
        # Configure Chrome options
        options = uc.ChromeOptions()
        
        if headless:
            options.add_argument("--headless=new")
        
        # Add additional options for Render environment
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-infobars")
        
        # Set user data directory
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # Create the driver with undetected-chromedriver
        logger.info("Creating Chrome driver with undetected-chromedriver...")
        driver = uc.Chrome(options=options)
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        logger.info("Chrome driver created successfully")
        return driver
    
    except Exception as e:
        logger.error(f"Error creating Chrome driver: {str(e)}")
        raise

def selenium_login(driver: webdriver.Chrome, username: str = USERNAME, password: str = PASSWORD) -> Tuple[bool, str]:
    """
    Log in to the college website using Selenium.
    
    Args:
        driver: webdriver.Chrome instance
        username: Login username
        password: Login password
        
    Returns:
        Tuple of (success status, error message if any)
    """
    try:
        # Navigate to the login page
        logger.info(f"Navigating to login page: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        # Wait for the login form to load
        logger.info("Waiting for login form...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        # Fill in the login form
        logger.info("Filling in login form...")
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        
        # Find and click the submit button
        submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
        submit_button.click()
        
        # Wait for the page to load after login
        time.sleep(3)
        
        # Check if login was successful
        current_url = driver.current_url
        if "login" not in current_url.lower():
            logger.info("Login successful")
            return True, ""
        else:
            logger.warning("Login failed - incorrect credentials or form fields")
            return False, "Login failed - please check your credentials"
    
    except TimeoutException as e:
        error_msg = f"Timeout during login: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    
    except WebDriverException as e:
        error_msg = f"WebDriver error during login: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Error during login: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def selenium_login_to_attendance(driver: webdriver.Chrome, username: str = USERNAME, password: str = PASSWORD) -> Tuple[bool, str]:
    """
    Log in to the attendance section of the college website using Selenium.
    
    Args:
        driver: webdriver.Chrome instance
        username: Login username
        password: Login password
        
    Returns:
        Tuple of (success status, error message if any)
    """
    try:
        # Navigate to the attendance login page
        logger.info(f"Navigating to attendance login page: {ATTENDANCE_LOGIN_URL}")
        driver.get(ATTENDANCE_LOGIN_URL)
        
        # Wait for the login form to load
        logger.info("Waiting for attendance login form...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        # Fill in the login form
        logger.info("Filling in attendance login form...")
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        
        # Find and click the submit button
        submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
        submit_button.click()
        
        # Wait for the page to load after login
        time.sleep(3)
        
        # Check if login was successful
        current_url = driver.current_url
        if "login" not in current_url.lower():
            logger.info("Attendance login successful")
            return True, ""
        else:
            logger.warning("Attendance login failed - incorrect credentials or form fields")
            return False, "Attendance login failed - please check your credentials"
    
    except TimeoutException as e:
        error_msg = f"Timeout during attendance login: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    
    except WebDriverException as e:
        error_msg = f"WebDriver error during attendance login: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Error during attendance login: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def is_selenium_logged_in(driver: webdriver.Chrome) -> bool:
    """
    Check if the Selenium driver is logged in.
    
    Args:
        driver: webdriver.Chrome instance
        
    Returns:
        Boolean indicating login status
    """
    try:
        # Try to access a page that requires authentication
        driver.get(ATTENDANCE_PORTAL_URL)
        
        # Wait briefly for the page to load
        time.sleep(2)
        
        # Check if we're redirected to the login page
        current_url = driver.current_url
        if "login" in current_url.lower():
            return False
        
        # Check for indicators of being logged in
        return True
    
    except Exception as e:
        logger.error(f"Error checking login status: {str(e)}")
        return False
