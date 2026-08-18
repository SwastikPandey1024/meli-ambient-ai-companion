# Changelog

All notable changes to Meli are documented in this file.

---

## [0.1.0] — 2026-08-19 (Production Release Candidate)

### Added
- **16-State Visual Performance System**: 16 standalone illustrations with 0-latency preloading and seamless crossfade transitions.
- **Voice Intelligence (PTT)**: Global `Ctrl+Shift+V` push-to-talk with Whisper STT and strictly feminine voice synthesis (**Autumn**, **Diana**, **Hannah**).
- **Tool Intelligence & Action Framework**: Auditable tool execution engine supporting `get_time`, `search_knowledge`, `open_url`, `create_note`, and `save_memory` with interactive confirmation cards.
- **Enterprise Memory & RAG**: PostgreSQL async repository layer for conversations and memories, paired with Elasticsearch BM25 enterprise document search.
- **Native Tauri Desktop Shell**: High-DPI transparent windowing with auto-expanding side-by-side chat drawer, system tray controls, and safe bounds clamping.
- **Interactive Physics & Portals**: 1200ms squash-and-stretch SINK/POP sequence with grounded portal rendering, single-click pet bounce, and hover proximity tracking.
- **Asset Performance Showcase**: Built-in 16-card interactive performance showcase with full-body preview stage (`Ctrl+Shift+S`).

### Fixed
- Fixed male voice leakage on Windows by implementing strict male token blacklisting and non-male English voice filtering.
- Re-anchored Signal Heart directly over the hoodie left-chest emblem (`X=53.50%, Y=47.00%`).
- Resolved Tauri mouse drag capture interference with single-clicks and double-clicks.
- Resolved window hiding on startup by enforcing explicit visibility and focus on application boot.
