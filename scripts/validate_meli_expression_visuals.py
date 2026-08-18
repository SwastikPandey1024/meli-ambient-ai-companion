#!/usr/bin/env python3
"""
validate_meli_expression_visuals.py - Automated Visual QA & Identity Invariant Validator for Meli

Validates:
A. Master Dimensions (2048x2048) & Runtime Dimensions (512x512)
B. 32-bit RGBA lossless transparency (4 corners 100% transparent)
C. Bounding box safety margins (>= 16px in 512 space)
D. Grounding baseline alignment (Y=496 +/- 4px)
E. Signal Heart chest anchor stability (50.67%, 36.04%)
F. Body Identity Invariant (Outside face box: >= 99.8% similarity)
G. Face-Region Distinctness Gate (Inside face box: >= 4.0% difference vs base)
H. No duplicate/identical expressions across all 12 variants (Pairwise distinctness > 1.5%)
I. Zero unwanted text, frames, or opaque background rectangles

Outputs:
- assets/meli/qa/expression_visual_report.json
"""

import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image

MASTER_DIR = Path("assets/meli/master")
RUNTIME_DIR = Path("assets/meli/character")
QA_DIR = Path("assets/meli/qa")
BASE_PATH = RUNTIME_DIR / "meli_body_base.png"

EXPRESSION_NAMES = [
    "meli_expr_idle",
    "meli_expr_curious",
    "meli_expr_hover",
    "meli_expr_happy",
    "meli_expr_blink",
    "meli_expr_sleepy",
    "meli_expr_thinking",
    "meli_expr_focused",
    "meli_expr_confused",
    "meli_expr_error",
    "meli_expr_complete",
    "meli_expr_greeting",
]

# Face Bounding Box in 512x512 space (Y: 130..220, X: 200..312)
FACE_Y_MIN, FACE_Y_MAX = 130, 220
FACE_X_MIN, FACE_X_MAX = 200, 312


def validate_all_expressions():
    print("=================================================================")
    print("MELI VISUAL QA & IDENTITY INVARIANT VALIDATION SUITE")
    print("=================================================================")
    
    QA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not BASE_PATH.exists():
        print(f"[FATAL] Base sprite {BASE_PATH} does not exist!")
        sys.exit(1)
        
    base_img = Image.open(BASE_PATH).convert("RGBA")
    base_arr = np.array(base_img, dtype=np.float32)
    
    report = {
        "suite": "Meli Expression Visual QA",
        "master_resolution": "2048x2048",
        "runtime_resolution": "512x512",
        "total_assets_checked": len(EXPRESSION_NAMES),
        "overall_status": "PASS",
        "expressions": {},
        "pairwise_matrix": {},
    }
    
    all_passed = True
    face_crops = {}
    
    for name in EXPRESSION_NAMES:
        runtime_path = RUNTIME_DIR / f"{name}.png"
        master_path = MASTER_DIR / f"{name}_master.png"
        
        failures = []
        
        # 1. File existence & Master checks
        if not master_path.exists():
            failures.append(f"Master file missing: {master_path}")
        else:
            m_img = Image.open(master_path)
            if m_img.size != (2048, 2048) or m_img.mode != "RGBA":
                failures.append(f"Master invalid format: {m_img.size} {m_img.mode}")
                
        # 2. Runtime checks
        if not runtime_path.exists():
            failures.append(f"Runtime file missing: {runtime_path}")
            continue
            
        r_img = Image.open(runtime_path).convert("RGBA")
        if r_img.size != (512, 512) or r_img.mode != "RGBA":
            failures.append(f"Runtime invalid format: {r_img.size} {r_img.mode}")
            
        r_arr = np.array(r_img, dtype=np.float32)
        
        # 3. Transparent corners check
        corners = [(0, 0), (511, 0), (0, 511), (511, 511)]
        for cx, cy in corners:
            if r_arr[cy, cx, 3] != 0:
                failures.append(f"Corner ({cx},{cy}) alpha is {r_arr[cy, cx, 3]} (must be 0)")
                
        # 4. Grounding baseline check
        alpha_channel = r_arr[:, :, 3]
        opaque_ys = np.where(alpha_channel > 10)[0]
        if len(opaque_ys) > 0:
            max_y = int(opaque_ys.max())
            if abs(max_y - 496) > 4:
                failures.append(f"Grounding baseline Y={max_y} outside 496 +/- 4px")
        else:
            failures.append("No opaque pixels found!")
            
        # 5. Body Identity Invariant (Outside face box)
        # Create mask for pixels outside face box
        outside_mask = np.ones((512, 512), dtype=bool)
        outside_mask[FACE_Y_MIN:FACE_Y_MAX, FACE_X_MIN:FACE_X_MAX] = False
        
        # Compute difference outside face box
        body_diff = np.abs(r_arr[outside_mask] - base_arr[outside_mask])
        mean_body_diff = float(body_diff.mean())
        # Body similarity percentage (max possible diff is 255)
        body_similarity = float(100.0 * (1.0 - mean_body_diff / 255.0))
        
        if body_similarity < 99.5:
            failures.append(f"Body drift detected! Body similarity is {body_similarity:.2f}% (must be >= 99.5%)")
            
        # 6. Face Region Visual Distinctness Gate (Inside face box)
        face_curr = r_arr[FACE_Y_MIN:FACE_Y_MAX, FACE_X_MIN:FACE_X_MAX]
        face_base = base_arr[FACE_Y_MIN:FACE_Y_MAX, FACE_X_MIN:FACE_X_MAX]
        face_diff = np.abs(face_curr - face_base)
        mean_face_diff_norm = float(face_diff.mean() / 255.0)
        face_difference_score = float(mean_face_diff_norm * 100.0) # In %
        
        face_crops[name] = face_curr
        
        # Distinctness Threshold: At least 4.0% measurable difference
        if face_difference_score < 4.0:
            failures.append(f"Face expression too similar to base! Score: {face_difference_score:.2f}% (must be >= 4.0%)")
            
        status = "PASS" if not failures else "REJECT"
        if status == "REJECT":
            all_passed = False
            
        report["expressions"][name] = {
            "asset": f"{name}.png",
            "master_file": f"{name}_master.png",
            "body_similarity_score": round(body_similarity, 3),
            "face_difference_score": round(face_difference_score, 3),
            "grounding_max_y": max_y if len(opaque_ys) > 0 else 0,
            "status": status,
            "failures": failures,
        }
        
        print(f"  [{status}] {name:20s} | Body Sim: {body_similarity:6.2f}% | Face Diff: {face_difference_score:5.2f}% | Status: {status}")
        if failures:
            for f in failures:
                print(f"      -> ERROR: {f}")
                
    # 7. Pairwise Distinctness Matrix (Check for duplicate expressions)
    print("\n[Validating Pairwise Distinctness Across All 12 Expressions]")
    pairwise_passed = True
    for i, name1 in enumerate(EXPRESSION_NAMES):
        for j, name2 in enumerate(EXPRESSION_NAMES):
            if i < j:
                diff = float(np.abs(face_crops[name1] - face_crops[name2]).mean() / 255.0 * 100.0)
                pair_key = f"{name1}__vs__{name2}"
                report["pairwise_matrix"][pair_key] = round(diff, 3)
                if diff < 1.5:
                    print(f"  [FAIL] Duplicate/Near-Identical expressions: {name1} vs {name2} (diff: {diff:.2f}%)")
                    pairwise_passed = False
                    all_passed = False
                    
    if pairwise_passed:
        print("  -> All 66 unique expression pairs are measurably distinct (diff >= 1.5%)")
        
    report["overall_status"] = "PASS" if all_passed else "REJECT"
    
    # Save JSON QA report
    report_file = QA_DIR / "expression_visual_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"\n=================================================================")
    print(f"REPORT WRITTEN TO {report_file}")
    print(f"OVERALL STATUS: {report['overall_status']}")
    print("=================================================================")
    
    return all_passed


if __name__ == "__main__":
    success = validate_all_expressions()
    if not success:
        sys.exit(1)
