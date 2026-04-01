#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║   Dadarzz Agent — macOS Build Script                    ║
# ║   Run this on your Mac to create the distributable app  ║
# ╚══════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="DadarzzAgent"
DIST_DIR="$SCRIPT_DIR/dist"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  🧠 Building $APP_NAME for macOS...         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Step 1: Create venv & install deps ───────────────
if [ ! -d ".venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv .venv
fi

echo "→ Installing dependencies..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
.venv/bin/pip install --quiet pyinstaller

# ── Step 2: Build with PyInstaller ───────────────────
echo "→ Building executable (this takes 1-2 minutes)..."
.venv/bin/pyinstaller --noconfirm --onedir \
    --name "$APP_NAME" \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "config:config" \
    --hidden-import "groq" \
    --hidden-import "flask" \
    --hidden-import "dotenv" \
    --hidden-import "pypdf" \
    --hidden-import "jinja2.ext" \
    --hidden-import "markupsafe" \
    main.py

# ── Step 3: Create launch helper ─────────────────────
echo "→ Creating launch helper..."
cat > "$DIST_DIR/$APP_NAME/launch.command" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
echo ""
echo "╔══════════════════════════════════════╗"
echo "║  🧠 Dadarzz Agent is running...     ║"
echo "║  Close this window to stop.         ║"
echo "╚══════════════════════════════════════╝"
echo ""
(sleep 2 && open "http://127.0.0.1:5000") &
./DadarzzAgent
EOF
chmod +x "$DIST_DIR/$APP_NAME/launch.command"

# ── Step 4: Add instructions for friends ─────────────
echo "→ Adding README for your friends..."
cat > "$DIST_DIR/$APP_NAME/README.txt" << 'EOF'
╔══════════════════════════════════════════╗
║     Dadarzz Agent — Quick Start         ║
╠══════════════════════════════════════════╣
║                                          ║
║  1. Double-click "launch.command"        ║
║                                          ║
║  2. If macOS blocks it:                  ║
║     Right-click → Open → Open            ║
║                                          ║
║  3. Your browser will open               ║
║     automatically at localhost:5000      ║
║                                          ║
║  4. To stop the app:                     ║
║     Close the Terminal window            ║
║                                          ║
╠══════════════════════════════════════════╣
║  FIRST TIME SETUP:                       ║
║  You need a free Groq API key:           ║
║  → https://console.groq.com/keys        ║
║  Sign up and create a key, then          ║
║  paste it in the setup wizard.           ║
╠══════════════════════════════════════════╣
║  STILL BLOCKED?                          ║
║  Open Terminal and run:                  ║
║  xattr -cr ~/Downloads/DadarzzAgent     ║
║  Then try again.                         ║
╚══════════════════════════════════════════╝
EOF

# ── Step 5: Create ZIP for sharing ───────────────────
echo "→ Creating distributable ZIP..."
cd "$DIST_DIR"
zip -r -q "${APP_NAME}-macOS.zip" "$APP_NAME/"
cd "$SCRIPT_DIR"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  ✅ Build complete!                          ║"
echo "╠══════════════════════════════════════════════╣"
echo "║                                              ║"
echo "║  Output:                                     ║"
echo "║    dist/$APP_NAME/          (app folder)     ║"
echo "║    dist/$APP_NAME-macOS.zip (shareable)      ║"
echo "║                                              ║"
echo "║  To test: ./dist/$APP_NAME/launch.command    ║"
echo "║  To share: send the .zip to your friends     ║"
echo "║                                              ║"
echo "║  Friends: unzip → double-click launch.command║"
echo "║  If blocked: xattr -cr DadarzzAgent/         ║"
echo "║                                              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
