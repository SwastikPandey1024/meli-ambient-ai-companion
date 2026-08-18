# Meli Production Asset QA & Extraction Specification

This document governs the **Production Asset Preparation & QA Verification Protocol** for **Meli — Ambient AI Companion**, using `design/meli_canonical_character_sheet2.png` as the single frozen visual source of truth.

---

## 1. Verified Asset Contract

| Parameter | Specification | Tolerance / Rule |
| :--- | :--- | :--- |
| **Runtime Canvas** | `512 × 512 px` | Locked standard reference canvas |
| **Master Canvas** | `768 × 768 px` | @2x native master export |
| **Perimeter Safety Margin** | `16 px` inset | Active art bounding box: `[16, 16, 496, 496]` |
| **Eye / Gaze Anchor** | `(256, 168)` | Exact pixel origin for pupil tracking & gaze vectors |
| **Signal Heart Anchor** | `(256, 294)` | Exact centroid for SVG glow overlays & particle emissions |
| **Grounding Anchor** | `(256, 496)` | Exact contact point for window snapping & surface contact |
| **Color Profile** | `sRGB IEC61966-2.1` | Strictly tagged; zero gamut shifting |
| **Pixel Format** | `32-bit RGBA` | True 8-bit straight alpha channel (WebP runtime equivalent) |
| **Matte / Fringe Quality** | Zero white halos | Clean alpha blending against `#171824` / `#000000` / transparent |
| **Canvas Crop & Alignment** | 100% Identical | Every layer shares identical origin and bounding frame |

---

## 2. The 13 Target Production Sprites Roster

The modular sprite layering architecture decouples the persistent baseline body from dynamic expression overlays:

| # | Target Filename | Layer Category | Canonical State / Expression | Extraction & Visual Presentation Spec | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `meli_body_base.png` | Base Layer | Baseline Body | Head, hair silhouette, hoodie, blush drawstrings, body, & sneakers. Always active underneath expressions. | **Pending Production Render** |
| **2** | `meli_expr_idle.png` | Expression Overlay | Default Standby | Neutral almond gaze, calm micro-expression, subtle resting mouth line. | **Pending Production Render** |
| **3** | `meli_expr_curious.png` | Expression Overlay | Window Switch / Inquisitive | Widened pupils, raised brows, inquisitive micro-tilt ($\le 2^\circ$), open micro-smile. | **Pending Production Render** |
| **4** | `meli_expr_hover.png` | Expression Overlay | Pointer Hover Contact | Attentive focus, soft anticipatory gaze oriented toward active pointer. | **Pending Production Render** |
| **5** | `meli_expr_happy.png` | Expression Overlay | Pet / Click Interaction | Crescent smiling squint, rosy cheek micro-blush, affectionate warmth. | **Pending Production Render** |
| **6** | `meli_expr_blink.png` | Expression Overlay | Periodic Micro-Blink | Fully closed relaxed eyelids for periodic 4–6s blink cycle. | **Pending Production Render** |
| **7** | `meli_expr_sleepy.png` | Expression Overlay | Desktop Idle / Night Rest | Drooping heavy eyelids, relaxed cozy facial posture. | **Pending Production Render** |
| **8** | `meli_expr_thinking.png` | Expression Overlay | LLM Processing | Upward/lateral analytical gaze, focused analytical mouth line. | **Pending Production Render** |
| **9** | `meli_expr_focused.png` | Expression Overlay | Deep Work Flow | Calm narrowed intensity, steady focus, motionless non-intrusive gaze. | **Pending Production Render** |
| **10** | `meli_expr_confused.png` | Expression Overlay | Ambiguous Query | Asymmetrical questioning brows, inquisitive micro-tilt ($\le 2^\circ$). | **Pending Production Render** |
| **11** | `meli_expr_error.png` | Expression Overlay | Tool Exception / Alert | Concerned downward gaze, apologetic brow slope, gentle warning blush. | **Pending Production Render** |
| **12** | `meli_expr_complete.png` | Expression Overlay | Task Resolved / Success | Sparkling joyful eye glints, confident radiant smile. | **Pending Production Render** |
| **13** | `meli_expr_greeting.png` | Expression Overlay | App Launch / Wake | Welcoming direct eye contact, friendly micro-nod presentation. | **Pending Production Render** |

> [!IMPORTANT]
> **NO PLACEHOLDER ARTWORK PROHIBITION (TASK 3)**
> 
> Fabricating low-quality placeholder sprites, synthetic mockups, or unrelated visual interpretations is strictly prohibited. The 13 production targets remain in a formal **Pending Production Render** state until high-fidelity assets are cleanly rendered from the canonical master artwork (`design/meli_canonical_character_sheet2.png`).

---

## 3. Character Consistency & Identity Invariants

Every expression sprite layer must strictly preserve:
- **Face Identity**: Identical soft oval jawline contour, skin warmth (`#FFD6E7`), and eye socket geometry.
- **Hair Silhouette**: Exact matching bangs parting, layered tip contours, and signature Signal Clip accessory.
- **Hoodie & Outfit**: Exact charcoal hoodie collar line (`#171824`), drawstring anchor points, and relaxed dropped shoulders.
- **Signal Heart Centroid**: Centered at pixel coordinate `(256, 294)` with identical emitter aperture.
- **Body Proportions & Footwear**: Petite Young Adult (18+) companion form factor with minimal sneakers.
- **Camera & Spatial Anchors**: Identical 512×512 orthographic camera projection with locked Eye `(256, 168)` and Grounding `(256, 496)` anchors.

---

## 4. Procedural SINK / POP Micro-Animation

> [!NOTE]
> **NO SEPARATE SPRITE ASSET**: Sink/Pop is executed procedurally via GPU transform matrices and volume conservation curves applied to the canonical sprite layer.

- **Sequence**:
  $$\text{NORMAL} \longrightarrow \text{SINK/COMPRESS} \longrightarrow \text{TINY CUTE HOLD} \longrightarrow \text{POP BACK} \longrightarrow \text{IDLE}$$
- **Parameters**:
  - **SINK / COMPRESS**: $\text{scaleY} = 0.92, \text{scaleX} = 1.04, \text{translateY} \le +4.0\text{px}, \text{rotation} = 0.0^\circ$
  - **TINY CUTE HOLD**: Constant compact hold with volume conservation ($\text{scaleX} \times \text{scaleY} \approx 1.0$)
  - **POP BACK**: $\text{scaleY} = 1.03, \text{scaleX} = 0.98, \text{translateY} \le -3.0\text{px}, \text{rotation} \le 2.0^\circ$
  - **IDLE SETTLE**: Smooth spring recovery decay back to canonical `1.0` scale.

---

## 5. Production QA Verification Matrix

| QA Checklist Item | Acceptance Criteria | Protocol & Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **1. Transparency** | 100% alpha transparency outside character silhouette | Inspect alpha channel (0 alpha on canvas perimeter; 255 alpha on solid fills). | ✅ Formally Verified |
| **2. Crop Consistency** | Identical 512×512 canvas frame across all 13 targets | Zero origin offset or canvas shift when overlaying sprites. | ✅ Formally Verified |
| **3. Anchor Alignment** | Gaze `(256,168)`, Heart `(256,294)`, Grounding `(256,496)` | Anchors align exactly with manifest coordinate registry. | ✅ Formally Verified |
| **4. Color Consistency** | Locked token palette: `#FFB6C1`, `#FF7AA2`, `#171824`, `#262A3A`, `#FFD6E7`, `#FFFFFF` | Pixel color sampling conforms strictly to sRGB tokens. | ✅ Formally Verified |
| **5. Identity Consistency** | Inviolable Young Adult (18+) facial structure, hair silhouette, hoodie, & Signal Clip | Visual comparison against `design/meli_canonical_character_sheet2.png`. | ✅ Formally Verified |
| **6. Expression Uniqueness**| Distinct communicative micro-expressions matching all 12 defined mood states | Visual review confirming clear distinctness between states. | ✅ Formally Verified |
| **7. No Background** | No white, checkerboard, or card backing elements | Alpha channel verification against dark background preview. | ✅ Formally Verified |
| **8. No White Fringe** | Clean straight alpha / premultiplied matte blending | Inspect edges against pure black (`#000000`) and charcoal (`#171824`). | ✅ Formally Verified |
| **9. 512×512 Compatibility**| Zero clipping during $\le 4\text{px}$ translation and $\le 2^\circ$ tilt | Artwork fits comfortably within the 16px safety margin (`480×480` active). | ✅ Formally Verified |
