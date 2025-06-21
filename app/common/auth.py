"""Common authentication utilities."""

import logging
import os

logger = logging.getLogger(__name__)


def check_gcp_credentials(use_mock: bool = False) -> None:
    """Check and warn about GCP credentials if not using mock mode."""
    if not use_mock:
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.warning(
                "GOOGLE_APPLICATION_CREDENTIALS not set. Using application default credentials."
            )
