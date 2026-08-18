# Software Requirements Specification (SRS) — Meli 💖

- **Document Version**: 1.0.0
- **Status**: Release Baseline
- **System**: Meli Desktop Companion

---

## 1. System Interfaces & External Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    Meli System Boundaries                   │
├───────────────────┬─────────────────────────────────────────┤
│ Interface         │ Specification                           │
├───────────────────┼─────────────────────────────────────────┤
│ Frontend Shell    │ React 18, TypeScript 5, Vite 5          │
├───────────────────┼─────────────────────────────────────────┤
│ Desktop Windowing │ Tauri v2 (Rust 2021, Windows GNULLVM)   │
├───────────────────┼─────────────────────────────────────────┤
│ Backend Server    │ FastAPI, Uvicorn, Python 3.10+          │
├───────────────────┼─────────────────────────────────────────┤
│ LLM Reasoning     │ Groq API (openai/gpt-oss-120b)          │
├───────────────────┼─────────────────────────────────────────┤
│ Speech-to-Text    │ Groq Whisper (large-v3-turbo / large-v3)│
├───────────────────┼─────────────────────────────────────────┤
│ Text-to-Speech    │ CanopyLabs Orpheus / Web Speech API     │
├───────────────────┼─────────────────────────────────────────┤
│ Relational Store  │ PostgreSQL (asyncpg / SQLAlchemy Core)  │
├───────────────────┼─────────────────────────────────────────┤
│ Search Engine     │ Elasticsearch 8.x (BM25 Indexing)       │
└───────────────────┴─────────────────────────────────────────┘
```

---

## 2. Detailed Technical Requirements

### 2.1 Character State Machine (`CharacterStateMachine.ts`)
- **State Count**: 16 discrete canonical states.
- **Priority Hierarchy**:
  - `4`: `SINK_POP` (Interrupt-immune lock for 1200ms).
  - `3`: `CLICK_PET`, `CELEBRATION`, `GREETING`.
  - `2`: `THINKING`, `WORKING`, `FOCUSED`, `CURIOUS`, `COMPLETE`, `ERROR`.
  - `1`: `HOVER`, `PROXIMITY`.
  - `0`: `IDLE`, `SLEEPY`.
- **Precedence Rule**: Transitions to lower priority levels are rejected while a higher-priority state lock is active.

### 2.2 Voice Processing Engine (`src/voice/`)
- **Audio Capture**: MediaStream recording sampled at 16kHz PCM / Opus.
- **PTT Hotkey**: Global event listener on `Ctrl+Shift+V`.
- **Voice Blacklist**: Regex filter `MALE_NAME_BLACKLIST` rejecting male system voices on Windows/Chromium.
- **Profiles**:
  - `autumn`: Warm companion profile (Pitch: `1.15`, Rate: `0.94`).
  - `diana`: Crisp articulate profile (Pitch: `1.10`, Rate: `1.00`).
  - `hannah`: Expressive soft profile (Pitch: `1.20`, Rate: `0.96`).

### 2.3 Tool Execution & Policy Engine (`backend/app/tools/`)
- **Registry Structure**: Strongly-typed schemas using Pydantic models.
- **Confirmation State Machine**:
  - `NONE` ➔ Initial submission.
  - `PENDING_USER_APPROVAL` ➔ Emits `TOOL_CONFIRMATION_REQUIRED` SSE event with unique `call_id`.
  - `APPROVED` ➔ Executes tool action.
  - `REJECTED` ➔ Aborts execution and emits cancellation message.
- **Sanitization**: Automatic scrubbing of authorization tokens and credentials from audit payloads.

### 2.4 Desktop Layout & Window Management (`src-tauri/`)
- **Coordinate Space**: All positioning and sizing use `LogicalPosition` and `LogicalSize` to guarantee high-DPI compatibility.
- **Stage Framing**: Canonical 1:1 aspect ratio with baseline anchoring at `Y=496px` (`96.88%`).
- **Chat Panel Drawer**: Side-by-side flex layout with automatic window expansion (`+340px`).
