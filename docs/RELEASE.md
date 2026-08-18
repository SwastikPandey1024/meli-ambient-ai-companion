# Meli Release Management & Packaging

This document outlines the release checklist, build packaging instructions, and versioning standards for Meli.

---

## 1. Current Release: `v1.0.0` (First Public Production Milestone)

- **Release Date**: 2026-08-19
- **Target Version**: `1.0.0`
- **Milestone Scope**:
  - Ambient AI desktop companion with transparent high-DPI desktop windowing
  - Full PostgreSQL conversation & salient fact memory persistence
  - Elasticsearch BM25 enterprise RAG knowledge retrieval
  - Voice intelligence (Push-to-Talk `Ctrl+Shift+V`, Whisper STT, feminine TTS voice presets)
  - Tool intelligence framework with `CREATE_NOTE` interactive confirmation and hard-blocked shell commands
  - 16 frozen standalone character illustrations with 0-latency preloading
  - Dynamic 1200ms SINK/POP grounded physics animation
  - Aligned Signal Heart chest emblem system (`X=53.50%, Y=47.00%`)
  - Auto-expanding side-by-side chat drawer (`+340px`)
  - Responsive layout across S/M/L presets with zero crop
  - 16-card Asset Performance Showcase (`Ctrl+Shift+S`)

---

## 2. Release Verification Checklist

Prior to tagging or publishing a release:

- [x] All 16 standalone PNG illustrations verified intact and frozen.
- [x] Frontend Vitest suite passes 100% (`80 / 80` tests passed).
- [x] TypeScript build compiles cleanly (`npm run build`).
- [x] Phase 0 Engine QA passes (`13 / 13` tests passed).
- [x] Meli Motion & Sizing QA passes (`7 / 7` tests passed).
- [x] Backend Pytest suite passes (`52 / 52` tests passed).
- [x] Native Rust / Cargo check passes (`cargo_wrapper.ps1 check`).
- [x] E2E Tool Intelligence suite passes (`7 / 7` tests passed).
- [x] Secrets and `.env` credentials scanned and excluded from Git.

---

## 3. Building Production Bundles & Standalone Packaging

### Step 1: Compile Frontend Bundle
```powershell
npm.cmd run build
```
*Compiles TypeScript and bundles static frontend assets into `dist/`.*

### Step 2: Build Native Release Binary
```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\cargo_wrapper.ps1 build --release
```
*Compiles optimized release binary `meli-app.exe` with embedded frontend assets.*

### Step 3: Package Self-Contained Release
```powershell
python scripts\package_windows_release.py
```
*Packages `meli-app.exe` alongside required native PE runtime DLLs (`libunwind.dll`, `libc++.dll`, `WebView2Loader.dll`) into `release/meli-v1.0.0-windows-x64/`.*

### Step 4: Verify Standalone Integrity
```powershell
python scripts\test_standalone_release.py
```
*Validates that the packaged binary boots cleanly in an isolated environment without Vite or compiler PATH dependencies.*

---

## 4. Release Layout Specification

```
release/meli-v1.0.0-windows-x64/
├── meli-app.exe         # Standalone desktop application with embedded UI
├── libunwind.dll        # LLVM MinGW unwinder runtime library
├── libc++.dll           # LLVM C++ runtime library
├── WebView2Loader.dll   # Microsoft WebView2 native loader
├── README.md            # Product overview & manual quickstart
└── LICENSE              # MIT License
```

---

## 5. Versioning Standards

Meli adheres to [Semantic Versioning (SemVer 2.0.0)](https://semver.org/):
- **MAJOR** (`1.0.0`): Incompatible architectural or protocol breaking changes.
- **MINOR** (`0.1.0`): Backwards-compatible new features (e.g. vision pipelines).
- **PATCH** (`0.0.1`): Backwards-compatible bug fixes and motion calibrations.
- **MAJOR (`x.0.0`)**: Breaking architectural changes, major database schema overhauls.
- **MINOR (`0.x.0`)**: New companion capabilities, voice providers, or tool integrations.
- **PATCH (`0.0.x`)**: Bug fixes, performance optimizations, and visual calibrations.
