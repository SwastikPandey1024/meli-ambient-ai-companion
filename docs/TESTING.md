# Meli Testing & Verification Guide

This document defines the automated test matrix, validation scripts, and manual QA checklists.

---

## 1. Automated Test Matrix

| Suite Name | Target Area | Command | Test Count | Expected Result |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend Vitest** | State machine, voice, shell, responsive layout, showcase | `npm.cmd run test` | **80 / 80** | All 9 test files passed |
| **TypeScript Build** | Type safety and bundling | `npm.cmd run build` | **N/A** | 0 errors, clean bundle |
| **Phase 0 Engine** | 14-point technical QA, SINK/POP metrics, chest anchor | `python scripts/test_phase0_engine.py` | **13 / 13** | All 13 invariant checks passed |
| **Meli Engine QA** | Motion bounds, squash/stretch volume conservation | `python scripts/test_meli_engine.py` | **7 / 7** | All 7 motion checks passed |
| **Backend Pytest** | FastAPI endpoints, database repositories, tool engine, RAG | `python -m pytest backend/tests/ -v` | **52 / 52** | All 52 backend tests passed |
| **Rust / Cargo** | Tauri native code compilation & dependencies | `powershell scripts/cargo_wrapper.ps1 check` | **N/A** | Finished dev profile (0 errors) |
| **Native Layout QA** | Tauri config, responsive CSS rules, window constraints | `python scripts/verify_native_layout.py` | **5 / 5** | All 5 layout checks passed |
| **UX Verification** | 16 PNG existence, TTS info endpoint, prompt pollution | `python scripts/verify_phase1d_ux.py` | **5 / 5** | All 5 UX checks passed |
| **E2E Tool Intelligence**| Tool execution, confirmation flow, memory recall | `python scripts/verify_phase1d_e2e.py` | **7 / 7** | All 7 E2E scenarios passed |

---

## 2. Complete Verification Run

To execute the entire verification suite sequentially in PowerShell:

```powershell
# 1. Frontend & TypeScript
npm.cmd run test
npm.cmd run build

# 2. Character & Motion QA
python scripts/test_phase0_engine.py
python scripts/test_meli_engine.py

# 3. Backend & Tool Framework
python -m pytest backend/tests/ -v

# 4. Native Desktop & Layout QA
powershell -ExecutionPolicy Bypass -File scripts/cargo_wrapper.ps1 check
python scripts/verify_native_layout.py
python scripts/verify_phase1d_ux.py
python scripts/verify_phase1d_e2e.py
```

---

## 3. Regression Safeguards

- **Asset Immutability Check**: Verify MD5 hashes of all 16 runtime PNGs against `public/manifest.json`.
- **DPI Scaling Invariant**: Verify that `Size::Logical` is used in all Tauri window operations to ensure crisp scaling on 100%, 125%, and 150% DPI monitors.
- **Voice Blacklist Check**: Verify that `isNotMaleVoice()` in `web_speech_tts.ts` excludes male tokens and defaults to female profiles.
