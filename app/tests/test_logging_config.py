"""Tests for unified logging configuration."""

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.common.logging_config import LoggingConfig


class TestLoggingConfig:
    """Tests for LoggingConfig."""

    def test_setup_basic(self):
        """Test basic logging setup."""
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Setup logging
        LoggingConfig.setup(level="INFO")
        
        # Check root logger
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 1
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)

    def test_setup_with_file(self, tmp_path):
        """Test logging setup with file handler."""
        log_file = tmp_path / "test.log"
        
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Setup logging with file
        LoggingConfig.setup(level="DEBUG", log_file=str(log_file))
        
        # Check handlers
        assert len(root_logger.handlers) == 2
        handler_types = [type(h) for h in root_logger.handlers]
        assert logging.StreamHandler in handler_types
        
        # Test logging
        test_logger = LoggingConfig.get_logger("test")
        test_logger.info("Test message")
        
        # Check log file
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_from_env(self):
        """Test logging setup from environment variables."""
        with patch.dict(os.environ, {"PADDI_LOG_LEVEL": "WARNING"}):
            # Clear existing handlers
            root_logger = logging.getLogger()
            root_logger.handlers.clear()
            
            # Setup from env
            LoggingConfig.setup_from_env()
            
            # Check level
            assert root_logger.level == logging.WARNING

    def test_custom_format(self):
        """Test custom format string."""
        custom_format = "%(levelname)s: %(message)s"
        
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Setup with custom format
        LoggingConfig.setup(format_string=custom_format)
        
        # Check format
        handler = root_logger.handlers[0]
        assert handler.formatter._fmt == custom_format

    def test_get_logger(self):
        """Test getting logger instance."""
        logger = LoggingConfig.get_logger("test.module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_silence_noisy_libraries(self):
        """Test silencing noisy libraries."""
        # Set some libraries to DEBUG
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
        logging.getLogger("google.auth").setLevel(logging.DEBUG)
        
        # Silence them
        LoggingConfig.silence_noisy_libraries()
        
        # Check they're now WARNING level
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("google.auth").level == logging.WARNING

    def test_log_rotation(self, tmp_path):
        """Test log rotation setup."""
        log_file = tmp_path / "rotating.log"
        
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Setup with rotation
        LoggingConfig.setup(
            log_file=str(log_file),
            enable_rotation=True
        )
        
        # Find rotating handler
        file_handlers = [
            h for h in root_logger.handlers 
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        
        assert len(file_handlers) == 1
        handler = file_handlers[0]
        assert handler.maxBytes == 10 * 1024 * 1024  # 10MB
        assert handler.backupCount == 5