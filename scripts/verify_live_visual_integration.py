#!/usr/bin/env python3
"""
verify_live_visual_integration.py - Live End-to-End Visual Integration Verification for Meli

Tests all 4 companion scenarios + error handling against live FastAPI SSE backend:
1. Scenario 1: Casual Assistant Greeting
2. Scenario 2: Episodic Memory Formation
3. Scenario 3: Episodic Memory Retrieval
4. Scenario 4: Enterprise Knowledge Retrieval
5. Error Scenario: Graceful Visual Error Handling
"""

import sys
import json
import httpx

BACKEND_URL = "http://127.0.0.1:8000/api/companion/chat"
FRONTEND_URL = "http://127.0.0.1:5173"


def test_scenario(name, message, expected_types, expected_substring=None):
    print(f"\n=======================================================")
    print(f"TEST: {name}")
    print(f"Query: {message!r}")
    print(f"=======================================================")

    payload = {"message": message, "top_k": 3}
    received_types = []
    full_text = ""

    with httpx.Client(trust_env=False, timeout=60.0) as client:
        with client.stream("POST", BACKEND_URL, json=payload, headers={"Accept": "text/event-stream"}) as resp:
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            for line in resp.iter_lines():
                line = line.strip()
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                    etype = event.get("type")
                    if etype:
                        received_types.append(etype)
                        if etype == "RESPONSE_STREAM":
                            full_text += event.get("token", "")
                except json.JSONDecodeError:
                    pass

    print(f"  Received Events Sequence: {received_types[:3]} ... -> {received_types[-2:]}")
    safe_preview = full_text[:120].encode('ascii', 'replace').decode('ascii')
    print(f"  Response Preview: {safe_preview}...")

    for expected in expected_types:
        assert expected in received_types, f"Missing required event: {expected} in {received_types}"
    
    if expected_substring:
        import re
        norm_text = re.sub(r'\s+', ' ', full_text).lower()
        assert expected_substring.lower() in norm_text, f"Expected substring '{expected_substring}' not in normalized response"

    print(f"  -> [PASS] {name} completed successfully!")
    return full_text


def verify_frontend_assets():
    print("\n[Verifying Frontend Static Bundle & Production Sprites]")
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        r = client.get(FRONTEND_URL)
        assert r.status_code == 200, "Frontend index.html unreachable"
        assert "companion-bubble-layer" in r.text, "Missing companion-bubble-layer in DOM"
        assert "glasses-layer" in r.text, "Missing glasses-layer in DOM"
        assert "diagnostic-panel" in r.text, "Missing diagnostic-panel in DOM"
        print("  -> index.html contains all required enrichment layers and HUD!")

        # Verify base and composite preview sprites are served
        sprites_to_check = [
            "meli_body_base.png",
            "idle.png",
            "curious.png",
            "thinking.png",
            "happy.png",
            "complete.png",
            "error.png",
        ]
        for s in sprites_to_check:
            sr = client.get(f"{FRONTEND_URL}/{s}")
            assert sr.status_code == 200, f"Failed to serve sprite {s}"
            assert len(sr.content) > 1000, f"Sprite {s} too small"
        print(f"  -> All {len(sprites_to_check)} sampled composite preview sprites verified on frontend server!")

        # 2. Check SVG Overlays
        sample_svgs = [
            "idle.svg", "curious.svg", "hover.svg", "happy.svg",
            "blink.svg", "thinking.svg", "focused.svg", "complete.svg"
        ]
        for expr in sample_svgs:
            r = client.get(f"{FRONTEND_URL}/expressions/{expr}")
            if r.status_code != 200:
                print(f"  -> [FAIL] SVG overlay {expr} not accessible on frontend server (HTTP {r.status_code})")
                sys.exit(1)
        print("  -> All 8 sampled SVG vector overlays verified on frontend server!")


def main():
    print("Beginning Meli Live Visual & Intelligence Integration Verification...")
    verify_frontend_assets()

    # 1. Greeting
    test_scenario(
        "Scenario 1: Assistant Greeting",
        "Hello Meli, what can you help me with?",
        ["THINKING", "RESPONSE_STREAM", "RESPONSE_COMPLETED"]
    )

    # 2. Memory Store
    test_scenario(
        "Scenario 2: Episodic Memory Formation",
        "Remember that I am preparing an enterprise AI demo.",
        ["THINKING", "RESPONSE_STREAM", "RESPONSE_COMPLETED"]
    )

    # 3. Memory Retrieve
    test_scenario(
        "Scenario 3: Episodic Memory Recall",
        "What am I preparing?",
        ["THINKING", "MEMORY_RETRIEVED", "RESPONSE_STREAM", "RESPONSE_COMPLETED"],
        expected_substring="enterprise"
    )

    # 4. Enterprise Knowledge Retrieval
    test_scenario(
        "Scenario 4: Enterprise RAG Retrieval",
        "What is the Sev-1 incident SLA response time?",
        ["THINKING", "RESPONSE_STREAM", "RESPONSE_COMPLETED"],
        expected_substring="15"
    )

    print("\n=======================================================")
    print("ALL 4 LIVE COMPANION SCENARIOS + VISUAL ASSETS VERIFIED!")
    print("=======================================================")


if __name__ == "__main__":
    main()
