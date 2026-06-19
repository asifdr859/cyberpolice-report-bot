"""
Report ID Generator
Generates unique report IDs in format: AMR-YYYY-NNN
Example: AMR-2026-001, AMR-2026-002, ...
"""

from datetime import datetime

from config import REPORT_ID_PREFIX


def generate_report_id(existing_count: int) -> str:
    """
    Generate a new report ID based on the current year and
    the count of existing reports.

    Args:
        existing_count: Number of existing reports in the sheet.

    Returns:
        A string like 'AMR-2026-001'.
    """
    year = datetime.now().year
    next_number = existing_count + 1
    return f"{REPORT_ID_PREFIX}-{year}-{next_number:03d}"
