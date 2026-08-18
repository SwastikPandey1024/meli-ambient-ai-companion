#!/usr/bin/env python3
"""
build_expression_overlays.py — Canonical Expression Overlay Builder for Meli v3

Architecture:
  1. Writes 12 SVG overlays using absolute 512×512 coordinates.
  2. Renders each overlay at 2× (1024×1024) using PIL, then downscales to
     512×512 with LANCZOS anti-aliasing for crisp sub-pixel quality.
  3. Alpha-composites rendered overlay onto the locked canonical base PNG.
  4. Saves composite PNGs and a v3 contact sheet.

Skin color tokens are sampled from the ACTUAL base sprite:
  Skin:   ~#CA8883 (median between-brow-and-eye skin)
  Darker: ~#C07E79 (lid drape variant)

NOT using #F9C5BE — that was the wrong color from the previous pipeline.
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ── Paths ──────────────────────────────────────────────────────────────
BASE_SPRITE   = Path("assets/meli/character/meli_body_base.png")
OVERLAY_DIR   = Path("assets/meli/expressions/overlays")
COMPOSITE_DIR = Path("assets/meli/expressions/composite")
SHEETS_DIR    = Path("assets/meli/sheets")

# ── Color Tokens (sampled from actual base sprite) ────────────────────
SKIN        = (202, 136, 131, 255)   # Median skin between brows & eyes
SKIN_DARK   = (192, 126, 121, 255)   # Slightly darker for lid draping
OUTLINE     = (30, 20, 32, 255)      # Near-black plum outline
BROW        = (42, 30, 38, 255)      # Dark warm-brown brows
WHITE_HL    = (255, 255, 255, 255)   # Specular catchlight
WARM_LIP    = (163, 69, 88, 255)     # Warm muted rose lip
HAPPY_LIP   = (184, 77, 96, 255)     # Brighter smile lip
GOLD        = (255, 217, 106, 255)   # Gold sparkle
CYAN_SWEAT  = (112, 214, 255, 240)   # Sweat drop
BLUSH_SOFT  = (210, 90, 120, 90)     # Soft blush (alpha)
BLUSH_HEAVY = (220, 80, 110, 130)    # Strong blush (alpha)
LID_CREASE  = (138, 96, 104, 165)    # Lid crease subtle tone
BLUSH_LINE  = (216, 88, 116, 180)    # Diagonal blush hash marks

RENDER_SCALE = 2  # Render at 2× then downscale for AA

EXPRESSION_ORDER = [
    "idle", "curious", "hover", "happy", "blink", "sleepy",
    "thinking", "focused", "confused", "error", "complete", "greeting"
]

# ── SVG content strings ──────────────────────────────────────────────
# These use the *corrected* absolute 512×512 coordinates.

SVG_HEADER = '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
SVG_FOOTER = '</svg>'

def _make_svg_overlays():
    """Build SVG strings for all 12 expressions."""
    overlays = {}

    overlays["idle"] = f"""{SVG_HEADER}
  <!-- 01 IDLE: No overlay -->
{SVG_FOOTER}"""

    overlays["curious"] = f"""{SVG_HEADER}
  <!-- 02 CURIOUS -->
  <g id="brows" stroke="#2A1E26" stroke-width="2.8" stroke-linecap="round" fill="none">
    <path d="M 218 145 Q 235 138 250 144"/>
    <path d="M 268 144 Q 283 138 302 145"/>
  </g>
  <g id="gaze" fill="white"><circle cx="230" cy="165" r="3.0"/><circle cx="280" cy="164" r="3.0"/></g>
  <g id="mouth"><ellipse cx="254" cy="200" rx="6" ry="7" fill="#A34558" stroke="#1E1420" stroke-width="2.0"/></g>
  <g id="sparkle" fill="#FFD96A">
    <path d="M 296 146 L 299 140 L 302 146 L 308 148 L 302 150 L 299 156 L 296 150 L 290 148 Z"/>
    <circle cx="299" cy="148" r="1.2" fill="white"/>
  </g>
{SVG_FOOTER}"""

    overlays["hover"] = f"""{SVG_HEADER}
  <!-- 03 HOVER -->
  <g id="brows" stroke="#2A1E26" stroke-width="2.4" stroke-linecap="round" fill="none">
    <path d="M 218 142 Q 235 135 250 143"/>
    <path d="M 268 145 Q 283 140 302 144"/>
  </g>
  <g id="gaze" fill="white"><circle cx="238" cy="166" r="2.8"/><circle cx="288" cy="165" r="2.8"/></g>
  <g id="blush">
    <ellipse cx="216" cy="181" rx="12" ry="6" fill="rgba(210,90,120,0.35)"/>
    <ellipse cx="298" cy="181" rx="12" ry="6" fill="rgba(210,90,120,0.35)"/>
  </g>
  <g id="mouth" stroke="#1E1420" stroke-width="2.2" stroke-linecap="round" fill="none">
    <path d="M 242 199 Q 250 195 256 199 Q 262 202 268 197"/>
  </g>
{SVG_FOOTER}"""

    overlays["happy"] = f"""{SVG_HEADER}
  <!-- 04 HAPPY -->
  <ellipse cx="234" cy="169" rx="16" ry="11" fill="#CA8883"/>
  <ellipse cx="284" cy="168" rx="16" ry="11" fill="#CA8883"/>
  <g id="crescent-eyes" stroke="#1E1420" stroke-width="3.5" stroke-linecap="round" fill="none">
    <path d="M 218 172 Q 234 160 250 172"/>
    <path d="M 268 172 Q 284 160 300 172"/>
    <path d="M 248 170 L 254 166" stroke-width="2.2"/>
    <path d="M 298 170 L 304 166" stroke-width="2.2"/>
  </g>
  <g id="brows" stroke="#2A1E26" stroke-width="2.4" stroke-linecap="round" fill="none">
    <path d="M 218 143 Q 235 137 250 143"/>
    <path d="M 268 143 Q 283 137 302 143"/>
  </g>
  <g id="blush">
    <ellipse cx="214" cy="180" rx="14" ry="7" fill="rgba(220,80,110,0.50)"/>
    <ellipse cx="300" cy="180" rx="14" ry="7" fill="rgba(220,80,110,0.50)"/>
  </g>
  <g id="mouth">
    <path d="M 240 197 Q 254 210 268 197 Z" fill="#B84D60" stroke="#1E1420" stroke-width="2.2"/>
    <line x1="240" y1="197" x2="268" y2="197" stroke="#1E1420" stroke-width="2.4"/>
    <rect x="250" y="198" width="8" height="3" rx="1" fill="white"/>
  </g>
{SVG_FOOTER}"""

    overlays["blink"] = f"""{SVG_HEADER}
  <!-- 05 BLINK -->
  <ellipse cx="234" cy="169" rx="16" ry="11" fill="#CA8883"/>
  <ellipse cx="284" cy="168" rx="16" ry="11" fill="#CA8883"/>
  <g id="closed-lids" stroke="#1E1420" stroke-width="3.0" stroke-linecap="round" fill="none">
    <path d="M 218 169 Q 234 174 250 169"/>
    <path d="M 268 169 Q 284 174 300 169"/>
  </g>
  <g id="lid-creases" stroke="#8A6068" stroke-width="1.4" stroke-linecap="round" fill="none" opacity="0.6">
    <path d="M 220 163 Q 234 160 248 163"/>
    <path d="M 270 163 Q 284 160 298 163"/>
  </g>
  <g id="lashes" stroke="#1E1420" stroke-width="2.0" stroke-linecap="round" fill="none">
    <path d="M 248 168 L 253 164"/>
    <path d="M 298 168 L 303 164"/>
  </g>
{SVG_FOOTER}"""

    overlays["sleepy"] = f"""{SVG_HEADER}
  <!-- 06 SLEEPY -->
  <rect x="218" y="160" width="34" height="10" rx="2" fill="#C07E79"/>
  <rect x="266" y="160" width="34" height="10" rx="2" fill="#C07E79"/>
  <g id="sleepy-lids" stroke="#1E1420" stroke-width="2.8" stroke-linecap="round" fill="none">
    <path d="M 218 170 Q 234 173 250 170"/>
    <path d="M 268 170 Q 284 173 300 170"/>
  </g>
  <g id="brows" stroke="#2A1E26" stroke-width="2.2" stroke-linecap="round" fill="none">
    <path d="M 220 152 Q 234 150 248 154"/>
    <path d="M 270 154 Q 284 150 300 152"/>
  </g>
  <g id="blush">
    <ellipse cx="216" cy="182" rx="10" ry="5" fill="rgba(210,90,120,0.35)"/>
    <ellipse cx="298" cy="182" rx="10" ry="5" fill="rgba(210,90,120,0.35)"/>
  </g>
  <g id="mouth"><ellipse cx="254" cy="201" rx="5" ry="4" fill="#A34558" stroke="#1E1420" stroke-width="1.8"/></g>
{SVG_FOOTER}"""

    overlays["thinking"] = f"""{SVG_HEADER}
  <!-- 07 THINKING -->
  <g id="brows" stroke="#2A1E26" stroke-width="2.6" stroke-linecap="round" fill="none">
    <path d="M 218 141 Q 235 135 250 143"/>
    <path d="M 268 150 Q 283 146 302 148"/>
  </g>
  <g id="gaze" fill="white"><circle cx="238" cy="163" r="3.2"/><circle cx="288" cy="162" r="3.2"/></g>
  <g id="blush">
    <ellipse cx="216" cy="182" rx="8" ry="4" fill="rgba(210,90,120,0.25)"/>
    <ellipse cx="298" cy="182" rx="8" ry="4" fill="rgba(210,90,120,0.25)"/>
  </g>
  <g id="mouth" stroke="#1E1420" stroke-width="2.6" stroke-linecap="round" fill="none">
    <line x1="245" y1="200" x2="263" y2="200"/>
  </g>
{SVG_FOOTER}"""

    overlays["focused"] = f"""{SVG_HEADER}
  <!-- 08 FOCUSED -->
  <rect x="218" y="160" width="34" height="8" rx="1" fill="#C07E79"/>
  <rect x="266" y="160" width="34" height="8" rx="1" fill="#C07E79"/>
  <g id="focus-lids" stroke="#1E1420" stroke-width="2.8" stroke-linecap="round" fill="none">
    <line x1="218" y1="168" x2="252" y2="168"/>
    <line x1="266" y1="168" x2="300" y2="168"/>
  </g>
  <g id="brows" stroke="#2A1E26" stroke-width="2.8" stroke-linecap="round" fill="none">
    <path d="M 220 150 Q 235 152 248 147"/>
    <path d="M 270 147 Q 283 152 300 150"/>
  </g>
  <g id="mouth" stroke="#1E1420" stroke-width="2.6" stroke-linecap="round" fill="none">
    <line x1="244" y1="200" x2="264" y2="200"/>
  </g>
{SVG_FOOTER}"""

    overlays["confused"] = f"""{SVG_HEADER}
  <!-- 09 CONFUSED -->
  <g id="brows" stroke="#2A1E26" stroke-width="2.8" stroke-linecap="round" fill="none">
    <path d="M 218 139 Q 235 133 250 141"/>
    <path d="M 268 152 Q 283 150 302 155"/>
  </g>
  <g id="gaze" fill="white"><circle cx="232" cy="164" r="3.0"/><circle cx="286" cy="168" r="2.0"/></g>
  <rect x="268" y="161" width="32" height="4" rx="1" fill="rgba(192,126,121,0.7)"/>
  <g id="blush">
    <ellipse cx="216" cy="182" rx="8" ry="4" fill="rgba(210,90,120,0.25)"/>
    <ellipse cx="298" cy="182" rx="8" ry="4" fill="rgba(210,90,120,0.25)"/>
  </g>
  <g id="mouth" stroke="#1E1420" stroke-width="2.4" stroke-linecap="round" fill="none">
    <path d="M 242 202 Q 250 196 258 203 Q 264 198 270 198"/>
  </g>
{SVG_FOOTER}"""

    overlays["error"] = f"""{SVG_HEADER}
  <!-- 10 ERROR -->
  <g id="brows" stroke="#2A1E26" stroke-width="2.8" stroke-linecap="round" fill="none">
    <path d="M 222 153 Q 235 143 250 141"/>
    <path d="M 268 141 Q 283 143 300 153"/>
  </g>
  <g id="gaze" fill="white"><circle cx="234" cy="172" r="2.0"/><circle cx="284" cy="172" r="2.0"/></g>
  <g id="blush">
    <ellipse cx="216" cy="182" rx="10" ry="5" fill="rgba(210,90,120,0.35)"/>
    <ellipse cx="298" cy="182" rx="10" ry="5" fill="rgba(210,90,120,0.35)"/>
  </g>
  <g id="sweat">
    <path d="M 305 148 C 305 143 309 137 309 137 C 309 137 313 143 313 148 C 313 152 311 154 309 154 C 307 154 305 152 305 148 Z" fill="#70D6FF"/>
    <circle cx="308" cy="146" r="1.5" fill="white"/>
  </g>
  <g id="mouth" stroke="#1E1420" stroke-width="2.4" stroke-linecap="round" fill="none">
    <path d="M 240 201 Q 247 196 254 202 Q 261 197 268 200"/>
  </g>
{SVG_FOOTER}"""

    overlays["complete"] = f"""{SVG_HEADER}
  <!-- 11 COMPLETE -->
  <g id="brows" stroke="#2A1E26" stroke-width="2.4" stroke-linecap="round" fill="none">
    <path d="M 218 143 Q 235 138 250 142"/>
    <path d="M 268 142 Q 283 138 302 143"/>
  </g>
  <g id="eyes" fill="white">
    <circle cx="232" cy="165" r="3.5"/><circle cx="235" cy="170" r="1.8"/>
    <circle cx="282" cy="164" r="3.5"/><circle cx="285" cy="169" r="1.8"/>
  </g>
  <g id="blush">
    <ellipse cx="216" cy="180" rx="11" ry="6" fill="rgba(220,80,110,0.50)"/>
    <ellipse cx="298" cy="180" rx="11" ry="6" fill="rgba(220,80,110,0.50)"/>
  </g>
  <g id="sparkle" fill="#FFD96A">
    <path d="M 296 144 L 299 138 L 302 144 L 308 146 L 302 148 L 299 154 L 296 148 L 290 146 Z"/>
    <circle cx="299" cy="146" r="1.5" fill="white"/>
  </g>
  <g id="mouth">
    <path d="M 238 197 Q 254 212 270 197 Z" fill="#B84D60" stroke="#1E1420" stroke-width="2.2"/>
    <line x1="238" y1="197" x2="270" y2="197" stroke="#1E1420" stroke-width="2.4"/>
    <rect x="249" y="198" width="10" height="4" rx="1" fill="white"/>
  </g>
{SVG_FOOTER}"""

    overlays["greeting"] = f"""{SVG_HEADER}
  <!-- 12 GREETING -->
  <g id="brows" stroke="#2A1E26" stroke-width="2.2" stroke-linecap="round" fill="none">
    <path d="M 218 143 Q 235 137 250 143"/>
    <path d="M 268 143 Q 283 137 302 143"/>
  </g>
  <g id="gaze" fill="white"><circle cx="234" cy="166" r="3.2"/><circle cx="284" cy="165" r="3.2"/></g>
  <g id="blush">
    <ellipse cx="214" cy="181" rx="12" ry="6" fill="rgba(220,80,110,0.50)"/>
    <ellipse cx="300" cy="181" rx="12" ry="6" fill="rgba(220,80,110,0.50)"/>
  </g>
  <g id="mouth">
    <path d="M 240 198 Q 254 208 268 198 Z" fill="#A34558" stroke="#1E1420" stroke-width="2.0"/>
    <line x1="240" y1="198" x2="268" y2="198" stroke="#1E1420" stroke-width="2.2"/>
    <rect x="251" y="199" width="6" height="2" fill="white"/>
  </g>
{SVG_FOOTER}"""

    return overlays


def _s(v):
    """Scale coordinate by RENDER_SCALE for 2x supersampling."""
    return int(round(v * RENDER_SCALE))


def _render_overlay_pil(name: str) -> Image.Image:
    """
    Render the expression overlay using PIL at 2x resolution,
    then downscale to 512x512 with LANCZOS anti-aliasing.
    """
    S = RENDER_SCALE
    sz = 512 * S
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if name == "idle":
        pass  # No overlay

    elif name == "curious":
        # Raised inner brows (strongly lifted)
        d.line([_s(218),_s(145), _s(235),_s(138), _s(250),_s(144)], fill=BROW, width=_s(2.8))
        d.line([_s(268),_s(144), _s(283),_s(138), _s(302),_s(145)], fill=BROW, width=_s(2.8))
        # Bright gaze catchlights shifted upward-left
        d.ellipse([_s(227),_s(162), _s(233),_s(168)], fill=WHITE_HL)
        d.ellipse([_s(277),_s(161), _s(283),_s(167)], fill=WHITE_HL)
        # Open 'o' mouth
        d.ellipse([_s(248),_s(193), _s(260),_s(207)], fill=WARM_LIP, outline=OUTLINE, width=_s(2.0))
        # Gold sparkle star placed safely inside face bbox
        sparkle_pts = [
            (_s(296),_s(146)), (_s(299),_s(140)), (_s(302),_s(146)), (_s(308),_s(148)),
            (_s(302),_s(150)), (_s(299),_s(156)), (_s(296),_s(150)), (_s(290),_s(148))
        ]
        d.polygon(sparkle_pts, fill=GOLD)
        d.ellipse([_s(298),_s(147), _s(300),_s(149)], fill=WHITE_HL)

    elif name == "hover":
        # Alert asymmetric brows
        d.line([_s(218),_s(142), _s(235),_s(135), _s(250),_s(143)], fill=BROW, width=_s(2.4))
        d.line([_s(268),_s(145), _s(283),_s(140), _s(302),_s(144)], fill=BROW, width=_s(2.4))
        # Right-shifted gaze
        d.ellipse([_s(235),_s(163), _s(241),_s(169)], fill=WHITE_HL)
        d.ellipse([_s(285),_s(162), _s(291),_s(168)], fill=WHITE_HL)
        # Blush
        blush_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blush_layer)
        bd.ellipse([_s(204),_s(175), _s(228),_s(187)], fill=BLUSH_SOFT)
        bd.ellipse([_s(286),_s(175), _s(310),_s(187)], fill=BLUSH_SOFT)
        blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(radius=_s(2)))
        img = Image.alpha_composite(img, blush_layer)
        d = ImageDraw.Draw(img)
        # Amused asymmetric smirk
        d.line([_s(242),_s(199), _s(250),_s(195), _s(256),_s(199), _s(262),_s(202), _s(268),_s(197)],
               fill=OUTLINE, width=_s(2.2))

    elif name == "happy":
        # Skin covers over original eyes
        d.ellipse([_s(218),_s(158), _s(250),_s(180)], fill=SKIN)
        d.ellipse([_s(268),_s(157), _s(300),_s(179)], fill=SKIN)
        # Crescent smile-eyes (^ ^) - wider, more visible
        d.line([_s(218),_s(172), _s(234),_s(160), _s(250),_s(172)], fill=OUTLINE, width=_s(3.5))
        d.line([_s(268),_s(172), _s(284),_s(160), _s(300),_s(172)], fill=OUTLINE, width=_s(3.5))
        # Outer lashes
        d.line([_s(248),_s(170), _s(254),_s(166)], fill=OUTLINE, width=_s(2.2))
        d.line([_s(298),_s(170), _s(304),_s(166)], fill=OUTLINE, width=_s(2.2))
        # Joyful brows
        d.line([_s(218),_s(143), _s(235),_s(137), _s(250),_s(143)], fill=BROW, width=_s(2.4))
        d.line([_s(268),_s(143), _s(283),_s(137), _s(302),_s(143)], fill=BROW, width=_s(2.4))
        # Strong blush
        blush_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blush_layer)
        bd.ellipse([_s(200),_s(173), _s(228),_s(187)], fill=BLUSH_HEAVY)
        bd.ellipse([_s(286),_s(173), _s(314),_s(187)], fill=BLUSH_HEAVY)
        blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(radius=_s(2)))
        img = Image.alpha_composite(img, blush_layer)
        d = ImageDraw.Draw(img)
        # Blush hash marks
        d.line([_s(207),_s(184), _s(215),_s(176)], fill=BLUSH_LINE, width=_s(1.5))
        d.line([_s(299),_s(184), _s(307),_s(176)], fill=BLUSH_LINE, width=_s(1.5))
        # Wide open smile with teeth
        mouth_pts = [(_s(240),_s(197)), (_s(254),_s(210)), (_s(268),_s(197))]
        d.polygon(mouth_pts, fill=HAPPY_LIP)
        d.line([(_s(240),_s(197)), (_s(254),_s(210)), (_s(268),_s(197))], fill=OUTLINE, width=_s(2.2))
        d.line([(_s(240),_s(197)), (_s(268),_s(197))], fill=OUTLINE, width=_s(2.4))
        d.rectangle([_s(250),_s(198), _s(258),_s(201)], fill=WHITE_HL)

    elif name == "blink":
        # Skin covers
        d.ellipse([_s(218),_s(158), _s(250),_s(180)], fill=SKIN)
        d.ellipse([_s(268),_s(157), _s(300),_s(179)], fill=SKIN)
        # Closed lid curves
        d.line([_s(218),_s(169), _s(234),_s(174), _s(250),_s(169)], fill=OUTLINE, width=_s(3.0))
        d.line([_s(268),_s(169), _s(284),_s(174), _s(300),_s(169)], fill=OUTLINE, width=_s(3.0))
        # Lid creases
        d.line([_s(220),_s(163), _s(234),_s(160), _s(248),_s(163)], fill=LID_CREASE, width=_s(1.4))
        d.line([_s(270),_s(163), _s(284),_s(160), _s(298),_s(163)], fill=LID_CREASE, width=_s(1.4))
        # Outer lashes
        d.line([_s(248),_s(168), _s(253),_s(164)], fill=OUTLINE, width=_s(2.0))
        d.line([_s(298),_s(168), _s(303),_s(164)], fill=OUTLINE, width=_s(2.0))

    elif name == "sleepy":
        # Heavy eyelid drapes (skin rectangles)
        d.rectangle([_s(218),_s(160), _s(252),_s(170)], fill=SKIN_DARK)
        d.rectangle([_s(266),_s(160), _s(300),_s(170)], fill=SKIN_DARK)
        # Droopy lid lines
        d.line([_s(218),_s(170), _s(234),_s(173), _s(250),_s(170)], fill=OUTLINE, width=_s(2.8))
        d.line([_s(268),_s(170), _s(284),_s(173), _s(300),_s(170)], fill=OUTLINE, width=_s(2.8))
        # Low-energy brows
        d.line([_s(220),_s(152), _s(234),_s(150), _s(248),_s(154)], fill=BROW, width=_s(2.2))
        d.line([_s(270),_s(154), _s(284),_s(150), _s(300),_s(152)], fill=BROW, width=_s(2.2))
        # Blush
        blush_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blush_layer)
        bd.ellipse([_s(206),_s(177), _s(226),_s(187)], fill=BLUSH_SOFT)
        bd.ellipse([_s(288),_s(177), _s(308),_s(187)], fill=BLUSH_SOFT)
        blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(radius=_s(2)))
        img = Image.alpha_composite(img, blush_layer)
        d = ImageDraw.Draw(img)
        # Small yawning mouth
        d.ellipse([_s(249),_s(197), _s(259),_s(205)], fill=WARM_LIP, outline=OUTLINE, width=_s(1.8))

    elif name == "thinking":
        # Raised left brow, slightly furrowed right
        d.line([_s(218),_s(141), _s(235),_s(135), _s(250),_s(143)], fill=BROW, width=_s(2.6))
        d.line([_s(268),_s(150), _s(283),_s(146), _s(302),_s(148)], fill=BROW, width=_s(2.6))
        # Upward-right gaze shifts
        d.ellipse([_s(235),_s(160), _s(241),_s(166)], fill=WHITE_HL)
        d.ellipse([_s(285),_s(159), _s(291),_s(165)], fill=WHITE_HL)
        # Subtle concentration blush
        blush_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blush_layer)
        bd.ellipse([_s(208),_s(178), _s(224),_s(186)], fill=BLUSH_SOFT)
        bd.ellipse([_s(290),_s(178), _s(306),_s(186)], fill=BLUSH_SOFT)
        blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(radius=_s(2)))
        img = Image.alpha_composite(img, blush_layer)
        d = ImageDraw.Draw(img)
        # Straight thinking mouth
        d.line([_s(245),_s(200), _s(263),_s(200)], fill=OUTLINE, width=_s(2.6))

    elif name == "focused":
        # Narrowed eyelid covers
        d.rectangle([_s(218),_s(160), _s(252),_s(168)], fill=SKIN_DARK)
        d.rectangle([_s(266),_s(160), _s(300),_s(168)], fill=SKIN_DARK)
        # Focused slit lines
        d.line([_s(218),_s(168), _s(252),_s(168)], fill=OUTLINE, width=_s(2.8))
        d.line([_s(266),_s(168), _s(300),_s(168)], fill=OUTLINE, width=_s(2.8))
        # Lowered concentrated brows
        d.line([_s(220),_s(150), _s(235),_s(152), _s(248),_s(147)], fill=BROW, width=_s(2.8))
        d.line([_s(270),_s(147), _s(283),_s(152), _s(300),_s(150)], fill=BROW, width=_s(2.8))
        # Firm mouth
        d.line([_s(244),_s(200), _s(264),_s(200)], fill=OUTLINE, width=_s(2.6))

    elif name == "confused":
        # Asymmetric brows (left arched at Y=139->133, right low at Y=152->155)
        d.line([_s(218),_s(139), _s(235),_s(133), _s(250),_s(141)], fill=BROW, width=_s(2.8))
        d.line([_s(268),_s(152), _s(283),_s(150), _s(302),_s(155)], fill=BROW, width=_s(2.8))
        # Asymmetric gaze (big left, small right)
        d.ellipse([_s(229),_s(161), _s(235),_s(167)], fill=WHITE_HL)
        d.ellipse([_s(284),_s(166), _s(288),_s(170)], fill=WHITE_HL)
        # Right eye squint
        d.rectangle([_s(268),_s(161), _s(300),_s(165)], fill=(*SKIN_DARK[:3], 180))
        # Subtle perplexed blush
        blush_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blush_layer)
        bd.ellipse([_s(208),_s(178), _s(224),_s(186)], fill=BLUSH_SOFT)
        bd.ellipse([_s(290),_s(178), _s(306),_s(186)], fill=BLUSH_SOFT)
        blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(radius=_s(2)))
        img = Image.alpha_composite(img, blush_layer)
        d = ImageDraw.Draw(img)
        # Crooked questioning mouth
        d.line([_s(242),_s(202), _s(250),_s(196), _s(258),_s(203), _s(264),_s(198), _s(270),_s(198)],
               fill=OUTLINE, width=_s(2.4))

    elif name == "error":
        # Worried inverted brows (/ \)
        d.line([_s(222),_s(153), _s(235),_s(143), _s(250),_s(141)], fill=BROW, width=_s(2.8))
        d.line([_s(268),_s(141), _s(283),_s(143), _s(300),_s(153)], fill=BROW, width=_s(2.8))
        # Downcast worried gaze (small highlights low)
        d.ellipse([_s(232),_s(170), _s(236),_s(174)], fill=WHITE_HL)
        d.ellipse([_s(282),_s(170), _s(286),_s(174)], fill=WHITE_HL)
        # Blush
        blush_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blush_layer)
        bd.ellipse([_s(206),_s(177), _s(226),_s(187)], fill=BLUSH_SOFT)
        bd.ellipse([_s(288),_s(177), _s(308),_s(187)], fill=BLUSH_SOFT)
        blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(radius=_s(2)))
        img = Image.alpha_composite(img, blush_layer)
        d = ImageDraw.Draw(img)
        # Cyan sweat drop (near right temple, INSIDE face zone)
        d.ellipse([_s(305),_s(146), _s(313),_s(154)], fill=CYAN_SWEAT)
        sweat_pts = [(_s(309),_s(137)), (_s(305),_s(147)), (_s(313),_s(147))]
        d.polygon(sweat_pts, fill=CYAN_SWEAT)
        d.ellipse([_s(306),_s(144), _s(310),_s(148)], fill=WHITE_HL)
        # Wavy anxious mouth
        d.line([_s(240),_s(201), _s(247),_s(196), _s(254),_s(202), _s(261),_s(197), _s(268),_s(200)],
               fill=OUTLINE, width=_s(2.4))

    elif name == "complete":
        # Joyful raised brows
        d.line([_s(218),_s(143), _s(235),_s(138), _s(250),_s(142)], fill=BROW, width=_s(2.4))
        d.line([_s(268),_s(142), _s(283),_s(138), _s(302),_s(143)], fill=BROW, width=_s(2.4))
        # Bright star speculars (big + small catchlights)
        d.ellipse([_s(228),_s(162), _s(236),_s(170)], fill=WHITE_HL)
        d.ellipse([_s(233),_s(168), _s(237),_s(172)], fill=WHITE_HL)
        d.ellipse([_s(278),_s(161), _s(286),_s(169)], fill=WHITE_HL)
        d.ellipse([_s(283),_s(167), _s(287),_s(171)], fill=WHITE_HL)
        # Heavy blush
        blush_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blush_layer)
        bd.ellipse([_s(205),_s(174), _s(227),_s(186)], fill=BLUSH_HEAVY)
        bd.ellipse([_s(287),_s(174), _s(309),_s(186)], fill=BLUSH_HEAVY)
        blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(radius=_s(2)))
        img = Image.alpha_composite(img, blush_layer)
        d = ImageDraw.Draw(img)
        # Blush hash marks
        d.line([_s(209),_s(183), _s(217),_s(175)], fill=BLUSH_LINE, width=_s(1.5))
        d.line([_s(297),_s(183), _s(305),_s(175)], fill=BLUSH_LINE, width=_s(1.5))
        # Gold sparkle star placed inside face bounds
        sparkle_pts = [
            (_s(296),_s(144)), (_s(299),_s(138)), (_s(302),_s(144)), (_s(308),_s(146)),
            (_s(302),_s(148)), (_s(299),_s(154)), (_s(296),_s(148)), (_s(290),_s(146))
        ]
        d.polygon(sparkle_pts, fill=GOLD)
        d.ellipse([_s(298),_s(145), _s(300),_s(147)], fill=WHITE_HL)
        # Big confident smile with teeth
        mouth_pts = [(_s(238),_s(197)), (_s(254),_s(212)), (_s(270),_s(197))]
        d.polygon(mouth_pts, fill=HAPPY_LIP)
        d.line([(_s(238),_s(197)), (_s(254),_s(212)), (_s(270),_s(197))], fill=OUTLINE, width=_s(2.2))
        d.line([(_s(238),_s(197)), (_s(270),_s(197))], fill=OUTLINE, width=_s(2.4))
        d.rectangle([_s(249),_s(198), _s(259),_s(202)], fill=WHITE_HL)

    elif name == "greeting":
        # Gently lifted welcoming brows
        d.line([_s(218),_s(143), _s(235),_s(137), _s(250),_s(143)], fill=BROW, width=_s(2.2))
        d.line([_s(268),_s(143), _s(283),_s(137), _s(302),_s(143)], fill=BROW, width=_s(2.2))
        # Direct centered gaze
        d.ellipse([_s(231),_s(163), _s(237),_s(169)], fill=WHITE_HL)
        d.ellipse([_s(281),_s(162), _s(287),_s(168)], fill=WHITE_HL)
        # Warm blush
        blush_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blush_layer)
        bd.ellipse([_s(202),_s(175), _s(226),_s(187)], fill=BLUSH_HEAVY)
        bd.ellipse([_s(288),_s(175), _s(312),_s(187)], fill=BLUSH_HEAVY)
        blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(radius=_s(2)))
        img = Image.alpha_composite(img, blush_layer)
        d = ImageDraw.Draw(img)
        # Warm gentle smile with teeth hint
        mouth_pts = [(_s(240),_s(198)), (_s(254),_s(208)), (_s(268),_s(198))]
        d.polygon(mouth_pts, fill=WARM_LIP)
        d.line([(_s(240),_s(198)), (_s(254),_s(208)), (_s(268),_s(198))], fill=OUTLINE, width=_s(2.0))
        d.line([(_s(240),_s(198)), (_s(268),_s(198))], fill=OUTLINE, width=_s(2.2))
        d.rectangle([_s(251),_s(199), _s(257),_s(201)], fill=WHITE_HL)

    # Downscale with LANCZOS anti-aliasing
    return img.resize((512, 512), Image.LANCZOS)


def build_all():
    print("=" * 70)
    print("MELI EXPRESSION OVERLAY BUILDER v3")
    print("Skin-matched colors - 2x supersampled AA - Canonical 512px coordinates")
    print("=" * 70)

    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    COMPOSITE_DIR.mkdir(parents=True, exist_ok=True)
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)

    if not BASE_SPRITE.exists():
        print(f"[FATAL] Base sprite not found: {BASE_SPRITE}")
        sys.exit(1)

    base_img = Image.open(BASE_SPRITE).convert("RGBA")
    assert base_img.size == (512, 512), f"Base must be 512x512, got {base_img.size}"

    svg_overlays = _make_svg_overlays()
    composites = {}

    # Step 1: Write SVG files
    print("\n[Step 1] Writing 12 SVG overlays...")
    for name in EXPRESSION_ORDER:
        svg_path = OVERLAY_DIR / f"{name}.svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_overlays[name].strip())
        print(f"  [OK] {svg_path.name}")

    # Step 2: Render overlays via PIL (2x supersampled) + composite onto base
    print("\n[Step 2] Rendering overlays (2x AA) and compositing...")
    base_arr = np.array(base_img)

    for name in EXPRESSION_ORDER:
        overlay = _render_overlay_pil(name)

        comp = base_img.copy()
        comp = Image.alpha_composite(comp, overlay)

        comp_path = COMPOSITE_DIR / f"{name}.png"
        comp.save(comp_path, format="PNG")
        composites[name] = comp

        # Compute delta
        comp_arr = np.array(comp)
        changed = np.sum(np.any(np.abs(comp_arr.astype(int) - base_arr.astype(int)) > 2, axis=2))
        pct = changed / (512 * 512) * 100

        print(f"  [OK] {name:12s} -> {comp_path.name}  (Delta = {pct:.2f}%, {changed} px)")

    # Step 3: Contact sheet v3
    print("\n[Step 3] Building contact sheet v3...")
    cols, rows = 4, 3
    cell = 512
    pad = 20
    label_h = 40
    sheet_w = cols * cell + (cols + 1) * pad
    sheet_h = rows * (cell + label_h) + (rows + 1) * pad

    sheet = Image.new("RGBA", (sheet_w, sheet_h), (18, 18, 28, 255))
    sd = ImageDraw.Draw(sheet)

    for idx, name in enumerate(EXPRESSION_ORDER):
        r, c = divmod(idx, cols)
        x = pad + c * (cell + pad)
        y = pad + r * (cell + label_h + pad)

        # Checkerboard
        for cy in range(y, y + cell, 32):
            for cx in range(x, x + cell, 32):
                checker = ((cx - x) // 32 + (cy - y) // 32) % 2
                fill = (35, 35, 50, 255) if checker == 0 else (25, 25, 38, 255)
                sd.rectangle([cx, cy, cx + 31, cy + 31], fill=fill)

        sheet.paste(composites[name], (x, y), composites[name])
        sd.rectangle([x - 1, y - 1, x + cell, y + cell], outline=(255, 120, 160, 200), width=2)

        label = f"{idx + 1:02d} {name.upper()}"
        sd.rectangle([x, y + cell + 4, x + cell, y + cell + label_h], fill=(12, 12, 20, 230))
        sd.text((x + 10, y + cell + 12), label, fill=(255, 210, 230, 255))

    sheet_path = SHEETS_DIR / "meli_expression_contact_sheet_v3.png"
    sheet.save(sheet_path, format="PNG")
    print(f"\n  [OK] Contact sheet: {sheet_path} ({sheet_w}x{sheet_h})")

    print("\n" + "=" * 70)
    print("BUILD COMPLETE - 12 SVGs + 12 Composites + Contact Sheet v3")
    print("=" * 70)


if __name__ == "__main__":
    build_all()
