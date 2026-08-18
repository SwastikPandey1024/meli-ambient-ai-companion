#!/usr/bin/env python3
"""
build_performance_assets.py — Performance Asset Extraction, Normalization & Master Sheet Assembly

Features:
1. High-precision background extraction and alpha-matting with anti-aliasing preservation
2. Canvas normalization to 512x512 RGBA with canonical grounding alignment (Y=495)
3. Assembly of transparent 4x3 Master Performance Sheet: design/meli_performance_master_sheet.png
4. Assembly of labeled 4x3 QA Review Sheet: design/qa/meli_performance_review.png
5. Special interaction keyframe generation (proximity, hover, click_pet)
"""

import sys
import os
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BRAIN_DIR = Path(r"C:\Users\Swastik Pandey\.gemini\antigravity-ide\brain\f281e1e9-b1a7-4798-ab18-31181b3a8292")
STATES_DIR = Path("assets/meli/character/states")
SPECIAL_DIR = Path("assets/meli/character/special")
DESIGN_DIR = Path("design")
QA_DIR = Path("design/qa")

BASE_IMG_PATH = Path("assets/meli/character/meli_body_base.png")

CORE_STATE_SOURCES = [
    ("meli_idle.png", BASE_IMG_PATH, "01. IDLE / OBSERVANT", "Calm almond gaze, relaxed neutral mouth, quiet natural presence"),
    ("meli_curious.png", BRAIN_DIR / "meli_curious_master_1786984560777.jpg", "02. CURIOUS", "Inquisitive bright gaze, raised brows, tiny curious smile, slight head tilt"),
    ("meli_happy.png", BRAIN_DIR / "meli_happy_master_1786983568021.jpg", "03. HAPPY", "Gentle smiling eyes, warm cheek blush, joyful micro-celebration posture"),
    ("meli_thinking.png", BRAIN_DIR / "meli_thinking_master_1786983846704.jpg", "04. THINKING", "Thoughtful lateral/upward gaze, hand near collar, analytical posture"),
    ("meli_working.png", BRAIN_DIR / "meli_working_master_1786984983224.jpg", "05. WORKING / BUSY", "Concentrated engaged state holding tech laptop, productive posture"),
    ("meli_focused.png", BRAIN_DIR / "meli_focused_master_1786985365918.jpg", "06. FOCUSED", "Narrowed determined gaze, upright concentrated posture, serious but calm"),
    ("meli_sleepy.png", BRAIN_DIR / "meli_sleepy_master_1786985743765.jpg", "07. SLEEPY", "Heavy drooping eyelids, relaxed soft shoulders, cozy resting stance"),
    ("meli_confused.png", BRAIN_DIR / "meli_confused_master_1786986068305.jpg", "08. CONFUSED", "Asymmetrical brows, head tilt, questioning gaze, hand raised quizzically"),
    ("meli_surprised.png", BRAIN_DIR / "meli_surprised_master_1786986671509.jpg", "09. SURPRISED", "Widened round pupils, raised brows, small 'o' mouth, subtle alert recoil"),
    ("meli_error.png", BRAIN_DIR / "meli_error_master_1786987121960.jpg", "10. ERROR / CONCERNED", "Worried brows, downward apologetic gaze, hands together, glowing amber Signal Heart"),
    ("meli_complete.png", BRAIN_DIR / "meli_complete_master_clean_1786987764010.jpg", "11. TASK COMPLETE", "Radiant joyful smile, proud victory celebration gesture, glowing emerald heart"),
    ("meli_greeting.png", BRAIN_DIR / "meli_greeting_master_1786987997190.jpg", "12. GREETING", "Welcoming eye contact, gentle hand wave, friendly approachable posture"),
]


def extract_clean_transparent(img_path: Path, output_path: Path, target_height_px=455, target_grounding_y=495):
    """
    Extracts foreground character from master image with clean boundary alpha matting.
    """
    if str(img_path).endswith(".png") and "meli_body_base.png" in str(img_path):
        img = Image.open(img_path).convert("RGBA")
        img.save(output_path, "PNG")
        print(f"  [OK] Copied canonical base to: {output_path}")
        return img

    img = Image.open(img_path).convert("RGB")
    arr = np.array(img).astype(float)
    h, w, _ = arr.shape
    
    # Distance to pure white (255, 255, 255)
    diff = np.sqrt(np.sum((arr - 255.0)**2, axis=2))
    
    # Flood-fill background mask from corners
    is_bg = np.zeros((h, w), dtype=bool)
    visited = np.zeros((h, w), dtype=bool)
    
    q = deque([(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)])
    for y, x in list(q):
        visited[y, x] = True
        
    while q:
        y, x = q.popleft()
        if diff[y, x] < 45.0:
            is_bg[y, x] = True
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                    visited[ny, nx] = True
                    if diff[ny, nx] < 45.0:
                        q.append((ny, nx))
                        
    # Alpha calculation
    alpha = np.zeros((h, w), dtype=np.uint8)
    alpha[~is_bg] = 255
    
    # Soften alpha transition along the boundary for clean subpixel anti-aliasing
    boundary = is_bg & (diff > 12.0)
    alpha[boundary] = np.clip((diff[boundary] - 12.0) / 25.0 * 255.0, 0, 255).astype(np.uint8)
    
    rgba = np.dstack([arr.astype(np.uint8), alpha])
    result_img = Image.fromarray(rgba, "RGBA")
    
    # Crop tightly to character bounds
    ys, xs = np.where(alpha > 15)
    min_y, max_y = ys.min(), ys.max()
    min_x, max_x = xs.min(), xs.max()
    
    cropped = result_img.crop((min_x, min_y, max_x + 1, max_y + 1))
    c_w, c_h = cropped.size
    
    # Scale to match standard Meli height
    scale = target_height_px / float(c_h)
    new_w = int(round(c_w * scale))
    new_h = int(round(c_h * scale))
    
    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Place on 512x512 canvas grounded at target_grounding_y
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    paste_x = (512 - new_w) // 2
    paste_y = target_grounding_y - new_h
    if paste_y < 8:
        paste_y = 8
        
    canvas.paste(resized, (paste_x, paste_y), resized)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG")
    print(f"  [OK] Processed {output_path.name:25} | Size: {canvas.size} | BBox: ({paste_x}, {paste_y}, {paste_x+new_w}, {paste_y+new_h})")
    return canvas


def assemble_master_performance_sheet(states_dir: Path, output_path: Path):
    """
    Creates design/meli_performance_master_sheet.png
    Layout: 4 columns x 3 rows = 12 complete standalone character performances
    Transparent background, no text, no labels, no borders.
    """
    cols = 4
    rows = 3
    cell_size = 512
    sheet_w = cols * cell_size
    sheet_h = rows * cell_size
    
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    
    for idx, (filename, _, _, _) in enumerate(CORE_STATE_SOURCES):
        r, c = divmod(idx, cols)
        x = c * cell_size
        y = r * cell_size
        
        p = states_dir / filename
        if p.exists():
            char_img = Image.open(p).convert("RGBA")
            sheet.paste(char_img, (x, y), char_img)
            
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, "PNG")
    print(f"[OK] Assembled Master Performance Sheet: {output_path} ({sheet_w}x{sheet_h} RGBA)")


def assemble_qa_review_sheet(states_dir: Path, output_path: Path):
    """
    Creates design/qa/meli_performance_review.png
    4 columns x 3 rows with dark theme, checkerboard alpha previews, and state labels.
    """
    cols = 4
    rows = 3
    card_w = 400
    card_h = 490
    pad = 20
    header_h = 100
    
    total_w = pad + cols * (card_w + pad)
    total_h = header_h + rows * (card_h + pad) + pad
    
    sheet = Image.new("RGBA", (total_w, total_h), (16, 14, 24, 255))
    draw = ImageDraw.Draw(sheet)
    
    # Master Header
    draw.text((pad, 20), "MELI — PERFORMANCE MASTER ARTWORK REVIEW BOARD (12 COMPLETE STATES)", fill=(255, 110, 160, 255))
    draw.text((pad, 48), "Authoritative Character Reference: design/meli_canonical_character_sheet.png", fill=(210, 200, 230, 255))
    draw.text((pad, 68), "Standalone Character Performances | No Expression Overlays | Identity & Silhouette Locked", fill=(160, 150, 180, 255))
    
    for idx, (filename, _, title, desc) in enumerate(CORE_STATE_SOURCES):
        r, c = divmod(idx, cols)
        x = pad + c * (card_w + pad)
        y = header_h + r * (card_h + pad)
        
        # Card body
        draw.rectangle([x, y, x + card_w, y + card_h], fill=(24, 22, 34, 255), outline=(50, 44, 70, 255), width=2)
        
        # Card header banner
        draw.rectangle([x, y, x + card_w, y + 36], fill=(34, 30, 48, 255))
        draw.text((x + 12, y + 10), title, fill=(255, 215, 230, 255))
        
        # Checkerboard box
        box_pad = 12
        box_x = x + box_pad
        box_y = y + 44
        box_w = card_w - 2 * box_pad
        box_h = 360
        
        checker = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        for cy in range(0, box_h, 16):
            for cx in range(0, box_w, 16):
                col = (44, 40, 56, 255) if ((cx // 16 + cy // 16) % 2 == 0) else (34, 30, 46, 255)
                checker.paste(col, (cx, cy, min(cx + 16, box_w), min(cy + 16, box_h)))
                
        p = states_dir / filename
        if p.exists():
            char_img = Image.open(p).convert("RGBA")
            # Fit inside box
            scale = min(box_w / float(char_img.size[0]), box_h / float(char_img.size[1]))
            nw = int(char_img.size[0] * scale)
            nh = int(char_img.size[1] * scale)
            resized = char_img.resize((nw, nh), Image.Resampling.LANCZOS)
            px = (box_w - nw) // 2
            py = (box_h - nh) // 2
            checker.paste(resized, (px, py), resized)
            
        sheet.paste(checker, (box_x, box_y))
        draw.rectangle([box_x - 1, box_y - 1, box_x + box_w, box_y + box_h], outline=(80, 70, 100, 255), width=1)
        
        # Description
        desc_y = box_y + box_h + 10
        draw.text((x + 12, desc_y), desc, fill=(170, 160, 190, 255))
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, "PNG")
    print(f"[OK] Assembled QA Review Sheet: {output_path} ({total_w}x{total_h} RGBA)")


def process_special_states(states_dir: Path, special_dir: Path):
    """
    Generates standalone assets for special interaction keyframes.
    """
    special_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Proximity: attentive leaning/interested state
    prox_src = states_dir / "meli_curious.png"
    if prox_src.exists():
        img = Image.open(prox_src)
        img.save(special_dir / "meli_proximity.png")
        print("  [OK] Saved special state: meli_proximity.png")
        
    # 2. Hover: responsive focused engagement
    hover_src = states_dir / "meli_curious.png"
    if hover_src.exists():
        img = Image.open(hover_src)
        img.save(special_dir / "meli_hover.png")
        print("  [OK] Saved special state: meli_hover.png")
        
    # 3. Click / Pet: joyful celebratory reaction
    pet_src = states_dir / "meli_happy.png"
    if pet_src.exists():
        img = Image.open(pet_src)
        img.save(special_dir / "meli_click_pet.png")
        print("  [OK] Saved special state: meli_click_pet.png")


def main():
    print("==================================================")
    print("MELI PERFORMANCE ASSET BUILDER & MASTER ASSEMBLER")
    print("==================================================")
    
    # Base sprite baseline metrics
    base_img = Image.open(BASE_IMG_PATH).convert("RGBA")
    base_arr = np.array(base_img)
    base_alpha = base_arr[:, :, 3]
    bys, _ = np.where(base_alpha > 15)
    base_h = bys.max() - bys.min()
    base_ground_y = bys.max()
    print(f"Canonical Base Baseline: height={base_h}px, grounding baseline Y={base_ground_y}")
    
    print("\n[Step 1] Extracting & Normalizing 12 Performance States...")
    for filename, src_path, _, _ in CORE_STATE_SOURCES:
        dest = STATES_DIR / filename
        extract_clean_transparent(src_path, dest, target_height_px=base_h, target_grounding_y=base_ground_y)
        
    print("\n[Step 2] Processing Special Interaction States...")
    process_special_states(STATES_DIR, SPECIAL_DIR)
    
    print("\n[Step 3] Assembling Master Performance Sheet (4x3 Transparent)...")
    assemble_master_performance_sheet(STATES_DIR, DESIGN_DIR / "meli_performance_master_sheet.png")
    
    print("\n[Step 4] Assembling QA Review Sheet (4x3 Labeled Board)...")
    assemble_qa_review_sheet(STATES_DIR, QA_DIR / "meli_performance_review.png")
    
    print("\n[COMPLETE] All performance assets and master sheets built.")


if __name__ == "__main__":
    main()
