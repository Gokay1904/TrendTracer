"""
Entry point for the crypto portfolio application.
"""
import sys
import os

# Add the parent directory to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import and run the application
from app.main import main

if __name__ == "__main__":
    sys.exit(main())
