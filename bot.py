"""
Amroha Police Cyber Fraud Reporting Bot
Main entry point — initializes and runs the Telegram bot.

Usage:
    python bot.py

Auto-installs dependencies on first run.
"""

import subprocess
import sys

# ─── Auto-install dependencies ───
def install_dependencies():
    """Auto-install all packages from requirements.txt."""
    try:
        import telegram  # noqa: F401
        import dotenv  # noqa: F401
        import httpx  # noqa: F401
    except ImportError:
        print("📦 Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"
        ])
        print("✅ Dependencies installed!")

install_dependencies()

# ─── Now import everything ───
import asyncio
import logging

from telegram.ext import ApplicationBuilder

from config import TELEGRAM_BOT_TOKEN
from handlers.awareness import get_awareness_handlers
from handlers.report import get_report_handler
from handlers.start import get_start_handlers
from handlers.status import get_status_handler

# =====================================================
# LOGGING CONFIGURATION
# =====================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    """Build and run the Telegram bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error(
            "❌ TELEGRAM_BOT_TOKEN is not set!\n"
            "   Add it to your .env file:\n"
            "   TELEGRAM_BOT_TOKEN=your_token_here"
        )
        sys.exit(1)

    logger.info("🚔 Starting Amroha Cyber Fraud Reporting Bot...")

    # Build application with generous timeouts
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )

    # ─── Register handlers (order matters!) ───

    # 1. Report handler (ConversationHandler — must come before generic callbacks)
    app.add_handler(get_report_handler())

    # 2. Status handler (ConversationHandler)
    app.add_handler(get_status_handler())

    # 3. Start / menu handlers
    for handler in get_start_handlers():
        app.add_handler(handler)

    # 4. Awareness tip handlers
    for handler in get_awareness_handlers():
        app.add_handler(handler)

    # ─── Start polling ───
    logger.info("✅ Bot is running! Press Ctrl+C to stop.")

    # Python 3.14+ fix: create event loop explicitly
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
