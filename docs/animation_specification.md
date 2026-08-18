# Meli Animation & Interaction Specification

This document defines the physics curves, state transitions, spatial envelopes, and micro-animation mechanics for **Meli — Ambient AI Companion**.

---

## 1. Canonical Motion Envelope & Core Principles

### 1.1 Canonical Global Limits
All procedural translations, spring physics, and rotation matrices must strictly adhere to the canonical global motion envelope:
- **Maximum Global Translation**: $\mathbf{\le 4.0\text{px}}$
- **Maximum Global Rotation**: $\mathbf{\le 2.0^\circ}$
- **Perimeter Safety Margin**: $\mathbf{16\text{px}}$ inset (Canvas: 512×512, Active Art Bounding Box: `[16, 16, 496, 496]`)

### 1.2 Core Principles
1. **Unobtrusive Coexistence**: Meli lives peacefully alongside the user's workflow; motion is gentle, organic, and never distractingly abrupt.
2. **Canonical Asset Integrity**: All animation mechanics operate procedurally on top of the static canonical artwork (`design/meli_canonical_character_sheet2.png`) via transform matrices, spring physics, and alpha blending. No animated distortions alter the canonical base assets.
3. **Character Metadata**: Persona demographic is registered as **"Young Adult — 18+"** with a grounded, observant, and respectful demeanor. Visual appearance is 100% locked.

---

## 2. Primary Desktop Interaction States

```
           +-----------------------------------------------------------+
           |                                                           |
           v                                                           |
       [ IDLE ]  <---------------------------------------------+       |
           |                                                   |       |
     Cursor within 80px                                        |       |
           v                                                   |       |
    [ PROXIMITY ]                                              |       |
           |                                                   |       |
     Cursor over Sprite                                        |       |
           v                                                   |       |
      [ HOVER ]                                                |       |
           |                                                   |       |
       Left Click                                          Hover Exit  |
           v                                                   |       |
     [ CLICK/PET ]                                             |       |
           |                                                   |       |
      On Complete                                              |       |
           v                                                   |       |
       [ HAPPY ] -----( 1.5s timeout )-----> [ RELAXING ] -----+-------+
```

### 2.1 NORMAL IDLE
- **Trigger**: Default standby state when no direct user input or background telemetry is active.
- **Active Expression**: `meli_expr_idle.png` + `meli_expr_blink.png` (periodic 4–6s cadence).
- **Body Motion (Breathing Cycle)**:
  - Vertical sinusoidal float: `translateY: [0px, -2.0px, 0px]` ($\le 2.0\text{px}$)
  - Period: `3.2s` with `easeInOut` sine easing.
  - Rotation: `0.0°` (stable baseline grounding).
- **Signal Heart**: Soft rhythmic pink pulse (`0.3 Hz`, `opacity: 0.40 → 0.70`).
- **Gaze**: Resting forward gaze centered at `(256, 168)`.

---

### 2.2 PROXIMITY AWARE
- **Trigger**: Cursor enters the 80px reactive zone around Meli's window.
- **Active Expression**: `meli_expr_idle.png` with procedural gaze vector offset.
- **Body Motion (Envelope-Corrected)**:
  - Attentive lift: `translateY: -2.0px` ($\le 2.0\text{px}$).
  - Subtle head tilt: `rotateZ: ±2.0°` ($\le \pm 2.0^\circ$).
  - Breathing rhythm tightens: `2.4s` cycle.
- **Gaze Tracking**: Pupil origin tracks pointer position within normalized clamp range (`dx: ±4px, dy: ±3px`).
- **Signal Heart**: Brightness warms to `85%` constant glow.

---

### 2.3 HOVER
- **Trigger**: Pointer directly hovers over Meli's active sprite bounds.
- **Active Expression**: `meli_expr_hover.png` (curious, attentive micro-smile).
- **Body Motion (Envelope-Corrected)**:
  - Buoyant micro-bob: `translateY: -3.5px` ($\le 3.5\text{px}$).
  - Inquisitive tilt: `rotateZ: +2.0°` ($\le \pm 2.0^\circ$).
  - Drawstrings and hair tips exert subtle secondary lag (`delay: 60ms`).
- **Signal Heart**: Warm rose glow with twin rhythmic pulses (`1.2 Hz`).

---

### 2.4 CLICK / PET
- **Trigger**: Direct left click or tap on Meli.
- **Active Expression**: `meli_expr_happy.png` (crescent smiling squint, rosy cheek blush).
- **Body Motion (Envelope-Corrected)**:
  - Tactile spring response: `translateY: +3.0px` compression on mousedown, springing to `translateY: -4.0px` ($\le 4.0\text{px}$ maximum).
  - Rotation: `rotateZ: ≤ 2.0°`.
  - Spring physics: `stiffness: 450, damping: 18`.
- **Signal Heart**: Radiant warm rose flash with dual SVG sparkle ripple rings expanding from `(256, 294)`.
- **Duration**: `600ms – 900ms`.

---

### 2.5 HAPPY
- **Trigger**: Successful interaction resolution following pet/click or positive companion feedback.
- **Active Expression**: `meli_expr_happy.png` → `meli_expr_complete.png`.
- **Body Motion (Envelope-Corrected)**:
  - Gentle recovery float: `translateY: -2.0px` ($\le 2.0\text{px}$).
  - Rotation: `rotateZ: ≤ 1.0°` ($\le 2.0^\circ$).
  - Settle micro-nod: `+1.5px` pitch settling.
- **Signal Heart**: Harmonic warm stabilizing glow.
- **Duration**: `1500ms` hold before initiating relaxation.

---

### 2.6 RELAXING
- **Trigger**: Interaction timeout, hover exit, or decay after active state.
- **Active Expression**: Crossfade from current expression back to `meli_expr_idle.png` over `400ms`.
- **Body Motion (Envelope-Corrected)**:
  - Smooth deceleration from active transform offsets back to baseline coordinate `(0, 0)`: `translation ≤ 2.0px`, `rotation ≤ 1.0°`.
  - Transition curve: `cubic-bezier(0.25, 1, 0.5, 1)` over `800ms`.
- **Signal Heart**: Gentle exponential fade back to idle `40%–70%` resting pulse.

---

## 3. Special Secondary Micro-Animation: MELI SINK / POP

### 3.1 Overview & Architectural Definition
> [!IMPORTANT]
> **SINK / POP IS AN ANIMATION STATE, NOT A SEPARATE CHARACTER ASSET.**
> 
> The Sink/Pop mechanic is executed purely via procedural GPU transforms (`scaleX`, `scaleY`, `translateY`) applied to the canonical sprite layer (`meli_body_base.png` + expression overlays). No alternate or deformed raster asset is generated.

### 3.2 Canonical Execution Limits
- **SINK / COMPRESS**:
  - `translateY`: **+4.0px maximum** ($\le 4\text{px}$)
  - `scaleY`: **0.92**
  - `scaleX`: **1.04**
  - `rotation`: **0.0°**
- **TINY CUTE HOLD**:
  - `translateY`: **+4.0px**
  - `scaleY`: **0.92**, `scaleX`: **1.04**
- **POP BACK**:
  - `translateY`: **-3.0px maximum** ($\le 3\text{px}$)
  - `scaleY`: **1.03**
  - `scaleX`: **0.98**
  - `rotation`: $\mathbf{\le 2.0^\circ}$
- **IDLE SETTLE**:
  - Smooth decay to `scaleY: 1.00, scaleX: 1.00, translateY: 0.0px, rotateZ: 0.0°`.

### 3.3 Motion Curve & Sequence

```
Scale Y
 1.03 |                                       ... Settle (1.0)
 1.00 | Normal (1.0)                     .---'
 0.92 |              \                 /
      |               '--- Hold (0.92)'
      +----------------------------------------------------> Time
        [ Baseline ]  [ Sink ]  [ Hold ]   [ Pop Back ] [ Settle ]
        0ms           180ms     350ms      550ms        750ms
```

| Phase | Duration | Transform Targets | Easing / Physics | Expression & Heart Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **1. NORMAL** | Baseline | `scaleY: 1.00`<br>`scaleX: 1.00`<br>`translateY: 0px` | Linear | `meli_expr_idle.png`<br>Standard idle pulse. |
| **2. SINK/COMPRESS** | `180ms` | `scaleY: 0.92`<br>`scaleX: 1.04`<br>`translateY: +4.0px` | `cubic-bezier(0.4, 0, 0.2, 1)` | Expression softens (`meli_expr_happy.png` or `sleepy`). Signal Heart dims slightly to cozy warm blush. |
| **3. TINY CUTE HOLD** | `170ms` | `scaleY: 0.92`<br>`scaleX: 1.04`<br>`translateY: +4.0px` | Constant hold with subtle micro-breathe (0.5px) | Meli stays in compact, cute posture; eye glints remain sharp. |
| **4. POP BACK** | `200ms` | `scaleY: 1.03`<br>`scaleX: 0.98`<br>`translateY: -3.0px`<br>`rotateZ: ≤ 2.0°` | Spring (`stiffness: 500, damping: 15`) | Cheerful snap-back; expression transitions smoothly to `meli_expr_curious.png` or `idle`. |
| **5. IDLE** | `200ms` | `scaleY: 1.00`<br>`scaleX: 1.00`<br>`translateY: 0px`<br>`rotateZ: 0.0°` | Smooth decay into normal 3.2s idle float | Returns seamlessly to baseline idle loop. |

### 3.4 Volume Conservation Law
To ensure Meli looks natural and retains physical mass during the squash:
$$\text{scaleX} \times \text{scaleY} = 1.04 \times 0.92 = 0.9568 \approx 1.0$$
The volume expansion is clamped to preserve strict visual fidelity.

---

## 4. Expression Sprite Preservation Validation Matrix

All 12 expression overlay sprites must strictly align with the canonical baseline (`meli_body_base.png`):

| Check Item | Validation Requirement | Verification Status |
| :--- | :--- | :--- |
| **Persona Age Metadata** | Demographic locked as "Young Adult — 18+". | ✅ Verified |
| **Face Identity** | Identical jawline contour, skin tones (`#FFD6E7`), and eye socket geometry. | ✅ Verified |
| **Hair Silhouette** | Exact matching bangs parting, tip contouring, and Signal Clip anchor. | ✅ Verified |
| **Outfit Geometry** | Charcoal hoodie collar line (`#171824`) and drawstring origins locked. | ✅ Verified |
| **Signal Heart Placement** | Exact centroid at pixel `(256, 294)` with identical emitter aperture. | ✅ Verified |
| **Anchor Alignment** | Gaze `(256, 168)`, Heart `(256, 294)`, Grounding `(256, 496)` pixel-identical. | ✅ Verified |
| **Motion Envelope Compliance**| All procedural transformations constrained to $\le 4\text{px}$ translation and $\le 2^\circ$ rotation. | ✅ Verified |

---

## 5. Production Checklist for PNG/WebP Exports

- [x] **Color Profile**: Strictly tagged with `sRGB IEC61966-2.1`.
- [x] **Alpha Channel**: True 8-bit straight alpha transparency (RGBA 32-bit).
- [x] **Background**: 100% transparent; no white or colored backing shapes.
- [x] **Edge Quality**: Zero white halos, dark edge bleeding, or anti-aliasing fringe against dark backgrounds (`#171824`).
- [x] **Crop & Canvas**: Every asset exported on identical 512×512 coordinate frame (master authored at 768×768).
- [x] **Safety Margins**: Strict 16px transparent margin maintained on all edges (`[16, 16, 496, 496]`).
- [x] **Anchor Preservation**: Spatial anchors registered and identical across all 13 production files.
