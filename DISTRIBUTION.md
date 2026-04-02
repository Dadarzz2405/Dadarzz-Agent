# 🧠 Dadarzz Agent — Distribution Guide

How to build and share this app across **macOS, Windows, and Linux**.

---

## Option A: Automated Builds via GitHub Releases ⭐

The easiest way — GitHub Actions builds for all platforms automatically.

### Create a Release

```bash
git tag v1.0.0
git push --tags
```

This triggers a CI pipeline that builds for **5 targets**:
| Platform | Architecture | Artifact |
|----------|-------------|----------|
| 🍎 macOS | Apple Silicon (M1/M2) | `DadarzzAgent-macOS-arm64.zip` |
| 🍎 macOS | Intel | `DadarzzAgent-macOS-x64.zip` |
| 🪟 Windows | x64 | `DadarzzAgent-Windows-x64.zip` |
| 🐧 Linux | x64 | `DadarzzAgent-Linux-x64.zip` |
| 🐧 Linux | ARM64 | `DadarzzAgent-Linux-arm64.zip` |

Download links appear on your GitHub **Releases** page.

### Manual Trigger

You can also trigger a build without a tag from the GitHub Actions tab → **Build & Release** → **Run workflow**.

---

## Option B: Build Locally (macOS only)

```bash
bash build-mac.sh
```

Creates `dist/DadarzzAgent-macOS.zip` — share via AirDrop/Drive/USB.

---

## How to Share

- **AirDrop** (macOS to macOS, fastest)
- **Google Drive / iCloud** link
- **USB flash drive**
- **GitHub Releases** link (best for cross-platform)

---

## What Your Friends Do

### 🍎 macOS
1. Unzip the file
2. Right-click `launch.command` → **Open** → **Open** (first time only)
3. Browser opens automatically — done!

**If blocked:** `xattr -cr ~/Downloads/DadarzzAgent` in Terminal

### 🪟 Windows
1. Unzip the file
2. Double-click `launch.bat`
3. If SmartScreen blocks it: click **More info** → **Run anyway**
4. Browser opens automatically — done!

### 🐧 Linux
1. Unzip the file
2. Open terminal in the folder
3. Run: `chmod +x launch.sh && ./launch.sh`
4. Browser opens automatically — done!

---

## Source Install (without PyInstaller)

For users who have Python 3 installed and want to run from source:

| Platform | Command |
|----------|---------|
| 🍎 macOS | Double-click `install.command` |
| 🪟 Windows | Double-click `install.bat` |
| 🐧 Linux | `chmod +x install.sh && ./install.sh` |

---

## Quick Reference Card

```
┌─────────────────────────────────────────┐
│       Dadarzz Agent — Quick Start       │
│                                         │
│  macOS:   double-click launch.command   │
│  Windows: double-click launch.bat       │
│  Linux:   ./launch.sh                   │
│                                         │
│  If blocked:                            │
│  macOS:   right-click → Open            │
│  Windows: More info → Run anyway        │
│  Linux:   chmod +x launch.sh            │
│                                         │
│  Need a Groq API key?                   │
│  → console.groq.com/keys (free)         │
└─────────────────────────────────────────┘
```

---

## Troubleshooting

| Problem | Platform | Fix |
|---------|----------|-----|
| "App is damaged" | macOS | `xattr -cr ~/Downloads/DadarzzAgent` |
| "Permission denied" | macOS/Linux | `chmod +x launch.command` or `chmod +x launch.sh` |
| SmartScreen blocks | Windows | Click **More info** → **Run anyway** |
| "python not found" | Windows | Reinstall Python, check **Add to PATH** |
| Nothing happens | All | Open terminal, run the launcher from there |
| Port 5000 in use | All | Close other Dadarzz Agent instances |
