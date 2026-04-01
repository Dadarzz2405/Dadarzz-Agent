"""
gmail_tool.py — Gmail integration: draft, send, read_inbox.
Uses Google Gmail API via service credentials stored in user's google_token.
"""

import json
from memory.db import save_draft, get_draft, update_draft_status, append_activity

# Google API imports (used when real OAuth token is available)
try:
    from googleapiclient.discovery import build as google_build
    from google.oauth2.credentials import Credentials
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


def _get_gmail_service(google_token):
    """Build Gmail API service from stored token."""
    if not google_token or google_token == "placeholder_token":
        return None
    if not HAS_GOOGLE:
        return None
    try:
        creds = Credentials.from_authorized_user_info(json.loads(google_token))
        return google_build("gmail", "v1", credentials=creds)
    except Exception:
        return None


def execute(action, params, user_id, google_token=None):
    """Route gmail actions."""
    if action == "draft":
        return draft(params, user_id)
    elif action == "send":
        return send_by_id(params, user_id, google_token)
    elif action == "read_inbox":
        return read_inbox(params, user_id, google_token)
    else:
        return json.dumps({"error": f"Unknown gmail action: {action}"})


def draft(params, user_id):
    """Create an email draft and store in DB for preview."""
    instruction = params.get("instruction", "")
    to_addr = params.get("to", "recipient@example.com")
    subject = params.get("subject", "No Subject")
    body = params.get("body", instruction)

    draft_id = save_draft(user_id, to_addr, subject, body)
    append_activity(user_id, "email_drafted", f"Draft #{draft_id}: {subject}")

    return json.dumps({
        "status": "drafted",
        "draft_id": draft_id,
        "to": to_addr,
        "subject": subject,
        "body": body,
        "message": "Email draft created. The user can preview and confirm sending in the UI."
    })


def send(user_id, draft_dict):
    """Send a draft email. Called from main.py on user confirmation."""
    service = None  # Would use _get_gmail_service in production

    if service:
        import base64
        from email.mime.text import MIMEText
        msg = MIMEText(draft_dict["body"])
        msg["to"] = draft_dict["to_addr"]
        msg["subject"] = draft_dict["subject"]
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        try:
            service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            return "✅ Email sent successfully!"
        except Exception as e:
            return f"❌ Failed to send email: {str(e)}"
    else:
        # Simulation mode — no real Google credentials
        append_activity(user_id, "email_sent_simulated",
                       f"To: {draft_dict['to_addr']} | Subject: {draft_dict['subject']}")
        return (f"📧 Email simulated (Google not connected).\n"
                f"To: {draft_dict['to_addr']}\n"
                f"Subject: {draft_dict['subject']}\n"
                f"Body: {draft_dict['body'][:200]}")


def send_by_id(params, user_id, google_token):
    """Send by draft ID (called via tool dispatch)."""
    draft_id = params.get("draft_id")
    if not draft_id:
        return json.dumps({"error": "No draft_id provided"})
    d = get_draft(int(draft_id))
    if not d:
        return json.dumps({"error": f"Draft #{draft_id} not found"})
    result = send(user_id, d)
    update_draft_status(int(draft_id), "sent")
    return json.dumps({"status": "sent", "message": result})


def read_inbox(params, user_id, google_token):
    """Read recent inbox messages."""
    count = int(params.get("count", 5))
    service = _get_gmail_service(google_token)

    if service:
        try:
            results = service.users().messages().list(
                userId="me", maxResults=count, labelIds=["INBOX"]
            ).execute()
            messages = results.get("messages", [])
            emails = []
            for msg_meta in messages[:count]:
                msg = service.users().messages().get(
                    userId="me", id=msg_meta["id"], format="metadata",
                    metadataHeaders=["Subject", "From"]
                ).execute()
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                emails.append({
                    "from": headers.get("From", "Unknown"),
                    "subject": headers.get("Subject", "No Subject"),
                    "snippet": msg.get("snippet", ""),
                })
            return json.dumps({"emails": emails, "count": len(emails)})
        except Exception as e:
            return json.dumps({"error": f"Failed to read inbox: {str(e)}"})
    else:
        return json.dumps({
            "status": "simulated",
            "message": "Google not connected. Connect your Google account in Settings to read real emails.",
            "emails": [
                {"from": "teacher@school.edu", "subject": "Assignment Due Reminder", "snippet": "Don't forget to submit..."},
                {"from": "classmate@school.edu", "subject": "Study Group Tonight", "snippet": "Hey, are you coming to..."},
            ]
        })
