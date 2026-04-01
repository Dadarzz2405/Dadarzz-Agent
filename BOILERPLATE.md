# 🛠️ SchoolAgent — Boilerplate Guide

> Everything you need to scaffold the project from zero and get it running.
> Dev: Arch Linux (UTM) | Target: macOS M1 | Python: 3.9+

---

## 📁 Project Structure

```
school-agent/
│
├── main.py                  # Flask entry point + all routes
├── agent.py                 # AI brain — Groq, tool dispatch, memory
│
├── tools/
│   ├── __init__.py
│   ├── gmail_tool.py
│   ├── calendar_tool.py
│   ├── drive_tool.py
│   ├── docs_tool.py
│   └── files_tool.py
│
├── memory/
│   ├── __init__.py
│   └── db.py                # SQLite init, per-user CRUD
│
├── notifications/
│   ├── __init__.py
│   └── notifier.py          # Background deadline checker
│
├── static/
│   ├── style.css
│   └── app.js
│
├── templates/
│   ├── index.html           # Main chat UI
│   ├── setup.html           # First-time setup wizard
│   ├── settings.html        # API key + Google account
│   └── log.html             # Activity log
│
├── config/                  # Auto-created at runtime
│   └── config.db            # SQLite — users, keys, tokens, history
│
├── credentials.json         # Downloaded from Google Cloud Console (gitignored)
├── pyproject.toml           # uv project config
├── uv.lock                  # uv lockfile (commit this)
├── requirements.txt         # For school Mac users (no uv needed)
├── .python-version          # Pins Python 3.9
├── .gitignore
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.9+ |
| Web framework | Flask |
| AI providers | Groq |
| Google APIs | `google-api-python-client`, `google-auth-oauthlib` |
| Database | SQLite (`sqlite3` — built-in) |
| File handling | `pathlib` (cross-platform) |
| Package manager | `uv` (dev) / `pip` (school Mac) |
| Dev tunnel | `ngrok` (OAuth redirect during dev) |

---

## 🚀 Dev Setup (Arch Linux)

### 1. Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env  # or restart terminal
```

### 2. Scaffold project
```bash
uv init school-agent
cd school-agent
uv python pin 3.9
```

### 3. Add dependencies
```bash
uv add flask \
       google-api-python-client \
       google-auth-oauthlib \
       google-auth-httplib2 \
       groq \
       python-dotenv \
       requests
```

### 4. Generate requirements.txt for school Mac users
```bash
uv pip compile pyproject.toml -o requirements.txt
```

### 5. Run
```bash
uv run python main.py
```

---

## 🍎 School Mac Setup (no uv needed)

```bash
# In the project folder
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

That's it. No sudo, no admin rights needed.

---

## 🔐 Google Cloud Console Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (e.g. `school-agent`)
3. Enable these APIs:
   - Gmail API
   - Google Drive API
   - Google Calendar API
   - Google Docs API
   - Google Sheets API
4. Go to **Credentials → Create Credentials → OAuth 2.0 Client ID**
   - Application type: **Web application**
   - Authorized redirect URI: `http://localhost:5000/oauth2callback`
5. Download `credentials.json` → place in project root
6. Go to **OAuth consent screen** → add your Google account as a test user

---

## 🗝️ API Keys (Free)

### Groq
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up → API Keys → Create key
3. No credit card needed

The key is entered via the **setup wizard** on first run — never hardcoded.

---

## 🗄️ SQLite Schema (config/config.db)

```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT NOT NULL,
    api_key_enc TEXT NOT NULL,       -- basic encrypted key
    google_token TEXT,               -- JSON string of OAuth token
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation history
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,              -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Activity log
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,            -- e.g. 'sent_email', 'created_event'
    detail TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🌐 Flask Routes (main.py)

```
GET  /                  → redirect to /setup (first run) or /chat
GET  /setup             → setup wizard (step 1–5)
POST /setup             → save config, redirect to next step
GET  /oauth2callback    → Google OAuth redirect handler
GET  /chat              → main chat UI
POST /chat              → receive message, call agent.py, return response
GET  /log               → activity log page
GET  /settings          → settings page (change key, re-auth)
POST /settings          → save updated settings
POST /notify/check      → trigger deadline check (called by JS on interval)
```

---

## 🧱 Boilerplate Files to Write First

In this order — each one is runnable/testable before the next:

```
1. memory/db.py          → SQLite init + basic CRUD functions
2. main.py               → Flask app, routes (stubs ok), first-run detection
3. templates/setup.html  → Wizard UI (5 steps)
4. agent.py              → Minimal: takes message, returns AI reply (no tools yet)
5. templates/index.html  → Chat UI — input box, message display, shortcuts bar
6. static/style.css      → Dark/light mode base styles
7. static/app.js         → Shortcut parsing, notification permission request
```

Once these are done → the shell of the app is working and you can add tools one by one.

---

## .gitignore

```
credentials.json
config/config.db
token*.json
*.pyc
__pycache__/
.env
venv/
.venv/
```
