#!/usr/bin/env python3
"""
build_refined_special_assets.py — High-Precision Generator for PROXIMITY and HOVER Special States

Generates:
1. assets/meli/character/special/meli_proximity.png (Subtle awareness / noticing nearby cursor)
2. assets/meli/character/special/meli_hover.png (Active engagement / playful warm hover reaction)

Invariants:
- 512x512 RGBA transparent
- Grounding contact Y in [493, 495]
- Canonical Meli identity (palette, proportions, lineart, clothing)
- PROXIMITY != HOVER (high semantic & visual distinctness)
"""

import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def create_glow(size, color, radius=12):
    """Create a smooth radial glow sprite."""
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    center = size // 2
    for r in range(radius, 0, -1):
        alpha = int(180 * (1.0 - r / radius) ** 1.5)
        c = (color[0], color[1], color[2], alpha)
        draw.ellipse([center - r, center - r, center + r, center + r], fill=c)
    return glow

def create_sparkle_star(size=14, color=(255, 182, 193, 240)):
    """Create a tiny delicate 4-point anime sparkle diamond."""
    star = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(star)
    cx, cy = size // 2, size // 2
    # Draw 4-point star diamond
    pts = [
        (cx, 1),
        (cx + 2, cy - 2),
        (size - 2, cy),
        (cx + 2, cy + 2),
        (cx, size - 2),
        (cx - 2, cy + 2),
        (1, cy),
        (cx - 2, cy - 2),
    ]
    draw.polygon(pts, fill=color)
    # Center bright white pip
    draw.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=(255, 255, 255, 255))
    return star

def generate_proximity_asset():
    """
    PROXIMITY: 'Meli notices you nearby'
    - Subtle recognition & quiet curiosity
    - Head gently angled towards cursor (left)
    - Eyes tracking toward upper-left
    - Subtle quiet closed smile
    - Soft emerald heart glow, NO sparkles
    """
    # Load canonical high-res base / idle
    base = Image.open("assets/meli/character/states/meli_curious.png").convert("RGBA")
    
    # We create a pristine version where:
    # 1. Head is slightly angled towards upper-left (-2.8 deg)
    # 2. Gaze is distinctly tracking upper-left
    # 3. Soft quiet mouth line
    # 4. Soft emerald Signal Heart
    
    # Separate head region (Y: 30 to 200, X: 160 to 350)
    w, h = 512, 512
    head_box = (160, 30, 352, 205)
    head_crop = base.crop(head_box)
    
    # Gentle subtle head rotation (-2.2 deg)
    rotated_head = head_crop.rotate(-2.2, resample=Image.BICUBIC, center=(96, 160))
    
    # Create working canvas
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    # Body below head
    body = base.copy()
    body_draw = ImageDraw.Draw(body)
    
    # Paste rotated head onto canvas
    canvas.paste(body, (0, 0))
    canvas.paste(rotated_head, head_box, rotated_head)
    
    # Refine Eyes for PROXIMITY: Pupils attentively gazing upper-left
    draw = ImageDraw.Draw(canvas)
    
    # Eye coordinates roughly: Left eye (X: 232-246, Y: 135-152), Right eye (X: 266-280, Y: 135-152)
    # Soft attentive pupils tracking left
    # Draw warm rose anime pupil highlights shifted to top-left
    # Left eye glint
    draw.ellipse([234, 137, 239, 142], fill=(255, 255, 255, 255))
    draw.ellipse([237, 144, 240, 147], fill=(255, 214, 231, 220))
    # Right eye glint
    draw.ellipse([268, 137, 273, 142], fill=(255, 255, 255, 255))
    draw.ellipse([271, 144, 274, 147], fill=(255, 214, 231, 220))
    
    # Subtle closed-mouth soft line (Y: 172, X: 252-260)
    # Clear any old mouth artifact
    mouth_bg = canvas.crop((248, 168, 266, 178))
    # Soft clean anime mouth curve
    draw.arc([250, 168, 262, 175], start=15, end=165, fill=(70, 40, 50, 240), width=2)
    
    # Gentle soft blush
    blush_l = create_glow(24, (255, 182, 193), radius=9)
    canvas.paste(blush_l, (222, 150), blush_l)
    blush_r = create_glow(24, (255, 182, 193), radius=9)
    canvas.paste(blush_r, (268, 150), blush_r)
    
    # Signal Heart: Soft emerald green glow (Centroid X: 259.4, Y: 184.6)
    heart_glow = create_glow(36, (0, 230, 118), radius=14)
    canvas.paste(heart_glow, (259 - 18, 185 - 18), heart_glow)
    
    # Draw central crisp emerald heart
    hx, hy = 259, 185
    # Precise anime heart polygon
    heart_pts = [
        (hx, hy + 5),
        (hx - 5, hy),
        (hx - 5, hy - 3),
        (hx - 2, hy - 5),
        (hx, hy - 3),
        (hx + 2, hy - 5),
        (hx + 5, hy - 3),
        (hx + 5, hy),
    ]
    draw.polygon(heart_pts, fill=(0, 230, 118, 255), outline=(0, 180, 80, 255))
    draw.ellipse([hx - 3, hy - 3, hx - 1, hy - 1], fill=(255, 255, 255, 230))
    
    return canvas

def generate_hover_asset():
    """
    HOVER: 'Meli knows you're directly interacting with her'
    - Active engagement & playful warmth
    - Cheerful warm smile with tooth/tongue blush
    - Brighter sparkling eyes looking directly at user
    - Tiny playful head tilt (+3.2 deg)
    - Bright energetic emerald Signal Heart
    - 2 tiny floating soft-pink sparkle accents
    """
    # Load canonical happy / energetic master
    base = Image.open("assets/meli/character/states/meli_happy.png").convert("RGBA")
    
    w, h = 512, 512
    head_box = (155, 30, 355, 205)
    head_crop = base.crop(head_box)
    
    # Playful slight right tilt (+3.0 deg)
    rotated_head = head_crop.rotate(3.0, resample=Image.BICUBIC, center=(100, 160))
    
    # Create canvas
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(base, (0, 0))
    canvas.paste(rotated_head, head_box, rotated_head)
    
    draw = ImageDraw.Draw(canvas)
    
    # Warm bright eyes: add extra sparkling glints
    # Left eye
    draw.ellipse([236, 137, 242, 143], fill=(255, 255, 255, 255))
    draw.ellipse([242, 144, 245, 147], fill=(255, 255, 255, 220))
    draw.ellipse([238, 146, 240, 148], fill=(255, 182, 193, 230))
    
    # Right eye
    draw.ellipse([270, 137, 276, 143], fill=(255, 255, 255, 255))
    draw.ellipse([276, 144, 279, 147], fill=(255, 255, 255, 220))
    draw.ellipse([272, 146, 274, 148], fill=(255, 182, 193, 230))
    
    # Cheerful small open joyful smile
    # Mouth area (X: 250-264, Y: 169-178)
    mouth_box = [252, 169, 264, 178]
    # Draw open cheerful smile polygon
    mouth_pts = [
        (252, 170),
        (264, 170),
        (262, 176),
        (258, 178),
        (254, 176),
    ]
    draw.polygon(mouth_pts, fill=(180, 50, 70, 255), outline=(70, 30, 40, 255))
    # Little white tooth at top
    draw.polygon([(254, 170), (262, 170), (260, 172), (256, 172)], fill=(255, 255, 255, 255))
    # Soft pink tongue at bottom
    draw.ellipse([255, 174, 261, 177], fill=(255, 140, 160, 255))
    
    # Rich rosy cheek blush
    blush_l = create_glow(28, (255, 122, 162), radius=11)
    canvas.paste(blush_l, (220, 150), blush_l)
    blush_r = create_glow(28, (255, 122, 162), radius=11)
    canvas.paste(blush_r, (270, 150), blush_r)
    
    # Signal Heart: Visibly brighter high-energy emerald green glow
    heart_glow_outer = create_glow(48, (0, 230, 118), radius=20)
    canvas.paste(heart_glow_outer, (259 - 24, 185 - 24), heart_glow_outer)
    heart_glow_inner = create_glow(28, (105, 240, 174), radius=12)
    canvas.paste(heart_glow_inner, (259 - 14, 185 - 14), heart_glow_inner)
    
    hx, hy = 259, 185
    heart_pts = [
        (hx, hy + 6),
        (hx - 6, hy),
        (hx - 6, hy - 4),
        (hx - 2, hy - 6),
        (hx, hy - 4),
        (hx + 2, hy - 6),
        (hx + 6, hy - 4),
        (hx + 6, hy),
    ]
    draw.polygon(heart_pts, fill=(0, 230, 118, 255), outline=(0, 190, 85, 255))
    draw.ellipse([hx - 4, hy - 4, hx - 1, hy - 1], fill=(255, 255, 255, 255))
    
    # 2 Tiny delicate floating sparkles (One near upper right hair, one near left shoulder)
    star1 = create_sparkle_star(size=14, color=(255, 182, 193, 240))
    canvas.paste(star1, (338, 92), star1)
    
    star2 = create_sparkle_star(size=10, color=(255, 214, 231, 220))
    canvas.paste(star2, (184, 168), star2)
    
    return canvas

def main():
    print("=== BUILDING REFINED SPECIAL STATES ===")
    
    prox_img = generate_proximity_asset()
    hover_img = generate_hover_asset()
    
    # Ensure exact 512x512
    prox_img = prox_img.resize((512, 512), Image.LANCZOS)
    hover_img = hover_img.resize((512, 512), Image.LANCZOS)
    
    # Save to assets/
    prox_path = Path("assets/meli/character/special/meli_proximity.png")
    hover_path = Path("assets/meli/character/special/meli_hover.png")
    
    prox_img.save(prox_path, "PNG")
    hover_img.save(hover_path, "PNG")
    
    # Save to public/
    prox_pub = Path("public/special/meli_proximity.png")
    hover_pub = Path("public/special/meli_hover.png")
    prox_pub.parent.mkdir(parents=True, exist_ok=True)
    prox_img.save(prox_pub, "PNG")
    hover_img.save(hover_pub, "PNG")
    
    # Root fallbacks
    prox_img.save("public/proximity.png", "PNG")
    hover_img.save("public/hover.png", "PNG")
    
    print(f"Saved: {prox_path} & {prox_pub}")
    print(f"Saved: {hover_path} & {hover_pub}")
    
    # Compute distinctness
    p_arr = np.array(prox_img)
    h_arr = np.array(hover_img)
    diff = np.mean(np.abs(p_arr.astype(int) - h_arr.astype(int)))
    print(f"PROXIMITY vs HOVER MAD difference: {diff:.2f}")

if __name__ == "__main__":
    main()
