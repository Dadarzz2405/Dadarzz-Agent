#!/bin/bash
# ╔══════════════════════════════════════════════════════╗
# ║       Dadarzz Agent — Linux Installer               ║
# ╚══════════════════════════════════════════════════════╝
# Run: chmod +x install.sh && ./install.sh

set -e

APP_NAME="Dadarzz Agent"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LAUNCH_SCRIPT="$SCRIPT_DIR/launch.sh"
DESKTOP="$HOME/Desktop"
APPLICATIONS="$HOME/.local/share/applications"

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
    echo "  Ubuntu/Debian:  sudo apt install python3 python3-venv python3-pip"
    echo "  Fedora:         sudo dnf install python3 python3-pip"
    echo "  Arch:           sudo pacman -S python python-pip"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

PYTHON_VER=$(python3 --version 2>&1)
echo "✅ Found $PYTHON_VER"

# ── Step 2: Check for python3-venv (Debian/Ubuntu) ───
if ! python3 -m venv --help &> /dev/null; then
    echo "⚠️  python3-venv is not installed."
    echo "   Run: sudo apt install python3-venv"
    read -p "Press Enter to close..."
    exit 1
fi

# ── Step 3: Create virtual environment ───────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Setting up environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "✅ Environment already exists"
fi

# ── Step 4: Install dependencies ─────────────────────
echo "📥 Installing dependencies (this may take a minute)..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
echo "✅ Dependencies installed"

# ── Step 5: Make launch script executable ────────────
chmod +x "$LAUNCH_SCRIPT"

# ── Step 6: Create .desktop launcher ─────────────────
mkdir -p "$APPLICATIONS"
cat > "$APPLICATIONS/dadarzz-agent.desktop" << EOF
[Desktop Entry]
Name=Dadarzz Agent
Comment=AI Study Assistant
Exec=bash "$LAUNCH_SCRIPT"
Terminal=true
Type=Application
Categories=Education;Utility;
StartupNotify=true
EOF
chmod +x "$APPLICATIONS/dadarzz-agent.desktop"

# Also copy to Desktop if it exists
if [ -d "$DESKTOP" ]; then
    cp "$APPLICATIONS/dadarzz-agent.desktop" "$DESKTOP/dadarzz-agent.desktop"
    chmod +x "$DESKTOP/dadarzz-agent.desktop"
    # Mark as trusted on GNOME
    if command -v gio &> /dev/null; then
        gio set "$DESKTOP/dadarzz-agent.desktop" metadata::trusted true 2>/dev/null || true
    fi
fi

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║    ✅ Installation complete!                 ║"
echo "╠══════════════════════════════════════════════╣"
echo "║                                              ║"
echo "║  You can now:                                ║"
echo "║    • Click 'Dadarzz Agent' in your apps      ║"
echo "║    • Or run: ./launch.sh                     ║"
echo "║                                              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Auto-launch after install ────────────────────────
read -p "🚀 Launch now? (Y/n): " LAUNCH_NOW
LAUNCH_NOW=${LAUNCH_NOW:-Y}
if [[ "$LAUNCH_NOW" =~ ^[Yy]$ ]]; then
    bash "$LAUNCH_SCRIPT"
fi
