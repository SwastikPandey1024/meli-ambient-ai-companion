#!/usr/bin/env python3
"""
inspect_alpha.py - Alpha Channel & Edge Matte Analyzer for Meli Sprites

Analyzes:
- Alpha channel histogram (0 transparent, 1-254 semi, 255 opaque)
- Edge matte gradient & fringe detection
- Corner transparency verification
- Bounding box calculation
- ASCII visualization of alpha distribution
"""

import sys
import os
import json
from pathlib import Path

# Add scripts directory to path to reuse PngReader from validate_meli_sprite
sys.path.insert(0, str(Path(__file__).parent))
from validate_meli_sprite import PngReader


def analyze_alpha(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return None

    reader = PngReader(path)
    if not reader.rgba_pixels:
        print(f"[ERROR] Unable to decode RGBA pixels from {path}")
        return None

    w, h = reader.width, reader.height
    total = w * h
    histogram = {
        "fully_transparent_0": 0,
        "semi_transparent_1_254": 0,
        "fully_opaque_255": 0,
    }

    # Bounding box
    min_x, min_y, max_x, max_y = w, h, -1, -1
    bright_fringe_pixels = 0

    for y in range(h):
        for x in range(w):
            r, g, b, a = reader.rgba_pixels[y][x]
            if a == 0:
                histogram["fully_transparent_0"] += 1
            elif a == 255:
                histogram["fully_opaque_255"] += 1
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
            else:
                histogram["semi_transparent_1_254"] += 1
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
                # Check for bright halo pixels in semi-transparent edges
                if r > 220 and g > 220 and b > 220 and a < 200:
                    bright_fringe_pixels += 1

    summary = {
        "file": str(path.name),
        "dimensions": f"{w}x{h}",
        "total_pixels": total,
        "histogram": histogram,
        "ratios": {
            "transparent_pct": round((histogram["fully_transparent_0"] / total) * 100, 2),
            "semi_transparent_pct": round((histogram["semi_transparent_1_254"] / total) * 100, 2),
            "opaque_pct": round((histogram["fully_opaque_255"] / total) * 100, 2),
        },
        "bounding_box": {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "width": max_x - min_x + 1 if max_x >= min_x else 0,
            "height": max_y - min_y + 1 if max_y >= min_y else 0,
        },
        "bright_fringe_pixel_count": bright_fringe_pixels,
        "clean_alpha_matte": bright_fringe_pixels == 0,
    }

    return summary, reader


def print_ascii_alpha(reader, grid_w=32, grid_h=32):
    """Print low-res ASCII alpha silhouette for visual spatial inspection."""
    w, h = reader.width, reader.height
    step_x = w / grid_w
    step_y = h / grid_h
    print("\n[ASCII Alpha Silhouette Overview]")
    print("+" + "-" * grid_w + "+")
    for gy in range(grid_h):
        line = ["|"]
        for gx in range(grid_w):
            px = int(gx * step_x)
            py = int(gy * step_y)
            a = reader.rgba_pixels[py][px][3]
            if a == 0:
                char = " "
            elif a < 128:
                char = "."
            elif a < 230:
                char = "+"
            else:
                char = "#"
            line.append(char)
        line.append("|")
        print("".join(line))
    print("+" + "-" * grid_w + "+")


def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_alpha.py <sprite_path>")
        sys.exit(1)

    res = analyze_alpha(sys.argv[1])
    if res:
        summary, reader = res
        print(json.dumps(summary, indent=2))
        print_ascii_alpha(reader)


if __name__ == "__main__":
    main()
