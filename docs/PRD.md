# Product Requirements Document (PRD) — Meli 💖

- **Product Name**: Meli — Ambient AI Desktop Companion
- **Version**: 1.0.0
- **Document Status**: Approved / Production Baseline
- **Target Audience**: Developers, power users, and enterprise knowledge workers seeking a companion AI on their desktop.

---

## 1. Executive Summary & Vision

**Meli** is an ambient desktop companion engineered to bridge conversational generative AI with physical desktop presence, low-latency audio interaction, enterprise knowledge grounding, and auditable tool execution.

Unlike browser-bound chat interfaces, Meli lives directly on the operating system workspace inside a high-DPI transparent window. She observes user activity, reacts to mouse proximity, listens via global push-to-talk, queries enterprise databases, and performs authorized system actions while maintaining a delightful anime aesthetic.

---

## 2. Product Goals & Core Objectives

1. **Ambient Desktop Integration**: Provide a responsive, transparent character presence that occupies minimal screen estate without obstructive backgrounds.
2. **Interactive Tactile Feedback**: Support intuitive direct interactions including hover gaze tracking, single-click petting bounces, and double-click portal sink-and-pop animations.
3. **Low-Latency Push-to-Talk (PTT)**: Enable hands-free voice interaction via global hotkey (`Ctrl+Shift+V`) with accurate transcription and warm feminine voice synthesis.
4. **Enterprise Knowledge Grounding (RAG)**: Deliver factual answers grounded in company documents retrieved via Elasticsearch BM25 search.
5. **Auditable Tool & Action Intelligence**: Execute system tasks (time lookup, web navigation, note creation, memory persistence) through a deterministic policy engine with explicit user confirmations for state-modifying actions.
6. **Zero-Crop Responsive Layout**: Ensure character composition remains 100% visible from top ahoge to shoes across Compact (280x420), Default (360x520), and Large (460x640) presets and various DPI scalings (100%, 125%, 150%).

---

## 3. User Personas & Use Cases

### Personas
- **Developer / Engineer**: Wants a low-friction assistant to trigger quick queries, take meeting notes, and inspect documentation without switching browser tabs.
- **Enterprise Knowledge Worker**: Needs quick access to internal corporate guidelines, policies, and project notes with instant memory recall.
- **Companion / Avatar Enthusiast**: Enjoys an aesthetically rich, interactive desktop companion with expressive anime visual states and voice personality.

### Key Use Cases
- **Hands-Free Querying**: Holding `Ctrl+Shift+V` while coding to ask for documentation or current time.
- **Contextual Note Taking**: Asking Meli to create a note, reviewing the in-chat confirmation card, and approving persistence to the local database.
- **Knowledge Retrieval**: Asking questions about enterprise deployment policies and receiving cited, grounded summaries.
- **Ambient Focus Companion**: Having Meli sit unobtrusively on the screen edge, showing focused, working, or thinking states matching the user's workflow.

---

## 4. Functional Requirements

| Requirement ID | Feature Area | Description | Priority |
| :--- | :--- | :--- | :--- |
| **FR-01** | **Visual Performance System** | 16 standalone illustrations with 0-latency preloading and crossfade transitions. | P0 |
| **FR-02** | **Signal Heart Glow** | Chromatic pulsing heart icon anchored directly on the left-chest emblem (`X=53.50%, Y=47.00%`). | P0 |
| **FR-03** | **SINK/POP Portal** | 1200ms grounded physics sequence with volume conservation and elastic settle. | P0 |
| **FR-04** | **Push-To-Talk Voice** | Global `Ctrl+Shift+V` audio capture with Whisper STT and feminine TTS playback. | P0 |
| **FR-05** | **Feminine Voice Presets** | Dedicated female voice profiles (**Autumn**, **Diana**, **Hannah**) with male voice blacklisting. | P0 |
| **FR-06** | **Tool Execution Framework** | Typed tool framework with `AUTO_APPROVED`, `CONFIRMATION_REQUIRED`, and `BLOCKED` tiers. | P0 |
| **FR-07** | **Interactive Confirmation Cards** | In-chat `[Approve]` / `[Cancel]` cards for `CREATE_NOTE` and `SAVE_MEMORY`. | P0 |
| **FR-08** | **Enterprise Memory & RAG** | PostgreSQL conversation storage & Elasticsearch BM25 enterprise document search. | P0 |
| **FR-09** | **Side-by-Side Chat Drawer** | Flex stage layout where opening chat expands native window width (`+340px`) without covering Meli. | P0 |
| **FR-10** | **Asset Showcase Modal** | 16-card responsive showcase with full-body preview stage triggered via `Ctrl+Shift+S`. | P1 |

---

## 5. Non-Functional Requirements

- **Performance & Latency**:
  - State machine transition latency < 16ms (60fps animation budget).
  - STT transcription latency < 600ms via `whisper-large-v3-turbo`.
  - Local asset preloading completes in < 200ms on boot.
- **Reliability & Availability**:
  - Offline fallback to Web Speech API when remote TTS is unreachable.
  - Automatic database reconnection on connection drop.
- **Security & Privacy**:
  - Zero plain-text credentials in logs or frontend payloads.
  - Hard rejection of shell execution attempts (`execute_shell`, `eval`).
  - Audio buffers discarded immediately after transcription.
- **Compatibility**:
  - Windows 10/11 x64, macOS, and Linux (Tauri v2 runtime).
