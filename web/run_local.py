#!/usr/bin/env python3
"""Local development runner for Paddi Web Dashboard."""

import os
import sys
from pathlib import Path

# Add parent directory to Python path to access app modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Set development environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Import and run the app
from web.app import app

if __name__ == '__main__':
    print("🚀 Starting Paddi Web Dashboard in development mode...")
    print("📍 Dashboard will be available at: http://localhost:8080")
    print("🔧 Debug mode is enabled")
    print("Press Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=8080, debug=True)