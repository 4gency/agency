#!/usr/bin/env python3
import os
import logging
import colorlog
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure a logger with colored console output and file output.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        console_output: Whether to output to console (default: True)
        file_output: Whether to output to file (default: True)
        log_file: Custom log file path (default: None)
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Define format for logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Add console handler with colors if requested
    if console_output:
        # Define colors for different levels
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s' + log_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(color_formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if file_output:
        if log_file is None:
            # Create logs directory if it doesn't exist
            logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            log_file = os.path.join(logs_dir, f"{name}.log")
        
        file_formatter = logging.Formatter(log_format)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger 