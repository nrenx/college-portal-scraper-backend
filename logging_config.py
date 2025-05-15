"""
Logging configuration for the NBKRIST student portal scrapers.

This module provides a centralized logging configuration for all scrapers.
It includes custom formatters, handlers, and filters to make logs more focused and informative.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Define log file paths
MAIN_LOG_FILE = LOGS_DIR / "scraper.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"
SUPABASE_LOG_FILE = LOGS_DIR / "supabase.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug.log"

# Maximum log file size (10 MB)
MAX_LOG_SIZE = 10 * 1024 * 1024

# Maximum number of backup log files
MAX_LOG_BACKUPS = 5

# Define a custom JSON formatter for structured logging
class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON.
    This makes it easier to parse and analyze logs.
    """
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields if available
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

# Define a custom filter for error logs
class ErrorFilter(logging.Filter):
    """
    Custom filter that only allows error and critical log records.
    """
    def filter(self, record):
        return record.levelno >= logging.ERROR

# Define a custom filter for Supabase logs
class SupabaseFilter(logging.Filter):
    """
    Custom filter that only allows logs related to Supabase operations.
    """
    def filter(self, record):
        return "supabase" in record.name.lower() or "supabase" in record.getMessage().lower()

# Configure the root logger
def configure_logging(
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    enable_json: bool = False
) -> None:
    """
    Configure the root logger with console and file handlers.
    
    Args:
        console_level: Logging level for the console handler
        file_level: Logging level for the file handler
        enable_json: Whether to use JSON formatting for logs
    """
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set the root logger level
    root_logger.setLevel(logging.DEBUG)
    
    # Create formatters
    if enable_json:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create main file handler (rotating file handler to manage log size)
    try:
        from logging.handlers import RotatingFileHandler
        
        # Main log file - contains all logs
        main_file_handler = RotatingFileHandler(
            MAIN_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=MAX_LOG_BACKUPS
        )
        main_file_handler.setLevel(file_level)
        main_file_handler.setFormatter(formatter)
        root_logger.addHandler(main_file_handler)
        
        # Error log file - contains only error and critical logs
        error_file_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=MAX_LOG_BACKUPS
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        error_file_handler.addFilter(ErrorFilter())
        root_logger.addHandler(error_file_handler)
        
        # Supabase log file - contains only Supabase-related logs
        supabase_file_handler = RotatingFileHandler(
            SUPABASE_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=MAX_LOG_BACKUPS
        )
        supabase_file_handler.setLevel(logging.DEBUG)
        supabase_file_handler.setFormatter(formatter)
        supabase_file_handler.addFilter(SupabaseFilter())
        root_logger.addHandler(supabase_file_handler)
        
        # Debug log file - contains all debug logs
        debug_file_handler = RotatingFileHandler(
            DEBUG_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=MAX_LOG_BACKUPS
        )
        debug_file_handler.setLevel(logging.DEBUG)
        debug_file_handler.setFormatter(formatter)
        root_logger.addHandler(debug_file_handler)
        
    except ImportError:
        # Fall back to regular file handler if RotatingFileHandler is not available
        file_handler = logging.FileHandler(MAIN_LOG_FILE)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log the configuration
    logging.info(f"Logging configured with console_level={console_level}, file_level={file_level}, enable_json={enable_json}")
    logging.info(f"Log files: main={MAIN_LOG_FILE}, error={ERROR_LOG_FILE}, supabase={SUPABASE_LOG_FILE}, debug={DEBUG_LOG_FILE}")

# Helper function to get a logger with extra context
def get_logger(name: str, extra: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger with extra context.
    
    Args:
        name: Name of the logger
        extra: Extra context to add to all log records
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    if extra:
        # Create a filter that adds extra context to all log records
        class ContextFilter(logging.Filter):
            def filter(self, record):
                for key, value in extra.items():
                    setattr(record, key, value)
                return True
        
        # Add the filter to the logger
        logger.addFilter(ContextFilter())
    
    return logger

# Function to get recent error logs
def get_recent_error_logs(max_lines: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent error logs from the error log file.
    
    Args:
        max_lines: Maximum number of lines to return
        
    Returns:
        List of error log entries
    """
    if not ERROR_LOG_FILE.exists():
        return []
    
    try:
        with open(ERROR_LOG_FILE, "r") as f:
            lines = f.readlines()
        
        # Get the last max_lines lines
        lines = lines[-max_lines:]
        
        # Parse the lines as JSON if possible
        logs = []
        for line in lines:
            try:
                if line.strip():
                    # Try to parse as JSON first
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                    continue
            except json.JSONDecodeError:
                pass
            
            # If not JSON, parse as regular log entry
            logs.append({"message": line.strip()})
        
        return logs
    except Exception as e:
        return [{"error": f"Error reading error log file: {str(e)}"}]

# Function to get recent Supabase logs
def get_recent_supabase_logs(max_lines: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent Supabase logs from the Supabase log file.
    
    Args:
        max_lines: Maximum number of lines to return
        
    Returns:
        List of Supabase log entries
    """
    if not SUPABASE_LOG_FILE.exists():
        return []
    
    try:
        with open(SUPABASE_LOG_FILE, "r") as f:
            lines = f.readlines()
        
        # Get the last max_lines lines
        lines = lines[-max_lines:]
        
        # Parse the lines as JSON if possible
        logs = []
        for line in lines:
            try:
                if line.strip():
                    # Try to parse as JSON first
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                    continue
            except json.JSONDecodeError:
                pass
            
            # If not JSON, parse as regular log entry
            logs.append({"message": line.strip()})
        
        return logs
    except Exception as e:
        return [{"error": f"Error reading Supabase log file: {str(e)}"}]
