#!/usr/bin/env python3
"""
rebuild_proximity_and_hover_from_authorities.py — Regenerate ONLY meli_proximity.png & meli_hover.png

Single Visual Authorities:
- PROXIMITY: `design/artifacts/meli_proximity_review.png`
- HOVER: `design/artifacts/meli_hover_review.png`

Outputs:
1. assets/meli/character/special/meli_proximity.png
2. assets/meli/character/special/meli_hover.png
3. assets/meli/qa/special_proximity_hover_review.png (LEFT=PROXIMITY, RIGHT=HOVER)
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def extract_from_checkerboard(src_path, target_height=454, grounding_y=494):
    img = Image.open(src_path).convert('RGBA')
    arr = np.array(img)
    h, w, _ = arr.shape
    rgb = arr[:, :, :3].astype(float)
    
    # Background checkerboard colors in review card
    c1 = np.array([28, 30, 44], dtype=float)
    c2 = np.array([36, 38, 54], dtype=float)
    c3 = np.array([24, 26, 38], dtype=float)
    
    d1 = np.sqrt(np.sum((rgb - c1)**2, axis=2))
    d2 = np.sqrt(np.sum((rgb - c2)**2, axis=2))
    d3 = np.sqrt(np.sum((rgb - c3)**2, axis=2))
    
    min_d = np.minimum(np.minimum(d1, d2), d3)
    
    # Foreground mask
    alpha = np.zeros((h, w), dtype=np.uint8)
    alpha[min_d > 45.0] = 255
    
    # Subpixel anti-aliasing transition
    boundary = (min_d > 20.0) & (min_d <= 45.0)
    alpha[boundary] = np.clip((min_d[boundary] - 20.0) / 25.0 * 255.0, 0, 255).astype(np.uint8)
    
    # Color un-matting
    out_rgb = np.copy(rgb)
    for c in range(3):
        bg_val = c1[c]
        a = alpha.astype(float) / 255.0
        valid = a > 0.05
        out_rgb[valid, c] = np.clip((rgb[valid, c] - bg_val * (1.0 - a[valid])) / a[valid], 0, 255)
        
    rgba = np.dstack([out_rgb.astype(np.uint8), alpha])
    clean = Image.fromarray(rgba, 'RGBA')
    
    # Crop to character bounds
    ys, xs = np.where(alpha > 15)
    cropped = clean.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    
    # Scale to standard height
    scale = target_height / float(cropped.height)
    new_w = int(cropped.width * scale)
    new_h = int(cropped.height * scale)
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)
    
    canvas = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    paste_x = int((512 - new_w) / 2)
    paste_y = grounding_y - new_h
    canvas.paste(resized, (paste_x, paste_y), resized)
    return canvas

def main():
    print("=" * 65)
    print("REGENERATING ONLY PROXIMITY & HOVER FROM SPECIFIED SINGLE AUTHORITIES")
    print("=" * 65)

    ref_prox_path = Path("design/artifacts/meli_proximity_review.png")
    ref_hover_path = Path("design/artifacts/meli_hover_review.png")

    if not ref_prox_path.exists():
        print(f"[FAIL] Missing reference authority: {ref_prox_path}")
        return False
    if not ref_hover_path.exists():
        print(f"[FAIL] Missing reference authority: {ref_hover_path}")
        return False

    prox = extract_from_checkerboard(ref_prox_path, target_height=454, grounding_y=494)
    hover = extract_from_checkerboard(ref_hover_path, target_height=454, grounding_y=494)

    # Save to special production paths
    p_prox = Path("assets/meli/character/special/meli_proximity.png")
    p_hover = Path("assets/meli/character/special/meli_hover.png")

    p_prox.parent.mkdir(parents=True, exist_ok=True)
    prox.save(p_prox, "PNG")
    hover.save(p_hover, "PNG")

    # Sync to public paths
    pub_dir = Path("public/special")
    pub_dir.mkdir(parents=True, exist_ok=True)
    prox.save(pub_dir / "meli_proximity.png", "PNG")
    hover.save(pub_dir / "meli_hover.png", "PNG")

    # Root public fallbacks
    prox.save("public/proximity.png", "PNG")
    hover.save("public/hover.png", "PNG")

    print(f"  [SAVED] {p_prox} (512x512 RGBA, Grounding Y=494)")
    print(f"  [SAVED] {p_hover} (512x512 RGBA, Grounding Y=494)")

    # Validate difference
    arr_prox = np.array(prox)
    arr_hover = np.array(hover)
    mad = np.mean(np.abs(arr_prox.astype(int) - arr_hover.astype(int)))
    print(f"\n[Visual QA] PROXIMITY vs HOVER MAD: {mad:.2f} (Required >= 3.50)")
    if mad < 3.5:
        print("[FAIL] PROXIMITY and HOVER are too similar!")
        return False
    else:
        print("[PASS] PROXIMITY and HOVER are genuinely distinct character performances.")

    # Create assets/meli/qa/special_proximity_hover_review.png
    qa_dir = Path("assets/meli/qa")
    qa_dir.mkdir(parents=True, exist_ok=True)
    review_path = qa_dir / "special_proximity_hover_review.png"

    card_w = 440
    card_h = 540
    sheet_w = card_w * 2 + 50
    sheet_h = card_h + 70

    review_sheet = Image.new("RGBA", (sheet_w, sheet_h), (245, 246, 250, 255))
    draw = ImageDraw.Draw(review_sheet)

    # Header
    draw.rectangle([0, 0, sheet_w, 55], fill=(30, 32, 48, 255))
    draw.text((25, 18), "MELI SPECIAL ASSET REVIEW: PROXIMITY (LEFT) vs HOVER (RIGHT)", fill=(255, 255, 255, 255))
    draw.text((sheet_w - 280, 20), "512x512 RGBA • Grounding Y≈494", fill=(180, 190, 215, 255))

    items = [
        ("01 — PROXIMITY", "Quiet Cursor Awareness", "Observant side gaze, relaxed stance, soft rose heart glow. NO sparkles.", prox),
        ("02 — HOVER", "Active Interaction", "+4.5° playful tilt, drawstring hold, direct eye contact, cheerful smile, 2 sparkles.", hover),
    ]

    for idx, (title, intent, desc, img) in enumerate(items):
        x_off = 20 + idx * (card_w + 10)
        y_off = 65

        # Card box
        draw.rounded_rectangle([x_off, y_off, x_off + card_w, y_off + card_h], radius=8, fill=(255, 255, 255, 255), outline=(220, 225, 235, 255), width=2)

        # Checkerboard sprite background
        sprite_h = 370
        for cy in range(y_off + 8, y_off + sprite_h, 16):
            for cx in range(x_off + 8, x_off + card_w - 8, 16):
                color = (245, 246, 250, 255) if ((cx // 16) + (cy // 16)) % 2 == 0 else (235, 238, 245, 255)
                draw.rectangle([cx, cy, cx + 16, cy + 16], fill=color)

        # Grounding line at Y=494
        scale_factor = 350 / 512.0
        ground_canvas_y = int(y_off + 10 + 494 * scale_factor)
        draw.line([x_off + 10, ground_canvas_y, x_off + card_w - 10, ground_canvas_y], fill=(0, 200, 100, 140), width=1)

        # Character sprite
        resized_sprite = img.resize((int(512 * scale_factor), int(512 * scale_factor)), Image.LANCZOS)
        paste_x = x_off + int((card_w - resized_sprite.width) / 2)
        review_sheet.paste(resized_sprite, (paste_x, y_off + 10), resized_sprite)

        # Labels
        text_y = y_off + sprite_h + 15
        draw.text((x_off + 15, text_y), title, fill=(25, 28, 40, 255))
        draw.text((x_off + 15, text_y + 20), f"Intent: {intent}", fill=(230, 75, 115, 255))
        
        words = desc.split(" ")
        line1 = " ".join(words[:6])
        line2 = " ".join(words[6:])
        draw.text((x_off + 15, text_y + 40), line1, fill=(100, 105, 125, 255))
        if line2:
            draw.text((x_off + 15, text_y + 56), line2, fill=(100, 105, 125, 255))

    review_sheet.save(review_path, "PNG")
    print(f"\n[Artifact] Saved review sheet: {review_path}")

    # Synchronize review sheet to design/qa/
    design_qa_path = Path("design/qa/special_proximity_hover_review.png")
    review_sheet.save(design_qa_path, "PNG")
    print(f"[Artifact] Synchronized review sheet: {design_qa_path}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
