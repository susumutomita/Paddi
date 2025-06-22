"""WSGI entry point for production deployment."""

import os
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from web.app import app

if __name__ == "__main__":
    # For development
    app.run()
else:
    # For production with gunicorn
    # Run with: gunicorn --bind :8080 --workers 2 --threads 8 --timeout 120 wsgi:app
    application = app