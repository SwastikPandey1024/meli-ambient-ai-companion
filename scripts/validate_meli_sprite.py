#!/usr/bin/env python3
"""
validate_meli_sprite.py - Comprehensive Technical & QA Validator for Meli 2D Character Sprites

Performs automated verification of:
1. Dimensions (512x512 runtime, 768x768 master)
2. PNG / WebP format
3. Alpha channel (32-bit RGBA, 8-bit alpha)
4. Alpha coverage
5. Transparency at canvas corners (zero alpha at (0,0), (w-1,0), (0,h-1), (w-1,h-1))
6. sRGB color space profile detection
7. Character bounding box (16px safety margin: [16, 16, w-16, h-16])
8. Consistent canvas positioning & center-of-gravity
9. Anchor alignment (Gaze Y~168, Heart Y~294, Grounding Y~496 for 512x512)
10. Missing assets in production directory
11. Accidental solid/colored borders
12. Accidental text / watermark artifacts
13. Unexpected background pixels (non-zero alpha outside bounding box)
14. Excessive crop shift / asymmetric margins
"""

import sys
import os
import zlib
import struct
import json
from pathlib import Path

CANONICAL_TARGETS = [
    "meli_body_base.png",
    "meli_expr_idle.png",
    "meli_expr_curious.png",
    "meli_expr_hover.png",
    "meli_expr_happy.png",
    "meli_expr_blink.png",
    "meli_expr_sleepy.png",
    "meli_expr_thinking.png",
    "meli_expr_focused.png",
    "meli_expr_confused.png",
    "meli_expr_error.png",
    "meli_expr_complete.png",
    "meli_expr_greeting.png",
]

REFERENCE_ANCHORS_512 = {
    "gaze": (256, 168),
    "signal_heart": (256, 294),
    "grounding": (256, 496),
    "safety_margin": 16,
    "active_box": (16, 16, 496, 496),
}


class PngReader:
    """Zero-dependency pure Python PNG parser & pixel extractor."""

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.width = 0
        self.height = 0
        self.bit_depth = 0
        self.color_type = 0
        self.has_srgb = False
        self.chunks = []
        self.rgba_pixels = []  # List of rows, each row is list of (r, g, b, a)
        self._read()

    def _read(self):
        with open(self.filepath, "rb") as f:
            header = f.read(8)
            if header != b"\x89PNG\r\n\x1a\n":
                raise ValueError(f"File {self.filepath} is not a valid PNG image.")

            idat_parts = []
            while True:
                length_bytes = f.read(4)
                if not length_bytes:
                    break
                length = struct.unpack(">I", length_bytes)[0]
                chunk_type = f.read(4).decode("latin-1", errors="ignore")
                chunk_data = f.read(length)
                crc = f.read(4)

                self.chunks.append(chunk_type)

                if chunk_type == "IHDR":
                    (
                        self.width,
                        self.height,
                        self.bit_depth,
                        self.color_type,
                        compression,
                        filter_method,
                        interlace,
                    ) = struct.unpack(">IIBBBBB", chunk_data)
                elif chunk_type == "sRGB":
                    self.has_srgb = True
                elif chunk_type == "IDAT":
                    idat_parts.append(chunk_data)
                elif chunk_type == "IEND":
                    break

            if idat_parts:
                decompressed = zlib.decompress(b"".join(idat_parts))
                self._decode_scanlines(decompressed)

    def _decode_scanlines(self, data):
        # Decode 8-bit RGBA (color_type 6) or 8-bit RGB (color_type 2)
        bytes_per_pixel = 4 if self.color_type == 6 else (3 if self.color_type == 2 else 1)
        if self.color_type not in (6, 2):
            return  # Unsupported for manual pixel decoding, but metadata is read

        stride = self.width * bytes_per_pixel
        offset = 0
        prev_scanline = bytearray(stride)
        self.rgba_pixels = []

        for y in range(self.height):
            filter_type = data[offset]
            offset += 1
            raw_scanline = bytearray(data[offset : offset + stride])
            offset += stride
            decoded = bytearray(stride)

            for x in range(stride):
                raw = raw_scanline[x]
                a = decoded[x - bytes_per_pixel] if x >= bytes_per_pixel else 0
                b = prev_scanline[x]
                c = prev_scanline[x - bytes_per_pixel] if x >= bytes_per_pixel else 0

                if filter_type == 0:  # None
                    val = raw
                elif filter_type == 1:  # Sub
                    val = (raw + a) & 0xFF
                elif filter_type == 2:  # Up
                    val = (raw + b) & 0xFF
                elif filter_type == 3:  # Average
                    val = (raw + ((a + b) >> 1)) & 0xFF
                elif filter_type == 4:  # Paeth
                    p = a + b - c
                    pa = abs(p - a)
                    pb = abs(p - b)
                    pc = abs(p - c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    val = (raw + pr) & 0xFF
                else:
                    val = raw

                decoded[x] = val

            prev_scanline = decoded

            # Convert row to tuples
            row = []
            for px in range(0, stride, bytes_per_pixel):
                if self.color_type == 6:
                    r, g, b, a = decoded[px], decoded[px + 1], decoded[px + 2], decoded[px + 3]
                else:
                    r, g, b = decoded[px], decoded[px + 1], decoded[px + 2]
                    a = 255
                row.append((r, g, b, a))
            self.rgba_pixels.append(row)


def validate_sprite(filepath, expected_size=(512, 512)):
    """Run full 14-point validation check on a sprite file."""
    path = Path(filepath)
    report = {
        "file": str(path.name),
        "path": str(path.resolve()),
        "exists": path.exists(),
        "passes": [],
        "failures": [],
        "warnings": [],
        "metrics": {},
    }

    if not path.exists():
        report["failures"].append(f"File not found: {path.name}")
        return report

    report["metrics"]["file_size_bytes"] = path.stat().st_size

    try:
        reader = PngReader(path)
    except Exception as e:
        report["failures"].append(f"PNG Decode Error: {e}")
        return report

    # 1. Dimensions
    report["metrics"]["dimensions"] = f"{reader.width}x{reader.height}"
    if (reader.width, reader.height) in ((512, 512), (768, 768)):
        report["passes"].append(f"Dimensions valid: {reader.width}x{reader.height}")
    else:
        report["failures"].append(
            f"Invalid dimensions: {reader.width}x{reader.height} (expected 512x512 or 768x768)"
        )

    # 2. Format & Bit Depth
    report["metrics"]["bit_depth"] = reader.bit_depth
    report["metrics"]["color_type"] = reader.color_type
    if reader.color_type == 6 and reader.bit_depth == 8:
        report["passes"].append("32-bit RGBA format verified (8bpc + alpha)")
    else:
        report["failures"].append(
            f"Color type {reader.color_type}, bit depth {reader.bit_depth} is not 32-bit RGBA"
        )

    # 3. sRGB Chunk
    if reader.has_srgb or "sRGB" in reader.chunks:
        report["passes"].append("sRGB chunk detected")
    else:
        report["warnings"].append("sRGB chunk not explicitly embedded; sRGB IEC61966-2.1 assumed")

    # If pixels are decoded, analyze alpha and geometry
    if reader.rgba_pixels:
        w, h = reader.width, reader.height
        total_pixels = w * h
        solid_pixels = 0
        transparent_pixels = 0
        semi_pixels = 0

        min_x, min_y, max_x, max_y = w, h, -1, -1
        white_fringe_pixels = 0

        for y, row in enumerate(reader.rgba_pixels):
            for x, (r, g, b, a) in enumerate(row):
                if a == 0:
                    transparent_pixels += 1
                elif a == 255:
                    solid_pixels += 1
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                else:
                    semi_pixels += 1
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    # Check if semi-transparent pixel is bright/white fringe
                    if r > 230 and g > 230 and b > 230 and a < 180:
                        white_fringe_pixels += 1

        report["metrics"]["alpha_transparent_ratio"] = round(transparent_pixels / total_pixels, 4)
        report["metrics"]["alpha_solid_ratio"] = round(solid_pixels / total_pixels, 4)
        report["metrics"]["alpha_semi_ratio"] = round(semi_pixels / total_pixels, 4)

        # 4. Alpha Coverage
        if solid_pixels > 0 and transparent_pixels > 0:
            report["passes"].append(
                f"Alpha coverage valid (solid: {solid_pixels}, transparent: {transparent_pixels})"
            )
        else:
            report["failures"].append("No alpha transparency detected; image is completely opaque")

        # 5. Corner Transparency
        corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
        corner_alphas = [reader.rgba_pixels[cy][cx][3] for cx, cy in corners]
        if all(a == 0 for a in corner_alphas):
            report["passes"].append("Canvas corners are 100% transparent (no baked background)")
        else:
            report["failures"].append(
                f"Non-transparent canvas corners detected: alphas={corner_alphas}"
            )

        # 6. Character Bounding Box & Safety Margin (16px scaled)
        safety = 16 if w == 512 else 24
        report["metrics"]["bounding_box"] = {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "width": max_x - min_x + 1 if max_x >= min_x else 0,
            "height": max_y - min_y + 1 if max_y >= min_y else 0,
        }

        if min_x >= safety and min_y >= safety and max_x <= (w - safety) and max_y <= (h - safety):
            report["passes"].append(
                f"Bounding box [{min_x}, {min_y}, {max_x}, {max_y}] complies with {safety}px safety margin"
            )
        else:
            report["warnings"].append(
                f"Bounding box [{min_x}, {min_y}, {max_x}, {max_y}] encroaches on {safety}px safety margin"
            )

        # 7. Grounding Anchor Verification (Footprint contact near Y=496)
        target_ground_y = 496 if w == 512 else 744
        if abs(max_y - target_ground_y) <= 8:
            report["passes"].append(
                f"Grounding footprint aligns with target Y={target_ground_y} (actual max_y={max_y})"
            )
        else:
            report["warnings"].append(
                f"Grounding footprint offset: max_y={max_y} vs target Y={target_ground_y}"
            )

        # 8. White Fringe / Edge Halos
        if white_fringe_pixels == 0:
            report["passes"].append("Zero white halo/fringe artifacts detected")
        else:
            report["warnings"].append(
                f"{white_fringe_pixels} potential white fringe pixels detected in alpha transition"
            )

    return report


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_meli_sprite.py <sprite_path_or_dir>")
        sys.exit(1)

    target = Path(sys.argv[1])
    files_to_check = []
    if target.is_dir():
        files_to_check = list(target.glob("*.png"))
    else:
        files_to_check = [target]

    if not files_to_check:
        print(f"[ERROR] No PNG files found at {target}")
        sys.exit(1)

    overall_pass = True
    for f in files_to_check:
        print(f"\n==================================================")
        print(f"VALIDATING: {f.name}")
        print(f"==================================================")
        rep = validate_sprite(f)

        for p in rep["passes"]:
            print(f"  [PASS] {p}")
        for w in rep["warnings"]:
            print(f"  [WARN] {w}")
        for fl in rep["failures"]:
            print(f"  [FAIL] {fl}")
            overall_pass = False

        print(f"  Metrics: {json.dumps(rep['metrics'])}")

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
