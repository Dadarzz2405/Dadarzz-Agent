# 🧠 Dadarzz Agent — Distribution Guide

How to package and distribute this app to **school Macs (M1/M2)** where users have **no admin access** and **no Python installed**.

---

## Strategy: PyInstaller → Unix Executable

PyInstaller bundles Python + all dependencies into a single executable. No install needed — friends just double-click.

> [!IMPORTANT]
> PyInstaller **cannot cross-compile**. You must build on the same OS/arch you're targeting.
> To build for macOS ARM (M1/M2), you need to build **on** a Mac ARM machine.

---

## Option A: Build on a Mac (Manual)

If you have temporary access to any M1/M2 Mac:

### 1. Install build tools (one-time)

```bash
python3 -m pip install pyinstaller
```

### 2. Build the executable

```bash
cd /path/to/AgenticV2

pyinstaller --onedir \
  --name "DadarzzAgent" \
  --add-data "templates:templates" \
  --add-data "static:static" \
  --add-data "config:config" \
  --hidden-import "groq" \
  --hidden-import "flask" \
  --hidden-import "dotenv" \
  --hidden-import "pypdf" \
  main.py
```

### 3. Output

```
dist/
└── DadarzzAgent/
    ├── DadarzzAgent          ← the unix executable
    ├── templates/
    ├── static/
    └── (bundled libs)
```

### 4. Distribute

ZIP the `dist/DadarzzAgent/` folder → share via AirDrop/USB/Drive.
Friends unzip → double-click `DadarzzAgent` → browser opens.

---

## Option B: GitHub Actions (Automated, No Mac Needed)

Push code → GitHub builds the macOS ARM binary → you download the `.zip`.

### 1. Create `.github/workflows/build-mac.yml`

```yaml
name: Build macOS ARM

on:
  push:
    tags: ['v*']          # triggers on version tags like v1.0
  workflow_dispatch:       # also allows manual trigger

jobs:
  build:
    runs-on: macos-14      # Apple Silicon (M1) runner
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build executable
        run: |
          pyinstaller --onedir \
            --name "DadarzzAgent" \
            --add-data "templates:templates" \
            --add-data "static:static" \
            --add-data "config:config" \
            --hidden-import "groq" \
            --hidden-import "flask" \
            --hidden-import "dotenv" \
            --hidden-import "pypdf" \
            main.py

      - name: Create launch helper
        run: |
          cat > dist/DadarzzAgent/launch.command << 'EOF'
          #!/bin/bash
          DIR="$(cd "$(dirname "$0")" && pwd)"
          cd "$DIR"
          (sleep 2 && open "http://127.0.0.1:5000") &
          ./DadarzzAgent
          EOF
          chmod +x dist/DadarzzAgent/launch.command

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: DadarzzAgent-macOS-arm64
          path: dist/DadarzzAgent/
```

### 2. Usage

```bash
git tag v1.0
git push origin v1.0
```

Then go to **GitHub → Actions → latest run → Artifacts** → download `DadarzzAgent-macOS-arm64.zip`.

---

## What Your Friends Do

1. **Unzip** the folder
2. **Double-click** `launch.command` (or `DadarzzAgent` directly)
3. If macOS blocks it: **right-click → Open → Open**
4. Browser opens automatically → app is running ✅

> [!TIP]
> To bypass Gatekeeper without admin: friends can run this in Terminal:
> ```bash
> xattr -cr ~/Downloads/DadarzzAgent/
> ```
> This removes the quarantine flag so macOS stops blocking it.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| "App is damaged" / Gatekeeper block | `xattr -cr /path/to/DadarzzAgent/` |
| "Permission denied" | `chmod +x DadarzzAgent launch.command` |
| Port 5000 in use | Kill existing: `lsof -ti:5000 \| xargs kill` |
| Missing module errors | Add to `--hidden-import` in build command |
| App crashes silently | Run `./DadarzzAgent` from Terminal to see errors |

---

## Recommended Workflow

1. Develop on your Linux machine
2. Push to GitHub with a version tag
3. GitHub Actions builds the macOS ARM binary
4. Download and share with friends
5. Repeat for updates
