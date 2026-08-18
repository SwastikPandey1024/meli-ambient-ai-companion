#!/usr/bin/env python3
"""
verify_core_preservation.py — Proves that 12 Approved Core States were 100% untouched.
"""

import sys
import json
import hashlib
from pathlib import Path

def check_core():
    baseline_path = Path("scripts/core_checksums_baseline.json")
    if not baseline_path.exists():
        print("[FAIL] Baseline checksums file not found!")
        return False

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    
    print("=" * 65)
    print("CORE ASSET IMMUTABILITY SHA256 VERIFICATION")
    print("=" * 65)

    all_matched = True
    for file_str, expected_hash in baseline.items():
        p = Path(file_str)
        if not p.exists():
            print(f"[FAIL] {p.name:32} is MISSING!")
            all_matched = False
            continue
        current_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        if current_hash == expected_hash:
            print(f"  [PASS - UNTOUCHED] {p.name:32} : {current_hash[:16]}... OK")
        else:
            print(f"  [FAIL - MUTATED!]  {p.name:32}")
            print(f"    Expected: {expected_hash}")
            print(f"    Got:      {current_hash}")
            all_matched = False

    print("=" * 65)
    if all_matched:
        print("[SUCCESS] ALL 12 APPROVED CORE STATES + BASE ASSETS REMAIN 100% UNTOUCHED (BYTE-FOR-BYTE IDENTICAL).")
    else:
        print("[FAILURE] CORE ASSETS WERE MODIFIED!")
    print("=" * 65)
    return all_matched

if __name__ == "__main__":
    success = check_core()
    sys.exit(0 if success else 1)
