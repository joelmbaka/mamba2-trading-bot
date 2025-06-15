"""Centralized logger configuration for the application."""
import sys
from pathlib import Path
from typing import Optional

from loguru import logger as loguru_logger

# Remove default logger
loguru_logger.remove()

# Log format
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Use built-in loguru levels
# TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL are already defined in loguru

def configure_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
    enqueue: bool = True,
) -> None:
    """
    Configure the application logger.

    Args:
        log_level: Minimum log level to display (TRACE, DEBUG, INFO, etc.)
        log_file: Path to the log file. If None, file logging is disabled.
        rotation: When to rotate the log file (e.g., "10 MB", "1 day")
        retention: How long to keep log files (e.g., "7 days", "1 month")
        enqueue: Whether to make the logger thread-safe
    """
    # Set log level
    log_level_upper = log_level.upper()
    
    # Configure console handler
    loguru_logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level=log_level_upper,
        enqueue=enqueue,
        colorize=True
    )
    
    # Configure file handler if log file is specified
    if log_file:
        log_file_path = Path(log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            str(log_file_path),
            rotation=rotation,
            retention=retention,
            level=log_level_upper,
            enqueue=enqueue,
            encoding='utf-8',
            backtrace=True,
            diagnose=True
        )
    
    # Set up logger for external libraries
    loguru_logger.disable("__main__")
    loguru_logger.enable("mamba2")

# Default logger configuration
configure_logger(
    log_level="DEBUG",
    log_file="logs/mamba2.log"
)

# Export logger for easy access
logger = loguru_logger

# Example usage:
# from mamba2.crew.logger import logger
# logger.info("This is an info message")
# logger.error("This is an error message")
# logger.debug("This is a debug message")