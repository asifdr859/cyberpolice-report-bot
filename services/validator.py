"""
Validator Service
Validates UPI IDs, URLs, phone numbers, amounts, and dates.
"""

import re
from datetime import datetime


def validate_upi(upi_id: str) -> bool:
    """
    Validate UPI ID format.
    Valid examples: abc@paytm, test@ybl, demo@okaxis
    """
    pattern = r'^[a-zA-Z0-9._\-]+@[a-zA-Z]+$'
    return bool(re.match(pattern, upi_id.strip()))


def validate_url(url: str) -> bool:
    """
    Validate that a URL starts with http:// or https://
    """
    url = url.strip().lower()
    return url.startswith("http://") or url.startswith("https://")


def validate_phone(phone: str) -> bool:
    """
    Validate Indian 10-digit mobile number.
    """
    phone = phone.strip()
    # Remove country code if present
    if phone.startswith("+91"):
        phone = phone[3:]
    elif phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]

    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_amount(amount_str: str) -> float | None:
    """
    Validate and parse a monetary amount.
    Returns the float value if valid, None otherwise.
    """
    try:
        # Remove currency symbols and commas
        cleaned = amount_str.strip().replace("₹", "").replace(",", "").replace("Rs", "").replace("rs", "")
        amount = float(cleaned)
        if amount > 0:
            return amount
        return None
    except (ValueError, TypeError):
        return None


def validate_date(date_str: str) -> str | None:
    """
    Parse a date string in common Indian formats.
    Returns standardised DD-MM-YYYY string if valid, None otherwise.
    """
    formats = [
        "%d-%m-%Y",    # 18-06-2026
        "%d/%m/%Y",    # 18/06/2026
        "%d.%m.%Y",    # 18.06.2026
        "%Y-%m-%d",    # 2026-06-18
        "%d %m %Y",    # 18 06 2026
        "%d-%m-%y",    # 18-06-26
        "%d/%m/%y",    # 18/06/26
    ]
    date_str = date_str.strip()
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%d-%m-%Y")
        except ValueError:
            continue
    return None


def classify_identifier(text: str) -> str:
    """
    Classify the user's input as UPI, URL, or Phone number.
    Returns: 'upi', 'url', 'phone', or 'unknown'
    """
    text = text.strip()
    if validate_upi(text):
        return "upi"
    if validate_url(text):
        return "url"
    if validate_phone(text):
        return "phone"
    return "unknown"
