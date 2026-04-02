#!/bin/bash
# ╔══════════════════════════════════════════════════════╗
# ║       Dadarzz Agent — One-Click Installer           ║
# ╚══════════════════════════════════════════════════════╝
# Double-click this file to install and launch Dadarzz Agent.

set -e

APP_NAME="Dadarzz Agent"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LAUNCH_SCRIPT="$SCRIPT_DIR/launch.command"
DESKTOP="$HOME/Desktop"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║    🧠 Installing $APP_NAME...               ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Step 1: Check for Python 3 ───────────────────────
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo ""
    echo "Please install it first:"
    echo "  1. Open Terminal"
    echo "  2. Run: xcode-select --install"
    echo "  3. Then re-run this installer"
    echo ""
    echo "Or install from https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

PYTHON_VER=$(python3 --version 2>&1)
echo "✅ Found $PYTHON_VER"

# ── Step 2: Create virtual environment ───────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Setting up environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "✅ Environment already exists"
fi

# ── Step 3: Install dependencies ─────────────────────
echo "📥 Installing dependencies (this may take a minute)..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
echo "✅ Dependencies installed"

# ── Step 4: Create launch script ─────────────────────
cat > "$LAUNCH_SCRIPT" << 'LAUNCHER'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv and start server
source .venv/bin/activate

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║    🧠 Dadarzz Agent is starting...          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Opening in your browser..."
echo "To stop: close this window or press Ctrl+C"
echo ""

# Start the app (browser auto-opens from main.py)
python main.py
LAUNCHER
chmod +x "$LAUNCH_SCRIPT"

# ── Step 5: Create desktop shortcut (.command) ───────
DESKTOP_SHORTCUT="$DESKTOP/$APP_NAME.command"
cat > "$DESKTOP_SHORTCUT" << SHORTCUT
#!/bin/bash
cd "$SCRIPT_DIR"
bash launch.command
SHORTCUT
chmod +x "$DESKTOP_SHORTCUT"

# ── Step 6: Create a macOS .app bundle (optional) ────
APP_BUNDLE="$DESKTOP/$APP_NAME.app"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

cat > "$APP_BUNDLE/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Dadarzz Agent</string>
    <key>CFBundleDisplayName</key>
    <string>Dadarzz Agent</string>
    <key>CFBundleIdentifier</key>
    <string>com.dadarzz.agent</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
</dict>
</plist>
PLIST

cat > "$APP_BUNDLE/Contents/MacOS/launch" << APPSCRIPT
#!/bin/bash
cd "$SCRIPT_DIR"
source .venv/bin/activate
python main.py
APPSCRIPT
chmod +x "$APP_BUNDLE/Contents/MacOS/launch"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║    ✅ Installation complete!                 ║"
echo "╠══════════════════════════════════════════════╣"
echo "║                                              ║"
echo "║  You can now:                                ║"
echo "║    • Double-click '$APP_NAME' on Desktop     ║"
echo "║    • Or run ./launch.command                 ║"
echo "║                                              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Auto-launch after install ────────────────────────
read -p "🚀 Launch now? (Y/n): " LAUNCH_NOW
LAUNCH_NOW=${LAUNCH_NOW:-Y}
if [[ "$LAUNCH_NOW" =~ ^[Yy]$ ]]; then
    bash "$LAUNCH_SCRIPT"
fi
