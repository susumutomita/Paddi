"""Unified logging configuration for Paddi."""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


class LoggingConfig:
    """Centralized logging configuration."""
    
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_LEVEL = logging.INFO
    
    @staticmethod
    def setup(
        level: Optional[str] = None,
        log_file: Optional[str] = None,
        format_string: Optional[str] = None,
        enable_rotation: bool = True
    ) -> None:
        """Set up logging configuration.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (if None, only console logging)
            format_string: Custom format string
            enable_rotation: Enable log rotation for file logging
        """
        # Determine logging level
        log_level = getattr(logging, level.upper()) if level else LoggingConfig.DEFAULT_LEVEL
        
        # Use custom format or default
        log_format = format_string or LoggingConfig.DEFAULT_FORMAT
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(exist_ok=True, parents=True)
            
            if enable_rotation:
                # Rotating file handler (10MB max, keep 5 backups)
                file_handler = logging.handlers.RotatingFileHandler(
                    log_path,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
            else:
                # Simple file handler
                file_handler = logging.FileHandler(log_path, encoding='utf-8')
            
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    @staticmethod
    def setup_from_env() -> None:
        """Set up logging from environment variables."""
        level = os.getenv("PADDI_LOG_LEVEL", "INFO")
        log_file = os.getenv("PADDI_LOG_FILE")
        
        LoggingConfig.setup(level=level, log_file=log_file)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger instance with the given name.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    @staticmethod
    def silence_noisy_libraries() -> None:
        """Reduce logging verbosity for noisy third-party libraries."""
        noisy_libs = [
            "urllib3",
            "google.auth",
            "google.api_core",
            "google.cloud",
            "requests",
            "azure",
        ]
        
        for lib in noisy_libs:
            logging.getLogger(lib).setLevel(logging.WARNING)