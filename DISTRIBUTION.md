# 🧠 Dadarzz Agent — Distribution Guide

How to build and share this app with friends on **school Macs (M1/M2)** — no admin access or Python needed on their end.

---

## Step 1: Build on Your Mac

```bash
bash build-mac.sh
```

This creates:
- `dist/DadarzzAgent/` — the app folder with everything bundled
- `dist/DadarzzAgent-macOS.zip` — ready-to-share zip file

> Test it yourself first: `./dist/DadarzzAgent/launch.command`

---

## Step 2: Share the ZIP

Send `dist/DadarzzAgent-macOS.zip` to your friends using:
- **AirDrop** (fastest)
- Google Drive / iCloud link
- USB flash drive

---

## Step 3: What Your Friends Do

### First Time Setup
1. **Unzip** the file (double-click the .zip)
2. **Right-click** `launch.command` → **Open** → **Open**
   - This is needed only the first time (macOS security)
3. The app opens in their browser — done!
4. The **setup wizard** will guide them through entering their API key

### If macOS Says "Cannot Be Opened"
Open **Terminal** (Spotlight → type "Terminal") and paste:
```
xattr -cr ~/Downloads/DadarzzAgent
```
Then try step 2 again.

### Every Time After
Just double-click `launch.command` to start.

---

## Quick Reference Card

Print or send this to your friends:

```
┌─────────────────────────────────────┐
│       Dadarzz Agent — Quick Start   │
│                                     │
│  1. Unzip the file                  │
│  2. Open the folder                 │
│  3. Double-click "launch.command"   │
│  4. If blocked: right-click → Open  │
│  5. Browser opens automatically     │
│  6. To stop: close the Terminal     │
│                                     │
│  Need a Groq API key?              │
│  → console.groq.com/keys (free)    │
└─────────────────────────────────────┘
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "App is damaged" | Run `xattr -cr ~/Downloads/DadarzzAgent` in Terminal |
| "Permission denied" | Run `chmod +x launch.command` in Terminal |
| Nothing happens | Open Terminal, drag `launch.command` into it, press Enter |
| Port 5000 in use | Close any other Dadarzz Agent windows first |
