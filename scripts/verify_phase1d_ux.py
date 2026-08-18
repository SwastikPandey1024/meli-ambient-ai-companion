"""
verify_phase1d_ux.py - Phase 1D UX Integration & Voice Verification Suite
==========================================================================
Verifies:
1. Health & core LLM model: openai/gpt-oss-120b
2. TTS Info & Orpheus female voices (autumn, diana, hannah)
3. TTS synthesis & WebSpeech fallback contracts
4. All 16 canonical PNG performance assets exist on disk in public/
5. Clean chat interactions without voice token leakage
"""

import sys
import os
from pathlib import Path
import httpx

BACKEND_URL = "http://127.0.0.1:8000"
ROOT_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT_DIR / "public"

CANONICAL_STATES = [
    "meli_idle.png",
    "meli_curious.png",
    "meli_happy.png",
    "meli_thinking.png",
    "meli_working.png",
    "meli_focused.png",
    "meli_sleepy.png",
    "meli_confused.png",
    "meli_surprised.png",
    "meli_error.png",
    "meli_complete.png",
    "meli_greeting.png",
]

CANONICAL_SPECIALS = [
    "meli_celebration.png",
    "meli_click_pet.png",
    "meli_hover.png",
    "meli_proximity.png",
]


def test_asset_files_exist():
    print("[1/5] Verifying 16 Approved Frozen PNG Assets on disk...")
    for f in CANONICAL_STATES:
        p = PUBLIC_DIR / "states" / f
        if not p.exists() or p.stat().st_size == 0:
            print(f"FAILED: State asset missing: {f}")
            return False

    for f in CANONICAL_SPECIALS:
        p = PUBLIC_DIR / "special" / f
        if not p.exists() or p.stat().st_size == 0:
            print(f"FAILED: Special asset missing: {f}")
            return False

    base_p = PUBLIC_DIR / "meli_body_base.png"
    if not base_p.exists() or base_p.stat().st_size == 0:
        print("FAILED: meli_body_base.png missing")
        return False

    print("       -> All 16 runtime assets + meli_body_base.png verified on disk.")
    return True


def test_backend_health():
    print("[2/5] Testing Backend Health & Core Model ID...")
    with httpx.Client(base_url=BACKEND_URL, timeout=10.0) as client:
        resp = client.get("/api/health")
        if resp.status_code != 200:
            print(f"FAILED: /api/health returned {resp.status_code}")
            return False
        data = resp.json()
        if data.get("model_configured") != "openai/gpt-oss-120b":
            print(f"FAILED: model_configured is {data.get('model_configured')} (expected openai/gpt-oss-120b)")
            return False
        print(f"       -> Model verified: {data.get('model_configured')}")
    return True


def test_tts_info_endpoint():
    print("[3/5] Testing /api/companion/tts/info endpoint...")
    with httpx.Client(base_url=BACKEND_URL, timeout=10.0) as client:
        resp = client.get("/api/companion/tts/info")
        if resp.status_code != 200:
            print(f"FAILED: /api/companion/tts/info returned {resp.status_code}")
            return False
        data = resp.json()
        voices = data.get("supported_voices", {})
        if "autumn" not in voices or "diana" not in voices or "hannah" not in voices:
            print(f"FAILED: Missing expected female voices in {voices}")
            return False
        if data.get("default_voice") != "autumn":
            print(f"FAILED: Default voice is {data.get('default_voice')} (expected autumn)")
            return False
        print(f"       -> TTS Info verified: model={data.get('model')}, default={data.get('default_voice')}")
    return True


def test_tts_synthesize_endpoint():
    print("[4/5] Testing /api/companion/synthesize endpoint...")
    with httpx.Client(base_url=BACKEND_URL, timeout=10.0) as client:
        resp = client.post(
            "/api/companion/synthesize",
            json={"text": "Hello, I am Meli.", "voice": "hannah"},
        )
        if resp.status_code != 200:
            print(f"FAILED: /api/companion/synthesize returned {resp.status_code}")
            return False
        content_type = resp.headers.get("content-type", "")
        if "audio/" in content_type:
            print("       -> Remote audio synthesis received.")
        else:
            data = resp.json()
            if data.get("fallback") != "web_speech":
                print(f"FAILED: Fallback is {data.get('fallback')} (expected web_speech)")
                return False
            print(f"       -> Synthesis fallback verified: {data.get('status')} -> {data.get('fallback')}")
    return True


def test_companion_chat_without_voice_directive():
    print("[5/5] Testing Companion Chat synthesis without voice directives...")
    with httpx.Client(base_url=BACKEND_URL, timeout=30.0) as client:
        resp = client.post(
            "/api/companion/chat",
            json={"message": "Introduce yourself in one warm sentence."},
        )
        if resp.status_code != 200:
            print(f"FAILED: /api/companion/chat returned {resp.status_code}")
            return False
        content = resp.text
        # Verify no bracketed raw voice markers leaked in response
        if "[Hannah voice" in content or "[Diana voice" in content or "[Autumn voice" in content:
            print("FAILED: Raw voice bracket marker leaked in chat response!")
            return False
        print("       -> Chat response verified clean without voice directive pollution.")
    return True


def main():
    print("=" * 60)
    print("MELI PHASE 1D UX INTEGRATION VERIFICATION SUITE")
    print("=" * 60)

    checks = [
        test_asset_files_exist,
        test_backend_health,
        test_tts_info_endpoint,
        test_tts_synthesize_endpoint,
        test_companion_chat_without_voice_directive,
    ]

    for check in checks:
        if not check():
            print("\nUX VERIFICATION FAILED!")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL PHASE 1D UX INTEGRATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
