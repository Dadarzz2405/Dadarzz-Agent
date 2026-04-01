"""
notifier.py — Background deadline reminder system.
Runs every 15 minutes, checks calendar for upcoming deadlines,
stores notifications in SQLite for the frontend to poll.
"""

import json
import threading
import time
import logging
from datetime import datetime

from memory.db import (
    get_user, add_notification, get_pending_notifications, append_activity
)

logger = logging.getLogger(__name__)

# How often to check (seconds)
CHECK_INTERVAL = 15 * 60  # 15 minutes

_notifier_thread = None
_stop_event = threading.Event()


def start_notifier(app):
    """Start the background notifier thread."""
    global _notifier_thread

    if _notifier_thread and _notifier_thread.is_alive():
        return  # Already running

    _stop_event.clear()
    _notifier_thread = threading.Thread(
        target=_notification_loop,
        args=(app,),
        daemon=True,
        name="DadarzzAgent-Notifier"
    )
    _notifier_thread.start()
    logger.info("Notifier thread started (checking every %d seconds)", CHECK_INTERVAL)


def stop_notifier():
    """Stop the background notifier thread."""
    _stop_event.set()
    if _notifier_thread:
        _notifier_thread.join(timeout=5)
    logger.info("Notifier thread stopped")


def _notification_loop(app):
    """Main loop — runs inside background thread."""
    # Wait a bit before first check to let app start up
    time.sleep(5)

    while not _stop_event.is_set():
        try:
            with app.app_context():
                _check_all_users()
        except Exception as e:
            logger.error("Notifier error: %s", e)

        # Wait for interval or until stopped
        _stop_event.wait(CHECK_INTERVAL)


def _check_all_users():
    """Check deadlines for all users."""
    # Simple approach: check user IDs 1-100 (or until no more users)
    for uid in range(1, 101):
        user = get_user(uid)
        if not user:
            continue

        google_token = user.get("google_token")

        try:
            from tools.calendar_tool import find_deadlines
            result_str = find_deadlines({}, uid, google_token)
            result = json.loads(result_str)

            deadlines = result.get("deadlines", [])
            for deadline in deadlines:
                title = deadline.get("title", "Upcoming Deadline")
                due_at = deadline.get("due_at", "")

                # Calculate time remaining for the notification message
                time_msg = _format_time_remaining(due_at)
                notification_title = f"📚 {title} {time_msg}"

                # Store notification (DB will handle dedup via the notified flag)
                add_notification(uid, notification_title, due_at or datetime.utcnow().isoformat())
                append_activity(uid, "deadline_notification", notification_title)

        except Exception as e:
            logger.debug("Failed to check deadlines for user %d: %s", uid, e)


def _format_time_remaining(due_at_str):
    """Format a human-readable time remaining string."""
    if not due_at_str:
        return "coming up soon!"

    try:
        # Try parsing ISO format
        due = datetime.fromisoformat(due_at_str.replace("Z", "+00:00").replace("+00:00", ""))
        now = datetime.utcnow()
        diff = due - now

        hours = int(diff.total_seconds() / 3600)
        if hours <= 0:
            return "is due NOW! ⏰"
        elif hours == 1:
            return "due in 1 hour!"
        elif hours < 24:
            return f"due in {hours} hours!"
        else:
            days = hours // 24
            return f"due in {days} day{'s' if days > 1 else ''}!"
    except Exception:
        return "coming up soon!"
