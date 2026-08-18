# Meli Release Management & Packaging

This document outlines the release checklist, build packaging instructions, and versioning standards for Meli.

---

## 1. Release Verification Checklist

Prior to tagging or publishing a release candidate:

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

## 2. Building Production Bundles

### Frontend Bundle
```powershell
npm.cmd run build
```
*Outputs static assets into `dist/`.*

### Native Windows Tauri Installer / Executable
```powershell
npm.cmd run tauri build
```
*Outputs the production executable and MSI/NSIS installer into `src-tauri/target/release/`.*

---

## 3. Versioning Standards

Meli adheres to [Semantic Versioning (SemVer 2.0.0)](https://semver.org/):
- **MAJOR (`x.0.0`)**: Breaking architectural changes, major database schema overhauls.
- **MINOR (`0.x.0`)**: New companion capabilities, voice providers, or tool integrations.
- **PATCH (`0.0.x`)**: Bug fixes, performance optimizations, and visual calibrations.
