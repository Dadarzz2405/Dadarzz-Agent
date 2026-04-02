# 🧠 Dadarzz Agent

Your AI-Agent. Dadarzz Agent is a local-first interface that connects a powerful LLM to your digital life: your files, Google Drive, Gmail, and Google Calendar.

---

## 🌟 Features

- **Document Understanding (PDFs/TXT)**: Upload files and ask questions directly.
- **Google Drive Integration**: List, read, search, upload, and download files from your Drive.
- **Gmail & Calendar**: Draft emails, send them via your account, view your inbox, schedule events, and check upcoming deadlines.
- **Local File Management**: Let the agent organize, create, and manage your local files safely.
- **Background Reminders**: Automatically reminds you of upcoming deadlines via an unobtrusive notification system.

---

## 🚀 Quick Start (Pre-Built Binaries)

The easiest way to use Dadarzz Agent is to download the pre-built binaries from the [GitHub Releases](https://github.com/Dadarzz2405/Dadarzz-Agent/releases/latest) page. **No Python required!**

| Platform | Architecture | What to Download |
|----------|-------------|------------------|
| 🍎 **macOS** | Apple Silicon (M1/M2/M3) | `DadarzzAgent-macOS-arm64.zip` |
| 🪟 **Windows** | x64 (Intel/AMD) | `DadarzzAgent-Windows-x64.zip` |
| 🐧 **Linux** | x64 (Intel/AMD) | `DadarzzAgent-Linux-x64.zip` |
| 🐧 **Linux** | ARM64 (Raspberry Pi, etc.) | `DadarzzAgent-Linux-arm64.zip` |

### Instructions:
1. **Unzip** the downloaded file
2. **Launch**:
   - **macOS**: double-click `launch.command` *(if blocked: right-click → Open → Open)*
   - **Windows**: double-click `launch.bat` *(if SmartScreen blocks: More info → Run anyway)*
   - **Linux**: run `./launch.sh`
3. Enter your free [Groq API key](https://console.groq.com/keys) in the browser window that opens.

---

## 🛠️ Run from Source (For Developers)

If you have Python 3 installed and want to run or modify the code yourself:

**macOS:**
Double-click `install.command` to auto-install dependencies and create a launcher.

**Windows:**
Double-click `install.bat`. It will create a Desktop shortcut for you.

**Linux:**
```bash
chmod +x install.sh
./install.sh
```

---

## ❓ Troubleshooting

| Problem | Platform | Fix |
|---------|----------|-----|
| "App is damaged" | macOS | Open Terminal and run: `xattr -cr ~/Downloads/DadarzzAgent` |
| "Permission denied" | macOS/Linux | `chmod +x launch.command` or `chmod +x launch.sh` |
| Nothing happens | All | Try launching from a Terminal/Command Prompt to see the error message |
| Port 5000 in use | All | Close any other running instances of Dadarzz Agent |
| "python not found" | Windows | Make sure to check **Add Python to PATH** when installing Python |

---

## 🛑 Stopping the App

To stop Dadarzz Agent, simply close the Terminal/Command Prompt window that opened, or press `Ctrl+C` in it.
