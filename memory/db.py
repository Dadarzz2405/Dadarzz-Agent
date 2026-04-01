import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.db')


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            api_key_enc TEXT NOT NULL,
            google_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            detail TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_at TIMESTAMP NOT NULL,
            notified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS email_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            to_addr TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()


# ── User CRUD ──────────────────────────────────────────────

def get_user(user_id=1):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def create_user(display_name, api_key_enc, google_token=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (display_name, api_key_enc, google_token)
        VALUES (?, ?, ?)
    ''', (display_name, api_key_enc, google_token))
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return user_id


def update_user(user_id, display_name=None, api_key_enc=None, google_token=None):
    conn = get_connection()
    c = conn.cursor()
    fields = []
    values = []
    if display_name is not None:
        fields.append("display_name = ?")
        values.append(display_name)
    if api_key_enc is not None:
        fields.append("api_key_enc = ?")
        values.append(api_key_enc)
    if google_token is not None:
        fields.append("google_token = ?")
        values.append(google_token)

    if not fields:
        conn.close()
        return

    values.append(user_id)
    query = "UPDATE users SET {} WHERE id = ?".format(', '.join(fields))
    c.execute(query, values)
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM activity_log WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM email_drafts WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# ── History CRUD ───────────────────────────────────────────

def add_history(user_id, role, content):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO history (user_id, role, content)
        VALUES (?, ?, ?)
    ''', (user_id, role, content))
    conn.commit()
    conn.close()


def get_history(user_id=1, limit=20):
    conn = get_connection()
    history = conn.execute('''
        SELECT role, content, timestamp FROM history
        WHERE user_id = ?
        ORDER BY timestamp ASC LIMIT ?
    ''', (user_id, limit)).fetchall()
    conn.close()
    return [dict(row) for row in history]


def clear_history(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ── Activity Log ───────────────────────────────────────────

def append_activity(user_id, action, detail=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO activity_log (user_id, action, detail)
        VALUES (?, ?, ?)
    ''', (user_id, action, detail))
    conn.commit()
    conn.close()


def get_activity_log(user_id, action_filter=None, limit=100):
    conn = get_connection()
    if action_filter:
        rows = conn.execute('''
            SELECT action, detail, timestamp FROM activity_log
            WHERE user_id = ? AND action = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (user_id, action_filter, limit)).fetchall()
    else:
        rows = conn.execute('''
            SELECT action, detail, timestamp FROM activity_log
            WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (user_id, limit)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ── Notifications ──────────────────────────────────────────

def add_notification(user_id, title, due_at):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO notifications (user_id, title, due_at)
        VALUES (?, ?, ?)
    ''', (user_id, title, due_at))
    conn.commit()
    conn.close()


def get_pending_notifications(user_id):
    conn = get_connection()
    rows = conn.execute('''
        SELECT id, title, due_at FROM notifications
        WHERE user_id = ? AND notified = 0
        ORDER BY due_at ASC
    ''', (user_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_notified(notification_id):
    conn = get_connection()
    conn.execute("UPDATE notifications SET notified = 1 WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()


# ── Email Drafts ───────────────────────────────────────────

def save_draft(user_id, to_addr, subject, body):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO email_drafts (user_id, to_addr, subject, body)
        VALUES (?, ?, ?, ?)
    ''', (user_id, to_addr, subject, body))
    conn.commit()
    draft_id = c.lastrowid
    conn.close()
    return draft_id


def get_draft(draft_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM email_drafts WHERE id = ?", (draft_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_draft_status(draft_id, status):
    conn = get_connection()
    conn.execute("UPDATE email_drafts SET status = ? WHERE id = ?", (status, draft_id))
    conn.commit()
    conn.close()
