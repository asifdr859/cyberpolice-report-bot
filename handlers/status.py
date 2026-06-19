"""
Status Handler
Allows users to check the status of their fraud report.
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from services.sheets import search_report

logger = logging.getLogger(__name__)

# States
WAITING_REPORT_ID = 0


async def check_status_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point — ask for Report ID."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "🔍 *Check Report Status*\n\n"
            "Please enter your Report ID:\n"
            "Example: `AMR-2026-001`",
            parse_mode="Markdown",
        )
    elif update.message:
        await update.message.reply_text(
            "🔍 *Check Report Status*\n\n"
            "Please enter your Report ID:\n"
            "Example: `AMR-2026-001`",
            parse_mode="Markdown",
        )

    return WAITING_REPORT_ID


async def report_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Look up the report by ID."""
    report_id = update.message.text.strip().upper()

    try:
        report = await search_report(report_id)
    except Exception as e:
        logger.error("Error searching for report: %s", e)
        report = None

    keyboard = [[InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if report:
        # Map sheet column headers to display
        status_emoji = {
            "New": "🆕",
            "In Progress": "🔄",
            "Resolved": "✅",
            "Closed": "🔒",
        }
        current_status = report.get("Status", "Unknown")
        emoji = status_emoji.get(current_status, "❓")

        message = (
            f"📋 *Report Found*\n\n"
            f"🆔 Report ID: `{report.get('Report ID', report_id)}`\n"
            f"📅 Submitted: {report.get('Timestamp', 'N/A')}\n"
            f"🔖 Fraud Type: {report.get('Fraud Type', 'N/A')}\n"
            f"💰 Amount: ₹{report.get('Amount Lost', 'N/A')}\n"
            f"⚠️ Risk: {report.get('Risk Score', 'N/A')}\n"
            f"📊 Status: {emoji} *{current_status}*\n"
        )
    else:
        message = (
            f"❌ *Report Not Found*\n\n"
            f"No report found with ID: `{report_id}`\n\n"
            f"Please check the ID and try again.\n"
            f"Report IDs look like: `AMR-2026-001`"
        )

    await update.message.reply_text(
        message, parse_mode="Markdown", reply_markup=reply_markup
    )
    return ConversationHandler.END


async def cancel_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel status check."""
    await update.message.reply_text(
        "Cancelled. Use /start to return to the main menu.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


def get_status_handler():
    """Return the ConversationHandler for status checking."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(check_status_start, pattern="^check_status$"),
        ],
        states={
            WAITING_REPORT_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, report_id_received),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_status),
        ],
        per_message=False,
        allow_reentry=True,
    )
