import os
import json
import base64
import secrets
from pathlib import Path

from flask import (
    Flask, redirect, url_for, render_template, request,
    jsonify, session, send_file
)
from dotenv import load_dotenv

from memory.db import (
    init_db, get_user, create_user, update_user, delete_user,
    get_history, clear_history, get_activity_log, append_activity,
    get_pending_notifications, mark_notified,
    get_draft, update_draft_status
)
import agent as ai_agent

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit

UPLOAD_DIR = Path("/tmp/dadarzzagent_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize DB on startup
init_db()


# ── Helpers ────────────────────────────────────────────────

def current_user():
    """Return user dict from session or None."""
    uid = session.get("user_id")
    if uid:
        return get_user(uid)
    return None


def require_user(f):
    """Decorator: redirect to /setup if no session user."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("setup"))
        return f(*args, **kwargs)
    return wrapper


def encode_key(raw_key):
    """Simple base64 obfuscation for API key storage."""
    return base64.b64encode(raw_key.encode()).decode()


def decode_key(enc_key):
    """Reverse base64 obfuscation."""
    try:
        return base64.b64decode(enc_key.encode()).decode()
    except Exception:
        return enc_key


# ── Routes ─────────────────────────────────────────────────

@app.route("/")
def index():
    user = current_user()
    if not user:
        return redirect(url_for("setup"))
    return redirect(url_for("chat"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        display_name = request.form.get("display_name", "Student").strip()
        api_key = request.form.get("api_key", "").strip()

        if not api_key:
            return render_template("setup.html", error="API key is required.")

        # Test the API key with a quick Groq call
        test_result = ai_agent.test_api_key(api_key)
        if not test_result["ok"]:
            return render_template(
                "setup.html",
                error=f"API key test failed: {test_result['error']}"
            )

        enc_key = encode_key(api_key)
        uid = create_user(display_name, enc_key)
        session["user_id"] = uid
        append_activity(uid, "setup_complete", f"User '{display_name}' created")
        return redirect(url_for("chat"))

    return render_template("setup.html")


@app.route("/oauth2callback")
def oauth2callback():
    """Google OAuth callback — placeholder for real OAuth flow."""
    # In production: exchange code for token, store in DB
    # For now: store a dummy token so the user can proceed
    user = current_user()
    if user:
        update_user(user["id"], google_token="placeholder_token")
        append_activity(user["id"], "google_auth", "Google account connected")
    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:60px">
    <h2>✅ Google Connected</h2>
    <p>You can close this tab and return to setup.</p>
    <script>setTimeout(()=>window.close(),2000)</script>
    </body></html>
    """


@app.route("/api/test-key", methods=["POST"])
def test_key():
    """AJAX endpoint to test an API key without submitting the form."""
    data = request.get_json(silent=True) or {}
    api_key = data.get("api_key", "").strip()
    if not api_key:
        return jsonify({"ok": False, "error": "No key provided"})
    result = ai_agent.test_api_key(api_key)
    return jsonify(result)


@app.route("/chat", methods=["GET", "POST"])
@require_user
def chat():
    user = current_user()

    if request.method == "POST":
        # Handle JSON or form data
        if request.is_json:
            data = request.get_json()
            message = data.get("message", "").strip()
            confirm = data.get("confirm")
            draft_id = data.get("draft_id")
        else:
            message = request.form.get("message", "").strip()
            confirm = request.form.get("confirm")
            draft_id = request.form.get("draft_id")

        # Handle email send confirmation
        if confirm == "send_email" and draft_id:
            draft = get_draft(int(draft_id))
            if draft:
                # Attempt to send via gmail tool
                from tools.gmail_tool import send as gmail_send
                result = gmail_send(user["id"], draft)
                update_draft_status(int(draft_id), "sent")
                append_activity(user["id"], "sent_email", f"To: {draft['to_addr']}")
                return jsonify({"response": result})
            return jsonify({"response": "Draft not found."})

        if not message:
            return jsonify({"response": "Please type a message."})

        # Handle file upload for /ask
        uploaded_path = None
        if "file" in request.files:
            f = request.files["file"]
            if f.filename:
                safe_name = f.filename.replace("/", "_").replace("\\", "_")
                uploaded_path = str(UPLOAD_DIR / safe_name)
                f.save(uploaded_path)

        # Decode API key and run agent
        api_key = decode_key(user["api_key_enc"])
        reply = ai_agent.run(
            user_id=user["id"],
            message=message,
            api_key=api_key,
            file_path=uploaded_path,
            google_token=user.get("google_token")
        )

        return jsonify({"response": reply})

    return render_template("index.html", user=user)


@app.route("/log")
@require_user
def log():
    user = current_user()
    action_filter = request.args.get("filter")
    logs = get_activity_log(user["id"], action_filter=action_filter)
    return render_template("log.html", logs=logs, user=user, current_filter=action_filter)


@app.route("/log/export")
@require_user
def log_export():
    """Export activity log as CSV."""
    import csv
    import io
    user = current_user()
    logs = get_activity_log(user["id"], limit=10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Action", "Detail"])
    for entry in logs:
        writer.writerow([entry["timestamp"], entry["action"], entry.get("detail", "")])
    output.seek(0)
    return output.getvalue(), 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=activity_log.csv"
    }


@app.route("/settings", methods=["GET", "POST"])
@require_user
def settings():
    user = current_user()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_key":
            new_key = request.form.get("api_key", "").strip()
            if new_key:
                test = ai_agent.test_api_key(new_key)
                if test["ok"]:
                    update_user(user["id"], api_key_enc=encode_key(new_key))
                    append_activity(user["id"], "settings_update", "API key changed")
                    return render_template("settings.html", user=user, success="API key updated!")
                else:
                    return render_template("settings.html", user=user, error=f"Key test failed: {test['error']}")

        elif action == "clear_history":
            clear_history(user["id"])
            append_activity(user["id"], "clear_history", "Conversation history cleared")
            return render_template("settings.html", user=user, success="History cleared!")

        elif action == "reset":
            uid = user["id"]
            delete_user(uid)
            session.clear()
            return redirect(url_for("setup"))

        return redirect(url_for("settings"))

    return render_template("settings.html", user=user)


@app.route("/notify/check", methods=["POST"])
@require_user
def notify_check():
    user = current_user()
    pending = get_pending_notifications(user["id"])
    # Mark them as notified once delivered
    for n in pending:
        mark_notified(n["id"])
    return jsonify({"notifications": pending})


if __name__ == "__main__":
    # Start notification background thread
    from notifications.notifier import start_notifier
    start_notifier(app)
    app.run(debug=True, port=5000, use_reloader=False)
