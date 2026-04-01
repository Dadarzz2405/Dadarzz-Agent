"""
calendar_tool.py — Google Calendar integration.
Actions: create_event, list_events, find_deadlines, delete_event.
"""

import json
from datetime import datetime, timedelta
from memory.db import append_activity

try:
    import dateparser
    HAS_DATEPARSER = True
except ImportError:
    HAS_DATEPARSER = False

try:
    from googleapiclient.discovery import build as google_build
    from google.oauth2.credentials import Credentials
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


def _get_calendar_service(google_token):
    """Build Calendar API service from stored token."""
    if not google_token or google_token == "placeholder_token":
        return None
    if not HAS_GOOGLE:
        return None
    try:
        creds = Credentials.from_authorized_user_info(json.loads(google_token))
        return google_build("calendar", "v3", credentials=creds)
    except Exception:
        return None


def _parse_date(date_str):
    """Parse natural language date string to datetime."""
    if HAS_DATEPARSER:
        parsed = dateparser.parse(date_str, settings={"PREFER_DATES_FROM": "future"})
        if parsed:
            return parsed
    # Fallback: try standard formats
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _parse_time(time_str):
    """Parse time string like '15:00' or '3pm'."""
    if HAS_DATEPARSER:
        parsed = dateparser.parse(time_str)
        if parsed:
            return parsed.strftime("%H:%M")
    # Simple fallback
    for fmt in ["%H:%M", "%I:%M%p", "%I%p"]:
        try:
            return datetime.strptime(time_str.replace(" ", ""), fmt).strftime("%H:%M")
        except ValueError:
            continue
    return "12:00"


def execute(action, params, user_id, google_token=None):
    """Route calendar actions."""
    if action == "create_event":
        return create_event(params, user_id, google_token)
    elif action == "list_events":
        return list_events(params, user_id, google_token)
    elif action == "find_deadlines":
        return find_deadlines(params, user_id, google_token)
    elif action == "delete_event":
        return delete_event(params, user_id, google_token)
    else:
        return json.dumps({"error": f"Unknown calendar action: {action}"})


def create_event(params, user_id, google_token):
    """Create a new calendar event."""
    title = params.get("title", "Untitled Event")
    date_str = params.get("date", "")
    time_str = params.get("time", "12:00")
    duration = int(params.get("duration_minutes", 60))

    event_date = _parse_date(date_str) if date_str else datetime.now() + timedelta(days=1)
    time_parsed = _parse_time(time_str)

    if event_date:
        hour, minute = map(int, time_parsed.split(":"))
        event_date = event_date.replace(hour=hour, minute=minute, second=0)
    else:
        event_date = datetime.now() + timedelta(days=1)

    end_date = event_date + timedelta(minutes=duration)

    service = _get_calendar_service(google_token)

    if service:
        event_body = {
            "summary": title,
            "start": {"dateTime": event_date.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_date.isoformat(), "timeZone": "UTC"},
        }
        try:
            event = service.events().insert(calendarId="primary", body=event_body).execute()
            append_activity(user_id, "created_event", f"{title} — {event_date.strftime('%Y-%m-%d %H:%M')}")
            return json.dumps({
                "status": "created",
                "event_id": event.get("id"),
                "link": event.get("htmlLink"),
                "title": title,
                "date": event_date.strftime("%Y-%m-%d"),
                "time": event_date.strftime("%H:%M"),
            })
        except Exception as e:
            return json.dumps({"error": f"Failed to create event: {str(e)}"})
    else:
        # Simulation mode
        append_activity(user_id, "created_event_simulated",
                       f"{title} — {event_date.strftime('%Y-%m-%d %H:%M')}")
        return json.dumps({
            "status": "created_simulated",
            "title": title,
            "date": event_date.strftime("%Y-%m-%d"),
            "time": event_date.strftime("%H:%M"),
            "duration_minutes": duration,
            "message": "Event created (simulated — connect Google Calendar for real events)."
        })


def list_events(params, user_id, google_token):
    """List upcoming events."""
    period = params.get("period", "today")
    service = _get_calendar_service(google_token)

    now = datetime.utcnow()
    if period == "this_week":
        end = now + timedelta(days=7)
    else:
        end = now.replace(hour=23, minute=59, second=59)

    if service:
        try:
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now.isoformat() + "Z",
                timeMax=end.isoformat() + "Z",
                maxResults=20,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            items = []
            for ev in events:
                start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
                items.append({"title": ev.get("summary", "Untitled"), "start": start})
            return json.dumps({"events": items, "count": len(items), "period": period})
        except Exception as e:
            return json.dumps({"error": f"Failed to list events: {str(e)}"})
    else:
        return json.dumps({
            "status": "simulated",
            "period": period,
            "events": [
                {"title": "Math Class", "start": now.strftime("%Y-%m-%d 09:00")},
                {"title": "Biology Lab", "start": now.strftime("%Y-%m-%d 14:00")},
            ],
            "message": "Showing sample events. Connect Google Calendar for real data."
        })


def find_deadlines(params, user_id, google_token):
    """Find events within the next 24 hours (used by notifier)."""
    service = _get_calendar_service(google_token)
    now = datetime.utcnow()
    end = now + timedelta(hours=24)

    if service:
        try:
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now.isoformat() + "Z",
                timeMax=end.isoformat() + "Z",
                maxResults=50,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            deadlines = []
            for ev in events:
                start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
                deadlines.append({
                    "title": ev.get("summary", "Untitled"),
                    "due_at": start,
                    "event_id": ev.get("id"),
                })
            return json.dumps({"deadlines": deadlines, "count": len(deadlines)})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        return json.dumps({
            "status": "simulated",
            "deadlines": [],
            "message": "No deadlines (Google Calendar not connected)."
        })


def delete_event(params, user_id, google_token):
    """Delete a calendar event by title (searches for match)."""
    title = params.get("title", "")
    service = _get_calendar_service(google_token)

    if service and title:
        try:
            now = datetime.utcnow()
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now.isoformat() + "Z",
                maxResults=50,
                singleEvents=True,
                q=title
            ).execute()
            events = events_result.get("items", [])
            if events:
                event = events[0]
                service.events().delete(calendarId="primary", eventId=event["id"]).execute()
                append_activity(user_id, "deleted_event", title)
                return json.dumps({"status": "deleted", "title": event.get("summary", title)})
            return json.dumps({"error": f"No event found matching '{title}'"})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        append_activity(user_id, "deleted_event_simulated", title)
        return json.dumps({
            "status": "deleted_simulated",
            "title": title,
            "message": "Event deletion simulated."
        })
