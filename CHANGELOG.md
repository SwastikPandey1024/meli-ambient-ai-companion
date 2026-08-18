# Changelog

All notable changes to Meli are documented in this file.

---

## [1.0.0] — 2026-08-19 (First Public Production Milestone)

### Highlights & Core Capabilities
- **Ambient AI Desktop Companion**: Intelligent, responsive anime companion with zero-background transparent desktop windowing, interactive proximity tracking, single-click tactile petting, and double-click SINK/POP sequence.
- **Enterprise Memory & Context Selection**: Persistent conversation storage, automatic extraction of salient user facts, and long-term memory retrieval powered by PostgreSQL.
- **Enterprise RAG Knowledge System**: Grounded document retrieval pipeline utilizing Elasticsearch BM25 search over enterprise knowledge bases.
- **Voice Intelligence (PTT / STT / TTS)**: Low-latency push-to-talk (`Ctrl+Shift+V`) powered by Whisper (`whisper-large-v3-turbo` / `whisper-large-v3`) and multi-provider TTS featuring strictly feminine companion voice presets (**Autumn**, **Diana**, **Hannah**) with local Web Speech fallback.
- **Safe Tool Intelligence Framework**: Auditable execution engine with strict permission tiers (`AUTO_APPROVED`, `CONFIRMATION_REQUIRED`, `BLOCKED`).
- **Interactive Action Confirmations**: Interactive in-chat approval cards for sensitive tools such as `CREATE_NOTE` and `SAVE_MEMORY` with explicit `[Approve]` and `[Cancel]` controls.
- **Security & Shell Injection Prevention**: Hard blocking of unsafe commands (`execute_shell`, `eval`, arbitrary file operations) and strict URL scheme validation (`http`/`https` only).
- **16 Standalone Character Assets**: 16 frozen, high-definition standalone PNG illustrations (`public/states/*.png`, `public/special/*.png`) with zero-latency preloading and seamless state crossfades.
- **Dynamic SINK/POP Portal Sequence**: 1200ms grounded physics animation featuring volume conservation (`scaleY: 0.10`, `scaleX: 0.35`, `opacity: 0`), portal generation below `Y=496px`, and elastic overshoot settle.
- **Harmonized Signal Heart System**: Dynamically pulsing chromatic heart anchor (`X=53.50%, Y=47.00%`) aligned directly over the hoodie left-chest emblem across all 16 states.
- **Tauri Native Desktop Runtime**: High-DPI transparent windowing with auto-expanding side-by-side chat companion drawer (`+340px`), draggable window manager, system tray controls, and safe bounds clamping.
- **Responsive Native UI**: Safe character framing from ahoge to shoes across Compact (280x420), Default (360x520), and Large (460x640) presets.
- **Asset Performance Showcase**: Built-in 16-card interactive performance showcase with full-body preview stage (`Ctrl+Shift+S`).
- **Comprehensive Verification**: 100% test pass rate across Frontend Vitest (80/80), Backend Pytest (52/52), Phase 0 Sprite QA (13/13), Motion QA (7/7), and E2E Tool Intelligence (7/7).

---

## [0.1.0] — 2026-08-19 (Production Release Candidate)

### Added
- Initial project scaffold and core architecture.
- 16 performance asset integration and Vitest validation.
- Tool policy engine and Groq LLM integration.
