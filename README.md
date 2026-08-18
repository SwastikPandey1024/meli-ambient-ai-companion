# Meli 💖 — Ambient AI Desktop Companion

> **An intelligent, responsive, and aesthetically refined anime desktop companion powered by Groq LLM reasoning, local vector RAG, voice intelligence, and native desktop windowing.**

---

## 🌟 Overview

**Meli** is an ambient desktop companion engineered with a custom transparent UI, multi-layered visual feedback, low-latency push-to-talk speech synthesis, enterprise memory retrieval, and an auditable tool execution framework.

Meli upgrades the conversational AI experience from a standard web chat into a living desktop companion:
```
UNDERSTAND ➔ REMEMBER ➔ RETRIEVE ➔ REASON ➔ ACT ➔ REPORT RESULT
```

---

## ✨ Key Capabilities

| Feature | Description |
| :--- | :--- |
| **16-State Visual Engine** | 16 standalone illustrations with seamless crossfading, chromatic Signal Heart auras, and SINK/POP portals. |
| **Voice Intelligence (PTT)** | Global `Ctrl+Shift+V` push-to-talk with Whisper transcription and strictly feminine companion voices (**Autumn**, **Diana**, **Hannah**). |
| **Tool & Action Intelligence** | Secure, auditable tool framework with strict permission levels (`AUTO_APPROVED`, `CONFIRMATION_REQUIRED`, `BLOCKED`). |
| **Enterprise Memory & RAG** | PostgreSQL conversation storage and Elasticsearch BM25 document retrieval. |
| **Native Tauri Desktop Shell** | High-DPI transparent windowing with auto-expanding side-by-side chat drawer and safe bounds clamping. |
| **Interactive Physics** | Single-click pet bounce, double-click SINK/POP sequence, hover tracking, and idle breathing. |

---

## 🚀 Quickstart

### Prerequisites
- **Node.js**: `v18+` & `npm`
- **Python**: `3.10+` with `venv`
- **Rust & Cargo**: Latest stable toolchain
- **Groq API Key**: Set `GROQ_API_KEY` in `.env`

### Canonical Development Flow

#### Terminal 1 — FastAPI Backend (Port 8000)
```powershell
C:\Meli-Demo\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

#### Terminal 2 — Vite Frontend (Port 5173)
```powershell
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

#### Terminal 3 — Native Tauri Desktop App
```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\cargo_wrapper.ps1 run
```

### Health Verification
- **Backend API**: `http://127.0.0.1:8000/api/health`
- **Frontend Dev Server**: `http://127.0.0.1:5173/`

---

## 🎨 16 Performance States

Meli includes 16 standalone illustrations:

| State | Trigger / Mood | Signal Heart Glow |
| :--- | :--- | :--- |
| `01_idle` | Default ambient resting state | Soft Pink (`#FFB6C1`) |
| `02_curious` | Memory recalled or user asks clarifying questions | Warm Peach (`#FFAB91`) |
| `03_happy` | Positive feedback or companion praise | Warm Pink (`#FF80AB`) |
| `04_thinking` | LLM reasoning stream active | Soft Violet (`#B388FF`) |
| `05_working` | Background tool execution in progress | Golden Amber (`#FFD54F`) |
| `06_focused` | Enterprise search or multi-step execution | Deep Indigo (`#7C4DFF`) |
| `07_sleepy` | Extended user inactivity (> 45s) | Lavender (`#9FA8DA`) |
| `08_confused` | Ambiguous input or missing parameters | Warning Orange (`#FF9800`) |
| `09_surprised` | Unexpected external discovery | Radiant Sun (`#FFE082`) |
| `10_error` | Tool failure or blocked command attempt | Crimson Red (`#FF5252`) |
| `11_complete` | Task completed successfully | Spring Green (`#69F0AE`) |
| `12_greeting` | Application boot or return | Sunny Rose (`#FF80AB`) |
| `13_click_pet` | Single-click tactile petting | Radiant Magenta (`#FF4D88`) |
| `14_sink_pop` | Double-click portal sink and pop | Pulsing Rose (`#FF7AA2`) |
| `15_proximity` | Cursor proximity tracking | Soft Pink (`#FFB6C1`) |
| `16_celebration` | Milestone celebration / task success | Brilliant Gold (`#FFD700`) |

---

## 🎙️ Voice Architecture

- **Speech-to-Text (STT)**: Fast Whisper transcription (`whisper-large-v3-turbo` / `whisper-large-v3`).
- **Text-to-Speech (TTS)**: Multi-provider architecture supporting CanopyLabs Orpheus with seamless local Web Speech fallback.
- **Feminine Voice Presets**:
  - **Autumn** (Default): Warm, gentle, companion-like voice.
  - **Diana**: Crisp, calm, articulate voice.
  - **Hannah**: Soft, friendly, expressive voice.

---

## 🛠️ Security & Tool Permission Levels

| Permission Level | Behavior | Supported Tools |
| :--- | :--- | :--- |
| `AUTO_APPROVED` | Executes automatically; logged to audit trail. | `get_time`, `search_knowledge`, `open_url` |
| `CONFIRMATION_REQUIRED` | Requires explicit user approval in the UI. | `create_note`, `save_memory` |
| `BLOCKED` | Immediately rejected to protect host security. | `execute_shell`, `eval`, arbitrary file writes |

---

## 🧪 Testing

```powershell
# Run Frontend Vitest Unit Tests (80/80)
npm.cmd run test

# Verify Production TypeScript Build
npm.cmd run build

# Run Phase 0 Sprite QA Engine (13/13)
python scripts/test_phase0_engine.py

# Run Meli Motion & Sizing QA (7/7)
python scripts/test_meli_engine.py

# Run Backend Pytest Suite (52/52)
python -m pytest backend/tests/ -v

# Verify Native Cargo Compilation
powershell scripts/cargo_wrapper.ps1 check

# Verify Phase 1D Tool Intelligence E2E
python scripts/verify_phase1d_e2e.py
```

---

## 📁 Repository Structure

```
Meli/
├── backend/                  # FastAPI backend server
│   ├── app/
│   │   ├── companion/        # Chat orchestration, RAG, and TTS synthesis
│   │   ├── tools/            # Typed tool registry & policy engine
│   │   ├── repositories/     # PostgreSQL async repositories
│   │   └── search/           # Elasticsearch BM25 search
│   └── tests/                # Pytest test suite (52 tests)
├── src/                      # React frontend
│   ├── components/           # ChatPanel, SignalHeart, Showcase Modal
│   ├── enrichment/           # Viewport compositor & PerformanceAssetManager
│   ├── platform/             # Tauri window manager & shortcuts
│   ├── state/                # Authoritative CharacterStateMachine
│   ├── voice/                # PTT, STT, TTS, sound effects
│   └── tests/                # Vitest unit test suite (80 tests)
├── src-tauri/                # Native Rust desktop shell (Tauri v2)
├── public/                   # 16 approved frozen runtime PNG assets
│   ├── states/               # 12 core performance states
│   └── special/              # 4 special interaction states
├── docs/                     # Comprehensive engineering & user documentation
└── scripts/                  # QA test runners and verification scripts
```

---

## 📄 Documentation Index

- [**Quickstart Guide**](docs/QUICKSTART.md) — Step-by-step setup and manual acceptance walkthrough.
- [**Architecture Specification**](docs/ARCHITECTURE.md) — Full technical breakdown of state machine, voice, and RAG.
- [**Testing Guide**](docs/TESTING.md) — Comprehensive test matrix and verification commands.
- [**Security Policy**](docs/SECURITY.md) — Tool permission models and secret handling.
- [**Asset Manifest**](docs/ASSETS.md) — Specification of the 16 approved runtime PNG assets.
- [**Release Process**](docs/RELEASE.md) — Packaging and release verification checklists.

---

## ⚖️ License

This project is licensed under the [MIT License](LICENSE).
