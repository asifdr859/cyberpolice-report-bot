"""
Start Handler
Handles the /start command and main menu.
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from config import WELCOME_MESSAGE

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command — show welcome message and main menu."""
    keyboard = [
        [InlineKeyboardButton("🚨 Report Fraud", callback_data="report_fraud")],
        [InlineKeyboardButton("🔍 Check Status", callback_data="check_status")],
        [InlineKeyboardButton("💡 Awareness Tips", callback_data="awareness_tips")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            WELCOME_MESSAGE,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            WELCOME_MESSAGE,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Back to Menu' button."""
    await start_command(update, context)


def get_start_handlers():
    """Return the handlers for the start module."""
    return [
        CommandHandler("start", start_command),
        CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
    ]
