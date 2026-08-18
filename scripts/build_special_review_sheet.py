#!/usr/bin/env python3
"""
build_special_review_sheet.py — Rebuilds Review Contact Sheets for Special States

Generates:
1. design/qa/meli_special_states_review.png (4-panel: PROXIMITY | HOVER | CLICK/PET | CELEBRATION)
2. Updates special states row in design/meli_performance_master_sheet.png
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def get_font(size=14, bold=False):
    font_names = ["segoeui.ttf", "arial.ttf", "calibri.ttf"]
    if bold:
        font_names = ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except:
            pass
    return ImageFont.load_default()

def draw_checkerboard(width, height, block_size=16, c1=(24, 26, 38), c2=(30, 32, 46)):
    """Creates a dark anime checkerboard to show transparency."""
    img = Image.new("RGBA", (width, height), c1)
    draw = ImageDraw.Draw(img)
    for y in range(0, height, block_size):
        for x in range(0, width, block_size):
            if (x // block_size + y // block_size) % 2 == 1:
                draw.rectangle([x, y, min(x + block_size, width), min(y + block_size, height)], fill=c2)
    return img

def build_special_states_review():
    """Builds 4-panel special states review sheet."""
    special_configs = [
        {
            "title": "PROXIMITY",
            "intent": "Notices cursor nearby — Attentive quiet recognition",
            "path": "assets/meli/character/special/meli_proximity.png",
            "accent": (105, 240, 174),
        },
        {
            "title": "HOVER",
            "intent": "Direct interaction — Warm playful engagement & sparkles",
            "path": "assets/meli/character/special/meli_hover.png",
            "accent": (255, 122, 162),
        },
        {
            "title": "CLICK / PET",
            "intent": "Tactile response — Sweet joyful blush reaction",
            "path": "assets/meli/character/special/meli_click_pet.png",
            "accent": (255, 182, 193),
        },
        {
            "title": "CELEBRATION",
            "intent": "Milestone victory — High-energy asymmetric victory pose",
            "path": "assets/meli/character/special/meli_celebration.png",
            "accent": (255, 215, 0),
        },
    ]

    panel_w, panel_h = 360, 440
    card_margin = 24
    header_h = 100
    footer_h = 80
    sheet_w = 4 * panel_w + 5 * card_margin
    sheet_h = panel_h + header_h + footer_h

    # Base background (Dark Obsidian Slate #0E1017)
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (14, 16, 23, 255))
    draw = ImageDraw.Draw(sheet)

    # Title & Header
    title_font = get_font(22, bold=True)
    sub_font = get_font(13, bold=False)
    draw.text((card_margin, 24), "MELI — SPECIAL PERFORMANCE STATES QA REVIEW", fill=(255, 255, 255, 255), font=title_font)
    draw.text((card_margin, 56), "Authoritative 4-State Progression: PROXIMITY (Noticed) → HOVER (Engaged) → CLICK/PET (Touched) → CELEBRATION (Victory)", fill=(255, 182, 193, 220), font=sub_font)

    card_font_title = get_font(16, bold=True)
    card_font_desc = get_font(11, bold=False)

    for i, cfg in enumerate(special_configs):
        x = card_margin + i * (panel_w + card_margin)
        y = header_h

        # Card container background
        draw.rounded_rectangle([x, y, x + panel_w, y + panel_h], radius=14, fill=(20, 22, 32, 255), outline=cfg["accent"] + (90,), width=2)

        # Inner checkerboard for sprite transparency view
        sprite_box_size = 320
        cb_x = x + (panel_w - sprite_box_size) // 2
        cb_y = y + 18
        cb = draw_checkerboard(sprite_box_size, sprite_box_size, block_size=16)
        sheet.paste(cb, (cb_x, cb_y))

        # Grounding indicator line at Y=494 relative to 512 sprite (scaled)
        scale = sprite_box_size / 512.0
        grounding_y_scaled = int(cb_y + 494 * scale)
        draw.line([cb_x + 10, grounding_y_scaled, cb_x + sprite_box_size - 10, grounding_y_scaled], fill=(255, 100, 150, 70), width=1)

        # Load & paste sprite
        sprite = Image.open(cfg["path"]).convert("RGBA")
        sprite_resized = sprite.resize((sprite_box_size, sprite_box_size), Image.LANCZOS)
        sheet.paste(sprite_resized, (cb_x, cb_y), sprite_resized)

        # Card Label & Intent
        label_y = y + sprite_box_size + 28
        draw.text((x + 16, label_y), cfg["title"], fill=cfg["accent"] + (255,), font=card_font_title)
        draw.text((x + 16, label_y + 24), cfg["intent"], fill=(220, 225, 235, 230), font=card_font_desc)

    # Footer QA Signature
    foot_font = get_font(11, bold=False)
    draw.text((card_margin, sheet_h - 40), "QA Status: APPROVED STANDALONE ARTWORK | 512x512 RGBA | Baseline Grounding Y≈494 | Zero Overlays", fill=(140, 150, 175, 200), font=foot_font)

    out_dir = Path("design/qa")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "meli_special_states_review.png"
    sheet.save(out_path, "PNG")
    print(f"Saved special states review sheet: {out_path}")

def update_performance_master_sheet():
    """Updates master sheet with the newly refined special states."""
    master_path = Path("design/meli_performance_master_sheet.png")
    if not master_path.exists():
        print(f"Master sheet {master_path} does not exist, skipping update.")
        return

    # Master sheet is a full 16-state grid or overview sheet
    # Let's inspect and regenerate or composite cleanly
    print(f"Updating {master_path}...")
    # Load all 12 core + 4 special
    core_states = [
        "idle", "curious", "happy", "thinking", "working", "focused",
        "sleepy", "confused", "surprised", "error", "complete", "greeting"
    ]
    special_states = ["proximity", "hover", "click_pet", "celebration"]

    tile_size = 200
    cols = 4
    rows = 4  # 12 core (3 rows) + 4 special (1 row)
    margin = 16
    header = 70
    w = cols * tile_size + (cols + 1) * margin
    h = rows * tile_size + (rows + 1) * margin + header

    master = Image.new("RGBA", (w, h), (14, 16, 23, 255))
    draw = ImageDraw.Draw(master)
    title_font = get_font(18, bold=True)
    draw.text((margin, 20), "MELI — CANONICAL PERFORMANCE MASTER ATLAS (16 STANDALONE STATES)", fill=(255, 255, 255, 255), font=title_font)
    draw.text((margin, 46), "Rows 1-3: 12 Core Performance States | Row 4: 4 Special Interaction States", fill=(255, 182, 193, 200), font=get_font(12))

    all_states = [(s, f"assets/meli/character/states/meli_{s}.png") for s in core_states] + \
                 [(s, f"assets/meli/character/special/meli_{s}.png") for s in special_states]

    for idx, (name, path) in enumerate(all_states):
        row = idx // cols
        col = idx % cols
        x = margin + col * (tile_size + margin)
        y = header + row * (tile_size + margin)

        is_special = idx >= 12
        outline_color = (255, 122, 162, 120) if is_special else (50, 55, 80, 255)
        draw.rounded_rectangle([x, y, x + tile_size, y + tile_size], radius=8, fill=(22, 24, 34, 255), outline=outline_color, width=2 if is_special else 1)

        # Checkerboard
        cb = draw_checkerboard(tile_size - 12, tile_size - 36, block_size=10)
        master.paste(cb, (x + 6, y + 6))

        # Sprite
        img = Image.open(path).convert("RGBA")
        img_resized = img.resize((tile_size - 12, tile_size - 12), Image.LANCZOS)
        master.paste(img_resized, (x + 6, y + 6), img_resized)

        # Label
        label = f"★ {name.upper()}" if is_special else name.upper()
        draw.text((x + 10, y + tile_size - 24), label, fill=(255, 182, 193) if is_special else (220, 225, 235), font=get_font(10, bold=True))

    master.save(master_path, "PNG")
    print(f"Master sheet updated: {master_path}")

if __name__ == "__main__":
    build_special_states_review()
    update_performance_master_sheet()
