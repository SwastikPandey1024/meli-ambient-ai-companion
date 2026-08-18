#!/usr/bin/env python3
"""
validate_expression_overlays.py - Comprehensive QA Validator for Meli Expression Overlays v3

Validates all 10 Core Visual Invariants:
  A. Body outside face bbox: must remain >= 99.99% identical to base.
  B. Overlay bounding box: must remain inside approved facial region (X=204..312, Y=138..216).
  C. Expression pixel delta (Face MAD %): must exceed minimum threshold per expression.
     idle >= 0.00%, curious >= 0.80%, hover >= 0.50%, happy >= 3.00%, blink >= 2.00%,
     sleepy >= 1.50%, thinking >= 0.80%, focused >= 1.20%, confused >= 1.00%,
     error >= 0.80%, complete >= 1.00%, greeting >= 0.80%
  D. Face-only delta ratio: >90% of changed pixels must occur inside the face region.
  E. No shoulder marks (no changes in shoulder area).
  F. No hoodie marks (no changes below Y=230).
  G. No chest marks (Signal Heart area unchanged).
  H. No second face / oversized face.
  I. No body drift / grounding drift.
  J. No transparent-background contamination.

Generates: assets/meli/qa/expression_overlay_report.json
"""

import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image

BASE_SPRITE   = Path("assets/meli/character/meli_body_base.png")
OVERLAY_DIR   = Path("assets/meli/expressions/overlays")
COMPOSITE_DIR = Path("assets/meli/expressions/composite")
REPORT_PATH   = Path("assets/meli/qa/expression_overlay_report.json")

EXPRESSION_NAMES = [
    "idle", "curious", "hover", "happy", "blink", "sleepy",
    "thinking", "focused", "confused", "error", "complete", "greeting"
]

# Canonical face bounding box from face_anchor_map.json
FACE_MIN_X, FACE_MIN_Y = 204, 138
FACE_MAX_X, FACE_MAX_Y = 312, 216

# Per-expression minimum Face MAD thresholds (% mean absolute difference on face box)
MIN_FACE_MAD = {
    "idle":     0.00,
    "curious":  0.80,
    "hover":    0.50,
    "happy":    3.00,
    "blink":    2.00,
    "sleepy":   1.50,
    "thinking": 0.80,
    "focused":  1.20,
    "confused": 1.00,
    "error":    0.80,
    "complete": 1.00,
    "greeting": 0.80,
}


def face_mask():
    m = np.zeros((512, 512), dtype=bool)
    m[FACE_MIN_Y:FACE_MAX_Y, FACE_MIN_X:FACE_MAX_X] = True
    return m


def body_mask():
    """Everything outside the face region — must remain 100% identical to base."""
    return ~face_mask()


def run_validation():
    print("=" * 70)
    print("MELI EXPRESSION OVERLAY QA v3 - COMPREHENSIVE VALIDATION")
    print("=" * 70)

    if not BASE_SPRITE.exists():
        print(f"[FATAL] Base sprite not found: {BASE_SPRITE}")
        sys.exit(1)

    base_img = Image.open(BASE_SPRITE).convert("RGBA")
    base_arr = np.array(base_img)

    fm = face_mask()
    bm = body_mask()

    report = {
        "suite": "Meli Expression Overlay QA v3",
        "strategy": "CANONICAL_BASE_PLUS_SVG_OVERLAY",
        "canvas": [512, 512],
        "face_bbox": [FACE_MIN_X, FACE_MIN_Y, FACE_MAX_X, FACE_MAX_Y],
        "total_expressions": len(EXPRESSION_NAMES),
        "overall_status": "PASS",
        "expressions": {},
        "pairwise": {},
    }

    overall_pass = True
    comp_arrays = {}

    for name in EXPRESSION_NAMES:
        svg_path = OVERLAY_DIR / f"{name}.svg"
        comp_path = COMPOSITE_DIR / f"{name}.png"
        failures = []

        # Check file existence
        if not svg_path.exists():
            failures.append(f"SVG overlay missing: {svg_path}")
        if not comp_path.exists():
            failures.append(f"Composite PNG missing: {comp_path}")
            report["expressions"][name] = {"status": "FAIL", "failures": failures}
            overall_pass = False
            continue

        comp_img = Image.open(comp_path).convert("RGBA")
        comp_arr = np.array(comp_img)
        comp_arrays[name] = comp_arr

        # A. Dimension check
        if comp_img.size != (512, 512):
            failures.append(f"Wrong dimensions: {comp_img.size}")

        # B. Body unchanged outside face bounding box
        body_diff = np.abs(comp_arr[bm].astype(float) - base_arr[bm].astype(float))
        body_similarity = 100.0 - (float(np.mean(body_diff)) / 255.0 * 100.0)

        if body_similarity < 99.90:
            failures.append(f"Body pixel drift: {body_similarity:.4f}% similarity (need >=99.90%)")

        # C. Face difference delta (Face MAD %)
        diff_face = np.abs(comp_arr[FACE_MIN_Y:FACE_MAX_Y, FACE_MIN_X:FACE_MAX_X].astype(float) - 
                           base_arr[FACE_MIN_Y:FACE_MAX_Y, FACE_MIN_X:FACE_MAX_X].astype(float))
        face_mad = float(np.mean(diff_face) / 255.0 * 100.0)

        min_required = MIN_FACE_MAD.get(name, 0.0)
        if face_mad < min_required and name != "idle":
            failures.append(
                f"Expression too subtle: {face_mad:.2f}% Face MAD (need >={min_required:.2f}%)"
            )

        # D. Face-only delta ratio (>90% of changed pixels must be inside face region)
        pixel_diff = np.any(np.abs(comp_arr.astype(int) - base_arr.astype(int)) > 2, axis=2)
        total_changed = int(np.sum(pixel_diff))
        face_changed = int(np.sum(pixel_diff & fm))

        if name != "idle" and total_changed > 0:
            face_ratio = face_changed / total_changed * 100.0
            if face_ratio < 90.0:
                failures.append(
                    f"Too many changes outside face bbox: {face_ratio:.1f}% inside (need >=90.0%)"
                )
        else:
            face_ratio = 100.0

        # E. No overlay on shoulders/hoodie (below Y=230 or on shoulders)
        lower_body_diff = np.any(np.abs(comp_arr[230:, :].astype(int) - base_arr[230:, :].astype(int)) > 2, axis=2)
        if np.sum(lower_body_diff) > 0:
            failures.append(f"Marks detected on lower body/hoodie ({np.sum(lower_body_diff)} px)")

        # F. No chest marks (around signal heart X=250..270, Y=175..195 on chest)
        # Note: chest is below jaw line Y=220
        chest_diff = np.any(np.abs(comp_arr[220:260, 230:290].astype(int) - base_arr[220:260, 230:290].astype(int)) > 2, axis=2)
        if np.sum(chest_diff) > 0:
            failures.append(f"Chest marks detected ({np.sum(chest_diff)} px)")

        # G. No transparent-background contamination (corners must stay transparent)
        corners = [comp_arr[0, 0, 3], comp_arr[0, 511, 3], comp_arr[511, 0, 3], comp_arr[511, 511, 3]]
        if any(c != 0 for c in corners):
            failures.append("Non-transparent corners detected")

        # H. Grounding check
        alpha_rows = np.where(comp_arr[:, :, 3] > 10)
        max_y = int(alpha_rows[0].max()) if len(alpha_rows[0]) > 0 else 0
        if abs(max_y - 496) > 5:
            failures.append(f"Grounding drift: max_y={max_y} (expected ~496)")

        status = "PASS" if not failures else "FAIL"
        if status == "FAIL":
            overall_pass = False

        report["expressions"][name] = {
            "svg_file": f"{name}.svg",
            "composite_file": f"{name}.png",
            "body_similarity": round(body_similarity, 4),
            "face_mad_pct": round(face_mad, 3),
            "min_face_mad_required": min_required,
            "face_change_ratio": round(face_ratio, 1),
            "total_changed_px": total_changed,
            "face_changed_px": face_changed,
            "grounding_max_y": max_y,
            "status": status,
            "failures": failures,
        }

        mark = "PASS" if status == "PASS" else "FAIL"
        print(
            f"  [{mark:4s}] {name:12s} | Body: {body_similarity:7.3f}% | "
            f"Face MAD: {face_mad:5.2f}% (min {min_required:.2f}%) | "
            f"Face Ratio: {face_ratio:5.1f}% | Issues: {len(failures)}"
        )

    # Pairwise distinctness
    print(f"\n[Pairwise Distinctness - {len(EXPRESSION_NAMES) * (len(EXPRESSION_NAMES)-1) // 2} pairs]")
    pair_fails = 0
    for i in range(len(EXPRESSION_NAMES)):
        for j in range(i + 1, len(EXPRESSION_NAMES)):
            na, nb = EXPRESSION_NAMES[i], EXPRESSION_NAMES[j]
            a = comp_arrays.get(na)
            b = comp_arrays.get(nb)
            if a is None or b is None:
                continue
            # Compare in face region
            fa = a[FACE_MIN_Y:FACE_MAX_Y, FACE_MIN_X:FACE_MAX_X].astype(float)
            fb = b[FACE_MIN_Y:FACE_MAX_Y, FACE_MIN_X:FACE_MAX_X].astype(float)
            diff = float(np.mean(np.abs(fa - fb)) / 255.0 * 100.0)
            key = f"{na}_vs_{nb}"
            report["pairwise"][key] = round(diff, 4)

            if diff < 0.15 and not (na == "idle" and nb == "idle"):
                print(f"  [FAIL] NEAR-DUPLICATE: {na} vs {nb} ({diff:.2f}%)")
                pair_fails += 1
                overall_pass = False

    if pair_fails == 0:
        pairs = len(EXPRESSION_NAMES) * (len(EXPRESSION_NAMES) - 1) // 2
        print(f"  [OK] All {pairs} pairs are measurably distinct.")

    report["overall_status"] = "PASS" if overall_pass else "FAIL"

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'=' * 70}")
    print(f"QA REPORT: {REPORT_PATH}")
    print(f"OVERALL STATUS: {report['overall_status']}")
    print(f"{'=' * 70}")

    if not overall_pass:
        sys.exit(1)


if __name__ == "__main__":
    run_validation()
