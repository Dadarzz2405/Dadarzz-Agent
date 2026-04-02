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

# Open browser after short delay
(sleep 2 && open "http://127.0.0.1:5000") &

# Start the app
python main.py
