#!/usr/bin/env python3
"""
process_base_sprite.py - High-Performance Alpha Keying, Anchor Alignment & Scaling Pipeline for Meli Base Sprite
"""

import sys
import os
import zlib
import struct
import math
import subprocess
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from generate_contact_sheet import write_png


def read_image_fast(filepath):
    """Fast bitmap reader using .NET LockBits & Marshal.Copy."""
    abs_path = str(Path(filepath).resolve()).replace("\\", "\\\\")
    temp_bin = str(Path("temp_raw_pixels.bin").resolve()).replace("\\", "\\\\")

    ps_script = f"""
    Add-Type -AssemblyName System.Drawing
    $img = [System.Drawing.Image]::FromFile('{abs_path}')
    $bmp = New-Object System.Drawing.Bitmap($img)
    $w = $bmp.Width
    $h = $bmp.Height
    $rect = New-Object System.Drawing.Rectangle(0, 0, $w, $h)
    $bmpData = $bmp.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $stride = $bmpData.Stride
    $bytes = New-Object byte[] ($stride * $h)
    [System.Runtime.InteropServices.Marshal]::Copy($bmpData.Scan0, $bytes, 0, $bytes.Length)
    $bmp.UnlockBits($bmpData)
    $bmp.Dispose()
    $img.Dispose()
    [System.IO.File]::WriteAllBytes('{temp_bin}', $bytes)
    Write-Output "$w $h $stride"
    """
    res = subprocess.run(
        ["powershell", "-Command", ps_script], capture_output=True, text=True, check=True
    )
    w_str, h_str, stride_str = res.stdout.strip().split()
    w, h, stride = int(w_str), int(h_str), int(stride_str)

    with open("temp_raw_pixels.bin", "rb") as f:
        raw = f.read()
    if os.path.exists("temp_raw_pixels.bin"):
        os.remove("temp_raw_pixels.bin")

    # Format32bppArgb is BGRA in memory (B, G, R, A)
    pixels = []
    for y in range(h):
        row = []
        row_offset = y * stride
        for x in range(w):
            idx = row_offset + x * 4
            b = raw[idx]
            g = raw[idx + 1]
            r = raw[idx + 2]
            a = raw[idx + 3]
            row.append((r, g, b, a))
        pixels.append(row)

    return w, h, pixels


def remove_checkerboard_and_align(input_path, output_path, target_size=(512, 512)):
    w, h, pixels = read_image_fast(input_path)
    print(f"Loaded source image: {w}x{h} from {input_path}")

    # 1. Flood-fill mask from 4 corners and perimeter
    # In checkerboard, background pixels have gray tones where R ~ G ~ B (within 16 units) and >= 180
    visited = bytearray(w * h)
    is_bg = bytearray(w * h)

    def is_checkerboard(r, g, b):
        diff = max(abs(r - g), abs(r - b), abs(g - b))
        return diff <= 16 and (r >= 180 and g >= 180 and b >= 180)

    queue = []
    # Seed perimeter
    for x in range(w):
        for y in (0, h - 1):
            idx = y * w + x
            visited[idx] = 1
            r, g, b, _ = pixels[y][x]
            if is_checkerboard(r, g, b):
                is_bg[idx] = 1
                queue.append((x, y))

    for y in range(h):
        for x in (0, w - 1):
            idx = y * w + x
            if not visited[idx]:
                visited[idx] = 1
                r, g, b, _ = pixels[y][x]
                if is_checkerboard(r, g, b):
                    is_bg[idx] = 1
                    queue.append((x, y))

    head = 0
    while head < len(queue):
        cx, cy = queue[head]
        head += 1

        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h:
                nidx = ny * w + nx
                if not visited[nidx]:
                    visited[nidx] = 1
                    nr, ng, nb, _ = pixels[ny][nx]
                    if is_checkerboard(nr, ng, nb):
                        is_bg[nidx] = 1
                        queue.append((nx, ny))

    # Calculate bounding box of non-background character pixels
    min_x, min_y, max_x, max_y = w, h, -1, -1
    for y in range(h):
        row_offset = y * w
        for x in range(w):
            if not is_bg[row_offset + x]:
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y

    char_w = max_x - min_x + 1
    char_h = max_y - min_y + 1
    print(
        f"Detected character silhouette box: [{min_x}, {min_y}, {max_x}, {max_y}] ({char_w}x{char_h})"
    )

    # 2. Scale & align to target canvas
    target_w, target_h = target_size
    # Target height: ~456px, soles grounding contact at Y=496, crown at Y=40, Gaze at Y~168
    desired_h = 456
    scale = desired_h / char_h

    scaled_w = int(char_w * scale)
    scaled_h = int(char_h * scale)

    dest_y = 496 - scaled_h
    dest_x = (target_w - scaled_w) // 2

    print(
        f"Scaling to {scaled_w}x{scaled_h}, positioning at ({dest_x}, {dest_y}), soles at Y={dest_y + scaled_h}"
    )

    out_canvas = [[(0, 0, 0, 0) for _ in range(target_w)] for _ in range(target_h)]

    for ty in range(scaled_h):
        for tx in range(scaled_w):
            sx = min_x + int(tx / scale)
            sy = min_y + int(ty / scale)

            if 0 <= sx < w and 0 <= sy < h and not is_bg[sy * w + sx]:
                r, g, b, _ = pixels[sy][sx]

                # Check edge neighbors for feathering
                is_edge = False
                for ddx in (-1, 0, 1):
                    for ddy in (-1, 0, 1):
                        chk_x, chk_y = sx + ddx, sy + ddy
                        if 0 <= chk_x < w and 0 <= chk_y < h and is_bg[chk_y * w + chk_x]:
                            is_edge = True
                            break
                    if is_edge:
                        break

                alpha = 240 if is_edge else 255
                out_x = dest_x + tx
                out_y = dest_y + ty
                if 0 <= out_x < target_w and 0 <= out_y < target_h:
                    out_canvas[out_y][out_x] = (r, g, b, alpha)

    # Write output PNG
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_png(out_path, target_w, target_h, out_canvas)
    print(f"[SUCCESS] Exported 32-bit RGBA base sprite to: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_base_sprite.py <raw_image> <out_png>")
        sys.exit(1)
    remove_checkerboard_and_align(sys.argv[1], sys.argv[2])
