#!/usr/bin/env python3
"""Main entry point for the application."""

import asyncio
import logging
import argparse
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Yandex GO Car Registration Bot")
    parser.add_argument(
        "mode", 
        choices=["bot", "web", "both"], 
        default="bot", 
        nargs="?",
        help="Run mode: bot (default), web, or both"
    )
    
    args = parser.parse_args()
    
    if args.mode == "bot":
        print("Starting bot...")
        from app.bot import main as run_bot
        asyncio.run(run_bot())
    elif args.mode == "web":
        print("Starting web app...")
        from app.webapp.run import main as run_webapp
        run_webapp()
    elif args.mode == "both":
        print("Starting both bot and web app...")
        # Note: This is a simplified approach. In production, you might want to use separate processes
        from app.bot import main as run_bot
        from app.webapp.run import main as run_webapp
        import threading
        
        # Start the web app in a separate thread
        web_thread = threading.Thread(target=run_webapp)
        web_thread.daemon = True
        web_thread.start()
        
        # Start the bot in the main thread
        asyncio.run(run_bot())