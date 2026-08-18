#!/usr/bin/env python3
"""
debug_expression_alignment.py - Visual Debug QA for Meli Expression Overlays

For every expression, produces a debug image showing:
  - Canonical base sprite + overlay composite
  - Face bounding box outline (cyan)
  - Eye anchor points (yellow circles)
  - Brow anchors (green circles)
  - Mouth anchor (red circle)
  - Nose anchor (magenta circle)
  - Labels for each anchor
  - Delta bounding box & statistics

Output: assets/meli/qa/debug/<name>_alignment.png
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

BASE_SPRITE   = Path("assets/meli/character/meli_body_base.png")
COMPOSITE_DIR = Path("assets/meli/expressions/composite")
DEBUG_DIR     = Path("assets/meli/qa/debug")

# Canonical anchors from face_anchor_map.json
FACE_BBOX = (204, 138, 312, 216)  # (min_x, min_y, max_x, max_y)

ANCHORS = {
    "L-Eye":  (234.4, 168.6),
    "R-Eye":  (283.8, 167.5),
    "L-Brow": (236.9, 147.2),
    "R-Brow": (289.0, 147.7),
    "Nose":   (256.0, 184.0),
    "Mouth":  (254.0, 199.0),
    "L-Cheek":(216.0, 180.0),
    "R-Cheek":(298.0, 180.0),
}

ANCHOR_COLORS = {
    "L-Eye":  (255, 255, 0),
    "R-Eye":  (255, 255, 0),
    "L-Brow": (0, 255, 100),
    "R-Brow": (0, 255, 100),
    "Nose":   (255, 0, 255),
    "Mouth":  (255, 60, 60),
    "L-Cheek":(255, 180, 120),
    "R-Cheek":(255, 180, 120),
}

EXPRESSION_NAMES = [
    "idle", "curious", "hover", "happy", "blink", "sleepy",
    "thinking", "focused", "confused", "error", "complete", "greeting"
]


def build_debug_images():
    print("=" * 70)
    print("MELI EXPRESSION ALIGNMENT DEBUG TOOL")
    print("=" * 70)

    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    if not BASE_SPRITE.exists():
        print(f"[FATAL] Base sprite not found: {BASE_SPRITE}")
        sys.exit(1)

    base_img = Image.open(BASE_SPRITE).convert("RGBA")
    base_arr = np.array(base_img)

    for name in EXPRESSION_NAMES:
        comp_path = COMPOSITE_DIR / f"{name}.png"
        if not comp_path.exists():
            print(f"  [SKIP] {name}: Composite not found")
            continue

        comp_img = Image.open(comp_path).convert("RGBA")
        comp_arr = np.array(comp_img)

        # Create debug canvas
        debug = Image.new("RGBA", (512, 512), (32, 34, 48, 255))
        debug = Image.alpha_composite(debug, comp_img)
        draw = ImageDraw.Draw(debug)

        # Draw face bounding box
        bx0, by0, bx1, by1 = FACE_BBOX
        draw.rectangle([bx0, by0, bx1, by1], outline=(0, 255, 255, 220), width=2)
        draw.text((bx0 + 2, by0 - 12), "FACE BBOX [204..312, 138..216]", fill=(0, 255, 255, 220))

        # Draw anchor points
        for anchor_name, (ax, ay) in ANCHORS.items():
            color = ANCHOR_COLORS[anchor_name]
            r = 3
            draw.ellipse([ax - r, ay - r, ax + r, ay + r], outline=(*color, 255), width=2)
            draw.text((ax + r + 2, ay - 5), anchor_name, fill=(*color, 255))

        # Top banner
        draw.rectangle([0, 0, 512, 20], fill=(12, 14, 22, 220))
        draw.text((8, 4), f"DEBUG ALIGNMENT: {name.upper()}", fill=(255, 255, 255, 255))

        # Highlight overlay delta region
        diff = np.any(np.abs(comp_arr.astype(int) - base_arr.astype(int)) > 2, axis=2)

        if name != "idle" and np.any(diff):
            ys, xs = np.where(diff)
            dx0, dy0, dx1, dy1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            draw.rectangle([dx0 - 1, dy0 - 1, dx1 + 1, dy1 + 1], outline=(255, 120, 60, 220), width=1)
            draw.text((dx0, dy1 + 3), f"DELTA: {dx0},{dy0}->{dx1},{dy1}", fill=(255, 140, 60, 255))

            # Check if delta is inside face bbox
            face_mask = np.zeros((512, 512), dtype=bool)
            face_mask[by0:by1, bx0:bx1] = True
            inside_face = np.sum(diff & face_mask)
            total = np.sum(diff)
            face_pct = inside_face / max(total, 1) * 100
            draw.text((dx0, dy1 + 15), f"Face: {face_pct:.1f}% ({inside_face}/{total} px)", fill=(255, 220, 80, 255))

        debug_path = DEBUG_DIR / f"{name}_alignment.png"
        debug.save(debug_path, format="PNG")
        print(f"  [OK] {debug_path.name}")

    print(f"\nDebug images saved to: {DEBUG_DIR}/")


if __name__ == "__main__":
    build_debug_images()
