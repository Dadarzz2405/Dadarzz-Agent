# 📋 SchoolAgent — Full Plan & Task Execution

> Complete feature spec, build phases, and how the agent actually executes tasks.
> Every feature, every tool, every flow — documented before a line is written.

---

## 🧠 How the Agent Executes Tasks

The agent uses a **tool-calling loop** — it doesn't just reply with text, it decides
which tool to run, runs it, gets the result, then forms a final response.

### Execution Loop

```
User message
    ↓
agent.py builds prompt:
  ├── System prompt (agent identity + list of available tools)
  ├── Conversation history (last N messages from SQLite)
  └── User message (+ shortcut hint if /command used)
    ↓
Send to Groq
    ↓
AI response — two possible outcomes:
  ├── A) Plain text reply → return directly to user
  └── B) Tool call → { tool: "gmail", action: "send", params: {...} }
            ↓
        Execute the tool (gmail_tool.py, drive_tool.py, etc.)
            ↓
        Tool returns result (success / data / error)
            ↓
        Feed result back to AI as a follow-up message
            ↓
        AI forms final human-readable response
    ↓
Save exchange to SQLite (history table)
Log action to activity_log table
Return final response to Flask UI
```

### Tool Call Format (what the AI returns)

The system prompt instructs the AI to respond in JSON when it needs a tool:

```json
{
  "tool": "calendar",
  "action": "create_event",
  "params": {
    "title": "Math Study Session",
    "date": "2025-03-26",
    "time": "15:00",
    "duration_minutes": 60
  }
}
```

`agent.py` detects this, routes to the right tool, and loops back.

---

## 🎯 Feature Spec & Task Execution

---

### 1. 📧 Gmail — Draft & Send Email

**Shortcut:** `/email`
**File:** `tools/gmail_tool.py`

#### Actions
| Action | What it does |
|---|---|
| `draft` | AI composes email from natural language description |
| `preview` | Returns draft to Flask UI as a preview modal |
| `send` | User confirms in UI → actually sends via Gmail API |
| `read_inbox` | Returns list of recent emails (subject, sender, snippet) |

#### Execution Flow
```
User: "/email tell mr. hasan i'll be late submitting the assignment"
    ↓
agent.py → tool call: { tool: "gmail", action: "draft", params: { instruction: "..." } }
    ↓
gmail_tool.draft() → AI generates subject + body
    ↓
Return draft to Flask UI → preview modal shown
    ↓
User clicks "Send" → POST /chat with { confirm: "send_email", draft_id: "..." }
    ↓
gmail_tool.send() → Gmail API sends email
    ↓
Log: action="sent_email", detail="To: mr.hasan@school.edu"
```

#### Google API Scopes
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/gmail.readonly`

---

### 2. 📅 Calendar — Events & Deadlines

**Shortcut:** `/cal`
**File:** `tools/calendar_tool.py`

#### Actions
| Action | What it does |
|---|---|
| `create_event` | Creates a new event on Google Calendar |
| `list_events` | Lists upcoming events (today / this week) |
| `find_deadlines` | Returns events tagged as deadlines (used by notifier) |
| `delete_event` | Removes an event by title or ID |

#### Execution Flow
```
User: "/cal add biology project deadline next friday at 11:59pm"
    ↓
agent.py → tool call: { tool: "calendar", action: "create_event",
           params: { title: "Biology Project Deadline", date: "2025-03-28", time: "23:59" } }
    ↓
calendar_tool.create_event() → Google Calendar API
    ↓
Returns: { status: "created", event_id: "...", link: "..." }
    ↓
AI: "Done! I've added Biology Project Deadline on Friday March 28 at 11:59 PM. 🗓️"
    ↓
Log: action="created_event", detail="Biology Project Deadline — 2025-03-28"
```

#### Natural Language Date Parsing
Use Python's `dateparser` library or ask the AI to resolve dates before tool call.
```bash
uv add dateparser
```

#### Google API Scopes
- `https://www.googleapis.com/auth/calendar`

---

### 3. ⏰ Deadline Reminders

**Shortcut:** `/remind`
**File:** `notifications/notifier.py`

#### How it works
- Background thread runs every **15 minutes**
- Calls `calendar_tool.find_deadlines()` to get upcoming events
- If any deadline is within **24 hours** → trigger notification
- Notification types:
  - **In-app pop-up** — JS toast notification in Flask UI
  - **Browser notification** — Web Notifications API (user must grant permission on first load)

#### Execution Flow
```
notifier.py (background thread, every 15 min)
    ↓
calendar_tool.find_deadlines() → list of events in next 24h
    ↓
For each deadline:
    → Store in SQLite: notifications table { user_id, title, due_at, notified }
    → Flask /notify/check endpoint polled by JS every 60s
    ↓
JS receives pending notifications
    ↓
Show browser notification: "📚 Biology Project due in 3 hours!"
Show in-app toast: same message
    ↓
Mark as notified in DB (don't repeat)
```

#### Extra SQLite Table
```sql
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    due_at TIMESTAMP NOT NULL,
    notified INTEGER DEFAULT 0
);
```

---

### 4. 📄 Google Docs & Sheets

**Shortcut:** `/docs`
**File:** `tools/docs_tool.py`

#### Actions
| Action | What it does |
|---|---|
| `read_doc` | Returns text content of a Google Doc |
| `edit_doc` | Appends or replaces text in a Doc |
| `create_doc` | Creates a new Google Doc with given content |
| `read_sheet` | Returns rows from a Google Sheet as a list |
| `edit_sheet` | Updates a cell or range in a Sheet |
| `create_sheet` | Creates a new Google Sheet |

#### Execution Flow
```
User: "/docs summarize my Biology Notes doc"
    ↓
agent.py → tool call: { tool: "docs", action: "read_doc", params: { name: "Biology Notes" } }
    ↓
docs_tool.read_doc() → search Drive for doc by name → Docs API → get content
    ↓
Return content to agent → AI summarizes
    ↓
AI: "Here's a summary of your Biology Notes: ..."
```

#### Google API Scopes
- `https://www.googleapis.com/auth/documents`
- `https://www.googleapis.com/auth/spreadsheets`

---

### 5. 💾 Google Drive

**Shortcut:** `/drive`
**File:** `tools/drive_tool.py`

#### Actions
| Action | What it does |
|---|---|
| `list_files` | Lists files in Drive (or a specific folder) |
| `search_files` | Searches Drive by name or type |
| `upload_file` | Uploads a local file to Drive |
| `download_file` | Downloads a Drive file to local machine |
| `delete_file` | Moves a file to trash |
| `share_file` | Shares a file with an email address |

#### Execution Flow
```
User: "/drive upload my assignment pdf"
    ↓
Flask UI shows file picker (HTML input[type=file])
    ↓
File POSTed to /chat with multipart form
    ↓
agent.py → tool call: { tool: "drive", action: "upload_file",
           params: { local_path: "/tmp/uploaded_file.pdf", name: "assignment.pdf" } }
    ↓
drive_tool.upload_file() → Drive API
    ↓
Returns: { file_id: "...", link: "https://drive.google.com/..." }
    ↓
AI: "Uploaded! Here's the link: [assignment.pdf](https://drive.google.com/...)"
    ↓
Log: action="uploaded_file", detail="assignment.pdf"
```

#### Google API Scopes
- `https://www.googleapis.com/auth/drive`

---

### 6. 🗂️ Local File Management

**Shortcut:** `/files`
**File:** `tools/files_tool.py`

#### Actions
| Action | What it does |
|---|---|
| `create_file` | Creates a new file with given content |
| `read_file` | Returns content of a local file |
| `move_file` | Moves/renames a file |
| `delete_file` | Deletes a file (with confirmation) |
| `list_dir` | Lists files in a directory |
| `create_dir` | Creates a new folder |

#### Safety Rules (IMPORTANT)
- All paths resolved with `pathlib.Path` — cross-platform
- Operations restricted to user's **home directory** only
- Never allow `..` path traversal
- Delete always requires AI to confirm with user first

#### Execution Flow
```
User: "/files create a notes.txt in my Documents folder"
    ↓
agent.py → tool call: { tool: "files", action: "create_file",
           params: { path: "~/Documents/notes.txt", content: "" } }
    ↓
files_tool.create_file() → pathlib.Path.expanduser() → Path.write_text()
    ↓
Returns: { status: "created", path: "/Users/student/Documents/notes.txt" }
    ↓
AI: "Created notes.txt in your Documents folder. ✅"
```

---

### 7. ❓ School Q&A

**Shortcut:** `/ask`
**File:** handled in `agent.py` directly

#### How it works
- User uploads a school document (PDF, DOCX, TXT) via the chat UI
- File saved temporarily to `/tmp/`
- Content extracted and injected into the AI prompt as context
- AI answers questions based on that document

#### Execution Flow
```
User uploads "chapter5_biology.pdf" → types "/ask what is osmosis?"
    ↓
Flask reads file → extract text (use pypdf for PDF, plain read for txt)
    ↓
agent.py builds prompt:
  System: "You are a school assistant. Answer based on this document: [content]"
  User: "what is osmosis?"
    ↓
AI answers using document context
    ↓
No tool call — pure AI response
```

```bash
uv add pypdf  # for PDF text extraction
```

---

## 🧰 Shared Agent Utilities (agent.py)

```python
# Key functions in agent.py

def build_system_prompt(tools: list) -> str
    # Returns system prompt listing all available tools + JSON format instruction

def parse_tool_call(response: str) -> dict | None
    # Detects if AI response is a JSON tool call or plain text

def dispatch_tool(tool_call: dict, user_id: int) -> str
    # Routes to correct tool file + action

def run(user_id: int, message: str, file_path: str = None) -> str
    # Full execution loop — history → AI → tool? → loop → final reply

def load_history(user_id: int, limit: int = 20) -> list
    # Loads last N messages from SQLite for this user

def save_exchange(user_id: int, user_msg: str, ai_reply: str)
    # Saves both sides of convo to SQLite
```

---

## 🖥️ Flask UI Features

### Chat UI (index.html)
- Message input box with **send button**
- Shortcut bar: `/email` `/cal` `/drive` `/files` `/remind` `/ask` (clickable chips)
- Message thread (user messages right, agent messages left)
- File attachment button (for `/drive upload` and `/ask`)
- Email preview modal (confirm before sending)
- Toast notification area (bottom right)

### Setup Wizard (setup.html)
```
Step 1 — Welcome + project description
Step 2 — Paste API key + test button
Step 3 — Google OAuth → "Connect Google Account" button
Step 4 — Enter display name
Step 5 — All done! → Go to chat
```

### Settings (settings.html)
- Change AI provider / API key
- Re-authenticate Google account
- Clear conversation history
- Reset everything (start setup wizard again)

### Activity Log (log.html)
- Table: Timestamp | Action | Detail
- Filter by action type
- Export as CSV (simple Flask route returning CSV)

---

## 🌙 Dark / Light Mode

- CSS variables for all colors
- Toggle button in nav → adds/removes `.dark` class on `<body>`
- Preference saved to `localStorage`
- Default: follows system (`prefers-color-scheme`)

---

## 👥 Multi-User Design

- Each user = one row in `users` table
- Session stored in Flask `session` (cookie-based, secret key in `.env`)
- On `/chat` load → check `session['user_id']` → if missing → redirect to `/setup`
- Each user's history, token, API key are completely separate
- No user can access another user's data

---

## 🏗️ Build Phases & Tasks

### ✅ Phase 1 — Skeleton + Setup Wizard
- [ ] `memory/db.py` — init DB, create all tables, basic CRUD
- [ ] `main.py` — Flask app, all route stubs, first-run detection logic
- [ ] `templates/setup.html` — 5-step wizard UI
- [ ] Setup wizard backend — save user, API key (encrypted), redirect flow
- [ ] Google OAuth flow — `/oauth2callback` route, save token to DB
- [ ] API key test call — hit Groq with a "hello" before saving
- [ ] Session management — Flask secret key, session-based user tracking

### ✅ Phase 2 — AI Brain (no tools yet)
- [ ] `agent.py` — Groq client setup
- [ ] `build_system_prompt()` — system prompt with tool list in JSON format
- [ ] `parse_tool_call()` — detect JSON vs plain text in AI response
- [ ] `load_history()` + `save_exchange()` — SQLite memory per user
- [ ] `run()` — basic loop (no tool dispatch yet, just replies)
- [ ] `/email`, `/cal`, `/drive`, `/files`, `/remind`, `/ask` shortcut parsing
- [ ] `templates/index.html` — chat UI, shortcut chips, message thread
- [ ] `static/style.css` — base styles, dark/light mode CSS variables
- [ ] `static/app.js` — shortcut click handler, notification permission request

### ✅ Phase 3 — Google Workspace Tools
- [ ] `tools/gmail_tool.py` — draft, preview, send, read_inbox
- [ ] Email preview modal in `index.html` + confirm/cancel JS
- [ ] `tools/calendar_tool.py` — create_event, list_events, find_deadlines
- [ ] Natural language date parsing (`dateparser`)
- [ ] `tools/drive_tool.py` — list, search, upload, download, delete
- [ ] File upload input in chat UI → multipart POST handling in Flask
- [ ] `tools/docs_tool.py` — read_doc, edit_doc, create_doc, read_sheet, edit_sheet
- [ ] `dispatch_tool()` in `agent.py` — routes all tool calls
- [ ] Full tool-calling loop in `run()` — AI → tool → AI → reply

### ✅ Phase 4 — Local Files + Q&A
- [ ] `tools/files_tool.py` — create, read, move, delete, list_dir, create_dir
- [ ] Path safety check — restrict to home dir, block traversal
- [ ] Delete confirmation flow — AI asks user before deleting
- [ ] `/ask` — PDF/TXT extraction, inject into prompt as context
- [ ] `pypdf` integration for PDF reading

### ✅ Phase 5 — Notifications + Polish
- [ ] `notifications/notifier.py` — background thread, 15min interval
- [ ] `notifications` SQLite table — store pending alerts
- [ ] `POST /notify/check` Flask route — return pending notifications as JSON
- [ ] `static/app.js` — poll `/notify/check` every 60s, show browser notification
- [ ] In-app toast notification component (CSS + JS)
- [ ] `templates/log.html` — activity log table, filter, CSV export
- [ ] `templates/settings.html` — change key, re-auth, clear history, reset
- [ ] Dark/light mode toggle + localStorage persistence
- [ ] Error handling — friendly messages for API failures, quota errors

---

## 📦 Full Dependencies

```toml
# pyproject.toml (uv manages this)
[project]
name = "school-agent"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [
    "flask>=2.3.0",
    "google-api-python-client>=2.0.0",
    "google-auth-oauthlib>=1.0.0",
    "google-auth-httplib2>=0.1.0",
    "groq>=0.5.0",
    "python-dotenv>=1.0.0",
    "requests>=2.31.0",
    "dateparser>=1.2.0",
    "pypdf>=4.0.0",
]
```

---

## ⚠️ Key Gotchas

- **Python 3.9 compat** — no `match/case`, no `X | Y` union types, use `Optional[X]`
- **pathlib everywhere** — never hardcode `/Users/` or `/home/`, use `Path.home()`
- **OAuth on localhost** — works fine for school Mac users, ngrok only needed in dev
- **API key encryption** — don't store raw in SQLite; use `base64` + a local secret at minimum
- **Groq free tier limits** — varies per model, handle 429 errors gracefully
- **Google OAuth consent** — school Workspace accounts may need admin approval for some scopes
- **File tool safety** — always `Path(path).resolve()` and check it starts with `Path.home()`
- **Never commit** `credentials.json`, `config.db`, `token*.json`

---

*Full plan — ready to execute phase by phase. ☕🗿*