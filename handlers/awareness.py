"""
Awareness Tips Handler
Displays cyber fraud awareness tips and safety information.
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

logger = logging.getLogger(__name__)

TIPS = [
    {
        "title": "🔐 UPI Fraud Prevention",
        "tips": [
            "Never share your UPI PIN with anyone",
            "You do NOT need to enter PIN to RECEIVE money",
            "Verify the receiver's name before sending money",
            "Do not scan unknown QR codes",
            "Use only official apps (BHIM, Google Pay, PhonePe)",
        ],
    },
    {
        "title": "🔑 OTP & Password Safety",
        "tips": [
            "Never share OTP with anyone, even bank officials",
            "Banks never ask for OTP over phone or SMS",
            "Use strong, unique passwords for each account",
            "Enable two-factor authentication",
            "Do not click on links in suspicious SMS/emails",
        ],
    },
    {
        "title": "💼 Job & Loan Scam Alerts",
        "tips": [
            "No legitimate job requires you to pay money upfront",
            "Verify company details on official websites",
            "Be suspicious of 'work from home' offers with high pay",
            "Never pay 'processing fees' for loans via unknown apps",
            "Check RBI license before using any loan app",
        ],
    },
    {
        "title": "📈 Investment Scam Warning",
        "tips": [
            "If returns sound too good to be true, it's likely a scam",
            "Verify with SEBI before investing in any scheme",
            "Beware of crypto/forex trading groups on Telegram/WhatsApp",
            "Never invest based on tips from unknown callers",
            "Check the official SEBI registered intermediaries list",
        ],
    },
    {
        "title": "🌐 Website & Online Shopping Safety",
        "tips": [
            "Check for 'https://' and padlock icon before entering details",
            "Verify website URLs carefully (scammers use similar names)",
            "Avoid deals that seem unrealistically cheap",
            "Use Cash on Delivery when possible on new websites",
            "Report suspicious websites to cybercrime.gov.in",
        ],
    },
]

HELPLINE_INFO = (
    "📞 *Emergency Helplines*\n\n"
    "🚔 National Cyber Crime Helpline: *1930*\n"
    "🌐 Online Portal: cybercrime.gov.in\n"
    "📱 Amroha Police: *112*\n\n"
    "⏰ Report fraud within 24 hours for best chance of recovery!"
)


async def awareness_tips_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show awareness tips categories."""
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = []
    for i, tip_group in enumerate(TIPS):
        keyboard.append([
            InlineKeyboardButton(tip_group["title"], callback_data=f"tip_{i}")
        ])
    keyboard.append([
        InlineKeyboardButton("📞 Emergency Helplines", callback_data="tip_helplines")
    ])
    keyboard.append([
        InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "💡 *Cyber Fraud Awareness Tips*\n\n"
        "Stay safe online! Select a category to learn more:"
    )

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def show_tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show tips for a specific category."""
    query = update.callback_query
    await query.answer()

    tip_index = int(query.data.replace("tip_", ""))
    tip_group = TIPS[tip_index]

    tips_text = "\n".join(f"  • {tip}" for tip in tip_group["tips"])
    text = f"{tip_group['title']}\n\n{tips_text}"

    keyboard = [
        [InlineKeyboardButton("◀️ Back to Tips", callback_data="awareness_tips")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def show_helplines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show emergency helpline numbers."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("◀️ Back to Tips", callback_data="awareness_tips")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        HELPLINE_INFO, parse_mode="Markdown", reply_markup=reply_markup
    )


def get_awareness_handlers():
    """Return the handlers for awareness tips."""
    return [
        CallbackQueryHandler(awareness_tips_start, pattern="^awareness_tips$"),
        CallbackQueryHandler(show_tip, pattern=r"^tip_\d+$"),
        CallbackQueryHandler(show_helplines, pattern="^tip_helplines$"),
    ]
