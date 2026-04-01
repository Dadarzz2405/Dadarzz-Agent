"""
drive_tool.py — Google Drive integration.
Actions: list_files, search_files, upload_file, download_file, delete_file, share_file.
"""

import json
import os
from pathlib import Path
from memory.db import append_activity

try:
    from googleapiclient.discovery import build as google_build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from google.oauth2.credentials import Credentials
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


def _get_drive_service(google_token):
    """Build Drive API service from stored token."""
    if not google_token or google_token == "placeholder_token":
        return None
    if not HAS_GOOGLE:
        return None
    try:
        creds = Credentials.from_authorized_user_info(json.loads(google_token))
        return google_build("drive", "v3", credentials=creds)
    except Exception:
        return None


def execute(action, params, user_id, google_token=None):
    """Route drive actions."""
    actions = {
        "list_files": list_files,
        "search_files": search_files,
        "upload_file": upload_file,
        "download_file": download_file,
        "delete_file": delete_file,
        "share_file": share_file,
    }
    fn = actions.get(action)
    if fn:
        return fn(params, user_id, google_token)
    return json.dumps({"error": f"Unknown drive action: {action}"})


def list_files(params, user_id, google_token):
    """List files in Drive or a specific folder."""
    folder = params.get("folder", "")
    service = _get_drive_service(google_token)

    if service:
        try:
            query = f"'{folder}' in parents" if folder else None
            results = service.files().list(
                q=query, pageSize=20,
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute()
            files = results.get("files", [])
            items = [{"name": f["name"], "id": f["id"], "type": f["mimeType"],
                      "modified": f.get("modifiedTime", "")} for f in files]
            return json.dumps({"files": items, "count": len(items)})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        return json.dumps({
            "status": "simulated",
            "files": [
                {"name": "Biology Notes.docx", "type": "document", "modified": "2025-03-20"},
                {"name": "Math Homework.pdf", "type": "pdf", "modified": "2025-03-22"},
                {"name": "History Essay Draft.docx", "type": "document", "modified": "2025-03-24"},
            ],
            "message": "Showing sample files. Connect Google Drive for real data."
        })


def search_files(params, user_id, google_token):
    """Search Drive by name or type."""
    query = params.get("query", "")
    service = _get_drive_service(google_token)

    if service:
        try:
            results = service.files().list(
                q=f"name contains '{query}'", pageSize=20,
                fields="files(id, name, mimeType, webViewLink)"
            ).execute()
            files = results.get("files", [])
            items = [{"name": f["name"], "id": f["id"], "link": f.get("webViewLink", "")}
                     for f in files]
            return json.dumps({"files": items, "count": len(items)})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        return json.dumps({
            "status": "simulated",
            "query": query,
            "files": [],
            "message": f"Search for '{query}' — connect Google Drive for real results."
        })


def upload_file(params, user_id, google_token):
    """Upload a local file to Drive."""
    local_path = params.get("local_path", "")
    name = params.get("name", "")
    service = _get_drive_service(google_token)

    if not local_path or not Path(local_path).exists():
        return json.dumps({"error": f"File not found: {local_path}"})

    if not name:
        name = Path(local_path).name

    if service:
        try:
            file_metadata = {"name": name}
            media = MediaFileUpload(local_path)
            file = service.files().create(
                body=file_metadata, media_body=media, fields="id, webViewLink"
            ).execute()
            append_activity(user_id, "uploaded_file", name)
            return json.dumps({
                "status": "uploaded",
                "file_id": file.get("id"),
                "link": file.get("webViewLink", ""),
                "name": name,
            })
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        append_activity(user_id, "uploaded_file_simulated", name)
        return json.dumps({
            "status": "uploaded_simulated",
            "name": name,
            "message": f"Upload of '{name}' simulated. Connect Google Drive for real uploads."
        })


def download_file(params, user_id, google_token):
    """Download a file from Drive."""
    file_id = params.get("file_id", "")
    name = params.get("name", "downloaded_file")
    service = _get_drive_service(google_token)

    if service and file_id:
        try:
            import io
            request = service.files().get_media(fileId=file_id)
            dest = Path.home() / "Downloads" / name
            fh = io.FileIO(str(dest), "wb")
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            append_activity(user_id, "downloaded_file", f"{name} → {dest}")
            return json.dumps({"status": "downloaded", "path": str(dest), "name": name})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        return json.dumps({
            "status": "simulated",
            "message": f"Download of '{name}' simulated. Connect Google Drive for real downloads."
        })


def delete_file(params, user_id, google_token):
    """Move a file to trash."""
    file_id = params.get("file_id", "")
    name = params.get("name", "unknown")
    service = _get_drive_service(google_token)

    if service and file_id:
        try:
            service.files().update(fileId=file_id, body={"trashed": True}).execute()
            append_activity(user_id, "deleted_drive_file", name)
            return json.dumps({"status": "trashed", "name": name})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        append_activity(user_id, "deleted_drive_file_simulated", name)
        return json.dumps({
            "status": "trashed_simulated",
            "name": name,
            "message": f"Deletion of '{name}' simulated."
        })


def share_file(params, user_id, google_token):
    """Share a file with an email address."""
    file_id = params.get("file_id", "")
    name = params.get("name", "unknown")
    email = params.get("email", "")
    service = _get_drive_service(google_token)

    if not email:
        return json.dumps({"error": "No email provided for sharing"})

    if service and file_id:
        try:
            permission = {"type": "user", "role": "reader", "emailAddress": email}
            service.permissions().create(fileId=file_id, body=permission).execute()
            append_activity(user_id, "shared_file", f"{name} with {email}")
            return json.dumps({"status": "shared", "name": name, "shared_with": email})
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        append_activity(user_id, "shared_file_simulated", f"{name} with {email}")
        return json.dumps({
            "status": "shared_simulated",
            "name": name,
            "shared_with": email,
            "message": "Sharing simulated."
        })
