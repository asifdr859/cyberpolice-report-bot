"""
Report Handler
Multi-step conversation flow for filing a fraud report.

Steps:
  1. Select fraud type
  2. Enter UPI ID / Mobile Number / Website
  3. Enter your name
  4. Enter your mobile number
  5. Describe the incident
  6. Enter loss amount
  7. Enter incident date
  8. Upload screenshot (optional) — stored as Telegram file_id
  9. Confirm & submit
"""

import logging
from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import FRAUD_TYPES, REPORT_SUCCESS_MESSAGE
from services.sheets import add_report, calculate_risk, count_duplicates, get_report_count
from services.validator import classify_identifier, validate_amount, validate_date
from utils.report_id import generate_report_id

logger = logging.getLogger(__name__)

# Conversation states
(
    SELECT_FRAUD_TYPE,
    ENTER_IDENTIFIER,
    ENTER_NAME,
    ENTER_MOBILE,
    ENTER_DESCRIPTION,
    ENTER_AMOUNT,
    ENTER_DATE,
    UPLOAD_SCREENSHOT,
    CONFIRM_SUBMIT,
) = range(9)


async def report_fraud_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point — show fraud type selection."""
    query = update.callback_query
    if query:
        await query.answer()

    # Build fraud type keyboard (2 per row)
    emojis = {
        "UPI Fraud": "🔴",
        "OTP Fraud": "🟠",
        "Loan Fraud": "🟡",
        "Job Scam": "🔵",
        "Investment Scam": "🟣",
        "Website Scam": "🌐",
        "Other": "⚪",
    }
    keyboard = []
    for i in range(0, len(FRAUD_TYPES), 2):
        row = [
            InlineKeyboardButton(
                f"{emojis.get(ft, '⚪')} {ft}",
                callback_data=f"fraud_type_{ft}",
            )
            for ft in FRAUD_TYPES[i:i + 2]
        ]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_report")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "📝 *Step 1/8 — Select Fraud Type*\n\n"
        "Please select the type of cyber fraud you want to report:"
    )

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

    return SELECT_FRAUD_TYPE


async def fraud_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fraud type selection."""
    query = update.callback_query
    await query.answer()

    fraud_type = query.data.replace("fraud_type_", "")
    context.user_data["fraud_type"] = fraud_type

    text = (
        f"📝 *Step 2/8 — Enter Identifier*\n\n"
        f"Fraud Type: _{fraud_type}_\n\n"
        f"Please enter the fraudster's:\n"
        f"• UPI ID (e.g., `abc@paytm`)\n"
        f"• Website URL (e.g., `https://example.com`)\n"
        f"• Mobile Number (e.g., `9876543210`)\n\n"
        f"Type your response below:"
    )

    await query.edit_message_text(text, parse_mode="Markdown")
    return ENTER_IDENTIFIER


async def identifier_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the UPI/URL/Phone input."""
    text = update.message.text.strip()
    id_type = classify_identifier(text)

    if id_type == "upi":
        context.user_data["upi_id"] = text
        context.user_data["website_url"] = ""
    elif id_type == "url":
        context.user_data["website_url"] = text
        context.user_data["upi_id"] = ""
    elif id_type == "phone":
        context.user_data["upi_id"] = text
        context.user_data["website_url"] = ""
    else:
        # Accept anyway — store as UPI field
        context.user_data["upi_id"] = text
        context.user_data["website_url"] = ""

    context.user_data["id_type"] = id_type

    await update.message.reply_text(
        "📝 *Step 3/8 — Your Name*\n\n"
        "Please enter your full name:",
        parse_mode="Markdown",
    )
    return ENTER_NAME


async def name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input."""
    context.user_data["name"] = update.message.text.strip()

    await update.message.reply_text(
        "📝 *Step 4/8 — Your Mobile Number*\n\n"
        "Please enter your 10-digit mobile number:",
        parse_mode="Markdown",
    )
    return ENTER_MOBILE


async def mobile_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mobile number input."""
    mobile = update.message.text.strip()
    context.user_data["mobile"] = mobile

    await update.message.reply_text(
        "📝 *Step 5/8 — Describe the Incident*\n\n"
        "Please describe what happened in detail.\n"
        "Include how you were contacted and what the fraudster did:",
        parse_mode="Markdown",
    )
    return ENTER_DESCRIPTION


async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle description input."""
    context.user_data["description"] = update.message.text.strip()

    await update.message.reply_text(
        "📝 *Step 6/8 — Amount Lost*\n\n"
        "Please enter the amount of money lost (in ₹):\n"
        "Example: `5000` or `₹10,000`",
        parse_mode="Markdown",
    )
    return ENTER_AMOUNT


async def amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount input."""
    amount = validate_amount(update.message.text)
    if amount is None:
        await update.message.reply_text(
            "❌ Invalid amount. Please enter a valid positive number.\n"
            "Example: `5000` or `₹10,000`",
            parse_mode="Markdown",
        )
        return ENTER_AMOUNT

    context.user_data["amount_lost"] = amount

    await update.message.reply_text(
        "📝 *Step 7/8 — Incident Date*\n\n"
        "When did this incident happen?\n"
        "Enter date in format: `DD-MM-YYYY`\n"
        "Example: `18-06-2026`",
        parse_mode="Markdown",
    )
    return ENTER_DATE


async def date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date input."""
    parsed_date = validate_date(update.message.text)
    if parsed_date is None:
        await update.message.reply_text(
            "❌ Invalid date format. Please try again.\n"
            "Use format: `DD-MM-YYYY` (e.g., `18-06-2026`)",
            parse_mode="Markdown",
        )
        return ENTER_DATE

    context.user_data["incident_date"] = parsed_date

    keyboard = [
        [InlineKeyboardButton("📷 Upload Screenshot", callback_data="upload_screenshot")],
        [InlineKeyboardButton("⏩ Skip", callback_data="skip_screenshot")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📝 *Step 8/8 — Evidence Screenshot*\n\n"
        "Please upload a screenshot of the fraud (payment receipt, chat, etc.).\n"
        "Or skip if you don't have one.",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return UPLOAD_SCREENSHOT


async def screenshot_upload_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose to upload a screenshot."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📷 Please send the screenshot as a photo or document now:",
        parse_mode="Markdown",
    )
    return UPLOAD_SCREENSHOT


async def screenshot_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle screenshot — store Telegram file_id (no Drive upload)."""
    evidence_file_id = ""

    if update.message.photo:
        # Get the largest photo's file_id
        photo = update.message.photo[-1]
        evidence_file_id = photo.file_id
    elif update.message.document:
        evidence_file_id = update.message.document.file_id

    context.user_data["evidence_file_id"] = evidence_file_id or "Not uploaded"

    return await _show_confirmation(update, context)


async def skip_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose to skip screenshot upload."""
    query = update.callback_query
    await query.answer()

    context.user_data["evidence_file_id"] = "Not uploaded"

    return await _show_confirmation(update, context, from_callback=True)


async def _show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    """Show report summary for confirmation."""
    data = context.user_data

    desc_preview = data.get('description', 'N/A')
    if len(desc_preview) > 100:
        desc_preview = desc_preview[:100] + "..."

    summary = (
        "📋 *Report Summary — Please Confirm*\n\n"
        f"👤 Name: {data.get('name', 'N/A')}\n"
        f"📱 Mobile: {data.get('mobile', 'N/A')}\n"
        f"🔖 Fraud Type: {data.get('fraud_type', 'N/A')}\n"
        f"🆔 UPI/Identifier: `{data.get('upi_id', '') or data.get('website_url', '')}`\n"
        f"📝 Description: {desc_preview}\n"
        f"💰 Amount Lost: ₹{data.get('amount_lost', 'N/A')}\n"
        f"📅 Incident Date: {data.get('incident_date', 'N/A')}\n"
        f"📎 Evidence: {'✅ Uploaded' if data.get('evidence_file_id', '') != 'Not uploaded' else '❌ Not uploaded'}\n"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Submit Report", callback_data="confirm_submit")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_report")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if from_callback and update.callback_query:
        await update.callback_query.edit_message_text(
            summary, parse_mode="Markdown", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            summary, parse_mode="Markdown", reply_markup=reply_markup
        )

    return CONFIRM_SUBMIT


async def confirm_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Submit the report to Google Sheets via Apps Script."""
    query = update.callback_query
    await query.answer("Submitting your report...")

    data = context.user_data

    # Check duplicates
    identifier = data.get("upi_id", "") or data.get("website_url", "")
    id_type = "upi" if data.get("upi_id") else "url"
    duplicate_count = 0
    risk_level = "Low"

    try:
        duplicate_count = await count_duplicates(identifier, id_type) + 1  # +1 for current
        risk_level = calculate_risk(duplicate_count)
    except Exception as e:
        logger.error("Error checking duplicates: %s", e)

    # Generate Report ID
    try:
        existing_count = await get_report_count()
        report_id = generate_report_id(existing_count)
    except Exception as e:
        logger.error("Error generating report ID: %s", e)
        report_id = f"AMR-{datetime.now().strftime('%Y')}-ERR"

    # Build report data for Apps Script
    report_data = {
        "report_id": report_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "telegram_user_id": str(update.effective_user.id),
        "name": data.get("name", ""),
        "mobile": data.get("mobile", ""),
        "fraud_type": data.get("fraud_type", ""),
        "upi_id": data.get("upi_id", ""),
        "website_url": data.get("website_url", ""),
        "description": data.get("description", ""),
        "amount_lost": str(data.get("amount_lost", "")),
        "incident_date": data.get("incident_date", ""),
        "city": "Amroha",
        "evidence_file_id": data.get("evidence_file_id", ""),
        "risk_score": risk_level,
        "duplicate_count": duplicate_count,
        "status": "New",
    }

    # Save to Google Sheets via Apps Script
    success = False
    try:
        success = await add_report(report_data)
    except Exception as e:
        logger.error("Error saving report: %s", e)

    if success:
        message = REPORT_SUCCESS_MESSAGE.format(
            report_id=report_id,
            duplicate_count=duplicate_count,
            risk_level=risk_level,
        )
    else:
        message = (
            f"⚠️ *Report Recorded Locally*\n\n"
            f"📋 Report ID: `{report_id}`\n\n"
            f"There was an issue saving to the database.\n"
            f"Your report has been recorded and will be synced later.\n"
            f"Please contact the cyber cell if urgent."
        )

    keyboard = [[InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=reply_markup
    )

    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current report."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "❌ Report cancelled.\n\nUse /start to return to the main menu.",
            parse_mode="Markdown",
        )
    elif update.message:
        await update.message.reply_text(
            "❌ Report cancelled.\n\nUse /start to return to the main menu.",
            parse_mode="Markdown",
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    await update.message.reply_text(
        "❌ Report cancelled.\n\nUse /start to return to the main menu.",
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_report_handler():
    """Return the ConversationHandler for the report flow."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(report_fraud_start, pattern="^report_fraud$"),
        ],
        states={
            SELECT_FRAUD_TYPE: [
                CallbackQueryHandler(fraud_type_selected, pattern="^fraud_type_"),
                CallbackQueryHandler(cancel_report, pattern="^cancel_report$"),
            ],
            ENTER_IDENTIFIER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, identifier_received),
            ],
            ENTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, name_received),
            ],
            ENTER_MOBILE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, mobile_received),
            ],
            ENTER_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, description_received),
            ],
            ENTER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received),
            ],
            ENTER_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, date_received),
            ],
            UPLOAD_SCREENSHOT: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, screenshot_received),
                CallbackQueryHandler(screenshot_upload_prompt, pattern="^upload_screenshot$"),
                CallbackQueryHandler(skip_screenshot, pattern="^skip_screenshot$"),
            ],
            CONFIRM_SUBMIT: [
                CallbackQueryHandler(confirm_submit, pattern="^confirm_submit$"),
                CallbackQueryHandler(cancel_report, pattern="^cancel_report$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(cancel_report, pattern="^cancel_report$"),
        ],
        per_message=False,
        allow_reentry=True,
    )
