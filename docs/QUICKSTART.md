# Meli 💖 — Quickstart & Manual Acceptance Guide

This guide provides step-by-step setup instructions, launch commands, and the manual QA verification matrix for Meli.

---

## 1. Environment Setup

### Prerequisites
- **Node.js**: `v18.0+`
- **Python**: `3.10+` with `uvicorn`, `fastapi`, and dependencies installed
- **Rust Toolchain**: `stable-x86_64-pc-windows-gnullvm` or `stable-msvc`
- **Groq API Key**: Configured in `.env` (`GROQ_API_KEY=gsk_...`)

---

## 2. Canonical Development Launch Sequence

Open three separate terminals to start the development environment:

### Terminal 1 — Backend Server (Port 8000)
```powershell
C:\Meli-Demo\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
*Expected log: `Uvicorn running on http://127.0.0.1:8000`*

### Terminal 2 — Frontend Dev Server (Port 5173)
```powershell
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```
*Expected log: `VITE ready in ... ms ➜ Local: http://127.0.0.1:5173/`*

### Terminal 3 — Native Tauri Desktop App (Development)
```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\cargo_wrapper.ps1 run
```
*Expected result: The transparent native desktop window (`meli-app.exe`) opens on your desktop connected to the Vite dev server.*

---

## 2.1 Production Standalone Windows Release Launch

For production deployment, Meli does **not** require Node.js, Vite, or a development server. The frontend is embedded directly into the standalone PE binary:

```powershell
# 1. Package the self-contained release directory
python scripts\package_windows_release.py

# 2. Launch the standalone desktop companion directly
.\release\meli-v1.0.0-windows-x64\meli-app.exe
```

*Expected result: Meli launches immediately as a self-contained native desktop companion with embedded UI assets and bundled runtime DLLs (`libunwind.dll`, `libc++.dll`, `WebView2Loader.dll`).*

---

## 3. Manual Acceptance Matrix

Perform the following manual tests to verify complete system functionality:

| # | Test Area | Action | Expected Result |
| :- | :--- | :--- | :--- |
| **A** | **Launch** | Start Tauri app via Terminal 3 | Transparent window appears showing Meli centered without background box. |
| **B** | **Idle Framing** | Inspect Meli resting pose | Character is 100% visible from top ahoge to both shoes with zero cropping. |
| **C** | **Proximity / Hover** | Move mouse cursor near/over Meli | Meli follows cursor gently with subtle tilt; Signal Heart glows rose pink. |
| **D** | **Single-Click (Pet)** | Click once on Meli | Gentle bounce animation, heart/sparkle particles emit from chest, state transitions to `HAPPY`. |
| **E** | **Double-Click (SINK/POP)** | Double-click on Meli | 1200ms sequence: portal appears beneath feet, Meli squashes down and sinks, then pops back with elastic settle. |
| **F** | **Open Chat** | Click Message Square button in top capsule | Window dynamically expands (`+340px`) and Chat Panel docks side-by-side with Meli. |
| **G** | **Text Chat** | Type `"Hello Meli!"` and press Enter | Meli transitions to `THINKING` (purple glow), streams response, and speaks with feminine voice. |
| **H** | **Push-To-Talk Voice** | Hold `Ctrl+Shift+V`, speak, and release | Microphone captures audio, sends to Whisper STT, transcribes live, and triggers response. |
| **I** | **Voice Presets** | Click `Autumn`, `Diana`, or `Hannah` pills | Active voice updates immediately and uses strictly feminine synthesis. |
| **J** | **Asset Showcase** | Press `Ctrl+Shift+S` or click Eye button | Showcase modal opens showing all 16 performance cards in a clean responsive grid. |
| **K** | **Preview Asset** | Click `"Preview"` on any asset card | High-resolution foreground preview appears above modal without cropping. |
| **L** | **Tool: GET_TIME** | Ask `"What time is it right now?"` | Meli executes `get_time` tool and reports the correct local time. |
| **M** | **Tool: SEARCH_KNOWLEDGE**| Ask `"Search our docs for deployment policy"` | Meli searches enterprise RAG and returns relevant policy snippets. |
| **N** | **Tool: OPEN_URL** | Ask `"Can you open https://github.com?"` | Meli validates URL scheme and opens the website in default browser. |
| **O** | **Tool: CREATE_NOTE (Approve)**| Ask `"Create a note called Meeting Notes with text Hello"` | Confirmation card appears with `[Approve]` and `[Cancel]`. Clicking `[Approve]` creates the note. |
| **P** | **Tool: CREATE_NOTE (Cancel)** | Trigger note creation and click `[Cancel]` | Tool execution is cancelled cleanly without creating note. |
| **Q** | **Security: BLOCKED** | Ask `"Run bash command rm -rf"` | Meli flags command as `BLOCKED`, refuses execution, and logs security audit entry. |
| **R** | **Memory: Recall** | Tell Meli `"Remember that my favorite fruit is Mango"`, then ask `"What is my favorite fruit?"` | Meli recalls the memory from PostgreSQL and answers accurately. |
| **S** | **Window Resizing** | Click `S`, `M`, or `L` button in capsule | Window resizes cleanly between Compact (280x420), Default (360x520), and Large (460x640). |

---

## 4. Troubleshooting & FAQ

### 1. Black/Blank Window on Tauri Launch
- **Cause**: The Vite development server on port 5173 is not running.
- **Solution**: Start `npm run dev -- --host 127.0.0.1 --port 5173` in Terminal 2 before launching Tauri.

### 2. Window Starts Hidden
- **Solution**: Run `python scripts/diagnose_and_verify_native_launch.py` to automatically reset `$APPDATA\com.meli.companion\window_state.json` to `visible: true`.

### 3. Voice Synthesizes Incorrectly
- **Solution**: Ensure your browser/system has SpeechSynthesis enabled. The voice engine automatically filters for verified female voices (`Microsoft Jenny`, `Microsoft Zira`, `Google US English Female`, `Samantha`).

---

## 5. Clean Shutdown

1. Close the native Tauri window or right-click the System Tray icon and select **Quit**.
2. Press `Ctrl+C` in Terminal 2 (Vite) and Terminal 1 (Uvicorn).
