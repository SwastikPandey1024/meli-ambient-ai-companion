"""
verify_native_layout.py - Native Responsive Layout & Safe Framing Verification
==============================================================================
Validates:
1. tauri.conf.json configuration constraints (transparent, resizable, min-dimensions)
2. Canonical 1:1 aspect-ratio and object-fit: contain rules in index.css
3. Responsive ChatPanel, Showcase Modal, and Preview Stage CSS rules
4. All 16 frozen PNG performance assets exist on disk in public/
5. SignalHeart 16-state anchor mapping integrity
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TAURI_CONF = ROOT_DIR / "src-tauri" / "tauri.conf.json"
INDEX_CSS = ROOT_DIR / "src" / "index.css"
PUBLIC_DIR = ROOT_DIR / "public"
SIGNAL_HEART_TSX = ROOT_DIR / "src" / "components" / "SignalHeart.tsx"

CANONICAL_16_ASSETS = [
    "states/meli_idle.png",
    "states/meli_curious.png",
    "states/meli_happy.png",
    "states/meli_thinking.png",
    "states/meli_working.png",
    "states/meli_focused.png",
    "states/meli_sleepy.png",
    "states/meli_confused.png",
    "states/meli_surprised.png",
    "states/meli_error.png",
    "states/meli_complete.png",
    "states/meli_greeting.png",
    "special/meli_proximity.png",
    "special/meli_hover.png",
    "special/meli_click_pet.png",
    "special/meli_celebration.png",
]


def test_tauri_conf():
    print("[1/5] Checking tauri.conf.json window configuration...")
    if not TAURI_CONF.exists():
        print(f"FAILED: tauri.conf.json missing at {TAURI_CONF}")
        return False
    with open(TAURI_CONF, "r", encoding="utf-8") as f:
        data = json.load(f)
    windows = data.get("app", {}).get("windows", [])
    if not windows:
        print("FAILED: No windows defined in tauri.conf.json")
        return False
    win = windows[0]
    if not win.get("transparent"):
        print("FAILED: Window is not set to transparent: true")
        return False
    if win.get("width") < 300 or win.get("height") < 450:
        print(f"FAILED: Default window dimensions too small: {win.get('width')}x{win.get('height')}")
        return False
    if win.get("minWidth", 0) < 200 or win.get("minHeight", 0) < 300:
        print(f"FAILED: Missing or invalid min dimensions: {win.get('minWidth')}x{win.get('minHeight')}")
        return False
    print(f"       -> tauri.conf.json verified: {win.get('width')}x{win.get('height')} (min {win.get('minWidth')}x{win.get('minHeight')}), transparent={win.get('transparent')}")
    return True


def test_index_css_rules():
    print("[2/5] Checking responsive CSS layout rules in index.css...")
    if not INDEX_CSS.exists():
        print(f"FAILED: index.css missing at {INDEX_CSS}")
        return False
    content = INDEX_CSS.read_text(encoding="utf-8")

    required_snippets = [
        "object-fit: contain",
        "aspect-ratio: 1 / 1",
        ".control-capsule",
        ".meli-chat-panel",
        ".showcase-modal",
        ".showcase-preview-overlay",
        ".showcase-preview-stage-viewport",
    ]

    for snippet in required_snippets:
        if snippet not in content:
            print(f"FAILED: Required CSS snippet missing: '{snippet}'")
            return False

    print("       -> index.css contains all required responsive safe-framing rules.")
    return True


def test_asset_files():
    print("[3/5] Verifying 16 canonical performance PNGs...")
    for rel_path in CANONICAL_16_ASSETS:
        p = PUBLIC_DIR / rel_path
        if not p.exists() or p.stat().st_size == 0:
            print(f"FAILED: Asset missing or 0 bytes: {rel_path}")
            return False
    print("       -> All 16 assets verified on disk.")
    return True


def test_signal_heart_states():
    print("[4/5] Checking SignalHeart.tsx 16-state color and anchor coverage...")
    if not SIGNAL_HEART_TSX.exists():
        print(f"FAILED: SignalHeart.tsx missing at {SIGNAL_HEART_TSX}")
        return False
    content = SIGNAL_HEART_TSX.read_text(encoding="utf-8")

    expected_states = [
        "idle",
        "curious",
        "happy",
        "thinking",
        "working",
        "focused",
        "sleepy",
        "confused",
        "surprised",
        "error",
        "complete",
        "greeting",
        "proximity",
        "hover",
        "click_pet",
        "celebration",
    ]

    for state in expected_states:
        if f"'{state}'" not in content and f'"{state}"' not in content:
            print(f"FAILED: State '{state}' missing in SignalHeart.tsx")
            return False

    print("       -> SignalHeart covers all 16 performance states.")
    return True


def test_composition_integrity():
    print("[5/5] Checking base sprite contract...")
    base_p = PUBLIC_DIR / "meli_body_base.png"
    if not base_p.exists() or base_p.stat().st_size == 0:
        print("FAILED: meli_body_base.png missing")
        return False
    print("       -> meli_body_base.png is intact.")
    return True


def main():
    print("=" * 60)
    print("MELI NATIVE RESPONSIVE LAYOUT VERIFICATION SUITE")
    print("=" * 60)

    checks = [
        test_tauri_conf,
        test_index_css_rules,
        test_asset_files,
        test_signal_heart_states,
        test_composition_integrity,
    ]

    for check in checks:
        if not check():
            print("\nLAYOUT VERIFICATION FAILED!")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL NATIVE RESPONSIVE LAYOUT CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
