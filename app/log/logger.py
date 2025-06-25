"""Module for Logger."""

import logging
import os


class Logger:
    """
    Logger class to facilitate logging throughout the application.

    This class provides a convenient way to create and use loggers with a uniform format.
    """

    def __init__(self, name):
        """Initialize the logger with a specified name and level.

        Args:
            name (str): The name of the logger, typically the name of the module using the logger.
        """
        self.logger = logging.getLogger(name)
        log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        self.logger.setLevel(log_level)
        if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def info(self, message):
        """
        Logs an 'info' level message.

        Args:
            message (str): The message to be logged.
        """
        self.logger.info(message)

    def debug(self, message):
        """
        Logs a 'debug' level message.

        Args:
            message (str): The message to be logged.
        """
        self.logger.debug(message)

    def warning(self, message):
        """
        Logs a 'warning' level message.

        Args:
            message (str): The message to be logged.
        """
        self.logger.warning(message)

    def error(self, message):
        """
        Logs an 'error' level message.

        Args:
            message (str): The message to be logged.
        """
        self.logger.error(message)

    def critical(self, message):
        """
        Logs a 'critical' level message.

        Args:
            message (str): The message to be logged.
        """
        self.logger.critical(message)


def get_logger(name):
    """
    Create and return a logger instance.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = Logger(name)
    return logger.logger
