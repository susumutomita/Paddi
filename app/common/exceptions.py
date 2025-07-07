#!/usr/bin/env python3
"""
Custom exceptions for the application.
"""


class PaddiException(Exception):
    """Base exception for all Paddi-specific errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(PaddiException):
    """Raised when authentication fails."""

    def __init__(self, provider: str = "GCP", details: dict = None):
        message = f"認証エラー: {provider}への認証に失敗しました。"
        super().__init__(message, details)
        self.provider = provider


class CollectionError(PaddiException):
    """Raised when data collection fails."""

    def __init__(self, resource_type: str, details: dict = None):
        message = f"収集エラー: {resource_type}のデータ収集に失敗しました。"
        super().__init__(message, details)
        self.resource_type = resource_type


class ConfigurationError(PaddiException):
    """Raised when configuration is invalid."""

    def __init__(self, config_item: str, details: dict = None):
        message = f"設定エラー: {config_item}の設定が無効です。"
        super().__init__(message, details)
        self.config_item = config_item
