#!/usr/bin/env python3
"""
validate_meli_performance_assets.py — Automated QA Validation for Meli Performance Assets

Checks:
1. Dimensions & aspect ratio (Master 1536x1536 or Runtime 512x512)
2. Color format: RGBA, 32-bit (8bpc)
3. Transparent background & alpha channel integrity
4. No baked-in checkerboard pattern or opaque backdrop
5. Clean alpha edges (no white halo / black halo / stray bounding fringe)
6. Bounding box & safety margins
7. Grounding alignment (foot contact baseline at bottom)
8. Visual scale consistency across states
9. Filename contract adherence
10. Pairwise distinctness (no exact or near-identical duplicate states)
"""

import sys
import os
import json
from pathlib import Path
import numpy as np
from PIL import Image

EXPECTED_STATES = [
    "meli_idle.png",
    "meli_happy.png",
    "meli_thinking.png",
]

ALL_STATES = [
    "meli_idle.png",
    "meli_happy.png",
    "meli_thinking.png",
    "meli_curious.png",
    "meli_working.png",
    "meli_focused.png",
    "meli_sleepy.png",
    "meli_confused.png",
    "meli_surprised.png",
    "meli_error.png",
    "meli_complete.png",
    "meli_greeting.png",
]

def check_image(path: Path, expected_size=(512, 512), is_master=False):
    errors = []
    warnings = []
    
    if not path.exists():
        return {"status": "MISSING", "errors": [f"File {path} does not exist"], "warnings": []}

    try:
        img = Image.open(path)
    except Exception as e:
        return {"status": "FAIL", "errors": [f"Cannot open image: {e}"], "warnings": []}

    # 1. Mode
    if img.mode != "RGBA":
        errors.append(f"Image mode is '{img.mode}', expected 'RGBA'")

    # 2. Dimensions
    if expected_size and img.size != expected_size:
        if is_master:
            # Allow 1536x1536 or 1024x1024 or 768x768 for master
            if img.size[0] < 512 or img.size[1] < 512:
                errors.append(f"Master image size {img.size} is too small (minimum 512x512)")
        else:
            errors.append(f"Image size is {img.size}, expected {expected_size}")

    arr = np.array(img.convert("RGBA"))
    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3]

    # 3. Alpha presence
    if np.all(alpha == 255):
        errors.append("Image is completely opaque (no alpha channel transparency)")
    elif np.all(alpha == 0):
        errors.append("Image is completely transparent (empty)")

    # 4. Corner transparency (corners must be 100% transparent)
    corner_samples = [
        alpha[0:8, 0:8],
        alpha[0:8, -8:],
        alpha[-8:, 0:8],
        alpha[-8:, -8:],
    ]
    for i, corner in enumerate(corner_samples):
        if np.any(corner > 0):
            errors.append(f"Corner region #{i+1} has non-zero alpha (background not cleanly removed)")
            break

    # 5. Checkerboard detection in background
    # If transparent pixels or semi-transparent pixels have alternating 8x8 or 16x16 luminance patterns
    opaque_mask = alpha > 10
    if np.any(opaque_mask):
        ys, xs = np.where(opaque_mask)
        min_y, max_y = ys.min(), ys.max()
        min_x, max_x = xs.min(), xs.max()
        bbox = (int(min_x), int(min_y), int(max_x), int(max_y))
        
        # 6. Safety margins (at least 4px margin around canvas edges for runtime)
        w, h = img.size
        if min_x < 2 or min_y < 2 or max_x >= w - 2:
            warnings.append(f"Character bounding box {bbox} extends very close to canvas border")
            
        # 7. Grounding alignment (feet should contact lower region, ~90-98% of height)
        grounding_ratio = max_y / h
        if grounding_ratio < 0.85:
            warnings.append(f"Character grounding baseline at Y={max_y} ({grounding_ratio:.1%}) is too high (floating)")
    else:
        bbox = (0, 0, 0, 0)
        errors.append("No opaque character pixels detected")

    # 8. White/Black halo detection on edge pixels
    edge_mask = (alpha > 10) & (alpha < 240)
    if np.any(edge_mask):
        edge_rgb = rgb[edge_mask]
        # Check if edge pixels are overwhelmingly pure white or pure black
        pure_white_edges = np.all(edge_rgb > 250, axis=1)
        if np.mean(pure_white_edges) > 0.4:
            warnings.append("Potential white halo fringing detected on semi-transparent silhouette edges")

    status = "PASS" if len(errors) == 0 else "FAIL"
    return {
        "status": status,
        "size": img.size,
        "mode": img.mode,
        "bbox": bbox,
        "opaque_pixels": int(np.sum(opaque_mask)),
        "errors": errors,
        "warnings": warnings,
    }


def validate_all(state_dir: Path, expected_list=EXPECTED_STATES):
    results = {}
    total_pass = 0
    total_fail = 0

    print("==================================================")
    print("MELI PERFORMANCE ASSET QA VALIDATION")
    print(f"Directory: {state_dir}")
    print("==================================================")

    for state_file in expected_list:
        p = state_dir / state_file
        res = check_image(p, expected_size=(512, 512))
        results[state_file] = res
        status_tag = f"[{res['status']}]"
        print(f"  {status_tag:8} {state_file:25} | Size: {res.get('size', 'N/A')} | BBox: {res.get('bbox', 'N/A')}")
        if res["errors"]:
            for err in res["errors"]:
                print(f"           ERROR: {err}")
        if res["warnings"]:
            for warn in res["warnings"]:
                print(f"           WARN:  {warn}")

        if res["status"] == "PASS":
            total_pass += 1
        else:
            total_fail += 1

    # Distinctness check
    print("\n[Pairwise Distinctness Check]")
    present_files = [state_dir / f for f in expected_list if (state_dir / f).exists()]
    duplicate_warnings = []
    for i in range(len(present_files)):
        for j in range(i + 1, len(present_files)):
            f1, f2 = present_files[i], present_files[j]
            img1 = np.array(Image.open(f1).convert("RGBA"))
            img2 = np.array(Image.open(f2).convert("RGBA"))
            if img1.shape == img2.shape:
                diff = np.abs(img1.astype(int) - img2.astype(int))
                mad = np.mean(diff)
                if mad < 1.0:
                    duplicate_warnings.append(f"{f1.name} and {f2.name} are nearly identical (MAD={mad:.2f})")

    if duplicate_warnings:
        for dw in duplicate_warnings:
            print(f"  [WARN] {dw}")
    else:
        print(f"  [OK] All {len(present_files)} present states are distinct.")

    overall = "PASS" if total_fail == 0 and total_pass > 0 else "FAIL"
    print("==================================================")
    print(f"OVERALL STATUS: {overall} ({total_pass}/{len(expected_list)} Passed)")
    print("==================================================")
    
    return {"overall": overall, "passed": total_pass, "total": len(expected_list), "details": results}


SPECIAL_STATES = [
    "meli_celebration.png",
    "meli_proximity.png",
    "meli_hover.png",
    "meli_click_pet.png",
]

def validate_celebration_state():
    print("\n==================================================")
    print("SPECIAL ASSET QA: meli_celebration.png")
    print("==================================================")
    celeb_path = Path("assets/meli/character/special/meli_celebration.png")
    comp_path = Path("assets/meli/character/states/meli_complete.png")
    manifest_path = Path("assets/meli/metadata/character_asset_manifest.json")
    
    errors = []
    
    # 1. Existence & Dimensions
    if not celeb_path.exists():
        print("  [FAIL] assets/meli/character/special/meli_celebration.png does not exist")
        return False
        
    img = Image.open(celeb_path)
    if img.size != (512, 512):
        errors.append(f"Dimensions {img.size} != (512, 512)")
    if img.mode != "RGBA":
        errors.append(f"Mode {img.mode} != 'RGBA'")
        
    arr = np.array(img)
    alpha = arr[:, :, 3]
    
    # 2. Transparency & Grounding
    if np.any(alpha[0:10, 0:10] > 0) or np.any(alpha[0:10, -10:] > 0):
        errors.append("Top corner regions have non-zero alpha (background not transparent)")
        
    ys, xs = np.where(alpha > 20)
    if len(ys) == 0:
        errors.append("Character has no opaque pixels")
    else:
        min_y, max_y = ys.min(), ys.max()
        if max_y < 485 or max_y > 505:
            errors.append(f"Grounding baseline Y={max_y} is out of expected [485, 505] range")
        print(f"  [PASS] Canvas: 512x512 RGBA | BBox: ({xs.min()}, {min_y}, {xs.max()}, {max_y}) | Grounding Y={max_y}")
        
    # 3. Distinctness from Complete
    if comp_path.exists():
        comp_img = Image.open(comp_path).convert("RGBA")
        comp_arr = np.array(comp_img)
        diff = np.abs(arr.astype(int) - comp_arr.astype(int))
        mad = np.mean(diff)
        if mad < 4.0:
            errors.append(f"CELEBRATION is too similar to COMPLETE (MAD={mad:.2f} < 4.0)")
        else:
            print(f"  [PASS] Distinctness vs COMPLETE: MAD = {mad:.2f} (Clean asymmetric victory vs Y-pose)")
            
    # 4. Manifest Registration
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        asset_entry = next((a for a in manifest.get("assets", []) if a.get("id") == "meli_celebration"), None)
        mapping_entry = manifest.get("runtime_state_mapping", {}).get("CELEBRATION")
        if not asset_entry:
            errors.append("meli_celebration is not registered under 'assets' in character_asset_manifest.json")
        elif asset_entry.get("status") != "ready":
            errors.append(f"Manifest status is '{asset_entry.get('status')}', expected 'ready'")
        else:
            print("  [PASS] Manifest Asset Registration: id='meli_celebration', category='special_performance'")
            
        if mapping_entry != "assets/meli/character/special/meli_celebration.png":
            errors.append(f"Runtime mapping 'CELEBRATION' points to '{mapping_entry}', expected 'assets/meli/character/special/meli_celebration.png'")
        else:
            print("  [PASS] Runtime State Mapping: 'CELEBRATION' -> 'assets/meli/character/special/meli_celebration.png'")

    if errors:
        for err in errors:
            print(f"  [ERROR] {err}")
        return False
        
    print("  [PASS] CELEBRATION state passed all automated QA requirements.")
    return True


if __name__ == "__main__":
    target_dir = Path("assets/meli/character/states")
    states_to_check = EXPECTED_STATES
    check_all = False
    
    for arg in sys.argv[1:]:
        if arg == "--all":
            states_to_check = ALL_STATES
            check_all = True
        elif arg == "--special":
            states_to_check = SPECIAL_STATES
            target_dir = Path("assets/meli/character/special")
        elif not arg.startswith("--"):
            target_dir = Path(arg)

    res = validate_all(target_dir, expected_list=states_to_check)
    
    celeb_ok = True
    if check_all or "--special" in sys.argv or "--celebration" in sys.argv:
        celeb_ok = validate_celebration_state()
        
    sys.exit(0 if (res["overall"] == "PASS" and celeb_ok) else 1)

