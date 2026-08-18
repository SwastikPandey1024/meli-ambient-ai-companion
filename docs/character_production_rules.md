# Meli Character Production Rules & Export Matrix

This document defines the strict engineering and artistic production pipeline for all raster and vector visual assets generated for **Meli — Ambient AI Companion**.

---

## 1. Visual Source of Truth & Identity Lock

- **Canonical Reference Authority**: All assets must be derived from and strictly conform to:
  ```
  design/meli_canonical_character_sheet2.png (Primary Visual Authority)
  design/meli_canonical_character_sheet.png (Turnaround & Baseline Blueprint)
  ```
- **Persona & Demographic Metadata**:
  - **Age / Classification**: **"Young Adult — 18+"**
  - **Character Tone**: Empathetic, quiet, intelligent, observant, gently playful, and respectful.
- **Inviolable Visual Attributes**:
  - **Face & Eyes**: Soft oval jawline, almond-shaped eyes with dark coral irises, clean white glints, subtle cheek micro-blush.
  - **Hair**: Medium-length layered cut in dusty-rose / muted coral-pink (`#FFB6C1`) with parted bangs and signature Signal Clip accessory.
  - **Hoodie & Attire**: Oversized deep charcoal cotton hoodie (`#171824`) with relaxed dropped shoulders, elongated sleeves, and soft blush drawstrings (`#FFD6E7`).
  - **Signal Heart**: Chest-mounted ambient light indicator centered at `[256, 294]`.
  - **Proportions & Silhouette**: Petite, grounded companion proportions with low-profile minimal sneakers.
  - **Strict Prohibition**: No redesigns, no style divergence, no anime trope exaggeration, and no inconsistent cropping. Meli must maintain 100% visual identity consistency across every state.

---

## 2. Canvas, Dimensions & Scaling

| Property | Master Specification | Runtime Target |
| :--- | :--- | :--- |
| **Canvas Dimensions** | **768 × 768 px** (@2x Native Master) | **512 × 512 px** (Standard Reference) |
| **Display Viewports** | High-DPI Desktop Scaling | 120px – 160px companion window scale |
| **Safety Margin** | **24 px** (scaled master) | **16 px** (bounding inset) |
| **Active Art Bounding Box** | `[24, 24, 744, 744]` | `[16, 16, 496, 496]` (480 × 480 px active) |

> [!IMPORTANT]
> **No Inconsistent Cropping**: Every sprite layer (base body and expression overlays) MUST be exported on an identical full 512×512 canvas with identical origin coordinates. Do not crop tightly to faces or bounding regions; zero-latency sprite swapping relies on pixel-perfect coordinate alignment.

---

## 3. Pixel Anchors & Spatial Registration

All assets must be registered against the 512×512 reference coordinate system:

1. **Eye / Gaze Anchor (`[256, 168]`)**:
   - Primary reference origin for procedural pupil gaze tracking and parallax micro-tilts ($\le \pm 2.0^\circ$).
2. **Signal Heart Anchor (`[256, 294]`)**:
   - Geometric center for SVG dynamic glow overlays, state color ripples, and particle bursts.
3. **Grounding Footprint Anchor (`[256, 496]`)**:
   - Screen baseline contact point for window snapping, desktop surface contact, and physics grounding.
4. **Safety Margin (16px)**:
   - Preserves 16px transparent perimeter margin around artwork to prevent anti-aliasing clipping during $\le 4\text{px}$ translations and $\le 2^\circ$ tilt motions.

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

---

## 4. Format, Alpha Channel & Color Profile

- **Primary Master Format**: **Transparent 32-bit PNG (RGBA with 8-bit true alpha channel)**.
- **Runtime Performance Alternative**: **Lossless / Near-Lossless WebP with alpha**.
- **Color Profile**: Strictly locked to **sRGB IEC61966-2.1**.
- **Alpha Channel & Edge Quality**:
  - **100% Transparent Background**: No background shapes, colored backing cards, or artboard fills.
  - **No White Halo / Edge Fringe**: Anti-aliased edges must blend cleanly against pure dark backgrounds (`#171824` / `#000000`) without white matte bleed, fringe artifacts, or dirty alpha premultiplication fringes.

---

## 5. Production Asset Roster (13 Planned Assets)

| File Name | Layer Type | Mood / Interaction State | Visual Rationale |
| :--- | :--- | :--- | :--- |
| `meli_body_base.png` | Base Layer | Baseline Body | Head, hair, hoodie, drawstrings, body, & sneakers. Always active underneath expressions. |
| `meli_expr_idle.png` | Overlay | Standby Idle | Neutral almond gaze, calm micro-expression, subtle resting mouth. |
| `meli_expr_curious.png` | Overlay | Window Switch / Inquisitive | Widened pupils, raised brows, inquisitive tilt ($\le 2^\circ$), open micro-smile. |
| `meli_expr_hover.png` | Overlay | Pointer Hover Contact | Attentive focus, anticipatory soft gaze towards active pointer. |
| `meli_expr_happy.png` | Overlay | Pet / Click Interaction | Crescent smiling squint, rosy cheek blush, affectionate warmth. |
| `meli_expr_blink.png` | Overlay | Periodic Micro-Blink | Fully closed relaxed eyelids for 4–6s blink cycle. |
| `meli_expr_sleepy.png` | Overlay | Desktop Idle / Night Rest | Drooping heavy lids, relaxed posture, ambient rest. |
| `meli_expr_thinking.png` | Overlay | LLM Processing | Upward/lateral analytical gaze, focused analytical mouth line. |
| `meli_expr_focused.png` | Overlay | Deep Work Flow | Calm narrowed intensity, motionless non-intrusive anchor. |
| `meli_expr_confused.png` | Overlay | Ambiguous Query | Asymmetrical brows, questioning gaze, inquisitive tilt ($\le 2^\circ$). |
| `meli_expr_error.png` | Overlay | Tool Exception / Alert | Concerned downward gaze, apologetic brow slope, slight blush. |
| `meli_expr_complete.png` | Overlay | Task Resolved / Success | Sparkling joyful eye glints, confident radiant smile. |
| `meli_expr_greeting.png` | Overlay | App Launch / Wake | Welcoming direct eye contact, friendly micro-nod posture. |

---

## 6. Motion Envelope & Procedural Animation Limits

### 6.1 Canonical Global Limits
- **Max Translation**: $\mathbf{\le 4.0\text{px}}$
- **Max Rotation**: $\mathbf{\le 2.0^\circ}$

### 6.2 State Constraints
- **NORMAL IDLE**: `translateY: [0, -2.0px, 0]` ($\le 2\text{px}$), rotation $0.0^\circ$, periodic micro-blinks every 4–6s.
- **PROXIMITY**: `translation ≤ 2.0px`, `rotation ≤ ±2.0°`, gaze tracking clamped to `dx: ±4px, dy: ±3px`.
- **HOVER**: `translation ≤ 3.5px` (micro-bob), `rotation ≤ ±2.0°`.
- **CLICK / PET**: `translation ≤ 4.0px` (mousedown dip $\rightarrow$ release spring), `rotation ≤ 2.0°`.
- **HAPPY**: `translation ≤ 2.0px`, `rotation ≤ 1.0°` ($\le 2.0^\circ$), 1500ms hold.
- **RELAXING**: Deceleration to `(0, 0)` baseline (`translation ≤ 2.0px`, `rotation ≤ 1.0°`).

### 6.3 Special Micro-Animation: MELI SINK / POP
- **Type**: Procedural animation state (NOT a separate character asset).
- **Sequence**: `NORMAL` $\rightarrow$ `SINK/COMPRESS` $\rightarrow$ `TINY CUTE HOLD` $\rightarrow$ `POP BACK` $\rightarrow$ `IDLE`.
- **Parameters**:
  - `SINK/COMPRESS`: `translateY: +4px maximum`, `scaleY: 0.92`, `scaleX: 1.04`, `rotation: 0°`.
  - `TINY CUTE HOLD`: constant hold (170ms) with volume conservation ($\text{scaleX} \times \text{scaleY} \approx 1.0$).
  - `POP BACK`: `translateY: -3px maximum`, `scaleY: 1.03`, `scaleX: 0.98`, `rotation ≤ 2.0°`.
  - `IDLE`: smooth decay to canonical `1.0` scale.

---

## 7. Production Quality Checklist for PNG/WebP Exports

- [x] **sRGB Profile**: Strictly sRGB IEC61966-2.1 color space.
- [x] **True 8-Bit Alpha**: Clean 32-bit RGBA PNG / lossless WebP.
- [x] **No Background**: 100% transparent alpha.
- [x] **No White Halo**: Edges blend seamlessly on pure dark `#171824` / `#000000`.
- [x] **Zero Crop Shifts**: 512×512 standard canvas with identical origin coordinates.
- [x] **Consistent Bounding Box**: 16px safety margin preserved on all sides.
- [x] **Anchor Consistency**: Eye `(256, 168)`, Heart `(256, 294)`, Grounding `(256, 496)` pixel-identical.
- [x] **Motion Envelope Compliance**: All movements and transforms strictly obey $\le 4\text{px}$ translation and $\le 2^\circ$ rotation.
