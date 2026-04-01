"""
docs_tool.py — Google Docs & Sheets integration.
Actions: read_doc, edit_doc, create_doc, read_sheet, edit_sheet, create_sheet.
"""

import json
from memory.db import append_activity

try:
    from googleapiclient.discovery import build as google_build
    from google.oauth2.credentials import Credentials
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


def _get_docs_service(google_token):
    """Build Docs API service."""
    if not google_token or google_token == "placeholder_token":
        return None
    if not HAS_GOOGLE:
        return None
    try:
        creds = Credentials.from_authorized_user_info(json.loads(google_token))
        return google_build("docs", "v1", credentials=creds)
    except Exception:
        return None


def _get_sheets_service(google_token):
    """Build Sheets API service."""
    if not google_token or google_token == "placeholder_token":
        return None
    if not HAS_GOOGLE:
        return None
    try:
        creds = Credentials.from_authorized_user_info(json.loads(google_token))
        return google_build("sheets", "v4", credentials=creds)
    except Exception:
        return None


def _get_drive_service(google_token):
    """Build Drive API service for file search."""
    if not google_token or google_token == "placeholder_token":
        return None
    if not HAS_GOOGLE:
        return None
    try:
        creds = Credentials.from_authorized_user_info(json.loads(google_token))
        return google_build("drive", "v3", credentials=creds)
    except Exception:
        return None


def _find_file_by_name(google_token, name, mime_filter=None):
    """Search Drive for a file by name, return file ID."""
    drive = _get_drive_service(google_token)
    if not drive:
        return None
    try:
        q = f"name contains '{name}'"
        if mime_filter:
            q += f" and mimeType = '{mime_filter}'"
        results = drive.files().list(q=q, pageSize=1, fields="files(id, name)").execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None
    except Exception:
        return None


def execute(action, params, user_id, google_token=None):
    """Route docs/sheets actions."""
    actions = {
        "read_doc": read_doc,
        "edit_doc": edit_doc,
        "create_doc": create_doc,
        "read_sheet": read_sheet,
        "edit_sheet": edit_sheet,
        "create_sheet": create_sheet,
    }
    fn = actions.get(action)
    if fn:
        return fn(params, user_id, google_token)
    return json.dumps({"error": f"Unknown docs action: {action}"})


def read_doc(params, user_id, google_token):
    """Read text content of a Google Doc."""
    name = params.get("name", "")
    docs = _get_docs_service(google_token)

    if docs:
        doc_id = _find_file_by_name(google_token, name,
                                     "application/vnd.google-apps.document")
        if not doc_id:
            return json.dumps({"error": f"Document '{name}' not found"})
        try:
            doc = docs.documents().get(documentId=doc_id).execute()
            content = ""
            for elem in doc.get("body", {}).get("content", []):
                for para in elem.get("paragraph", {}).get("elements", []):
                    text_run = para.get("textRun", {})
                    content += text_run.get("content", "")
            append_activity(user_id, "read_doc", name)
            return json.dumps({"status": "read", "name": name, "content": content[:5000]})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        return json.dumps({
            "status": "simulated",
            "name": name,
            "content": f"[Simulated content for '{name}']\n\nThis is sample document content. Connect Google Docs for real data.",
            "message": "Connect Google account to read real documents."
        })


def edit_doc(params, user_id, google_token):
    """Edit a Google Doc (append or replace)."""
    name = params.get("name", "")
    content = params.get("content", "")
    mode = params.get("mode", "append")
    docs = _get_docs_service(google_token)

    if docs:
        doc_id = _find_file_by_name(google_token, name,
                                     "application/vnd.google-apps.document")
        if not doc_id:
            return json.dumps({"error": f"Document '{name}' not found"})
        try:
            requests_list = [{
                "insertText": {
                    "location": {"index": 1} if mode == "replace" else {"segmentId": ""},
                    "text": content
                }
            }]
            docs.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests_list}
            ).execute()
            append_activity(user_id, "edited_doc", f"{name} ({mode})")
            return json.dumps({"status": "edited", "name": name, "mode": mode})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        append_activity(user_id, "edited_doc_simulated", f"{name} ({mode})")
        return json.dumps({
            "status": "edited_simulated",
            "name": name,
            "mode": mode,
            "message": f"Edit of '{name}' simulated."
        })


def create_doc(params, user_id, google_token):
    """Create a new Google Doc."""
    title = params.get("title", "Untitled Document")
    content = params.get("content", "")
    docs = _get_docs_service(google_token)

    if docs:
        try:
            doc = docs.documents().create(body={"title": title}).execute()
            doc_id = doc.get("documentId")
            if content:
                docs.documents().batchUpdate(
                    documentId=doc_id,
                    body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]}
                ).execute()
            append_activity(user_id, "created_doc", title)
            return json.dumps({
                "status": "created",
                "title": title,
                "doc_id": doc_id,
                "link": f"https://docs.google.com/document/d/{doc_id}/edit"
            })
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        append_activity(user_id, "created_doc_simulated", title)
        return json.dumps({
            "status": "created_simulated",
            "title": title,
            "message": f"Document '{title}' creation simulated."
        })


def read_sheet(params, user_id, google_token):
    """Read rows from a Google Sheet."""
    name = params.get("name", "")
    range_str = params.get("range", "Sheet1!A1:Z100")
    sheets = _get_sheets_service(google_token)

    if sheets:
        sheet_id = _find_file_by_name(google_token, name,
                                       "application/vnd.google-apps.spreadsheet")
        if not sheet_id:
            return json.dumps({"error": f"Spreadsheet '{name}' not found"})
        try:
            result = sheets.spreadsheets().values().get(
                spreadsheetId=sheet_id, range=range_str
            ).execute()
            values = result.get("values", [])
            append_activity(user_id, "read_sheet", name)
            return json.dumps({"status": "read", "name": name, "rows": values, "count": len(values)})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        return json.dumps({
            "status": "simulated",
            "name": name,
            "rows": [["Subject", "Grade"], ["Math", "A"], ["Biology", "B+"]],
            "message": "Showing sample data. Connect Google Sheets for real data."
        })


def edit_sheet(params, user_id, google_token):
    """Update cells in a Google Sheet."""
    name = params.get("name", "")
    range_str = params.get("range", "Sheet1!A1")
    values = params.get("values", [])
    sheets = _get_sheets_service(google_token)

    if sheets:
        sheet_id = _find_file_by_name(google_token, name,
                                       "application/vnd.google-apps.spreadsheet")
        if not sheet_id:
            return json.dumps({"error": f"Spreadsheet '{name}' not found"})
        try:
            body = {"values": values if isinstance(values, list) else [[values]]}
            sheets.spreadsheets().values().update(
                spreadsheetId=sheet_id, range=range_str,
                valueInputOption="USER_ENTERED", body=body
            ).execute()
            append_activity(user_id, "edited_sheet", f"{name} @ {range_str}")
            return json.dumps({"status": "updated", "name": name, "range": range_str})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        append_activity(user_id, "edited_sheet_simulated", f"{name} @ {range_str}")
        return json.dumps({
            "status": "updated_simulated",
            "name": name,
            "range": range_str,
            "message": "Sheet edit simulated."
        })


def create_sheet(params, user_id, google_token):
    """Create a new Google Sheet."""
    title = params.get("title", "Untitled Spreadsheet")
    sheets = _get_sheets_service(google_token)

    if sheets:
        try:
            spreadsheet = sheets.spreadsheets().create(
                body={"properties": {"title": title}}
            ).execute()
            sheet_id = spreadsheet.get("spreadsheetId")
            append_activity(user_id, "created_sheet", title)
            return json.dumps({
                "status": "created",
                "title": title,
                "sheet_id": sheet_id,
                "link": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
            })
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        append_activity(user_id, "created_sheet_simulated", title)
        return json.dumps({
            "status": "created_simulated",
            "title": title,
            "message": f"Spreadsheet '{title}' creation simulated."
        })
