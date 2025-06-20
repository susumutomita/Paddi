import logging
import os
from unittest.mock import patch

import pytest
from log.logger import Logger


class TestLogger:
    def test_logger_initialization_default_level(self):
        logger = Logger("test_logger")
        assert logger.logger.name == "test_logger"
        assert logger.logger.level == logging.INFO

    def test_logger_initialization_custom_level(self):
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            logger = Logger("test_logger_debug")
            assert logger.logger.level == logging.DEBUG

    def test_logger_initialization_invalid_level(self):
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            logger = Logger("test_logger_invalid")
            assert logger.logger.level == logging.INFO

    def test_logger_has_stream_handler(self):
        logger = Logger("test_handler")
        handlers = logger.logger.handlers
        assert len(handlers) > 0
        assert any(isinstance(handler, logging.StreamHandler) for handler in handlers)

    def test_info_message(self):
        logger = Logger("test_info")
        with patch.object(logger.logger, "info") as mock_info:
            logger.info("Test info message")
            mock_info.assert_called_once_with("Test info message")

    def test_debug_message(self):
        logger = Logger("test_debug")
        with patch.object(logger.logger, "debug") as mock_debug:
            logger.debug("Test debug message")
            mock_debug.assert_called_once_with("Test debug message")

    def test_warning_message(self):
        logger = Logger("test_warning")
        with patch.object(logger.logger, "warning") as mock_warning:
            logger.warning("Test warning message")
            mock_warning.assert_called_once_with("Test warning message")

    def test_error_message(self):
        logger = Logger("test_error")
        with patch.object(logger.logger, "error") as mock_error:
            logger.error("Test error message")
            mock_error.assert_called_once_with("Test error message")

    def test_critical_message(self):
        logger = Logger("test_critical")
        with patch.object(logger.logger, "critical") as mock_critical:
            logger.critical("Test critical message")
            mock_critical.assert_called_once_with("Test critical message")

    def test_formatter_format(self):
        logger = Logger("test_formatter")
        handler = logger.logger.handlers[0]
        formatter = handler.formatter
        assert formatter._fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @pytest.mark.description("Test that multiple loggers don't duplicate handlers")
    def test_no_duplicate_handlers(self):
        logger1 = Logger("test_duplicate1")
        initial_handlers = len(logger1.logger.handlers)
        logger2 = Logger("test_duplicate1")
        assert len(logger2.logger.handlers) == initial_handlers
