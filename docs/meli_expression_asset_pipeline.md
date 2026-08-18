# Meli 2D Expression Asset Pipeline & QA Specification

## 1. Overview

This document specifies the authoritative 2D expression sprite pipeline for the **Meli Ambient AI Desktop Companion**.
All sprites are derived strictly from the canonical reference (`design/meli_canonical_character_sheet2.png` and `assets/meli/character/meli_body_base.png`).

---

## 2. Global Spatial Geometry & Anchors (512x512 Canvas)

| Anchor Name | Coordinate $(X, Y)$ | Normalized % | Description |
| :--- | :--- | :--- | :--- |
| **Gaze Anchor** | $(256, 168)$ | $(50.00\%, 32.81\%)$ | Eye & pupil tracking center origin |
| **Signal Heart Anchor** | $(259.42, 184.55)$ | $(50.67\%, 36.04\%)$ | Chest-mounted ambient light & particle emitter |
| **Grounding Anchor** | $(256, 496)$ | $(50.00\%, 96.88\%)$ | Baseline contact footprint for snapping & SINK/POP |
| **Bounding Box** | $[16, 16, 496, 496]$ | — | $480 \times 480$ px active bounding box (16px margin) |

---

## 3. Production Expression Matrix (12 Sprites)

| Filename | Mood / Event State | Visual Description |
| :--- | :--- | :--- |
| **`meli_expr_idle.png`** | `IDLE` | Calm observant eyes, relaxed brows, neutral mouth |
| **`meli_expr_curious.png`** | `MEMORY_RETRIEVED` | Slightly widened eyes, raised inner brow, subtle sparkle |
| **`meli_expr_hover.png`** | `HOVER` | Attentive gaze toward pointer, slight head tilt feel |
| **`meli_expr_happy.png`** | `RESPONSE_COMPLETED` | Crescent smiling eyes, warm smile, subtle cheek blush |
| **`meli_expr_blink.png`** | Micro-Blink | Gently closed eyelids, relaxed calm brows |
| **`meli_expr_sleepy.png`** | Inactive Idle | Half-closed heavy eyelids, relaxed mouth, soft blush |
| **`meli_expr_thinking.png`** | `THINKING` | Gaze slightly upward/lateral, analytical concentration |
| **`meli_expr_focused.png`** | `TOOL_STARTED` | Narrowed calm eyes, concentrated brows, small mouth |
| **`meli_expr_confused.png`** | Disambiguation | Asymmetric brows, slight questioning mouth |
| **`meli_expr_error.png`** | `ERROR` | Concerned downward gaze, apologetic expression, sweat drop |
| **`meli_expr_complete.png`** | Success Finish | Bright joyful eyes, confident gentle smile, success sparkle |
| **`meli_expr_greeting.png`** | Onboarding / Wake | Welcoming direct eye contact, soft smile, friendly gaze |

---

## 4. 14-Point Automated QA Protocol

Every sprite generated must pass `scripts/validate_meli_sprite.py`:
1. **Dimensions**: Exact $512 \times 512$ runtime format.
2. **Format**: 32-bit RGBA (8 bits per channel + 8-bit alpha).
3. **Color Space**: sRGB compliant.
4. **Alpha Integrity**: 100% transparent corners $(0,0), (512,0), (0,512), (512,512)$.
5. **Alpha Coverage**: Character coverage between $15\%$ and $45\%$ of total canvas area.
6. **Safety Margins**: At least 16px safety margin from canvas outer boundary.
7. **Grounding Alignment**: Character baseline strictly contacts $Y=496 \pm 4$px.
8. **Signal Heart Centroid**: Chest anchor aligned at $X=259.4, Y=184.6$ (derived from hoodie geometry).
9. **Zero Body Drift**: Body, hoodie, and feet pixels are 100% bit-identical across all 12 expression variants.
10. **Zero Fringing**: Straight alpha transparency without white/black halo artifacts.
11. **No Artifacts**: Zero unintended text, watermarks, frame borders, or bounding lines.
12. **Coordinate Stability**: SINK/POP transforms apply uniformly without sprite shearing.
13. **Layer Compositing**: Seamlessly composites with Glasses Accessory and Signal Heart overlays.
14. **Contact Sheet Verified**: All 13 canonical targets present in `assets/meli/sheets/meli_expression_contact_sheet.png`.
