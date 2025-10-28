#!/usr/bin/env python3
"""Main entry point for the Telegram bot."""

import asyncio
import logging

from app.bot import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())