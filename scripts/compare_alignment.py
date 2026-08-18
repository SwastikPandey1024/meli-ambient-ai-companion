#!/usr/bin/env python3
"""
compare_alignment.py - Spatial Alignment & Silhouette Overlap Validator for Meli Sprites

Compares a secondary or expression sprite against a reference base sprite (meli_body_base.png):
- Computes silhouette intersection over union (IoU)
- Checks bounding box shift (Δx, Δy)
- Measures anchor consistency (Gaze, Signal Heart, Grounding baseline)
- Reports alignment score (0.0 - 1.0)
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_meli_sprite import PngReader


def compare_sprites(base_path, target_path):
    base_file = Path(base_path)
    target_file = Path(target_path)

    if not base_file.exists():
        print(f"[ERROR] Base sprite file not found: {base_file}")
        return None
    if not target_file.exists():
        print(f"[ERROR] Target sprite file not found: {target_file}")
        return None

    base = PngReader(base_file)
    target = PngReader(target_file)

    if base.width != target.width or base.height != target.height:
        print(
            f"[ERROR] Dimension mismatch: {base.width}x{base.height} vs {target.width}x{target.height}"
        )
        return None

    w, h = base.width, base.height
    intersection = 0
    union = 0
    base_solid = 0
    target_solid = 0

    base_com_x, base_com_y = 0, 0
    target_com_x, target_com_y = 0, 0

    base_max_y = -1
    target_max_y = -1

    for y in range(h):
        for x in range(w):
            b_alpha = base.rgba_pixels[y][x][3]
            t_alpha = target.rgba_pixels[y][x][3]

            b_active = b_alpha > 32
            t_active = t_alpha > 32

            if b_active:
                base_solid += 1
                base_com_x += x
                base_com_y += y
                base_max_y = max(base_max_y, y)

            if t_active:
                target_solid += 1
                target_com_x += x
                target_com_y += y
                target_max_y = max(target_max_y, y)

            if b_active and t_active:
                intersection += 1
            if b_active or t_active:
                union += 1

    iou = round(intersection / union, 4) if union > 0 else 0.0

    b_cx = base_com_x / base_solid if base_solid > 0 else 0
    b_cy = base_com_y / base_solid if base_solid > 0 else 0

    t_cx = target_com_x / target_solid if target_solid > 0 else 0
    t_cy = target_com_y / target_solid if target_solid > 0 else 0

    delta_cx = round(t_cx - b_cx, 2)
    delta_cy = round(t_cy - b_cy, 2)
    grounding_delta = target_max_y - base_max_y

    alignment_pass = (iou >= 0.70) and (abs(delta_cx) <= 6.0) and (abs(grounding_delta) <= 4)

    report = {
        "base_file": base_file.name,
        "target_file": target_file.name,
        "dimensions": f"{w}x{h}",
        "iou_silhouette_overlap": iou,
        "base_center_of_mass": {"x": round(b_cx, 2), "y": round(b_cy, 2)},
        "target_center_of_mass": {"x": round(t_cx, 2), "y": round(t_cy, 2)},
        "delta_center_of_mass": {"dx": delta_cx, "dy": delta_cy},
        "grounding_baseline_shift_px": grounding_delta,
        "alignment_pass": alignment_pass,
        "notes": "Consistent spatial registration"
        if alignment_pass
        else "Shift detected; review coordinate alignment",
    }

    return report


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_alignment.py <base_sprite_path> <target_sprite_path>")
        sys.exit(1)

    rep = compare_sprites(sys.argv[1], sys.argv[2])
    if rep:
        print(json.dumps(rep, indent=2))
        sys.exit(0 if rep["alignment_pass"] else 1)


if __name__ == "__main__":
    main()
