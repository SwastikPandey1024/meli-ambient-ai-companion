#!/usr/bin/env python3
"""
generate_master_expressions.py - High-Resolution 2048x2048 Master Expression Pipeline for Meli

Generates:
1. Master 2048x2048 RGBA Lossless PNGs in assets/meli/master/
   - meli_body_base_master.png
   - meli_expr_idle_master.png
   - meli_expr_curious_master.png
   - meli_expr_hover_master.png
   - meli_expr_happy_master.png
   - meli_expr_blink_master.png
   - meli_expr_sleepy_master.png
   - meli_expr_thinking_master.png
   - meli_expr_focused_master.png
   - meli_expr_confused_master.png
   - meli_expr_error_master.png
   - meli_expr_complete_master.png
   - meli_expr_greeting_master.png

2. High-Quality Lanczos Downsampled 512x512 Runtime PNGs in assets/meli/character/ and dist/

3. Composite High-Resolution Contact Sheet in assets/meli/sheets/meli_expression_contact_sheet.png
"""

import math
import os
import shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MASTER_DIR = Path("assets/meli/master")
RUNTIME_DIR = Path("assets/meli/character")
DIST_DIR = Path("dist")
SHEETS_DIR = Path("assets/meli/sheets")
QA_DIR = Path("assets/meli/qa")

BASE_512_PATH = Path("assets/meli/character/meli_body_base.png")

# Palette Constants
SKIN_BASE = (249, 197, 190, 255)
SKIN_SHADOW = (242, 185, 178, 255)
OUTLINE_DARK = (45, 38, 50, 255)
BROW_DARK = (68, 52, 62, 255)
EYE_DARK_TOP = (38, 30, 44, 255)
EYE_MID_IRIS = (95, 48, 70, 255)
EYE_LIGHT_IRIS = (185, 95, 125, 255)
EYE_PUPIL = (24, 18, 28, 255)
WHITE = (255, 255, 255, 255)
MOUTH_INTERIOR_RED = (210, 80, 105, 255)
MOUTH_DARK = (52, 40, 52, 255)
BLUSH_PINK = (255, 115, 155, 130)
BLUSH_STROKE = (255, 122, 162, 220)
SPARKLE_GOLD = (255, 224, 130, 255)
SWEAT_CYAN = (112, 214, 255, 240)


def create_master_base():
    """Upscales 512 base sprite to 2048 master using high-quality Lanczos and cleans inner face canvas."""
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    img_512 = Image.open(BASE_512_PATH).convert("RGBA")
    master_base = img_512.resize((2048, 2048), resample=Image.Resampling.LANCZOS)
    
    # Save base master
    master_base_path = MASTER_DIR / "meli_body_base_master.png"
    master_base.save(master_base_path, format="PNG")
    print(f"  -> Generated {master_base_path} (2048x2048 RGBA)")
    return master_base


def get_clean_face_master(master_base):
    """
    Creates a base canvas where the inner facial features (eyes/mouth/brows)
    are smoothly restored to clean base skin tone while leaving hair bangs,
    ears, chin contour, hoodie, and body completely 100% intact.
    """
    canvas = master_base.copy()
    
    # Face skin patch in 2048 coordinates
    mask = Image.new("L", (2048, 2048), 0)
    draw_mask = ImageDraw.Draw(mask)
    
    # Draw soft polygon covering inner face region (between bangs and chin)
    face_poly = [
        (852, 620), (912, 590), (1024, 585), (1136, 590), (1196, 620),
        (1208, 715), (1180, 785), (1120, 830), (1024, 845), (928, 830),
        (868, 785), (844, 715)
    ]
    draw_mask.polygon(face_poly, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=6))
    
    # Smooth skin color image
    skin_fill = Image.new("RGBA", (2048, 2048), SKIN_BASE)
    draw_skin = ImageDraw.Draw(skin_fill)
    for y in range(580, 850):
        alpha_t = (y - 580) / 270.0
        r = int(249 - alpha_t * 5)
        g = int(197 - alpha_t * 10)
        b = int(190 - alpha_t * 10)
        draw_skin.line([(800, y), (1250, y)], fill=(r, g, b, 255), width=1)
        
    canvas.paste(skin_fill, (0, 0), mask)
    return canvas


def lock_body_pixels(edited_master, master_base):
    """
    Guarantees 100.0% bit-exact identicality for every pixel outside the face box.
    Face Box in 2048: Y: 520..880, X: 800..1248 (corresponds to Y: 130..220, X: 200..312 in 512).
    """
    result = master_base.copy()
    face_crop = edited_master.crop((800, 520, 1248, 880))
    result.paste(face_crop, (800, 520))
    return result


def draw_bezier_curve(draw, p0, p1, p2, fill, width=4):
    """Draws a smooth quadratic Bezier curve with specified line width."""
    steps = 60
    prev_pt = p0
    for s in range(1, steps + 1):
        t = s / float(steps)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        draw.line([prev_pt, (x, y)], fill=fill, width=width)
        prev_pt = (x, y)


def draw_cubic_curve(draw, p0, p1, p2, p3, fill, width=4):
    """Draws a smooth cubic Bezier curve with specified line width."""
    steps = 80
    prev_pt = p0
    for s in range(1, steps + 1):
        t = s / float(steps)
        x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
        draw.line([prev_pt, (x, y)], fill=fill, width=width)
        prev_pt = (x, y)


def draw_eyebrow(draw, start, ctrl, end, width=8, fill=BROW_DARK):
    """Draws a dynamic tapered anime eyebrow."""
    draw_bezier_curve(draw, start, ctrl, end, fill=fill, width=width)


def draw_open_anime_eye(canvas, cx, cy, gaze_dx=0, gaze_dy=0, pupil_scale=1.0, droop=0.0, highlight_extra=False, eye_style="normal"):
    """
    Renders an artist-grade anime eye at (cx, cy) with iris gradient, pupil, speculars, and eyelashes.
    """
    rx, ry = 30, 36
    eye_img = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(eye_img)
    
    # Sclera (eye white)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(255, 252, 252, 255))
    
    # Iris bounds (clipped inside sclera)
    iris_rx, iris_ry = int(24 * pupil_scale), int(30 * pupil_scale)
    iris_cx = cx + int(gaze_dx * 14)
    iris_cy = cy + int(gaze_dy * 10) + int(droop * 8)
    
    # Draw iris with multi-layer vertical gradient
    for y_off in range(-iris_ry, iris_ry + 1):
        norm_y = (y_off + iris_ry) / (2.0 * iris_ry)
        width_at_y = int(iris_rx * math.sqrt(max(0.0, 1.0 - (y_off / float(iris_ry)) ** 2)))
        if norm_y < 0.35:
            col = EYE_DARK_TOP
        elif norm_y < 0.70:
            col = EYE_MID_IRIS
        else:
            col = EYE_LIGHT_IRIS
        draw.line([(iris_cx - width_at_y, iris_cy + y_off), (iris_cx + width_at_y, iris_cy + y_off)], fill=col, width=1)
        
    # Pupil (dark center circle)
    pupil_r = int(11 * pupil_scale)
    draw.ellipse([iris_cx - pupil_r, iris_cy - pupil_r, iris_cx + pupil_r, iris_cy + pupil_r], fill=EYE_PUPIL)
    
    # Primary Specular Highlight (Crisp White circle upper-left)
    sp1_x = iris_cx - 9
    sp1_y = iris_cy - 11
    draw.ellipse([sp1_x - 7, sp1_y - 7, sp1_x + 7, sp1_y + 7], fill=WHITE)
    
    # Secondary Specular Highlight (Smaller soft white circle lower-right)
    sp2_x = iris_cx + 8
    sp2_y = iris_cy + 9
    draw.ellipse([sp2_x - 4, sp2_y - 4, sp2_x + 4, sp2_y + 4], fill=(255, 255, 255, 220))
    
    if highlight_extra:
        # Star or extra specular for complete/greeting/curious
        sp3_x = iris_cx - 6
        sp3_y = iris_cy + 11
        draw.ellipse([sp3_x - 3, sp3_y - 3, sp3_x + 3, sp3_y + 3], fill=WHITE)
        sp4_x = iris_cx + 10
        sp4_y = iris_cy - 8
        draw.ellipse([sp4_x - 3, sp4_y - 3, sp4_x + 3, sp4_y + 3], fill=WHITE)
    
    # If droop > 0 (sleepy / focused), mask upper part with skin eyelid
    if droop > 0.1:
        lid_y = cy - ry + int(droop * (2 * ry))
        draw.rectangle([cx - rx - 8, cy - ry - 8, cx + rx + 8, lid_y], fill=SKIN_BASE)
        # Eyelid crease line
        draw.line([(cx - rx - 4, lid_y), (cx + rx + 4, lid_y)], fill=OUTLINE_DARK, width=8)
    else:
        # Upper Eyelash Arc (Thick anime lash line)
        draw_bezier_curve(draw, (cx - rx - 8, cy - ry + 12), (cx, cy - ry - 6), (cx + rx + 8, cy - ry + 10), fill=OUTLINE_DARK, width=10)
        # Outer lash wing
        draw.line([(cx + rx + 6, cy - ry + 10), (cx + rx + 18, cy - ry + 2)], fill=OUTLINE_DARK, width=7)
        
    # Lower Eyelid line
    draw_bezier_curve(draw, (cx - rx + 4, cy + ry - 2), (cx, cy + ry + 4), (cx + rx - 4, cy + ry - 2), fill=OUTLINE_DARK, width=5)
    
    # Composite eye onto canvas
    canvas.paste(eye_img, (0, 0), eye_img)


def draw_closed_smiling_eye(canvas, cx, cy, width_scale=1.0):
    """Renders bold cheerful crescent smiling eyes (^_^) in 2048 master."""
    rx = int(36 * width_scale)
    eye_img = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(eye_img)
    
    # Crescent smiling curve
    draw_bezier_curve(draw, (cx - rx, cy + 14), (cx, cy - 22), (cx + rx, cy + 14), fill=OUTLINE_DARK, width=12)
    # Outer double lash tick
    draw.line([(cx + rx - 2, cy + 12), (cx + rx + 14, cy + 4)], fill=OUTLINE_DARK, width=7)
    draw.line([(cx + rx - 2, cy + 12), (cx + rx + 10, cy + 20)], fill=OUTLINE_DARK, width=6)
    
    canvas.paste(eye_img, (0, 0), eye_img)


def draw_blink_eye(canvas, cx, cy):
    """Renders gentle closed eyelid line with relaxed lash."""
    rx = 32
    eye_img = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(eye_img)
    
    # Soft downward resting curve
    draw_bezier_curve(draw, (cx - rx, cy + 4), (cx, cy + 14), (cx + rx, cy + 4), fill=OUTLINE_DARK, width=10)
    draw.line([(cx + rx, cy + 4), (cx + rx + 10, cy + 10)], fill=OUTLINE_DARK, width=6)
    
    # Eyelid crease above
    draw_bezier_curve(draw, (cx - rx + 4, cy - 14), (cx, cy - 20), (cx + rx - 4, cy - 14), fill=(165, 120, 130, 240), width=4)
    
    canvas.paste(eye_img, (0, 0), eye_img)


def draw_cheek_blush(canvas, cx, cy, radius_x=38, radius_y=24, alpha=0.55, with_lines=True):
    """Draws multi-layer soft Gaussian blush with optional anime hatching lines."""
    blush_img = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(blush_img)
    
    r_val = int(255 * alpha)
    draw.ellipse([cx - radius_x, cy - radius_y, cx + radius_x, cy + radius_y], fill=(255, 100, 145, r_val))
    blush_img = blush_img.filter(ImageFilter.GaussianBlur(radius=12))
    
    if with_lines:
        line_draw = ImageDraw.Draw(blush_img)
        for offset in (-14, 0, 14):
            line_draw.line([(cx + offset - 10, cy + 14), (cx + offset + 10, cy - 14)], fill=(255, 80, 130, 220), width=4)
            
    canvas.paste(blush_img, (0, 0), blush_img)


def draw_sparkle_star(canvas, cx, cy, size=28):
    """Draws a bright 4-point golden anime sparkle star."""
    star_img = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(star_img)
    
    pts = [
        (cx, cy - size), (cx + size * 0.25, cy - size * 0.25),
        (cx + size, cy), (cx + size * 0.25, cy + size * 0.25),
        (cx, cy + size), (cx - size * 0.25, cy + size * 0.25),
        (cx - size, cy), (cx - size * 0.25, cy - size * 0.25)
    ]
    draw.polygon(pts, fill=SPARKLE_GOLD)
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=WHITE)
    
    canvas.paste(star_img, (0, 0), star_img)


def draw_sweat_drop(canvas, cx, cy, size=26):
    """Draws a crystal clear cyan sweat drop for error/nervous emote."""
    drop_img = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(drop_img)
    
    draw.ellipse([cx - size // 2, cy, cx + size // 2, cy + size], fill=SWEAT_CYAN)
    draw.polygon([(cx, cy - size * 0.85), (cx - size // 2 + 1, cy + size // 2), (cx + size // 2 - 1, cy + size // 2)], fill=SWEAT_CYAN)
    draw.ellipse([cx - size // 4, cy + size // 4, cx, cy + size // 2], fill=WHITE)
    
    canvas.paste(drop_img, (0, 0), drop_img)


# ==============================================================================
# 12 DISTINCT MASTER EXPRESSION RENDERERS
# ==============================================================================

def render_01_idle(clean_face):
    """01 IDLE - Calm, observant, ambient presence."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: relaxed almond shape, calm direct gaze
    draw_open_anime_eye(c, 912, 664, gaze_dx=0.0, gaze_dy=0.0, pupil_scale=1.0)
    draw_open_anime_eye(c, 1136, 664, gaze_dx=0.0, gaze_dy=0.0, pupil_scale=1.0)
    
    # Eyebrows: soft, relaxed natural horizontal curves
    draw_eyebrow(draw, (864, 608), (912, 598), (960, 610), width=7)
    draw_eyebrow(draw, (1088, 610), (1136, 598), (1184, 608), width=7)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: gentle, relaxed neutral closed mouth curve
    draw_bezier_curve(draw, (1004, 786), (1024, 792), (1044, 786), fill=MOUTH_DARK, width=6)
    return c


def render_02_curious(clean_face):
    """02 CURIOUS - Enlarged pupils, raised brow, gaze shifted, tiny soft 'o'."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: enlarged pupils with bright highlight, gaze shifted up-left
    draw_open_anime_eye(c, 912, 658, gaze_dx=-0.6, gaze_dy=-0.5, pupil_scale=1.24, highlight_extra=True)
    draw_open_anime_eye(c, 1136, 658, gaze_dx=-0.6, gaze_dy=-0.5, pupil_scale=1.24, highlight_extra=True)
    
    # Eyebrows: Left brow arched high in intrigue, Right brow raised
    draw_eyebrow(draw, (860, 574), (912, 546), (964, 576), width=8)
    draw_eyebrow(draw, (1088, 594), (1136, 578), (1184, 596), width=7)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: distinct soft open "o" oval mouth
    draw.ellipse([1008, 774, 1040, 808], fill=MOUTH_INTERIOR_RED, outline=MOUTH_DARK, width=5)
    
    # Golden curiosity sparkle star near right temple
    draw_sparkle_star(c, 1200, 620, size=26)
    return c


def render_03_hover(clean_face):
    """03 HOVER - Attentive upward-right gaze following pointer, alert brows, cute smile."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: attentive upward-right gaze tracking cursor
    draw_open_anime_eye(c, 912, 656, gaze_dx=0.65, gaze_dy=-0.55, pupil_scale=1.12, highlight_extra=True)
    draw_open_anime_eye(c, 1136, 656, gaze_dx=0.65, gaze_dy=-0.55, pupil_scale=1.12, highlight_extra=True)
    
    # Eyebrows: alert raised brows with left brow slightly higher
    draw_eyebrow(draw, (862, 584), (912, 566), (962, 586), width=7)
    draw_eyebrow(draw, (1088, 594), (1136, 580), (1184, 594), width=7)
    
    # Soft warm cheek blush
    draw_cheek_blush(c, 860, 720, radius_x=32, radius_y=18, alpha=0.45, with_lines=False)
    draw_cheek_blush(c, 1188, 720, radius_x=32, radius_y=18, alpha=0.45, with_lines=False)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: cute soft cat-like / subtle smirk upward curve
    draw_cubic_curve(draw, (1002, 786), (1014, 796), (1024, 788), (1034, 796), fill=MOUTH_DARK, width=5)
    draw_bezier_curve(draw, (1034, 796), (1044, 794), (1052, 784), fill=MOUTH_DARK, width=5)
    return c


def render_04_happy(clean_face):
    """04 HAPPY - Crescent smiling eyes (^ ^), wide joyful curved smile, rosy blush."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: bold curved crescent smiling arcs (^ ^)
    draw_closed_smiling_eye(c, 912, 664, width_scale=1.15)
    draw_closed_smiling_eye(c, 1136, 664, width_scale=1.15)
    
    # Eyebrows: relaxed happy curved brows
    draw_eyebrow(draw, (864, 590), (912, 574), (960, 590), width=8)
    draw_eyebrow(draw, (1088, 590), (1136, 574), (1184, 590), width=8)
    
    # Cheeks: bright rosy blush circles with diagonal hatching lines
    draw_cheek_blush(c, 856, 715, radius_x=38, radius_y=24, alpha=0.65, with_lines=True)
    draw_cheek_blush(c, 1192, 715, radius_x=38, radius_y=24, alpha=0.65, with_lines=True)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: wide cheerful curved open smile with tooth highlight
    mouth_poly = [(990, 778), (1024, 820), (1058, 778)]
    draw.polygon(mouth_poly, fill=MOUTH_INTERIOR_RED)
    draw_bezier_curve(draw, (988, 778), (1024, 822), (1060, 778), fill=MOUTH_DARK, width=6)
    draw.line([(986, 778), (1062, 778)], fill=MOUTH_DARK, width=7)
    draw.rectangle([1010, 779, 1038, 788], fill=WHITE)
    return c


def render_05_blink(clean_face):
    """05 BLINK - Natural closed eyelids, relaxed calm brows, neutral mouth."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: gently closed, downward curved resting lash line
    draw_blink_eye(c, 912, 666)
    draw_blink_eye(c, 1136, 666)
    
    # Eyebrows: relaxed neutral
    draw_eyebrow(draw, (864, 608), (912, 598), (960, 610), width=7)
    draw_eyebrow(draw, (1088, 610), (1136, 598), (1184, 608), width=7)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: neutral closed line
    draw_bezier_curve(draw, (1004, 786), (1024, 792), (1044, 786), fill=MOUTH_DARK, width=6)
    return c


def render_06_sleepy(clean_face):
    """06 SLEEPY - Heavy half-closed droopy eyelids, relaxed low brows, soft blush."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: heavy half-closed droopy eyelids covering top 65% of pupils
    draw_open_anime_eye(c, 912, 670, gaze_dx=0.0, gaze_dy=0.5, pupil_scale=0.92, droop=0.62)
    draw_open_anime_eye(c, 1136, 670, gaze_dx=0.0, gaze_dy=0.5, pupil_scale=0.92, droop=0.62)
    
    # Eyebrows: soft, droopy, relaxed low-set brows
    draw_eyebrow(draw, (864, 622), (912, 616), (960, 628), width=7)
    draw_eyebrow(draw, (1088, 628), (1136, 616), (1184, 622), width=7)
    
    # Soft warm cozy blush
    draw_cheek_blush(c, 860, 722, radius_x=32, radius_y=18, alpha=0.45, with_lines=False)
    draw_cheek_blush(c, 1188, 722, radius_x=32, radius_y=18, alpha=0.45, with_lines=False)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: small relaxed open mouth
    draw.ellipse([1012, 784, 1036, 802], fill=MOUTH_INTERIOR_RED, outline=MOUTH_DARK, width=4)
    return c


def render_07_thinking(clean_face):
    """07 THINKING - Gaze looking up and to the right, analytical angled brows, concentrated mouth."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: pupils shifted visibly upward and to top-right
    draw_open_anime_eye(c, 912, 658, gaze_dx=0.75, gaze_dy=-0.7, pupil_scale=1.04)
    draw_open_anime_eye(c, 1136, 658, gaze_dx=0.75, gaze_dy=-0.7, pupil_scale=1.04)
    
    # Eyebrows: analytical angle (left brow slightly higher, right brow angled inward)
    draw_eyebrow(draw, (862, 590), (912, 572), (962, 594), width=8)
    draw_eyebrow(draw, (1086, 608), (1136, 590), (1186, 596), width=8)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: small concentrated straight / pursed line
    draw.line([(1006, 786), (1042, 786)], fill=MOUTH_DARK, width=6)
    return c


def render_08_focused(clean_face):
    """08 FOCUSED - Narrowed calm eyes, concentrated lower straight brows, small straight mouth."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: narrowed calm focused slit eyes with top eyelid lowered
    draw_open_anime_eye(c, 912, 664, gaze_dx=0.0, gaze_dy=0.0, pupil_scale=0.94, droop=0.42)
    draw_open_anime_eye(c, 1136, 664, gaze_dx=0.0, gaze_dy=0.0, pupil_scale=0.94, droop=0.42)
    
    # Eyebrows: firmly set lower concentration straight brows
    draw_eyebrow(draw, (864, 606), (912, 614), (960, 598), width=9)
    draw_eyebrow(draw, (1088, 598), (1136, 614), (1184, 606), width=9)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: small confident straight / taut line
    draw.line([(1004, 786), (1044, 786)], fill=MOUTH_DARK, width=6)
    return c


def render_09_confused(clean_face):
    """09 CONFUSED - Asymmetric brows (one high, one low), questioning asymmetric mouth."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: asymmetric (Left eye wide open, Right eye slightly squinted)
    draw_open_anime_eye(c, 912, 656, gaze_dx=-0.3, gaze_dy=-0.3, pupil_scale=1.18, highlight_extra=True)
    draw_open_anime_eye(c, 1136, 664, gaze_dx=0.2, gaze_dy=0.1, pupil_scale=0.90, droop=0.35)
    
    # Eyebrows: strong asymmetric slant (Left brow raised high, Right brow tilted down)
    draw_eyebrow(draw, (858, 564), (912, 538), (966, 568), width=8)
    draw_eyebrow(draw, (1088, 620), (1136, 614), (1184, 626), width=8)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: asymmetric wavy questioning mouth line
    draw_cubic_curve(draw, (998, 796), (1014, 780), (1034, 798), (1050, 778), fill=MOUTH_DARK, width=6)
    return c


def render_10_error(clean_face):
    """10 ERROR - Concerned downward gaze, worried inverted brows (/ \), wavy mouth, sweat drop."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: concerned downward/inward tilted eyes
    draw_open_anime_eye(c, 912, 670, gaze_dx=0.3, gaze_dy=0.6, pupil_scale=0.95)
    draw_open_anime_eye(c, 1136, 670, gaze_dx=-0.3, gaze_dy=0.6, pupil_scale=0.95)
    
    # Eyebrows: steep worried angle (/ \)
    draw_eyebrow(draw, (864, 622), (912, 580), (960, 580), width=8)
    draw_eyebrow(draw, (1088, 580), (1136, 580), (1184, 622), width=8)
    
    # Apologetic soft blush & Cyan sweat drop
    draw_cheek_blush(c, 860, 726, radius_x=30, radius_y=18, alpha=0.42, with_lines=False)
    draw_cheek_blush(c, 1188, 726, radius_x=30, radius_y=18, alpha=0.42, with_lines=False)
    draw_sweat_drop(c, 1204, 625, size=28)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: trembling wavy worried curve
    draw_cubic_curve(draw, (996, 792), (1012, 780), (1032, 798), (1052, 786), fill=MOUTH_DARK, width=6)
    return c


def render_11_complete(clean_face):
    """11 COMPLETE - Bright joyful open sparkling eyes, confident warm open smile, success sparkle."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: sparkling wide open joyful eyes with extra star highlights
    draw_open_anime_eye(c, 912, 658, gaze_dx=0.0, gaze_dy=-0.1, pupil_scale=1.15, highlight_extra=True)
    draw_open_anime_eye(c, 1136, 658, gaze_dx=0.0, gaze_dy=-0.1, pupil_scale=1.15, highlight_extra=True)
    
    # Eyebrows: triumphant confident raised brows
    draw_eyebrow(draw, (864, 580), (912, 560), (960, 580), width=8)
    draw_eyebrow(draw, (1088, 580), (1136, 560), (1184, 580), width=8)
    
    # Radiant cheerful blush
    draw_cheek_blush(c, 856, 715, radius_x=38, radius_y=24, alpha=0.65, with_lines=True)
    draw_cheek_blush(c, 1192, 715, radius_x=38, radius_y=24, alpha=0.65, with_lines=True)
    
    # Bright 4-point golden success sparkle star
    draw_sparkle_star(c, 1202, 610, size=30)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: bright, confident open cheerful smile
    mouth_poly = [(988, 774), (1024, 824), (1060, 774)]
    draw.polygon(mouth_poly, fill=MOUTH_INTERIOR_RED)
    draw_bezier_curve(draw, (986, 774), (1024, 826), (1062, 774), fill=MOUTH_DARK, width=6)
    draw.line([(984, 774), (1064, 774)], fill=MOUTH_DARK, width=7)
    draw.rectangle([1008, 775, 1040, 785], fill=WHITE)
    return c


def render_12_greeting(clean_face):
    """12 GREETING - Direct friendly eye contact, welcoming soft open smile, friendly gaze."""
    c = clean_face.copy()
    draw = ImageDraw.Draw(c)
    
    # Eyes: open, friendly, direct eye contact with warm specular highlights
    draw_open_anime_eye(c, 912, 660, gaze_dx=0.0, gaze_dy=0.0, pupil_scale=1.12, highlight_extra=True)
    draw_open_anime_eye(c, 1136, 660, gaze_dx=0.0, gaze_dy=0.0, pupil_scale=1.12, highlight_extra=True)
    
    # Eyebrows: welcoming soft brows
    draw_eyebrow(draw, (864, 588), (912, 572), (960, 588), width=7)
    draw_eyebrow(draw, (1088, 588), (1136, 572), (1184, 588), width=7)
    
    # Soft friendly pink blush
    draw_cheek_blush(c, 860, 718, radius_x=34, radius_y=20, alpha=0.48, with_lines=False)
    draw_cheek_blush(c, 1188, 718, radius_x=34, radius_y=20, alpha=0.48, with_lines=False)
    
    # Nose
    draw.ellipse([1022, 744, 1026, 748], fill=BROW_DARK)
    
    # Mouth: soft welcoming open gentle smile
    mouth_poly = [(996, 780), (1024, 808), (1052, 780)]
    draw.polygon(mouth_poly, fill=MOUTH_INTERIOR_RED)
    draw_bezier_curve(draw, (994, 780), (1024, 810), (1054, 780), fill=MOUTH_DARK, width=5)
    draw.line([(994, 780), (1054, 780)], fill=MOUTH_DARK, width=6)
    return c


RENDERERS = {
    "meli_expr_idle": render_01_idle,
    "meli_expr_curious": render_02_curious,
    "meli_expr_hover": render_03_hover,
    "meli_expr_happy": render_04_happy,
    "meli_expr_blink": render_05_blink,
    "meli_expr_sleepy": render_06_sleepy,
    "meli_expr_thinking": render_07_thinking,
    "meli_expr_focused": render_08_focused,
    "meli_expr_confused": render_09_confused,
    "meli_expr_error": render_10_error,
    "meli_expr_complete": render_11_complete,
    "meli_expr_greeting": render_12_greeting,
}


def build_all():
    print("=================================================================")
    print("MELI 2048x2048 MASTER EXPRESSION BUILD & LANCZOS REDUCTION")
    print("=================================================================")
    
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    
    master_base = create_master_base()
    clean_face = get_clean_face_master(master_base)
    
    master_images = {}
    runtime_images = {}
    
    for name, fn in RENDERERS.items():
        print(f"\n[Rendering Master 2048x2048: {name}]")
        raw_master = fn(clean_face)
        # Lock all pixels outside face box to be 100% identical to master_base
        master_img = lock_body_pixels(raw_master, master_base)
        
        master_file = MASTER_DIR / f"{name}_master.png"
        master_img.save(master_file, format="PNG")
        master_images[name] = master_img
        print(f"  -> Saved Master: {master_file} (2048x2048 RGBA)")
        
        # High-Quality Lanczos Reduction to 512x512
        runtime_img = master_img.resize((512, 512), resample=Image.Resampling.LANCZOS)
        runtime_file = RUNTIME_DIR / f"{name}.png"
        runtime_img.save(runtime_file, format="PNG")
        runtime_images[name] = runtime_img
        print(f"  -> Saved Runtime: {runtime_file} (512x512 RGBA, Lanczos)")
        
        # Copy to dist/
        dist_file = DIST_DIR / f"{name}.png"
        shutil.copy2(runtime_file, dist_file)
        print(f"  -> Copied to Dist: {dist_file}")
        
    # Generate High-Resolution Master Contact Sheet (3x4 grid)
    print("\n[Compositing 3x4 Contact Sheet]")
    cols, rows = 4, 3
    thumb_w, thumb_h = 512, 512
    margin_x, margin_y = 24, 50
    sheet_w = cols * thumb_w + (cols + 1) * margin_x
    sheet_h = rows * thumb_h + (rows + 1) * margin_y
    
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (23, 24, 36, 255))
    sheet_draw = ImageDraw.Draw(sheet)
    
    names_list = list(RENDERERS.keys())
    for idx, name in enumerate(names_list):
        r = idx // cols
        c_idx = idx % cols
        x = margin_x + c_idx * (thumb_w + margin_x)
        y = margin_y + r * (thumb_h + margin_y)
        
        # Checkerboard background for transparency preview
        for cy in range(y, y + thumb_h, 32):
            for cx in range(x, x + thumb_w, 32):
                if ((cx - x) // 32 + (cy - y) // 32) % 2 == 0:
                    sheet_draw.rectangle([cx, cy, cx + 31, cy + 31], fill=(38, 40, 56, 255))
                else:
                    sheet_draw.rectangle([cx, cy, cx + 31, cy + 31], fill=(28, 30, 44, 255))
                    
        # Paste runtime image
        sheet.paste(runtime_images[name], (x, y), runtime_images[name])
        
        # Border
        sheet_draw.rectangle([x, y, x + thumb_w, y + thumb_h], outline=(255, 122, 162, 160), width=2)
        
        # Label
        label_text = f"{idx+1:02d}. {name.replace('meli_expr_', '').upper()}"
        sheet_draw.rectangle([x, y + thumb_h + 6, x + thumb_w, y + thumb_h + 36], fill=(14, 16, 23, 220))
        sheet_draw.text((x + 12, y + thumb_h + 12), label_text, fill=(255, 214, 231, 255))
        
    sheet_path = SHEETS_DIR / "meli_expression_contact_sheet.png"
    sheet.save(sheet_path, format="PNG")
    print(f"\n[SUCCESS] Contact sheet generated at {sheet_path} ({sheet_w}x{sheet_h})")


if __name__ == "__main__":
    build_all()
