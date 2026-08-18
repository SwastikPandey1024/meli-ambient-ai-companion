# Architecture Decision Records (ADR) — Meli 💖

This document records the key architectural and technical decisions made during the design and implementation of Meli.

---

## ADR-001: Selection of Core LLM Reasoning Model
- **Date**: 2026-08-18
- **Status**: Accepted
- **Context**: The companion requires strong multi-step tool-calling, conversational warmth, and fast token streaming.
- **Decision**: Standardize on `openai/gpt-oss-120b` via Groq's high-speed inference engine.
- **Consequences**: Delivers sub-800ms time-to-first-token while maintaining reliable JSON structured outputs for tool invocations.

---

## ADR-002: Immutable 16-Asset Standalone Illustration Strategy
- **Date**: 2026-08-18
- **Status**: Accepted
- **Context**: Dynamic SVG face overlays created visual artifacts, alignment shifts, and neck displacement during state transitions.
- **Decision**: Freeze 16 standalone, artist-verified 512x512 PNG illustrations with 0-latency preloading on boot and crossfade transitions.
- **Consequences**: Guarantees visual perfection and zero jitter across all supported desktop resolutions and DPI scalings.

---

## ADR-003: Signal Heart Anchor Calibration & Chromatic Feedback
- **Date**: 2026-08-18
- **Status**: Accepted
- **Context**: The SVG glowing heart had duplicate displacement and misaligned positioning relative to Meli's hoodie chest graphic.
- **Decision**: Anchor the Signal Heart SVG directly to `X=53.50%, Y=47.00%` on the character transform container and apply state-specific chromatic drop-shadow glow filters.
- **Consequences**: Heart glows dynamically over the hoodie emblem across all 16 states without duplicate heart visuals.

---

## ADR-004: Three-Tier Tool Permission & Security Policy
- **Date**: 2026-08-18
- **Status**: Accepted
- **Context**: Enabling desktop automation carries security risks if arbitrary commands or unauthorized file writes are permitted.
- **Decision**: Implement a strict three-tier policy (`AUTO_APPROVED`, `CONFIRMATION_REQUIRED`, `BLOCKED`) enforced by the backend `ToolPolicyEngine`.
- **Consequences**: Unsafe shell commands (`execute_shell`, `eval`) are blocked at the engine layer; sensitive operations (`create_note`, `save_memory`) require explicit user confirmation.

---

## ADR-005: Strict Feminine Voice Profile & Blacklist Architecture
- **Date**: 2026-08-18
- **Status**: Accepted
- **Context**: On Windows Chromium/WebView2, `speechSynthesis.getVoices()` defaulted to male voices (e.g. `Microsoft David Desktop`).
- **Decision**: Introduce a strict male token blacklist (`MALE_NAME_BLACKLIST`) and curate three dedicated feminine profiles (**Autumn**, **Diana**, **Hannah**) with graceful Web Speech fallback.
- **Consequences**: Zero male voice leakage; consistent, soft companion vocalization.

---

## ADR-006: High-DPI Logical Windowing & Side-by-Side Flex Drawer
- **Date**: 2026-08-18
- **Status**: Accepted
- **Context**: Standard pixel-based windowing caused character cropping on 125%/150% Windows display scaling, and overlaying chat obscured the character.
- **Decision**: Use `LogicalPosition` and `LogicalSize` in Tauri and implement a flex-row stage that expands native window width (`+340px`) when chat opens.
- **Consequences**: Meli and chat remain side-by-side with full visibility from ahoge to shoes.
