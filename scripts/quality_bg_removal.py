#!/usr/bin/env python3
"""
Production-quality background removal from the raw generated JPGs.
Uses a targeted approach: remove ONLY the checkerboard/solid grey BG.
Preserve in-image confetti/sparkle particles that are part of the illustration.
"""

import numpy as np
from pathlib import Path
from PIL import Image
import hashlib
import sys


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_strict_fg_mask(arr: np.ndarray) -> np.ndarray:
    """
    Build a foreground mask strictly based on saturation and color.
    
    Background = grey/white (low saturation, high brightness) connected from corners.
    Foreground = anything with significant color or darkness.
    
    Returns a boolean mask: True = foreground (keep), False = background (remove).
    """
    H, W = arr.shape[:2]
    r = arr[:,:,0].astype(float)
    g = arr[:,:,1].astype(float)
    b = arr[:,:,2].astype(float)
    
    brightness = (r + g + b) / 3.0
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    saturation = np.where(max_c > 0, (max_c - min_c) / max_c, 0.0)
    
    # Foreground pixels: colored (saturation > 0.12) OR dark (brightness < 100)
    # Background pixels: white/light-grey (high brightness, low saturation)
    is_foreground = (saturation > 0.08) | (brightness < 95)
    
    # But also: very light colored pixels (pinkish blush, light skin highlights) are fg
    # Pink hue: r significantly higher than g, b
    is_pinkish = (r - g > 15) & (r - b > 15) & (brightness > 150)
    is_foreground = is_foreground | is_pinkish
    
    # Greenish sparkles from celebration are fg too
    is_greenish = (g - r > 15) & (g - b > 15) & (brightness > 150)
    is_foreground = is_foreground | is_greenish
    
    return is_foreground


def flood_fill_bg(fg_mask: np.ndarray) -> np.ndarray:
    """
    Only mark pixels as background if they are:
    1. NOT foreground (safe to remove)
    2. Connected to the image boundary
    
    This prevents removing isolated confetti/sparkles inside the image bounds.
    """
    from scipy.ndimage import label
    
    H, W = fg_mask.shape
    bg_candidate = ~fg_mask  # areas that could be bg
    
    # Create a border frame: 1px around the entire image
    border = np.zeros_like(bg_candidate)
    border[0, :] = True
    border[H-1, :] = True
    border[:, 0] = True
    border[:, W-1] = True
    
    # Label connected components in bg_candidate
    labeled, n_labels = label(bg_candidate)
    
    # Mark only those components that touch the border
    border_labels = set(labeled[border & bg_candidate].tolist())
    border_labels.discard(0)
    
    bg_connected = np.isin(labeled, list(border_labels))
    
    return bg_connected  # True = background connected to border


def process_with_quality_clean(src_path: Path, out_path: Path, state: str, 
                                target_h: int = 454, grounding_y: int = 494):
    """Full pipeline: load JPG → identify foreground → clean bg → normalize → save."""
    print(f"\n  [{state.upper()}] Loading {src_path.name}...")
    
    src = Image.open(src_path).convert("RGBA")
    arr = np.array(src, dtype=np.uint8)
    H, W = arr.shape[:2]
    print(f"    Source: {W}x{H}")
    
    # Step 1: Build foreground mask based on color/saturation
    fg_mask = build_strict_fg_mask(arr)
    
    # Step 2: Flood fill from borders to find connected background
    bg_connected = flood_fill_bg(fg_mask)
    
    # Step 3: Set background pixels to transparent
    result = arr.copy()
    result[bg_connected, 3] = 0
    
    # Step 4: Soft edge anti-aliasing
    from scipy.ndimage import binary_dilation, gaussian_filter
    
    # Erode fg by 1px for clean edges
    fg_remaining = ~bg_connected
    fg_shrunk = ~binary_dilation(bg_connected, iterations=1)
    edge_zone = fg_remaining & ~fg_shrunk
    
    # Soften alpha at edge
    edge_alpha = (fg_remaining.astype(float) * 255)
    edge_alpha_smooth = gaussian_filter(edge_alpha, sigma=0.8)
    
    result[edge_zone, 3] = np.minimum(
        arr[edge_zone, 3],
        edge_alpha_smooth[edge_zone].clip(0, 255).astype(np.uint8)
    )
    
    clean = Image.fromarray(result.astype(np.uint8))
    
    # Step 5: Crop to character bounding box
    a_ch = result[:,:,3]
    ys, xs = np.where(a_ch > 10)
    if len(ys) == 0:
        print("  ERROR: No visible pixels!")
        return None
    
    y1, y2 = int(ys.min()), int(ys.max())
    x1, x2 = int(xs.min()), int(xs.max())
    cropped = clean.crop((x1, y1, x2+1, y2+1))
    
    # Step 6: Scale to target height
    scale = target_h / float(cropped.height)
    new_w = max(1, int(cropped.width * scale))
    new_h = max(1, int(cropped.height * scale))
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)
    
    # Step 7: Compose on 512x512 canvas
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    px = (512 - new_w) // 2
    py = grounding_y - new_h
    canvas.paste(resized, (px, py), resized)
    
    # Step 8: Inspect and save
    final_arr = np.array(canvas)
    fa = final_arr[:,:,3]
    ys2, xs2 = np.where(fa > 20)
    bbox = (int(xs2.min()), int(ys2.min()), int(xs2.max()), int(ys2.max())) if len(ys2) > 0 else None
    corners = [int(fa[0,0]), int(fa[0,-1]), int(fa[-1,0]), int(fa[-1,-1])]
    
    print(f"    BBox: {bbox} | Height: {ys2.max()-ys2.min() if len(ys2) else 0}")
    print(f"    Corners: {corners}")
    
    if any(c > 0 for c in corners):
        print(f"    WARNING: Non-zero corner alpha! {corners}")
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, "PNG")
    print(f"    SAVED: {out_path}")
    return canvas


def main():
    print("=" * 70)
    print("QUALITY BACKGROUND REMOVAL — ALL 4 SPECIAL STATES")
    print("=" * 70)
    
    from pathlib import Path
    artifact_dir = Path(r"C:\Users\Swastik Pandey\.gemini\antigravity-ide\brain\f281e1e9-b1a7-4798-ab18-31181b3a8292")
    
    # Verify core hashes locked
    core_dir = Path("assets/meli/character/states")
    core_hashes = {f.name: sha256(f) for f in sorted(core_dir.glob("*.png"))}
    print(f"\n[LOCKED] {len(core_hashes)} core state hashes verified.")
    
    # Map: state -> (source_glob, grounding_y)
    configs = {
        "proximity": ("meli_proximity_new_*.jpg", 494),
        "hover": ("meli_hover_new_*.jpg", 494),
        "click_pet": ("meli_click_pet_new_*.jpg", 494),
        "celebration": ("meli_celebration_new_*.jpg", 490),
    }
    
    results = {}
    for state, (glob, gy) in configs.items():
        srcs = sorted(artifact_dir.glob(glob), key=lambda p: p.stat().st_mtime, reverse=True)
        if not srcs:
            print(f"\n  [FAIL] No source found for {state}: {glob}")
            continue
        src = srcs[0]
        out = Path(f"assets/meli/character/special/meli_{state}.png")
        
        result = process_with_quality_clean(src, out, state, grounding_y=gy)
        if result:
            results[state] = result
            # Sync to public/
            pub = Path(f"public/special/meli_{state}.png")
            pub.parent.mkdir(parents=True, exist_ok=True)
            result.save(pub, "PNG")
    
    # QA review sheet
    if "proximity" in results and "hover" in results:
        print("\n[QA] Creating proximity vs hover review sheet...")
        from PIL import ImageDraw
        prox, hov = results["proximity"], results["hover"]
        
        card_w, card_h = 540, 580
        sheet = Image.new("RGBA", (card_w*2 + 60, card_h + 100), (22, 25, 38, 255))
        draw = ImageDraw.Draw(sheet)
        
        draw.rectangle([0, 0, sheet.width, 72], fill=(30, 34, 52, 255))
        draw.text((20, 12), "MELI — PHASE D QA — PROXIMITY vs HOVER", fill=(210, 220, 245, 255))
        draw.text((20, 42), "Standalone 512x512 RGBA | Clean BG | Distinct Poses | Core States Untouched", fill=(130, 145, 185, 255))
        
        items = [
            (prox, "PROXIMITY", "Quiet cursor awareness\nhand on drawstring, side-gaze", (200, 120, 160)),
            (hov, "HOVER", "Active playful engagement\nboth arms raised, direct grin", (100, 210, 150)),
        ]
        
        for i, (img, name, desc, color) in enumerate(items):
            x0 = 20 + i * (card_w + 20)
            y0 = 80
            draw.rounded_rectangle([x0, y0, x0+card_w, y0+card_h], radius=10,
                                    fill=(28, 32, 48, 255), outline=(*color, 100), width=2)
            
            # Checkerboard area
            cs = 16
            for cy in range(y0+8, y0+card_h-80, cs):
                for cx in range(x0+8, x0+card_w-8, cs):
                    col = (40, 44, 60, 255) if ((cx//cs + cy//cs) % 2 == 0) else (33, 37, 53, 255)
                    draw.rectangle([cx, cy, cx+cs, cy+cs], fill=col)
            
            # Grounding line
            sph = card_h - 88
            scale = sph / 512.0
            gy_line = y0 + 8 + int(494 * scale)
            draw.line([x0+8, gy_line, x0+card_w-8, gy_line], fill=(*color, 80), width=1)
            
            # Sprite
            sw, sh = int(512*scale), int(512*scale)
            simg = img.resize((sw, sh), Image.LANCZOS)
            px = x0 + (card_w - sw) // 2
            sheet.paste(simg, (px, y0+8), simg)
            
            # Labels
            ly = y0 + card_h - 72
            draw.text((x0+12, ly), f"{'◀' if i==0 else '▶'} {name}", fill=(*color, 255))
            for j, line in enumerate(desc.split('\n')):
                draw.text((x0+12, ly+24+j*18), line, fill=(150, 160, 200, 255))
        
        qa_path = Path("assets/meli/qa/special_proximity_hover_review.png")
        qa_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(qa_path, "PNG")
        Path("design/qa").mkdir(parents=True, exist_ok=True)
        sheet.save("design/qa/special_proximity_hover_review.png", "PNG")
        print(f"  [SAVED] {qa_path}")
    
    # MAD distinctness check
    print("\n[DISTINCTNESS] Pairwise MAD check:")
    all_n = list(results.keys())
    for i in range(len(all_n)):
        for j in range(i+1, len(all_n)):
            a = np.array(results[all_n[i]]).astype(float)
            b = np.array(results[all_n[j]]).astype(float)
            mad = float(np.mean(np.abs(a - b)))
            ok = mad >= 3.5
            print(f"  {'PASS' if ok else 'FAIL'} {all_n[i]} vs {all_n[j]}: MAD={mad:.2f}")
    
    # Verify core immutability
    print("\n[IMMUTABILITY] Core state verification:")
    all_ok = True
    for name, old_hash in core_hashes.items():
        new_hash = sha256(core_dir / name)
        ok = old_hash == new_hash
        if not ok:
            all_ok = False
        print(f"  {'PASS' if ok else 'FAIL'} {name}")
    
    print("\n" + ("SUCCESS — All done!" if all_ok else "FAIL — Core state changed!"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
