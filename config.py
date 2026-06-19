"""
Configuration for the Cyber Fraud Reporting Bot.
Amroha Police — Telegram Bot

All secrets are loaded from .env file.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# =====================================================
# TELEGRAM BOT CONFIG
# =====================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# =====================================================
# GOOGLE APPS SCRIPT WEB APP URL
# =====================================================
# Deploy Code.gs as a web app and paste the URL in .env
# It looks like: https://script.google.com/macros/s/XXXXXXX/exec
APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL", "")

# =====================================================
# REPORT ID FORMAT
# =====================================================
REPORT_ID_PREFIX = "AMR"

# =====================================================
# RISK SCORING THRESHOLDS
# =====================================================
RISK_THRESHOLDS = {
    1: "Low",
    5: "Medium",
    20: "High",
    50: "Critical",
}

# =====================================================
# FRAUD TYPES
# =====================================================
FRAUD_TYPES = [
    "UPI Fraud",
    "OTP Fraud",
    "Loan Fraud",
    "Job Scam",
    "Investment Scam",
    "Website Scam",
    "Other",
]

# =====================================================
# BOT MESSAGES
# =====================================================
WELCOME_MESSAGE = (
    "🚔 *Welcome to Amroha Police Cyber Fraud Reporting System*\n\n"
    "This bot helps you report cyber fraud quickly and securely.\n"
    "Your report will be sent directly to Amroha Police Cyber Cell.\n\n"
    "Choose an option below:"
)

REPORT_SUCCESS_MESSAGE = (
    "✅ *Report Submitted Successfully!*\n\n"
    "📋 Report ID: `{report_id}`\n"
    "🔢 Duplicate Count: {duplicate_count}\n"
    "⚠️ Risk Level: *{risk_level}*\n\n"
    "Please save your Report ID to check status later.\n"
    "Our cyber cell team will review your complaint soon."
)
