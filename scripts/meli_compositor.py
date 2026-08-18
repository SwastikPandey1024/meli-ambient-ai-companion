#!/usr/bin/env python3
"""
meli_compositor.py — Canonical Meli Expression Pipeline v4

ROOT CAUSE FIX:
    Previous pipeline placed overlays at Y~138-216, which is the hoodie/chest area.
    Actual face coordinates: Y=65-155, X=210-310 (pixel-verified).

CANONICAL COORDINATE CONTRACT (512x512 canvas):
    Face region:    X=210..310, Y=65..155
    Left eye:       X=234, Y=108
    Right eye:      X=279, Y=108
    Gaze anchor:    X=256, Y=108
    Brow line:      Y=88
    Mouth center:   X=256, Y=143
    Blush centers:  L(220,130), R(292,130)

PIPELINE:
    1. Render each expression overlay to transparent 512x512 RGBA PNG (2x supersampled)
    2. Validate: all overlay pixels must be inside approved face zone
    3. alpha_composite(base, overlay) -> composite PNG
    4. Validate: outside face region must be identical to base
    5. Save composites, overlays, contact sheets, QA report
"""

import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_SPRITE   = Path("assets/meli/character/meli_body_base.png")
OVERLAY_DIR   = Path("assets/meli/character/overlays")
COMPOSITE_DIR = Path("assets/meli/character/composites")
SHEETS_DIR    = Path("assets/meli/sheets")
QA_DIR        = Path("assets/meli/qa")

# CORRECTED face coordinates (pixel-sampled from meli_body_base.png)
FACE_MIN_X, FACE_MAX_X = 210, 310
FACE_MIN_Y, FACE_MAX_Y = 65,  155

# Key anchors
LEFT_EYE_X,  LEFT_EYE_Y  = 234, 108
RIGHT_EYE_X, RIGHT_EYE_Y = 279, 108
BROW_Y  = 88
MOUTH_Y = 143
BLUSH_LX, BLUSH_RX, BLUSH_Y = 220, 292, 130

# Approved zone with antialiasing tolerance
APX0, APX1 = FACE_MIN_X - 12, FACE_MAX_X + 12   # 198, 322
APY0, APY1 = FACE_MIN_Y -  8, FACE_MAX_Y +  8   #  57, 163

# Color tokens (sampled from base sprite)
SKIN        = (202, 136, 131, 255)
SKIN_DARK   = (192, 126, 121, 255)
OUTLINE     = ( 30,  20,  32, 255)
BROW        = ( 42,  30,  38, 255)
WHITE_HL    = (255, 255, 255, 255)
WARM_LIP    = (163,  69,  88, 255)
HAPPY_LIP   = (184,  77,  96, 255)
GOLD        = (255, 217, 106, 255)
CYAN_SWEAT  = (112, 214, 255, 240)
BLUSH_SOFT  = (210,  90, 120,  90)
BLUSH_HEAVY = (220,  80, 110, 130)
LID_CREASE  = (138,  96, 104, 165)

RENDER_SCALE = 2

EXPRESSION_ORDER = [
    "idle", "curious", "hover", "happy", "blink", "sleepy",
    "thinking", "focused", "confused", "error", "complete", "greeting"
]


def _s(v):
    return int(round(v * RENDER_SCALE))


def _blush_layer(sz, lx, rx, y, rw=14, rh=7, color=None):
    if color is None:
        color = BLUSH_SOFT
    bl = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bl)
    bd.ellipse([_s(lx-rw), _s(y-rh), _s(lx+rw), _s(y+rh)], fill=color)
    bd.ellipse([_s(rx-rw), _s(y-rh), _s(rx+rw), _s(y+rh)], fill=color)
    blurred = bl.filter(ImageFilter.GaussianBlur(radius=_s(2.5)))
    # Clip blur halo strictly to approved face zone (prevent bleeding into transparent/body pixels)
    clipped = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    crop_box = (_s(APX0), _s(APY0), _s(APX1), _s(APY1))
    clipped.paste(blurred.crop(crop_box), (_s(APX0), _s(APY0)))
    return clipped


def render_overlay(name):
    sz = 512 * RENDER_SCALE
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def composite_blush(lx, rx, y, rw=14, rh=7, color=None):
        nonlocal img, d
        img = Image.alpha_composite(img, _blush_layer(sz, lx, rx, y, rw, rh, color))
        d = ImageDraw.Draw(img)

    if name == "idle":
        pass  # base face IS the idle expression

    elif name == "curious":
        d.line([_s(218),_s(90),_s(232),_s(82),_s(246),_s(88)], fill=BROW, width=_s(3))
        d.line([_s(264),_s(88),_s(278),_s(82),_s(296),_s(90)], fill=BROW, width=_s(3))
        d.ellipse([_s(225),_s(103),_s(232),_s(110)], fill=WHITE_HL)
        d.ellipse([_s(279),_s(102),_s(286),_s(109)], fill=WHITE_HL)
        d.ellipse([_s(249),_s(135),_s(263),_s(151)], fill=WARM_LIP, outline=OUTLINE, width=_s(2))
        pts = [(_s(296),_s(75)),(_s(299),_s(69)),(_s(302),_s(75)),(_s(308),_s(77)),
               (_s(302),_s(79)),(_s(299),_s(85)),(_s(296),_s(79)),(_s(290),_s(77))]
        d.polygon(pts, fill=GOLD)
        d.ellipse([_s(297),_s(76),_s(301),_s(78)], fill=WHITE_HL)

    elif name == "hover":
        d.line([_s(218),_s(89),_s(232),_s(82),_s(247),_s(89)], fill=BROW, width=_s(2))
        d.line([_s(265),_s(91),_s(278),_s(86),_s(296),_s(90)], fill=BROW, width=_s(2))
        d.ellipse([_s(235),_s(104),_s(241),_s(110)], fill=WHITE_HL)
        d.ellipse([_s(283),_s(103),_s(289),_s(109)], fill=WHITE_HL)
        composite_blush(BLUSH_LX, BLUSH_RX, BLUSH_Y, 14, 7, BLUSH_SOFT)
        d.line([_s(242),_s(141),_s(250),_s(137),_s(256),_s(141),
                _s(262),_s(144),_s(268),_s(139)], fill=OUTLINE, width=_s(2))

    elif name == "happy":
        # Cover eye sockets only (Y=105..122) -- avoids painting over hair above
        d.ellipse([_s(218),_s(105),_s(250),_s(122)], fill=SKIN)
        d.ellipse([_s(263),_s(105),_s(295),_s(122)], fill=SKIN)
        # Crescent eye curves (^_^)
        d.line([_s(218),_s(115),_s(234),_s(104),_s(250),_s(115)], fill=OUTLINE, width=_s(4))
        d.line([_s(263),_s(115),_s(279),_s(104),_s(295),_s(115)], fill=OUTLINE, width=_s(4))
        d.line([_s(248),_s(113),_s(254),_s(109)], fill=OUTLINE, width=_s(2))
        d.line([_s(292),_s(113),_s(298),_s(109)], fill=OUTLINE, width=_s(2))
        # Raised happy brows
        d.line([_s(218),_s(86),_s(234),_s(80),_s(250),_s(86)], fill=BROW, width=_s(2))
        d.line([_s(263),_s(86),_s(278),_s(80),_s(296),_s(86)], fill=BROW, width=_s(2))
        composite_blush(216, 295, 128, 16, 9, BLUSH_HEAVY)
        d.line([_s(208),_s(134),_s(216),_s(126)], fill=(216,88,116,180), width=_s(2))
        d.line([_s(298),_s(134),_s(306),_s(126)], fill=(216,88,116,180), width=_s(2))
        d.polygon([(_s(240),_s(141)),(_s(256),_s(156)),(_s(272),_s(141))], fill=HAPPY_LIP)
        d.line([_s(240),_s(141),_s(272),_s(141)], fill=OUTLINE, width=_s(2))
        d.rectangle([_s(251),_s(142),_s(261),_s(146)], fill=WHITE_HL)

    elif name == "blink":
        # Cover eye sockets only (Y=105..122)
        d.ellipse([_s(218),_s(105),_s(250),_s(122)], fill=SKIN)
        d.ellipse([_s(263),_s(105),_s(295),_s(122)], fill=SKIN)
        # Closed eyelid curves
        d.line([_s(218),_s(112),_s(234),_s(118),_s(250),_s(112)], fill=OUTLINE, width=_s(3))
        d.line([_s(263),_s(112),_s(279),_s(118),_s(295),_s(112)], fill=OUTLINE, width=_s(3))
        # Lid crease (upper lid detail)
        d.line([_s(220),_s(107),_s(234),_s(104),_s(248),_s(107)], fill=LID_CREASE, width=_s(1))
        d.line([_s(265),_s(107),_s(279),_s(104),_s(293),_s(107)], fill=LID_CREASE, width=_s(1))

    elif name == "sleepy":
        # Heavy drooping upper lids (start at Y=104 = upper eye socket)
        d.rectangle([_s(218),_s(104),_s(252),_s(115)], fill=SKIN_DARK)
        d.rectangle([_s(263),_s(104),_s(297),_s(115)], fill=SKIN_DARK)
        # Drooping lid lines
        d.line([_s(218),_s(114),_s(234),_s(119),_s(250),_s(114)], fill=OUTLINE, width=_s(3))
        d.line([_s(263),_s(114),_s(279),_s(119),_s(295),_s(114)], fill=OUTLINE, width=_s(3))
        # Relaxed low brows
        d.line([_s(220),_s(92),_s(234),_s(90),_s(248),_s(94)], fill=BROW, width=_s(2))
        d.line([_s(265),_s(94),_s(279),_s(90),_s(296),_s(92)], fill=BROW, width=_s(2))
        composite_blush(218, 292, 126, 12, 6, BLUSH_SOFT)
        d.ellipse([_s(251),_s(139),_s(261),_s(148)], fill=WARM_LIP, outline=OUTLINE, width=_s(2))

    elif name == "thinking":
        d.line([_s(218),_s(84),_s(232),_s(78),_s(246),_s(86)], fill=BROW, width=_s(3))
        d.line([_s(264),_s(92),_s(278),_s(89),_s(296),_s(91)], fill=BROW, width=_s(3))
        d.ellipse([_s(234),_s(101),_s(241),_s(108)], fill=WHITE_HL)
        d.ellipse([_s(283),_s(100),_s(290),_s(107)], fill=WHITE_HL)
        composite_blush(218, 292, 128, 10, 5, BLUSH_SOFT)
        d.line([_s(246),_s(143),_s(264),_s(143)], fill=OUTLINE, width=_s(3))

    elif name == "focused":
        # Narrowed slit eyes -- skin cover starts at Y=104 (eye socket)
        d.rectangle([_s(218),_s(104),_s(252),_s(114)], fill=SKIN_DARK)
        d.rectangle([_s(263),_s(104),_s(297),_s(114)], fill=SKIN_DARK)
        # Sharp horizontal slit lines
        d.line([_s(218),_s(113),_s(252),_s(113)], fill=OUTLINE, width=_s(3))
        d.line([_s(263),_s(113),_s(297),_s(113)], fill=OUTLINE, width=_s(3))
        # Intense inward-angled brows
        d.line([_s(220),_s(91),_s(234),_s(94),_s(248),_s(88)], fill=BROW, width=_s(3))
        d.line([_s(265),_s(88),_s(278),_s(94),_s(296),_s(91)], fill=BROW, width=_s(3))
        # Firm neutral mouth
        d.line([_s(245),_s(143),_s(267),_s(143)], fill=OUTLINE, width=_s(3))

    elif name == "confused":
        d.line([_s(218),_s(82),_s(232),_s(76),_s(246),_s(84)], fill=BROW, width=_s(3))
        d.line([_s(264),_s(93),_s(278),_s(91),_s(296),_s(97)], fill=BROW, width=_s(3))
        d.ellipse([_s(229),_s(102),_s(236),_s(109)], fill=WHITE_HL)
        d.ellipse([_s(281),_s(107),_s(285),_s(111)], fill=WHITE_HL)
        d.rectangle([_s(264),_s(102),_s(296),_s(106)], fill=(*SKIN_DARK[:3], 180))
        composite_blush(218, 292, 128, 10, 5, BLUSH_SOFT)
        d.line([_s(243),_s(144),_s(250),_s(138),_s(258),_s(145),
                _s(264),_s(140),_s(271),_s(140)], fill=OUTLINE, width=_s(2))

    elif name == "error":
        d.line([_s(222),_s(96),_s(234),_s(86),_s(248),_s(84)], fill=BROW, width=_s(3))
        d.line([_s(264),_s(84),_s(278),_s(86),_s(296),_s(96)], fill=BROW, width=_s(3))
        d.ellipse([_s(232),_s(112),_s(236),_s(116)], fill=WHITE_HL)
        d.ellipse([_s(277),_s(112),_s(281),_s(116)], fill=WHITE_HL)
        composite_blush(218, 292, 128, 12, 6, BLUSH_SOFT)
        d.ellipse([_s(302),_s(77),_s(310),_s(86)], fill=CYAN_SWEAT)
        d.polygon([(_s(306),_s(67)),(_s(302),_s(78)),(_s(310),_s(78))], fill=CYAN_SWEAT)
        d.ellipse([_s(303),_s(74),_s(307),_s(78)], fill=WHITE_HL)
        d.line([_s(241),_s(143),_s(248),_s(138),_s(255),_s(144),
                _s(262),_s(139),_s(269),_s(142)], fill=OUTLINE, width=_s(2))

    elif name == "complete":
        d.line([_s(218),_s(86),_s(232),_s(80),_s(248),_s(84)], fill=BROW, width=_s(2))
        d.line([_s(263),_s(84),_s(278),_s(80),_s(296),_s(86)], fill=BROW, width=_s(2))
        d.ellipse([_s(228),_s(103),_s(237),_s(112)], fill=WHITE_HL)
        d.ellipse([_s(233),_s(109),_s(237),_s(113)], fill=WHITE_HL)
        d.ellipse([_s(277),_s(102),_s(286),_s(111)], fill=WHITE_HL)
        d.ellipse([_s(282),_s(108),_s(286),_s(112)], fill=WHITE_HL)
        composite_blush(215, 295, 128, 15, 9, BLUSH_HEAVY)
        d.line([_s(210),_s(133),_s(218),_s(125)], fill=(216,88,116,180), width=_s(2))
        d.line([_s(299),_s(133),_s(307),_s(125)], fill=(216,88,116,180), width=_s(2))
        pts = [(_s(296),_s(74)),(_s(299),_s(68)),(_s(302),_s(74)),(_s(308),_s(76)),
               (_s(302),_s(78)),(_s(299),_s(84)),(_s(296),_s(78)),(_s(290),_s(76))]
        d.polygon(pts, fill=GOLD)
        d.ellipse([_s(297),_s(75),_s(301),_s(77)], fill=WHITE_HL)
        d.polygon([(_s(238),_s(141)),(_s(256),_s(158)),(_s(274),_s(141))], fill=HAPPY_LIP)
        d.line([_s(238),_s(141),_s(274),_s(141)], fill=OUTLINE, width=_s(2))
        d.rectangle([_s(250),_s(142),_s(262),_s(147)], fill=WHITE_HL)

    elif name == "greeting":
        d.line([_s(218),_s(87),_s(232),_s(81),_s(248),_s(87)], fill=BROW, width=_s(2))
        d.line([_s(263),_s(87),_s(278),_s(81),_s(296),_s(87)], fill=BROW, width=_s(2))
        d.ellipse([_s(231),_s(105),_s(238),_s(112)], fill=WHITE_HL)
        d.ellipse([_s(277),_s(104),_s(284),_s(111)], fill=WHITE_HL)
        composite_blush(215, 295, 128, 15, 8, (220, 80, 110, 135))
        d.polygon([(_s(241),_s(140)),(_s(256),_s(152)),(_s(271),_s(140))], fill=WARM_LIP)
        d.line([_s(241),_s(140),_s(271),_s(140)], fill=OUTLINE, width=_s(2))
        d.rectangle([_s(252),_s(141),_s(259),_s(144)], fill=WHITE_HL)

    return img.resize((512, 512), Image.LANCZOS)


def checkerboard(w, h, cell=16):
    cb = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(cb)
    for cy in range(0, h, cell):
        for cx in range(0, w, cell):
            c = 200 if ((cx // cell + cy // cell) % 2 == 0) else 160
            d.rectangle([cx, cy, cx+cell-1, cy+cell-1], fill=(c,c,c,255))
    return cb


def build_all():
    print("=" * 72)
    print("MELI EXPRESSION PIPELINE v4 -- CORRECTED COORDINATES")
    print("Face: X=210..310, Y=65..155  Eye L:(234,108) R:(279,108)")
    print("=" * 72)

    for p in [OVERLAY_DIR, COMPOSITE_DIR, SHEETS_DIR, QA_DIR]:
        p.mkdir(parents=True, exist_ok=True)

    if not BASE_SPRITE.exists():
        print(f"[FATAL] {BASE_SPRITE} not found"); sys.exit(1)

    base = Image.open(BASE_SPRITE).convert("RGBA")
    assert base.size == (512, 512), f"Base must be 512x512, got {base.size}"
    base_arr = np.array(base)
    print(f"[OK] Base: {BASE_SPRITE}")

    face_mask = np.zeros((512, 512), dtype=bool)
    face_mask[APY0:APY1, APX0:APX1] = True
    body_mask = ~face_mask

    overlay_imgs   = {}
    composite_imgs = {}
    qa_results     = {}

    print("\n[Step 1] Rendering overlays + compositing...")
    for name in EXPRESSION_ORDER:
        ov = render_overlay(name)
        overlay_imgs[name] = ov
        ov.save(OVERLAY_DIR / f"meli_expr_{name}_overlay.png", format="PNG")

        comp = Image.alpha_composite(base.copy(), ov)
        composite_imgs[name] = comp
        comp.save(COMPOSITE_DIR / f"meli_expr_{name}.png", format="PNG")

        comp_arr = np.array(comp)
        ov_arr   = np.array(ov)
        diff     = np.abs(comp_arr.astype(int) - base_arr.astype(int))
        pxdiff   = np.any(diff > 2, axis=2)

        body_changed  = int(np.sum(pxdiff & body_mask))
        face_changed  = int(np.sum(pxdiff & face_mask))
        total_changed = int(np.sum(pxdiff))
        ov_px = int(np.sum(ov_arr[:,:,3] > 10))

        body_mean_diff = float(np.mean(np.abs(
            comp_arr[body_mask].astype(float) - base_arr[body_mask].astype(float))))
        body_sim = 100.0 - body_mean_diff / 255.0 * 100.0

        face_region_diff = diff[APY0:APY1, APX0:APX1]
        face_mad = float(np.mean(face_region_diff) / 255.0 * 100.0)
        face_ratio = (face_changed / total_changed * 100.0) if total_changed > 0 else 100.0

        failures = []
        if body_changed > 0:
            failures.append(f"BODY DRIFT: {body_changed}px outside approved face zone")
        if name != "idle" and total_changed == 0:
            failures.append("No pixels changed -- expression not rendering")
        if name != "idle" and ov_px < 50:
            failures.append(f"Too few overlay pixels: {ov_px}")

        status = "PASS" if not failures else "FAIL"
        qa_results[name] = {
            "status": status, "failures": failures,
            "body_changed_px": body_changed, "face_changed_px": face_changed,
            "total_changed_px": total_changed, "overlay_alpha_px": ov_px,
            "body_similarity_pct": round(body_sim, 4),
            "face_mad_pct": round(face_mad, 3),
            "face_ratio_pct": round(face_ratio, 1),
        }
        mark = "PASS" if status == "PASS" else "FAIL"
        print(f"  [{mark}] {name:12s} | body_sim={body_sim:.4f}% | face_mad={face_mad:.2f}% "
              f"| face_ratio={face_ratio:.1f}% | dPx={total_changed} | ovPx={ov_px}")
        for f in failures:
            print(f"    [!] {f}")

    print("\n[Step 2] Pairwise distinctness check...")
    pairwise = {}
    all_ok = True
    for i, na in enumerate(EXPRESSION_ORDER):
        for j in range(i+1, len(EXPRESSION_ORDER)):
            nb = EXPRESSION_ORDER[j]
            fa = np.array(composite_imgs[na])[APY0:APY1, APX0:APX1].astype(float)
            fb = np.array(composite_imgs[nb])[APY0:APY1, APX0:APX1].astype(float)
            diff = float(np.mean(np.abs(fa - fb)) / 255.0 * 100.0)
            pairwise[f"{na}_vs_{nb}"] = round(diff, 4)
            if diff < 0.10:
                print(f"  [WARN] Near-duplicate: {na} vs {nb} ({diff:.3f}%)")
                all_ok = False
    if all_ok:
        print(f"  [OK] All {len(EXPRESSION_ORDER)*(len(EXPRESSION_ORDER)-1)//2} pairs distinct.")

    # Contact sheets
    print("\n[Step 3] Generating contact sheets...")
    cols, rows, cell, pad, lblh = 4, 3, 256, 16, 32
    sw = cols * cell + (cols+1)*pad
    sh = rows * (cell+lblh) + (rows+1)*pad
    font = ImageFont.load_default()

    def make_sheet(imgs_dict, title_suffix, border_color, label_color):
        sht = Image.new("RGBA", (sw, sh), (15, 12, 22, 255))
        sd = ImageDraw.Draw(sht)
        for idx, name in enumerate(EXPRESSION_ORDER):
            r, c = divmod(idx, cols)
            x = pad + c*(cell+pad)
            y = pad + r*(cell+lblh+pad)
            cb = checkerboard(cell, cell)
            thumb = imgs_dict[name].resize((cell, cell), Image.LANCZOS)
            cb.paste(thumb, mask=thumb)
            sht.paste(cb, (x, y))
            sd.rectangle([x-1, y-1, x+cell, y+cell], outline=border_color, width=1)
            sd.rectangle([x, y+cell+2, x+cell, y+cell+lblh], fill=(12,10,20,220))
            sd.text((x+8, y+cell+8), f"{idx+1:02d} {name.upper()}{title_suffix}",
                    fill=label_color, font=font)
        return sht

    comp_sheet = make_sheet(composite_imgs, "", (255,120,160,180), (255,200,230,255))
    comp_sheet.save(SHEETS_DIR / "meli_expression_contact_sheet_final.png")
    ov_sheet = make_sheet(overlay_imgs, " [OV]", (120,200,255,180), (180,230,255,255))
    ov_sheet.save(SHEETS_DIR / "meli_expression_overlay_contact_sheet.png")
    print("  [OK] Contact sheets saved.")

    overall_pass = all(r["status"] == "PASS" for r in qa_results.values())
    report = {
        "suite": "Meli Expression Pipeline v4",
        "version": "4.0.0",
        "root_cause_fix": "Previous pipeline overlays were at Y=138-216 (hoodie). Corrected to Y=65-155 (face).",
        "coordinate_contract": {
            "canvas": [512, 512],
            "approved_face_bbox": [APX0, APY0, APX1, APY1],
            "left_eye": [LEFT_EYE_X, LEFT_EYE_Y],
            "right_eye": [RIGHT_EYE_X, RIGHT_EYE_Y],
            "brow_y": BROW_Y, "mouth_y": MOUTH_Y, "blush_y": BLUSH_Y,
        },
        "overall_status": "PASS" if overall_pass else "FAIL",
        "expressions": qa_results,
        "pairwise": pairwise,
    }
    (QA_DIR / "expression_qa_report_v4.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    print(f"\n{'='*72}")
    print(f"COMPLETE -- Overall: {report['overall_status']}")
    print(f"  Overlays:   {OVERLAY_DIR}")
    print(f"  Composites: {COMPOSITE_DIR}")
    print(f"  Sheets:     {SHEETS_DIR}")
    print(f"  QA Report:  {QA_DIR / 'expression_qa_report_v4.json'}")
    print(f"{'='*72}")

    if not overall_pass:
        sys.exit(1)


if __name__ == "__main__":
    build_all()