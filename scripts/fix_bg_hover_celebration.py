#!/usr/bin/env python3
"""
Fix background removal artifacts in meli_hover.png and meli_celebration.png.
Uses a more aggressive flood-fill from corners approach to remove
checkerboard/grey background remnants.
"""

import numpy as np
from pathlib import Path
from PIL import Image
from collections import deque
import hashlib


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def flood_fill_alpha(arr: np.ndarray, seed_coords, threshold: int = 235) -> np.ndarray:
    """
    Flood-fill from seeds to mark background pixels.
    Only marks pixels where R,G,B are all above threshold (near-white or grey).
    Returns boolean mask of background pixels.
    """
    H, W = arr.shape[:2]
    visited = np.zeros((H, W), dtype=bool)
    mask = np.zeros((H, W), dtype=bool)
    
    queue = deque()
    for (sy, sx) in seed_coords:
        if not visited[sy, sx]:
            r, g, b = int(arr[sy, sx, 0]), int(arr[sy, sx, 1]), int(arr[sy, sx, 2])
            # Only seed from near-white or grey corners
            if r >= threshold and g >= threshold and b >= threshold:
                queue.append((sy, sx))
                visited[sy, sx] = True
    
    while queue:
        y, x = queue.popleft()
        r, g, b = int(arr[y, x, 0]), int(arr[y, x, 1]), int(arr[y, x, 2])
        
        # Accept: near-white, near-grey (checkerboard), or fully-transparent pixels
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        color_diff = max_c - min_c
        brightness = (r + g + b) / 3.0
        
        is_bg = (
            (r >= threshold - 10 and g >= threshold - 10 and b >= threshold - 10) or  # white
            (brightness > 130 and color_diff < 25) or   # grey (checkerboard)
            (brightness > 150 and color_diff < 40)       # light grey speckles
        )
        
        if is_bg:
            mask[y, x] = True
            for ny, nx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
                if 0 <= ny < H and 0 <= nx < W and not visited[ny, nx]:
                    visited[ny, nx] = True
                    queue.append((ny, nx))
    
    return mask


def clean_background_aggressive(src_path: Path, out_path: Path, state: str):
    """Remove background with aggressive flood fill from all 4 corners."""
    print(f"\n  Fixing {state}...")
    
    img = Image.open(src_path).convert("RGBA")
    arr = np.array(img, dtype=np.uint8)
    H, W = arr.shape[:2]
    
    # Seed from all 4 corners + all edge midpoints
    seeds = [
        (0, 0), (0, W-1), (H-1, 0), (H-1, W-1),
        (0, W//4), (0, W//2), (0, 3*W//4),
        (H-1, W//4), (H-1, W//2), (H-1, 3*W//4),
        (H//4, 0), (H//2, 0), (3*H//4, 0),
        (H//4, W-1), (H//2, W-1), (3*H//4, W-1),
    ]
    
    bg_mask = flood_fill_alpha(arr, seeds, threshold=230)
    
    # Set background to fully transparent
    result = arr.copy()
    result[bg_mask, 3] = 0
    
    # Soft edge feathering: pixels adjacent to removed background
    from scipy.ndimage import binary_dilation, distance_transform_edt
    fg_mask = ~bg_mask
    
    # Slightly erode the edge to remove fringe pixels
    fg_eroded = fg_mask.copy()
    for _ in range(1):  # 1px erosion
        fg_eroded = ~binary_dilation(~fg_eroded, iterations=1)
    
    edge_zone = fg_mask & ~fg_eroded
    dist = distance_transform_edt(~fg_eroded).clip(0, 3)
    edge_alpha = ((1.0 - dist / 3.0) * 255).clip(0, 255).astype(np.uint8)
    
    result[edge_zone, 3] = np.minimum(arr[edge_zone, 3], edge_alpha[edge_zone])
    
    clean = Image.fromarray(result, mode="RGBA")
    
    # Inspect
    a = result[:, :, 3]
    ys, xs = np.where(a > 20)
    corners = [int(a[0,0]), int(a[0,-1]), int(a[-1,0]), int(a[-1,-1])]
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(ys) > 0 else None
    print(f"    BBox: {bbox} | Corners: {corners}")
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    clean.save(out_path, "PNG")
    print(f"    SAVED: {out_path}")
    return clean


def main():
    print("=" * 70)
    print("BACKGROUND FIX — HOVER AND CELEBRATION")
    print("=" * 70)
    
    # CRITICAL: Lock core states first
    core_dir = Path("assets/meli/character/states")
    core_hashes = {f.name: sha256(f) for f in sorted(core_dir.glob("*.png"))}
    
    targets = {
        "hover": Path("assets/meli/character/special/meli_hover.png"),
        "celebration": Path("assets/meli/character/special/meli_celebration.png"),
    }
    
    results = {}
    for state, path in targets.items():
        if not path.exists():
            print(f"  SKIP: {path} not found")
            continue
        result = clean_background_aggressive(path, path, state)
        results[state] = result
        
        # Sync to public/
        pub_path = Path(f"public/special/meli_{state}.png")
        pub_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(pub_path, "PNG")
        print(f"    SYNC: {pub_path}")
    
    # Verify core immutability
    print("\n[VERIFY] Core state immutability:")
    for name, old_hash in core_hashes.items():
        new_hash = sha256(core_dir / name)
        ok = old_hash == new_hash
        print(f"  {'PASS' if ok else 'FAIL'} {name}")
    
    print("\nDONE.")


if __name__ == "__main__":
    main()
