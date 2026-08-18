# Meli 2D Character Sprite Production Specification

This document defines the complete technical, artistic, and quality assurance specification for producing the 2D production sprites for **Meli — Ambient AI Companion**.

---

## 1. Canonical Visual Authority

- **Single Visual Source of Truth**:
  ```
  design/meli_canonical_character_sheet2.png
  ```
- **Turnaround & Baseline Geometry Reference**:
  ```
  design/meli_canonical_character_sheet.png
  ```

All sprite layers, base bodies, and expression variants must strictly adhere to the frozen visual design defined in `design/meli_canonical_character_sheet2.png`. Under no circumstances may Meli be redesigned, re-imagined, or stylistically deviated.

---

## 2. Technical Asset Contract & Spatial Geometry

### 2.1 Resolution & Viewports
| Property | Master Artwork Specification | Runtime Display Target |
| :--- | :--- | :--- |
| **Canvas Dimensions** | **768 × 768 px** (High-DPI Master) | **512 × 512 px** (Standard Reference) |
| **Display Viewport Scale** | 240px – 320px | 120px – 160px companion window |
| **Perimeter Safety Margin** | **24 px** inset | **16 px** inset |
| **Active Art Bounding Box** | `[24, 24, 744, 744]` (720 × 720 px) | `[16, 16, 496, 496]` (480 × 480 px) |

### 2.2 Canonical Pixel Anchors (512 × 512 Reference Frame)
1. **Eye / Gaze Anchor**: $\mathbf{(256, 168)}$
   - Exact spatial centroid of Meli's eyes for procedural gaze tracking, pupil parallax, and micro-tilt transforms ($\le \pm 2.0^\circ$).
2. **Signal Heart Centroid Anchor**: $\mathbf{(256, 294)}$
   - Geometric center for dynamic SVG ambient light overlays, ripple effects, and telemetry glows.
3. **Grounding Footprint Anchor**: $\mathbf{(256, 496)}$
   - Sole contact baseline for desktop surface snapping, taskbar resting, and physics grounding.
4. **Perimeter Safety Inset**: $\mathbf{16\text{px}}$
   - Guarantees $16\text{px}$ transparent margin around the character silhouette to prevent anti-aliasing clipping during procedural breathing ($\le 2\text{px}$) and procedural motion envelope translations ($\le 4\text{px}$).

```
       0                    256                  512
     0 +---------------------+---------------------+
       |   16px Safety Margin Box                  |
       |     +-----------------------------------+ |
       |     |                                   | |
   168 |     |        ⚓ EYE / GAZE [256, 168]    | |
       |     |                                   | |
   294 |     |        💗 SIGNAL HEART [256, 294] | |
       |     |                                   | |
   496 |     |        ⚓ GROUNDING [256, 496]     | |
       |     +-----------------------------------+ |
   512 +---------------------+---------------------+
```

### 2.3 Format & Color Profile
- **File Format**: **32-bit RGBA PNG** (lossless/near-lossless WebP runtime alternative supported).
- **Color Space**: Strictly **sRGB IEC61966-2.1** (embedded or standardized sRGB chunk).
- **Alpha Channel**: True 8-bit straight alpha transparency (zero alpha on canvas exterior; 255 alpha on solid fills).
- **Prohibited Artifacts**:
  - No white backgrounds or colored card backings.
  - No baked checkerboards or simulated transparency patterns.
  - No borders, bounding boxes, watermarks, labels, UI elements, or text.
  - No drop shadows cast outside the character silhouette.
  - No white halos or dirty edge fringe against dark (`#171824`) and transparent backgrounds.

---

## 3. Character Invariants & Identity Preservation

Every sprite generated in the pipeline must strictly preserve:
- **Demographic & Persona**: **"Young Adult — 18+"**; observant, gentle, quiet, intelligent, and endearingly awkward companion.
- **Face & Eye Geometry**: Soft oval jawline, almond-shaped eye contour, dark coral irises with clean white circular glints, subtle cheek micro-blush.
- **Hair System**: Medium-length layered cut in dusty-rose / muted coral-pink (`#FFB6C1`) with parted bangs, layered tips, and signature Signal Clip accessory.
- **Hoodie & Attire**: Oversized deep charcoal cotton hoodie (`#171824`) with relaxed dropped shoulders, elongated sleeves, and soft blush drawstrings (`#FFD6E7`).
- **Signal Heart**: Centered chest light aperture at `(256, 294)`.
- **Lower Body & Footwear**: Cozy dark skirt/shorts, stockings, and low-profile minimal sneakers in matte charcoal with clean rose accent piping.
- **Proportions**: Petite Young Adult companion proportions with full body visible from head to sneaker soles.

---

## 4. Production Asset Roster

The pipeline targets 13 distinct modular sprite files stored in `assets/meli/character/`:

| # | File Name | Layer Type | Description |
| :--- | :--- | :--- | :--- |
| **1** | `meli_body_base.png` | **Base Layer** | Full-body standing neutral pose with complete outfit, hair, sneakers, and Signal Heart. |
| **2** | `meli_expr_idle.png` | Expression Overlay | Default Standby (Neutral almond gaze, calm micro-expression). |
| **3** | `meli_expr_curious.png` | Expression Overlay | Window Switch / Inquisitive (Widened pupils, raised brows, open micro-smile). |
| **4** | `meli_expr_hover.png` | Expression Overlay | Pointer Hover Contact (Attentive focus, anticipatory soft gaze). |
| **5** | `meli_expr_happy.png` | Expression Overlay | Pet / Click Interaction (Crescent smiling squint, rosy cheek micro-blush). |
| **6** | `meli_expr_blink.png` | Expression Overlay | Periodic Micro-Blink (Fully closed relaxed eyelids). |
| **7** | `meli_expr_sleepy.png` | Expression Overlay | Desktop Idle / Night Rest (Drooping heavy lids, relaxed facial posture). |
| **8** | `meli_expr_thinking.png` | Expression Overlay | LLM Processing (Upward/lateral analytical gaze, focused analytical mouth line). |
| **9** | `meli_expr_focused.png` | Expression Overlay | Deep Work Flow (Calm narrowed intensity, steady focus, motionless anchor). |
| **10** | `meli_expr_confused.png` | Expression Overlay | Ambiguous Query (Asymmetrical brows, questioning gaze, inquisitive micro-tilt $\le 2^\circ$). |
| **11** | `meli_expr_error.png` | Expression Overlay | Tool Exception / Alert (Concerned downward gaze, apologetic brow slope, gentle blush). |
| **12** | `meli_expr_complete.png` | Expression Overlay | Task Resolved / Success (Sparkling joyful eye glints, radiant smile). |
| **13** | `meli_expr_greeting.png` | Expression Overlay | App Launch / Wake (Welcoming direct eye contact, friendly micro-nod). |

---

## 5. Base Sprite Requirements (`meli_body_base.png`)

`assets/meli/character/meli_body_base.png` serves as the foundational **master anchor sprite** for the entire runtime engine:
1. **Pose**: Neutral standing posture, relaxed dropped shoulders, natural front-facing orthographic perspective.
2. **Full Body Visibility**: Complete character from crown of hair down to sneaker soles resting at Grounding coordinate $Y = 496$.
3. **Resting Expression**: Calm, observant neutral gaze matching canonical baseline.
4. **Signature Details**: Full oversized charcoal hoodie, blush drawstrings, Signal Heart centered at $(256, 294)$, Signal Clip, stockings, and sneakers.
5. **No Cropping Variance**: Centered on 512×512 canvas with identical spatial registration.

---

## 6. EXPRESSION PRODUCTION STRATEGY

> [!IMPORTANT]
> **STRICT STAGED GENERATION RULE**
> 
> Each expression must be generated separately using the validated base sprite (`meli_body_base.png`) as the visual and structural identity reference.
> 
> **DO NOT generate all expressions as one 4×4 grid or composite sheet.**
> Generating all expressions in a single combined grid introduces severe facial divergence, anchor drift, and inconsistent scale. Single-asset staged generation ensures 100% pixel-perfect coordinate registration and identity lock.

### Staged Production Workflow:
1. **Stage A — Master Base Sprite Generation**: Render `meli_body_base.png` and run full automated validation.
2. **Stage B — Identity Baseline Lock**: Freeze `meli_body_base.png` as the reference canvas.
3. **Stage C — Individual Expression Pass**: For each expression $1 \dots 12$, generate the targeted expression layer directly registered against `meli_body_base.png`.
4. **Stage D — Automated Alignment & Fringe QA**: Run pixel-diff and anchor validation against the baseline.

---

## 7. Procedural SINK / POP Motion Specification

- **Architectural Rule**: Sink/Pop is an animation state executed procedurally on the GPU transform layer—**no separate sprite asset is created**.
- **Sequence**:
  $$\text{NORMAL} \longrightarrow \text{SINK/COMPRESS (180ms)} \longrightarrow \text{TINY CUTE HOLD (170ms)} \longrightarrow \text{POP BACK (200ms)} \longrightarrow \text{IDLE SETTLE (200ms)}$$
- **Parameters**:
  - $\text{scaleY} = 0.92, \text{scaleX} = 1.04, \text{translateY} \le +4.0\text{px}, \text{rotation} = 0.0^\circ$
  - Pop overshoot: $\text{scaleY} = 1.03, \text{scaleX} = 0.98, \text{translateY} \le -3.0\text{px}, \text{rotation} \le 2.0^\circ$
  - Volume conservation: $\text{scaleX} \times \text{scaleY} \approx 1.0$.

---

## 8. Quality Assurance & Acceptance Criteria

Every production asset must pass automated validation with zero errors:
1. **Dimensions**: Exact $512 \times 512\text{px}$ runtime ($768 \times 768\text{px}$ master).
2. **True Alpha Channel**: 32-bit RGBA with $0$ alpha outside silhouette.
3. **Transparent Canvas Corners**: Corners at $(0,0), (511,0), (0,511), (511,511)$ must have alpha $= 0$.
4. **Bounding Box**: Confined strictly within $[16, 16, 496, 496]$ ($16\text{px}$ safety perimeter).
5. **Grounding Alignment**: Lowest solid alpha pixel rows must contact $Y \approx 496 \pm 4\text{px}$.
6. **Zero White Halo**: Straight alpha matte blending with clean edge falloff.
7. **Color Compliance**: Samples match canonical sRGB token palette.
