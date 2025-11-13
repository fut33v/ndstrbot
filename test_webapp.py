#!/usr/bin/env python3
"""Simple test script to run the web application."""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import and run the web app
try:
    from app.webapp.main import app
    import uvicorn
    
    if __name__ == "__main__":
        print("Starting web application on http://localhost:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you have installed the required dependencies:")
    print("pip install fastapi uvicorn sqlmodel aiosqlite asyncpg psycopg2-binary python-dotenv pydantic pydantic-settings")