"""
Google Sheets Service (via Google Apps Script Web API)
Sends HTTP requests to the deployed Apps Script web app.
No Google credentials needed on the Python side.
"""

import logging
from datetime import datetime

import httpx

from config import APPS_SCRIPT_URL, RISK_THRESHOLDS

logger = logging.getLogger(__name__)

# Timeout for Apps Script requests (seconds)
REQUEST_TIMEOUT = 30.0


async def _post_to_apps_script(payload: dict) -> dict:
    """
    Send a POST request to the Google Apps Script web app.
    Returns the JSON response as a dict.
    """
    if not APPS_SCRIPT_URL:
        logger.warning("APPS_SCRIPT_URL is not set in config.py!")
        return {"success": False, "error": "Apps Script URL not configured"}

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                APPS_SCRIPT_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error("Apps Script request timed out")
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        logger.error("Apps Script request failed: %s", e)
        return {"success": False, "error": str(e)}


async def get_report_count() -> int:
    """Get the total number of reports in the sheet."""
    result = await _post_to_apps_script({"action": "get_report_count"})
    if result.get("success"):
        return result.get("count", 0)
    return 0


async def add_report(report_data: dict) -> bool:
    """
    Add a new fraud report to the Google Sheet via Apps Script.

    Args:
        report_data: Dictionary with report fields.

    Returns:
        True if successful.
    """
    result = await _post_to_apps_script({
        "action": "add_report",
        "report": report_data,
    })
    if result.get("success"):
        logger.info("Report %s added via Apps Script", report_data.get("report_id"))
        return True
    logger.error("Failed to add report: %s", result.get("error"))
    return False


async def count_duplicates(identifier: str, id_type: str = "upi") -> int:
    """
    Count how many times a UPI ID or website has been reported.
    """
    result = await _post_to_apps_script({
        "action": "count_duplicates",
        "identifier": identifier,
        "id_type": id_type,
    })
    if result.get("success"):
        return result.get("count", 0)
    return 0


def calculate_risk(duplicate_count: int) -> str:
    """
    Calculate risk level based on duplicate count.

    Thresholds:
        1  → Low
        5  → Medium
        20 → High
        50 → Critical
    """
    risk = "Low"
    for threshold, level in sorted(RISK_THRESHOLDS.items()):
        if duplicate_count >= threshold:
            risk = level
    return risk


async def search_report(report_id: str) -> dict | None:
    """
    Search for a report by Report ID.
    Returns dict with report data, or None if not found.
    """
    result = await _post_to_apps_script({
        "action": "search_report",
        "report_id": report_id,
    })
    if result.get("success") and result.get("found"):
        return result.get("report")
    return None


async def update_status(report_id: str, new_status: str) -> bool:
    """Update the status of a report."""
    result = await _post_to_apps_script({
        "action": "update_status",
        "report_id": report_id,
        "status": new_status,
    })
    return result.get("success", False) and result.get("updated", False)


async def get_dashboard_stats() -> dict:
    """Get aggregate statistics for the dashboard."""
    result = await _post_to_apps_script({"action": "get_dashboard_stats"})
    if result.get("success"):
        return {"total": result.get("total", 0), "today": result.get("today", 0)}
    return {"total": 0, "today": 0}
