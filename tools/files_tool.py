"""
files_tool.py — Local file management with safety restrictions.
Actions: create_file, read_file, move_file, delete_file, list_dir, create_dir.
All paths restricted to user's home directory.
"""

import json
import os
import shutil
from pathlib import Path

from memory.db import append_activity

# Safety: all operations restricted to home directory
HOME = Path.home()


def _safe_path(path_str):
    """Resolve a path and verify it's within the home directory.
    Returns (Path, error_str). If error_str is not None, the path is unsafe."""
    try:
        p = Path(path_str).expanduser().resolve()
        # Block path traversal
        if ".." in str(path_str):
            return None, "Path traversal (..) is not allowed."
        if not str(p).startswith(str(HOME)):
            return None, f"Access denied: path must be within {HOME}"
        return p, None
    except Exception as e:
        return None, f"Invalid path: {str(e)}"


def execute(action, params, user_id):
    """Route file actions."""
    actions = {
        "create_file": create_file,
        "read_file": read_file,
        "move_file": move_file,
        "delete_file": delete_file,
        "list_dir": list_dir,
        "create_dir": create_dir,
    }
    fn = actions.get(action)
    if fn:
        return fn(params, user_id)
    return json.dumps({"error": f"Unknown files action: {action}"})


def create_file(params, user_id):
    """Create a new file with given content."""
    path_str = params.get("path", "")
    content = params.get("content", "")

    p, err = _safe_path(path_str)
    if err:
        return json.dumps({"error": err})

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        append_activity(user_id, "created_file", str(p))
        return json.dumps({"status": "created", "path": str(p)})
    except Exception as e:
        return json.dumps({"error": f"Failed to create file: {str(e)}"})


def read_file(params, user_id):
    """Read content of a local file."""
    path_str = params.get("path", "")

    p, err = _safe_path(path_str)
    if err:
        return json.dumps({"error": err})

    if not p.exists():
        return json.dumps({"error": f"File not found: {path_str}"})

    if not p.is_file():
        return json.dumps({"error": f"Not a file: {path_str}"})

    try:
        content = p.read_text(errors="ignore")
        # Limit content size for AI context
        if len(content) > 10000:
            content = content[:10000] + "\n... (truncated)"
        return json.dumps({"status": "read", "path": str(p), "content": content})
    except Exception as e:
        return json.dumps({"error": f"Failed to read file: {str(e)}"})


def move_file(params, user_id):
    """Move or rename a file."""
    src_str = params.get("src", "")
    dest_str = params.get("dest", "")

    src, err = _safe_path(src_str)
    if err:
        return json.dumps({"error": f"Source: {err}"})

    dest, err = _safe_path(dest_str)
    if err:
        return json.dumps({"error": f"Destination: {err}"})

    if not src.exists():
        return json.dumps({"error": f"Source not found: {src_str}"})

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        append_activity(user_id, "moved_file", f"{src} → {dest}")
        return json.dumps({"status": "moved", "from": str(src), "to": str(dest)})
    except Exception as e:
        return json.dumps({"error": f"Failed to move file: {str(e)}"})


def delete_file(params, user_id):
    """Delete a file. The AI should confirm with the user first."""
    path_str = params.get("path", "")

    p, err = _safe_path(path_str)
    if err:
        return json.dumps({"error": err})

    if not p.exists():
        return json.dumps({"error": f"File not found: {path_str}"})

    try:
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(str(p))
        append_activity(user_id, "deleted_file", str(p))
        return json.dumps({"status": "deleted", "path": str(p)})
    except Exception as e:
        return json.dumps({"error": f"Failed to delete: {str(e)}"})


def list_dir(params, user_id):
    """List files in a directory."""
    path_str = params.get("path", "~")

    p, err = _safe_path(path_str)
    if err:
        return json.dumps({"error": err})

    if not p.exists():
        return json.dumps({"error": f"Directory not found: {path_str}"})

    if not p.is_dir():
        return json.dumps({"error": f"Not a directory: {path_str}"})

    try:
        items = []
        for item in sorted(p.iterdir()):
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return json.dumps({"status": "listed", "path": str(p), "items": items[:100]})
    except Exception as e:
        return json.dumps({"error": f"Failed to list directory: {str(e)}"})


def create_dir(params, user_id):
    """Create a new directory."""
    path_str = params.get("path", "")

    p, err = _safe_path(path_str)
    if err:
        return json.dumps({"error": err})

    try:
        p.mkdir(parents=True, exist_ok=True)
        append_activity(user_id, "created_dir", str(p))
        return json.dumps({"status": "created", "path": str(p)})
    except Exception as e:
        return json.dumps({"error": f"Failed to create directory: {str(e)}"})
