#!/usr/bin/env python3
"""
rebuild_proximity_and_hover_only.py — Regenerate ONLY meli_proximity.png and meli_hover.png

Authoritative Reference: `design/qa/meli_celebration_review.png`
- PROXIMITY: FIRST character/panel (quiet cursor awareness, observant side-gaze, relaxed stance, soft rose heart, NO sparkles)
- HOVER: LAST character/panel (active interaction, playful head tilt, direct eye contact, cheerful smile, drawstring hold, emerald heart, 2 sparkles)

Outputs:
1. assets/meli/character/special/meli_proximity.png
2. assets/meli/character/special/meli_hover.png
3. assets/meli/qa/special_proximity_hover_review.png
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def extract_character_clean(panel_img, target_height=455, grounding_y=495):
    arr = np.array(panel_img)
    rgb = arr[:, :, :3].astype(float)
    bg = np.array([18, 20, 29], dtype=float)
    diff = np.sqrt(np.sum((rgb - bg)**2, axis=2))
    
    ys, xs = np.where(diff > 75.0)
    min_x, max_x = xs.min(), xs.max()
    min_y, max_y = ys.min(), ys.max()
    
    # Crop to character
    char_crop = panel_img.crop((min_x, min_y, max_x + 1, max_y + 1))
    arr_crop = np.array(char_crop)
    rgb_c = arr_crop[:, :, :3].astype(float)
    diff_c = np.sqrt(np.sum((rgb_c - bg)**2, axis=2))
    
    alpha = np.zeros(diff_c.shape, dtype=np.uint8)
    alpha[diff_c > 75.0] = 255
    boundary = (diff_c > 45.0) & (diff_c <= 75.0)
    alpha[boundary] = np.clip((diff_c[boundary] - 45.0) / 30.0 * 255.0, 0, 255).astype(np.uint8)
    
    # Color un-matting
    out_rgb = np.copy(rgb_c)
    for c in range(3):
        bg_val = bg[c]
        a = alpha.astype(float) / 255.0
        valid = a > 0.05
        out_rgb[valid, c] = np.clip((rgb_c[valid, c] - bg_val * (1.0 - a[valid])) / a[valid], 0, 255)
        
    rgba = np.dstack([out_rgb.astype(np.uint8), alpha])
    clean_char = Image.fromarray(rgba, 'RGBA')
    
    # Scale to standard height
    scale = target_height / float(clean_char.height)
    new_w = int(clean_char.width * scale)
    new_h = int(clean_char.height * scale)
    resized = clean_char.resize((new_w, new_h), Image.LANCZOS)
    
    canvas = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    paste_x = int((512 - new_w) / 2)
    paste_y = grounding_y - new_h
    canvas.paste(resized, (paste_x, paste_y), resized)
    return canvas

def main():
    print("=" * 65)
    print("REGENERATING ONLY PROXIMITY & HOVER FROM SPECIFIED BENCHMARK")
    print("=" * 65)

    ref_sheet_path = Path("design/qa/meli_celebration_review.png")
    if not ref_sheet_path.exists():
        print(f"[FAIL] Reference sheet missing: {ref_sheet_path}")
        return False

    sheet = Image.open(ref_sheet_path).convert("RGBA")

    # Crop panel 1 (FIRST character) and panel 3 (LAST character)
    p1 = sheet.crop((45, 85, 455, 470))
    p3 = sheet.crop((1005, 85, 1415, 470))

    prox = extract_character_clean(p1, target_height=455, grounding_y=495)
    hover = extract_character_clean(p3, target_height=455, grounding_y=495)

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

    print(f"  [SAVED] {p_prox} (512x512 RGBA, Grounding Y=495)")
    print(f"  [SAVED] {p_hover} (512x512 RGBA, Grounding Y=495)")

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

    card_w = 420
    card_h = 560
    sheet_w = card_w * 2 + 60
    sheet_h = card_h + 80

    review_sheet = Image.new("RGBA", (sheet_w, sheet_h), (245, 246, 250, 255))
    draw = ImageDraw.Draw(review_sheet)

    # Header
    draw.rectangle([0, 0, sheet_w, 65], fill=(30, 32, 48, 255))
    draw.text((25, 20), "MELI SPECIAL ASSET VERIFICATION: PROXIMITY vs HOVER", fill=(255, 255, 255, 255))
    draw.text((sheet_w - 280, 24), "512x512 RGBA • Grounding Y≈495", fill=(180, 190, 215, 255))

    items = [
        ("01 — PROXIMITY", "Quiet Cursor Awareness", "Observant side gaze, relaxed stance, soft rose heart glow. NO sparkles.", prox),
        ("02 — HOVER", "Active Interaction", "+4.5° playful tilt, drawstring hold, direct eye contact, cheerful smile, 2 sparkles.", hover),
    ]

    for idx, (title, intent, desc, img) in enumerate(items):
        x_off = 20 + idx * (card_w + 20)
        y_off = 75

        # Card box
        draw.rounded_rectangle([x_off, y_off, x_off + card_w, y_off + card_h], radius=10, fill=(255, 255, 255, 255), outline=(220, 225, 235, 255), width=2)

        # Checkerboard sprite background
        sprite_h = 380
        for cy in range(y_off + 10, y_off + sprite_h, 16):
            for cx in range(x_off + 10, x_off + card_w - 10, 16):
                color = (245, 246, 250, 255) if ((cx // 16) + (cy // 16)) % 2 == 0 else (235, 238, 245, 255)
                draw.rectangle([cx, cy, cx + 16, cy + 16], fill=color)

        # Grounding line at Y=495
        scale_factor = 360 / 512.0
        ground_canvas_y = int(y_off + 15 + 495 * scale_factor)
        draw.line([x_off + 15, ground_canvas_y, x_off + card_w - 15, ground_canvas_y], fill=(0, 200, 100, 140), width=1)

        # Character sprite
        resized_sprite = img.resize((int(512 * scale_factor), int(512 * scale_factor)), Image.LANCZOS)
        paste_x = x_off + int((card_w - resized_sprite.width) / 2)
        review_sheet.paste(resized_sprite, (paste_x, y_off + 15), resized_sprite)

        # Labels
        text_y = y_off + sprite_h + 15
        draw.text((x_off + 15, text_y), title, fill=(25, 28, 40, 255))
        draw.text((x_off + 15, text_y + 22), f"Intent: {intent}", fill=(230, 75, 115, 255))
        
        words = desc.split(" ")
        line1 = " ".join(words[:6])
        line2 = " ".join(words[6:])
        draw.text((x_off + 15, text_y + 44), line1, fill=(100, 105, 125, 255))
        if line2:
            draw.text((x_off + 15, text_y + 60), line2, fill=(100, 105, 125, 255))

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
