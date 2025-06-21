"""
Unit tests for the Logger module.
"""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest
from log.logger import Logger


class TestLogger:
    """Test cases for Logger class."""

    def test_logger_initialization_default_level(self):
        """Test logger initialization with default INFO level."""
        with patch.dict(os.environ, {}, clear=True):
            logger = Logger("test_logger")
            
            assert logger.logger.name == "test_logger"
            assert logger.logger.level == logging.INFO
            assert len(logger.logger.handlers) > 0
            
            # Check that a StreamHandler was added
            stream_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler)]
            assert len(stream_handlers) > 0

    def test_logger_initialization_custom_level(self):
        """Test logger initialization with custom log level from environment."""
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]
        
        for env_level, expected_level in test_cases:
            with patch.dict(os.environ, {"LOG_LEVEL": env_level}):
                # Clear existing handlers to avoid duplication
                logging.getLogger("test_logger_custom").handlers = []
                logger = Logger("test_logger_custom")
                
                assert logger.logger.level == expected_level

    def test_logger_initialization_invalid_level(self):
        """Test logger initialization with invalid log level defaults to INFO."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID_LEVEL"}):
            logger = Logger("test_logger_invalid")
            
            assert logger.logger.level == logging.INFO

    def test_logger_initialization_lowercase_level(self):
        """Test logger initialization with lowercase log level."""
        with patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
            # Clear existing handlers
            logging.getLogger("test_logger_lowercase").handlers = []
            logger = Logger("test_logger_lowercase")
            
            assert logger.logger.level == logging.DEBUG

    def test_logger_prevents_duplicate_handlers(self):
        """Test that logger doesn't add duplicate StreamHandlers."""
        # Clear any existing handlers
        test_logger_name = "test_duplicate_handler"
        logging.getLogger(test_logger_name).handlers = []
        
        # Create first logger instance
        logger1 = Logger(test_logger_name)
        handler_count_1 = len(logger1.logger.handlers)
        
        # Create second logger instance with same name
        logger2 = Logger(test_logger_name)
        handler_count_2 = len(logger2.logger.handlers)
        
        # Should not add another handler
        assert handler_count_1 == handler_count_2

    def test_info_logging(self):
        """Test info level logging."""
        with patch("logging.Logger.info") as mock_info:
            logger = Logger("test_info")
            test_message = "This is an info message"
            
            logger.info(test_message)
            
            mock_info.assert_called_once_with(test_message)

    def test_debug_logging(self):
        """Test debug level logging."""
        with patch("logging.Logger.debug") as mock_debug:
            logger = Logger("test_debug")
            test_message = "This is a debug message"
            
            logger.debug(test_message)
            
            mock_debug.assert_called_once_with(test_message)

    def test_warning_logging(self):
        """Test warning level logging."""
        with patch("logging.Logger.warning") as mock_warning:
            logger = Logger("test_warning")
            test_message = "This is a warning message"
            
            logger.warning(test_message)
            
            mock_warning.assert_called_once_with(test_message)

    def test_error_logging(self):
        """Test error level logging."""
        with patch("logging.Logger.error") as mock_error:
            logger = Logger("test_error")
            test_message = "This is an error message"
            
            logger.error(test_message)
            
            mock_error.assert_called_once_with(test_message)

    def test_critical_logging(self):
        """Test critical level logging."""
        with patch("logging.Logger.critical") as mock_critical:
            logger = Logger("test_critical")
            test_message = "This is a critical message"
            
            logger.critical(test_message)
            
            mock_critical.assert_called_once_with(test_message)

    def test_formatter_configuration(self):
        """Test that the formatter is correctly configured."""
        # Clear existing handlers
        test_logger_name = "test_formatter"
        logging.getLogger(test_logger_name).handlers = []
        
        logger = Logger(test_logger_name)
        
        # Get the StreamHandler
        stream_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0
        
        handler = stream_handlers[0]
        formatter = handler.formatter
        
        # Check formatter format string
        assert formatter._fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def test_multiple_loggers_different_names(self):
        """Test creating multiple loggers with different names."""
        logger1 = Logger("logger1")
        logger2 = Logger("logger2")
        
        assert logger1.logger.name == "logger1"
        assert logger2.logger.name == "logger2"
        assert logger1.logger is not logger2.logger