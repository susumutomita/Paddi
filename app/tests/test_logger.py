"""Tests for the Logger module."""

import logging
import os
from unittest.mock import patch

from log.logger import Logger


class TestLogger:
    """Test cases for the Logger class."""

    def test_initialization_default_level(self):
        """Test Logger initialization with default INFO level."""
        logger = Logger("test_logger")

        assert logger.logger.name == "test_logger"
        assert logger.logger.level == logging.INFO

        # Check handler setup
        handlers = logger.logger.handlers
        assert len(handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_initialization_with_debug_level(self):
        """Test Logger initialization with DEBUG level from environment."""
        logger = Logger("test_debug_logger")

        assert logger.logger.level == logging.DEBUG

    @patch.dict(os.environ, {"LOG_LEVEL": "ERROR"})
    def test_initialization_with_error_level(self):
        """Test Logger initialization with ERROR level from environment."""
        logger = Logger("test_error_logger")

        assert logger.logger.level == logging.ERROR

    @patch.dict(os.environ, {"LOG_LEVEL": "invalid"})
    def test_initialization_with_invalid_level(self):
        """Test Logger initialization with invalid level defaults to INFO."""
        logger = Logger("test_invalid_logger")

        # Should default to INFO when invalid level is provided
        assert logger.logger.level == logging.INFO

    def test_info_logging(self, caplog):
        """Test info level logging."""
        logger = Logger("test_info")

        with caplog.at_level(logging.INFO):
            logger.info("Test info message")

        assert "Test info message" in caplog.text
        assert "INFO" in caplog.text

    def test_debug_logging(self, caplog):
        """Test debug level logging."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            logger = Logger("test_debug")

            with caplog.at_level(logging.DEBUG):
                logger.debug("Test debug message")

            assert "Test debug message" in caplog.text
            assert "DEBUG" in caplog.text

    def test_warning_logging(self, caplog):
        """Test warning level logging."""
        logger = Logger("test_warning")

        with caplog.at_level(logging.WARNING):
            logger.warning("Test warning message")

        assert "Test warning message" in caplog.text
        assert "WARNING" in caplog.text

    def test_error_logging(self, caplog):
        """Test error level logging."""
        logger = Logger("test_error")

        with caplog.at_level(logging.ERROR):
            logger.error("Test error message")

        assert "Test error message" in caplog.text
        assert "ERROR" in caplog.text

    def test_critical_logging(self, caplog):
        """Test critical level logging."""
        logger = Logger("test_critical")

        with caplog.at_level(logging.CRITICAL):
            logger.critical("Test critical message")

        assert "Test critical message" in caplog.text
        assert "CRITICAL" in caplog.text

    def test_multiple_loggers_same_name(self):
        """Test that multiple Logger instances with same name share underlying logger."""
        logger1 = Logger("shared_logger")
        logger2 = Logger("shared_logger")

        # They should have the same underlying logger instance
        assert logger1.logger is logger2.logger

    def test_multiple_loggers_different_names(self):
        """Test that Logger instances with different names have different loggers."""
        logger1 = Logger("logger_one")
        logger2 = Logger("logger_two")

        # They should have different underlying logger instances
        assert logger1.logger is not logger2.logger
        assert logger1.logger.name == "logger_one"
        assert logger2.logger.name == "logger_two"

    def test_log_format(self, caplog):
        """Test that log messages follow the expected format."""
        logger = Logger("test_format")

        with caplog.at_level(logging.INFO):
            logger.info("Formatted message")

        # Check that the log includes timestamp, name, level, and message
        record = caplog.records[0]
        assert record.name == "test_format"
        assert record.levelname == "INFO"
        assert record.message == "Formatted message"

        # The formatted output should contain all parts
        assert "test_format" in caplog.text
        assert "INFO" in caplog.text
        assert "Formatted message" in caplog.text

    def test_no_duplicate_handlers(self):
        """Test that creating multiple Logger instances doesn't duplicate handlers."""
        # Create first logger
        logger1 = Logger("test_no_dupe")
        initial_handler_count = len(logger1.logger.handlers)

        # Create second logger with same name
        logger2 = Logger("test_no_dupe")

        # Handler count should not increase
        assert len(logger2.logger.handlers) == initial_handler_count
