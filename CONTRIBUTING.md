# Contributing to Meli

Thank you for your interest in contributing to Meli!

---

## 1. Development Workflow

1. Fork the repository and create a feature branch (`git checkout -b feature/amazing-companion-feature`).
2. Follow the canonical setup in [Quickstart](docs/QUICKSTART.md).
3. Ensure all tests pass before submitting changes (`npm.cmd run test`, `pytest backend/tests/ -v`).
4. Commit your changes with clear, descriptive conventional commit messages.
5. Open a Pull Request against `main`.

---

## 2. Asset Immutability Rule

> **CRITICAL**: The 16 runtime PNG assets (`public/states/*.png`, `public/special/*.png`) and `assets/meli/character/meli_body_base.png` are **100% frozen**.
> Pull requests that modify, resize, crop, or regenerate these image files will be rejected to protect visual fidelity.

---

## 3. Testing Requirements

All contributions must include unit tests for new functionality and pass the existing verification suites:
- Frontend Vitest suite (`npm.cmd run test`)
- Backend Pytest suite (`python -m pytest backend/tests/ -v`)
- Motion & Sizing QA (`python scripts/test_meli_engine.py`)
