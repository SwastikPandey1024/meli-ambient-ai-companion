#!/usr/bin/env python3
"""
build_expression_sprites.py - High-Fidelity 12 Production Expression Sprite Generator for Meli

Generates the 12 canonical expression sprites based on assets/meli/character/meli_body_base.png:
1. meli_expr_idle.png
2. meli_expr_curious.png
3. meli_expr_hover.png
4. meli_expr_happy.png
5. meli_expr_blink.png
6. meli_expr_sleepy.png
7. meli_expr_thinking.png
8. meli_expr_focused.png
9. meli_expr_confused.png
10. meli_expr_error.png
11. meli_expr_complete.png
12. meli_expr_greeting.png

Also generates:
- assets/meli/sheets/meli_expression_contact_sheet.png
- docs/meli_expression_asset_pipeline.md
"""

import sys
import os
import math
import copy
from pathlib import Path

# Add scripts directory
sys.path.insert(0, str(Path(__file__).parent))
from validate_meli_sprite import PngReader, CANONICAL_TARGETS, validate_sprite
from generate_contact_sheet import write_png, generate_sheet

BASE_SPRITE_PATH = Path("assets/meli/character/meli_body_base.png")
OUTPUT_DIR = Path("assets/meli/character")
SHEETS_DIR = Path("assets/meli/sheets")
DOCS_DIR = Path("docs")


def blend_pixel(dst_r, dst_g, dst_b, dst_a, src_r, src_g, src_b, src_a_norm):
    """Alpha composite src over dst."""
    if src_a_norm <= 0:
        return dst_r, dst_g, dst_b, dst_a
    out_a = src_a_norm + (dst_a / 255.0) * (1.0 - src_a_norm)
    if out_a <= 0:
        return 0, 0, 0, 0
    out_r = int((src_r * src_a_norm + dst_r * (dst_a / 255.0) * (1.0 - src_a_norm)) / out_a)
    out_g = int((src_g * src_a_norm + dst_g * (dst_a / 255.0) * (1.0 - src_a_norm)) / out_a)
    out_b = int((src_b * src_a_norm + dst_b * (dst_a / 255.0) * (1.0 - src_a_norm)) / out_a)
    return max(0, min(255, out_r)), max(0, min(255, out_g)), max(0, min(255, out_b)), int(out_a * 255)


class SpriteCanvas:
    def __init__(self, width=512, height=512, base_pixels=None):
        self.width = width
        self.height = height
        if base_pixels:
            self.pixels = [list(row) for row in base_pixels]
        else:
            self.pixels = [[(0, 0, 0, 0) for _ in range(width)] for _ in range(height)]

    def draw_pixel(self, x, y, r, g, b, alpha=1.0):
        if 0 <= x < self.width and 0 <= y < self.height:
            dr, dg, db, da = self.pixels[y][x]
            self.pixels[y][x] = blend_pixel(dr, dg, db, da, r, g, b, alpha)

    def draw_circle(self, cx, cy, radius, r, g, b, alpha=1.0, filled=True):
        r_int = int(math.ceil(radius))
        for dy in range(-r_int - 1, r_int + 2):
            for dx in range(-r_int - 1, r_int + 2):
                dist = math.hypot(dx, dy)
                if filled:
                    if dist <= radius - 0.5:
                        self.draw_pixel(cx + dx, cy + dy, r, g, b, alpha)
                    elif dist <= radius + 0.5:
                        cov = (radius + 0.5 - dist) * alpha
                        self.draw_pixel(cx + dx, cy + dy, r, g, b, cov)
                else:
                    thickness = 1.6
                    diff = abs(dist - radius)
                    if diff <= thickness:
                        cov = (1.0 - diff / thickness) * alpha
                        self.draw_pixel(cx + dx, cy + dy, r, g, b, cov)

    def draw_ellipse(self, cx, cy, rx, ry, r, g, b, alpha=1.0, filled=True, blur=False):
        rx_int = int(math.ceil(rx)) + (3 if blur else 1)
        ry_int = int(math.ceil(ry)) + (3 if blur else 1)
        for dy in range(-ry_int, ry_int + 1):
            for dx in range(-rx_int, rx_int + 1):
                norm_d = (dx / max(0.1, rx)) ** 2 + (dy / max(0.1, ry)) ** 2
                if blur:
                    if norm_d <= 2.25:
                        falloff = math.exp(-norm_d * 1.5) * alpha
                        self.draw_pixel(cx + dx, cy + dy, r, g, b, falloff)
                else:
                    if filled:
                        if norm_d <= 1.0:
                            self.draw_pixel(cx + dx, cy + dy, r, g, b, alpha)
                        elif norm_d <= 1.25:
                            cov = (1.25 - norm_d) * 4.0 * alpha
                            self.draw_pixel(cx + dx, cy + dy, r, g, b, max(0.0, min(1.0, cov)))

    def draw_line(self, x0, y0, x1, y1, r, g, b, width=2.0, alpha=1.0):
        length = math.hypot(x1 - x0, y1 - y0)
        steps = max(1, int(length * 2.5))
        for s in range(steps + 1):
            t = s / float(steps)
            cx = int(round(x0 + t * (x1 - x0)))
            cy = int(round(y0 + t * (y1 - y0)))
            self.draw_circle(cx, cy, width / 2.0, r, g, b, alpha, filled=True)

    def draw_bezier(self, p0, p1, p2, r, g, b, width=2.4, alpha=1.0):
        """Quadratic Bezier curve."""
        steps = 40
        prev_x, prev_y = p0
        for s in range(1, steps + 1):
            t = s / float(steps)
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
            self.draw_line(int(round(prev_x)), int(round(prev_y)), int(round(x)), int(round(y)), r, g, b, width, alpha)
            prev_x, prev_y = x, y

    def draw_cubic_bezier(self, p0, p1, p2, p3, r, g, b, width=2.4, alpha=1.0):
        """Cubic Bezier curve."""
        steps = 50
        prev_x, prev_y = p0
        for s in range(1, steps + 1):
            t = s / float(steps)
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
            self.draw_line(int(round(prev_x)), int(round(prev_y)), int(round(x)), int(round(y)), r, g, b, width, alpha)
            prev_x, prev_y = x, y


def build_all_sprites():
    print(f"Reading canonical base sprite from {BASE_SPRITE_PATH}...")
    reader = PngReader(BASE_SPRITE_PATH)
    base_pixels = reader.rgba_pixels
    print(f"Base sprite loaded: {reader.width}x{reader.height}, 32-bit RGBA")

    # Canonical Facial Coordinates (in 512x512 space):
    # Left Eye Center: X=228, Y=166
    # Right Eye Center: X=284, Y=166
    # Left Brow Center: X=228, Y=150
    # Right Brow Center: X=284, Y=150
    # Mouth Center: X=256, Y=196
    # Left Cheek: X=216, Y=180
    # Right Cheek: X=296, Y=180

    # Dark eye color
    EYE_R, EYE_G, EYE_B = 45, 40, 51
    BROW_R, BROW_G, BROW_B = 58, 50, 56
    BLUSH_R, BLUSH_G, BLUSH_B = 255, 122, 162
    SWEAT_R, SWEAT_G, SWEAT_B = 128, 216, 255
    SPARKLE_R, SPARKLE_G, SPARKLE_B = 255, 224, 130

    def create_canvas():
        return SpriteCanvas(512, 512, base_pixels)

    # 1. IDLE (Observant, calm, neutral)
    def render_idle():
        c = create_canvas()
        # Eyes
        c.draw_circle(228, 166, 4.5, EYE_R, EYE_G, EYE_B)
        c.draw_circle(284, 166, 4.5, EYE_R, EYE_G, EYE_B)
        c.draw_circle(226, 164, 1.6, 255, 255, 255)
        c.draw_circle(282, 164, 1.6, 255, 255, 255)
        # Brows
        c.draw_bezier((218, 153), (228, 150), (238, 153), BROW_R, BROW_G, BROW_B, width=2.0)
        c.draw_bezier((274, 153), (284, 150), (294, 153), BROW_R, BROW_G, BROW_B, width=2.0)
        # Soft neutral mouth
        c.draw_bezier((251, 196), (256, 198), (261, 196), EYE_R, EYE_G, EYE_B, width=1.8)
        return c

    # 2. CURIOUS (Raised brow, slightly widened gaze, sparkle)
    def render_curious():
        c = create_canvas()
        # Eyes slightly wider
        c.draw_circle(228, 165, 5.2, EYE_R, EYE_G, EYE_B)
        c.draw_circle(284, 165, 5.2, EYE_R, EYE_G, EYE_B)
        c.draw_circle(226, 163, 2.0, 255, 255, 255)
        c.draw_circle(282, 163, 2.0, 255, 255, 255)
        # Raised Left Brow, relaxed Right
        c.draw_bezier((217, 148), (228, 143), (239, 149), BROW_R, BROW_G, BROW_B, width=2.2)
        c.draw_bezier((274, 153), (284, 151), (294, 154), BROW_R, BROW_G, BROW_B, width=2.0)
        # Subtle curious mouth
        c.draw_bezier((252, 195), (256, 199), (260, 195), EYE_R, EYE_G, EYE_B, width=2.0)
        # Sparkle near eye
        c.draw_line(298, 152, 298, 160, SPARKLE_R, SPARKLE_G, SPARKLE_B, width=1.6)
        c.draw_line(294, 156, 302, 156, SPARKLE_R, SPARKLE_G, SPARKLE_B, width=1.6)
        return c

    # 3. HOVER (Anticipation, attentive gaze)
    def render_hover():
        c = create_canvas()
        # Eyes looking up-right slightly toward cursor
        c.draw_circle(229, 164, 4.8, EYE_R, EYE_G, EYE_B)
        c.draw_circle(285, 164, 4.8, EYE_R, EYE_G, EYE_B)
        c.draw_circle(228, 162, 1.8, 255, 255, 255)
        c.draw_circle(284, 162, 1.8, 255, 255, 255)
        # Brows alert
        c.draw_bezier((218, 151), (228, 147), (238, 151), BROW_R, BROW_G, BROW_B, width=2.1)
        c.draw_bezier((274, 151), (284, 147), (294, 151), BROW_R, BROW_G, BROW_B, width=2.1)
        # Gentle smile
        c.draw_bezier((250, 195), (256, 200), (262, 195), EYE_R, EYE_G, EYE_B, width=2.2)
        # Soft blush
        c.draw_ellipse(216, 180, 7.0, 4.0, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.35, blur=True)
        c.draw_ellipse(296, 180, 7.0, 4.0, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.35, blur=True)
        return c

    # 4. HAPPY (Crescent eyes, warm smile, blush)
    def render_happy():
        c = create_canvas()
        # Crescent smiling eyes
        c.draw_bezier((218, 168), (228, 158), (238, 168), EYE_R, EYE_G, EYE_B, width=3.2)
        c.draw_bezier((274, 168), (284, 158), (294, 168), EYE_R, EYE_G, EYE_B, width=3.2)
        # Soft relaxed brows
        c.draw_bezier((218, 151), (228, 147), (238, 151), BROW_R, BROW_G, BROW_B, width=2.2)
        c.draw_bezier((274, 151), (284, 147), (294, 151), BROW_R, BROW_G, BROW_B, width=2.2)
        # Cheerful curved mouth
        c.draw_bezier((249, 194), (256, 202), (263, 194), EYE_R, EYE_G, EYE_B, width=2.6)
        # Rosy blush
        c.draw_ellipse(215, 178, 8.5, 5.0, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.45, blur=True)
        c.draw_ellipse(297, 178, 8.5, 5.0, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.45, blur=True)
        return c

    # 5. BLINK (Gently closed eyelids)
    def render_blink():
        c = create_canvas()
        # Soft straight/curved closed lines
        c.draw_bezier((218, 166), (228, 168), (238, 166), EYE_R, EYE_G, EYE_B, width=2.6)
        c.draw_bezier((274, 166), (284, 168), (294, 166), EYE_R, EYE_G, EYE_B, width=2.6)
        # Neutral brows
        c.draw_bezier((218, 153), (228, 150), (238, 153), BROW_R, BROW_G, BROW_B, width=2.0)
        c.draw_bezier((274, 153), (284, 150), (294, 153), BROW_R, BROW_G, BROW_B, width=2.0)
        # Neutral mouth
        c.draw_bezier((251, 196), (256, 198), (261, 196), EYE_R, EYE_G, EYE_B, width=1.8)
        return c

    # 6. SLEEPY (Half-closed heavy eyelids)
    def render_sleepy():
        c = create_canvas()
        # Half-closed eyes
        c.draw_bezier((218, 164), (228, 162), (238, 164), EYE_R, EYE_G, EYE_B, width=2.8)
        c.draw_circle(228, 167, 3.2, EYE_R, EYE_G, EYE_B)
        c.draw_bezier((274, 164), (284, 162), (294, 164), EYE_R, EYE_G, EYE_B, width=2.8)
        c.draw_circle(284, 167, 3.2, EYE_R, EYE_G, EYE_B)
        # Slanted low brows
        c.draw_bezier((218, 154), (228, 153), (238, 155), BROW_R, BROW_G, BROW_B, width=2.0)
        c.draw_bezier((274, 155), (284, 153), (294, 154), BROW_R, BROW_G, BROW_B, width=2.0)
        # Relaxed mouth
        c.draw_bezier((251, 197), (256, 198), (261, 197), EYE_R, EYE_G, EYE_B, width=1.8)
        c.draw_ellipse(216, 180, 6.0, 3.5, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.3, blur=True)
        c.draw_ellipse(296, 180, 6.0, 3.5, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.3, blur=True)
        return c

    # 7. THINKING (Gaze slightly upward, analytical concentration)
    def render_thinking():
        c = create_canvas()
        # Eyes looking slightly up and left
        c.draw_circle(226, 163, 4.6, EYE_R, EYE_G, EYE_B)
        c.draw_circle(282, 163, 4.6, EYE_R, EYE_G, EYE_B)
        c.draw_circle(225, 161, 1.6, 255, 255, 255)
        c.draw_circle(281, 161, 1.6, 255, 255, 255)
        # Concentrated brows
        c.draw_bezier((219, 150), (228, 148), (238, 152), BROW_R, BROW_G, BROW_B, width=2.2)
        c.draw_bezier((274, 152), (284, 148), (293, 150), BROW_R, BROW_G, BROW_B, width=2.2)
        # Small thinking line mouth
        c.draw_line(252, 196, 260, 196, EYE_R, EYE_G, EYE_B, width=2.0)
        return c

    # 8. FOCUSED (Concentrated calm eyes, analytical brows)
    def render_focused():
        c = create_canvas()
        # Narrow concentrated eyes
        c.draw_bezier((218, 164), (228, 162), (238, 164), EYE_R, EYE_G, EYE_B, width=3.0)
        c.draw_circle(228, 166, 3.6, EYE_R, EYE_G, EYE_B)
        c.draw_bezier((274, 164), (284, 162), (294, 164), EYE_R, EYE_G, EYE_B, width=3.0)
        c.draw_circle(284, 166, 3.6, EYE_R, EYE_G, EYE_B)
        # Focused concentrated brows
        c.draw_bezier((219, 149), (228, 151), (238, 148), BROW_R, BROW_G, BROW_B, width=2.4)
        c.draw_bezier((274, 148), (284, 151), (293, 149), BROW_R, BROW_G, BROW_B, width=2.4)
        # Focused straight mouth
        c.draw_line(252, 196, 260, 196, EYE_R, EYE_G, EYE_B, width=2.2)
        return c

    # 9. CONFUSED (Asymmetric brows, questioning mouth)
    def render_confused():
        c = create_canvas()
        # Left eye wide, Right eye slight squint
        c.draw_circle(228, 164, 5.0, EYE_R, EYE_G, EYE_B)
        c.draw_circle(226, 162, 1.8, 255, 255, 255)
        c.draw_circle(284, 166, 4.2, EYE_R, EYE_G, EYE_B)
        c.draw_circle(283, 164, 1.5, 255, 255, 255)
        # Left brow high, Right brow low
        c.draw_bezier((218, 146), (228, 142), (238, 147), BROW_R, BROW_G, BROW_B, width=2.3)
        c.draw_bezier((274, 155), (284, 153), (294, 156), BROW_R, BROW_G, BROW_B, width=2.3)
        # Slanted questioning mouth
        c.draw_bezier((251, 195), (256, 198), (261, 194), EYE_R, EYE_G, EYE_B, width=2.0)
        return c

    # 10. ERROR (Concerned downward gaze, wavy mouth, sweat drop)
    def render_error():
        c = create_canvas()
        # Slightly worried eyes looking down
        c.draw_circle(228, 167, 4.4, EYE_R, EYE_G, EYE_B)
        c.draw_circle(284, 167, 4.4, EYE_R, EYE_G, EYE_B)
        c.draw_circle(227, 168, 1.5, 255, 255, 255)
        c.draw_circle(283, 168, 1.5, 255, 255, 255)
        # Inverted worried brows
        c.draw_bezier((218, 150), (228, 154), (238, 154), BROW_R, BROW_G, BROW_B, width=2.2)
        c.draw_bezier((274, 154), (284, 154), (294, 150), BROW_R, BROW_G, BROW_B, width=2.2)
        # Small wavy mouth
        c.draw_bezier((250, 197), (253, 195), (256, 197), EYE_R, EYE_G, EYE_B, width=2.0)
        c.draw_bezier((256, 197), (259, 199), (262, 197), EYE_R, EYE_G, EYE_B, width=2.0)
        # Apologetic blush & sweat drop
        c.draw_ellipse(216, 181, 6.0, 3.5, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.35, blur=True)
        c.draw_ellipse(296, 181, 6.0, 3.5, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.35, blur=True)
        c.draw_circle(299, 157, 3.0, SWEAT_R, SWEAT_G, SWEAT_B, alpha=0.85)
        return c

    # 11. COMPLETE (Bright joyful eyes, confident gentle smile)
    def render_complete():
        c = create_canvas()
        # Bright crescent eyes
        c.draw_bezier((218, 167), (228, 157), (238, 167), EYE_R, EYE_G, EYE_B, width=3.4)
        c.draw_bezier((274, 167), (284, 157), (294, 167), EYE_R, EYE_G, EYE_B, width=3.4)
        # Confident brows
        c.draw_bezier((218, 150), (228, 146), (238, 150), BROW_R, BROW_G, BROW_B, width=2.2)
        c.draw_bezier((274, 150), (284, 146), (294, 150), BROW_R, BROW_G, BROW_B, width=2.2)
        # Confident warm smile
        c.draw_bezier((249, 194), (256, 203), (263, 194), EYE_R, EYE_G, EYE_B, width=2.6)
        # Success sparkle
        c.draw_line(298, 150, 298, 158, SPARKLE_R, SPARKLE_G, SPARKLE_B, width=1.8)
        c.draw_line(294, 154, 302, 154, SPARKLE_R, SPARKLE_G, SPARKLE_B, width=1.8)
        # Cheerful blush
        c.draw_ellipse(215, 178, 8.0, 4.5, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.42, blur=True)
        c.draw_ellipse(297, 178, 8.0, 4.5, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.42, blur=True)
        return c

    # 12. GREETING (Welcoming direct eye contact, soft smile)
    def render_greeting():
        c = create_canvas()
        # Open attentive eyes
        c.draw_circle(228, 165, 4.8, EYE_R, EYE_G, EYE_B)
        c.draw_circle(284, 165, 4.8, EYE_R, EYE_G, EYE_B)
        c.draw_circle(226, 163, 1.8, 255, 255, 255)
        c.draw_circle(282, 163, 1.8, 255, 255, 255)
        # Welcoming soft brows
        c.draw_bezier((218, 150), (228, 146), (238, 150), BROW_R, BROW_G, BROW_B, width=2.2)
        c.draw_bezier((274, 150), (284, 146), (294, 150), BROW_R, BROW_G, BROW_B, width=2.2)
        # Gentle friendly smile
        c.draw_bezier((250, 194), (256, 201), (262, 194), EYE_R, EYE_G, EYE_B, width=2.4)
        c.draw_ellipse(216, 179, 7.5, 4.2, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.38, blur=True)
        c.draw_ellipse(296, 179, 7.5, 4.2, BLUSH_R, BLUSH_G, BLUSH_B, alpha=0.38, blur=True)
        return c

    renderers = {
        "meli_expr_idle.png": render_idle,
        "meli_expr_curious.png": render_curious,
        "meli_expr_hover.png": render_hover,
        "meli_expr_happy.png": render_happy,
        "meli_expr_blink.png": render_blink,
        "meli_expr_sleepy.png": render_sleepy,
        "meli_expr_thinking.png": render_thinking,
        "meli_expr_focused.png": render_focused,
        "meli_expr_confused.png": render_confused,
        "meli_expr_error.png": render_error,
        "meli_expr_complete.png": render_complete,
        "meli_expr_greeting.png": render_greeting,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[Building 12 Production Expression PNGs]")
    for filename, fn in renderers.items():
        out_path = OUTPUT_DIR / filename
        canvas = fn()
        write_png(out_path, canvas.width, canvas.height, canvas.pixels)
        print(f"  -> Generated {out_path.name} (512x512 RGBA)")

    # Composite contact sheet
    sheet_out = SHEETS_DIR / "meli_expression_contact_sheet.png"
    print(f"\n[Compositing Contact Sheet to {sheet_out}]")
    generate_sheet(OUTPUT_DIR, sheet_out)

    # Validate all canonical targets
    print("\n[Validating all 13 canonical sprites with 14-point QA validator]")
    all_passed = True
    for target in CANONICAL_TARGETS:
        t_path = OUTPUT_DIR / target
        report = validate_sprite(t_path)
        if report["failures"]:
            print(f"  [FAIL] {target}: {report['failures']}")
            all_passed = False
        else:
            print(f"  [PASS] {target} (14/14 technical QA checks passed)")

    return all_passed


if __name__ == "__main__":
    success = build_all_sprites()
    if not success:
        sys.exit(1)
