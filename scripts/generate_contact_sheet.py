#!/usr/bin/env python3
"""
generate_contact_sheet.py - Diagnostic Contact Sheet & Pipeline Review Tool for Meli

Generates a diagnostic overview of available character sprites and masks:
- Compiles active sprites in assets/meli/character/ into a structured matrix report
- Exports PNG contact sheet using pure Python PNG encoding when sprites are available
"""

import sys
import os
import zlib
import struct
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_meli_sprite import PngReader, CANONICAL_TARGETS


def write_png(filepath, width, height, rgba_data):
    """Write an uncompressed/zlib-compressed 32-bit RGBA PNG."""
    raw_bytes = bytearray()
    for row in rgba_data:
        raw_bytes.append(0)  # Filter type 0 (None)
        for r, g, b, a in row:
            raw_bytes.extend((r, g, b, a))

    compressed = zlib.compress(bytes(raw_bytes), 9)

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF

    with open(filepath, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        # IHDR
        f.write(struct.pack(">I", 13))
        f.write(b"IHDR")
        f.write(ihdr_data)
        f.write(struct.pack(">I", ihdr_crc))
        # IDAT
        f.write(struct.pack(">I", len(compressed)))
        f.write(b"IDAT")
        f.write(compressed)
        f.write(struct.pack(">I", idat_crc))
        # IEND
        f.write(struct.pack(">I", 0))
        f.write(b"IEND")
        f.write(struct.pack(">I", iend_crc))


def generate_sheet(assets_dir, output_path):
    adir = Path(assets_dir)
    out_file = Path(output_path)

    existing_sprites = {}
    for target in CANONICAL_TARGETS:
        p = adir / target
        if p.exists():
            try:
                reader = PngReader(p)
                existing_sprites[target] = reader
            except Exception as e:
                print(f"[WARN] Error reading {p.name}: {e}")

    print(f"\n[Contact Sheet Report]")
    print(f"Total Canonical Targets : {len(CANONICAL_TARGETS)}")
    print(f"Available Sprites       : {len(existing_sprites)}")
    print(f"Pending Sprites         : {len(CANONICAL_TARGETS) - len(existing_sprites)}")

    if not existing_sprites:
        print("[INFO] No sprite images available yet to composite into a contact sheet.")
        return False

    # If we have sprites, let's composite them into a grid
    cols = 4
    rows = (len(CANONICAL_TARGETS) + cols - 1) // cols
    tile_w, tile_h = 256, 256  # Scaled half-size tiles for overview
    sheet_w = cols * tile_w
    sheet_h = rows * tile_h

    # Create transparent blank canvas
    grid = [[(23, 24, 36, 255) for _ in range(sheet_w)] for _ in range(sheet_h)]

    for idx, name in enumerate(CANONICAL_TARGETS):
        col = idx % cols
        row = idx // cols
        ox = col * tile_w
        oy = row * tile_h

        reader = existing_sprites.get(name)
        if reader and reader.rgba_pixels:
            sw, sh = reader.width, reader.height
            step_x = sw / tile_w
            step_y = sh / tile_h
            for ty in range(tile_h):
                for tx in range(tile_w):
                    sx = int(tx * step_x)
                    sy = int(ty * step_y)
                    r, g, b, a = reader.rgba_pixels[sy][sx]
                    # Alpha blend over dark background
                    if a > 0:
                        alpha_norm = a / 255.0
                        bg_r, bg_g, bg_b, _ = grid[oy + ty][ox + tx]
                        out_r = int(r * alpha_norm + bg_r * (1 - alpha_norm))
                        out_g = int(g * alpha_norm + bg_g * (1 - alpha_norm))
                        out_b = int(b * alpha_norm + bg_b * (1 - alpha_norm))
                        grid[oy + ty][ox + tx] = (out_r, out_g, out_b, 255)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    write_png(out_file, sheet_w, sheet_h, grid)
    print(f"[SUCCESS] Contact sheet generated at {out_file}")
    return True


def main():
    assets_dir = sys.argv[1] if len(sys.argv) > 1 else "assets/meli/character"
    output_path = (
        sys.argv[2] if len(sys.argv) > 2 else "assets/meli/qa/meli_production_contact_sheet.png"
    )
    generate_sheet(assets_dir, output_path)


if __name__ == "__main__":
    main()
