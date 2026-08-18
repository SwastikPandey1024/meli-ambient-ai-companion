# Canonical Character Design Lock & Reference Authority

## 1. Visual Source of Truth
The approved canonical character sheet and expression reference is registered at:
```
design/meli_canonical_character_sheet2.png (Primary Visual Authority)
design/meli_canonical_character_sheet.png (Turnaround & Baseline Blueprint)
```

`design/meli_canonical_character_sheet2.png` serves as the **single, definitive visual source of truth** for all character assets, expressions, renders, spatial alignment, and production artwork for **Meli**.

> [!IMPORTANT]
> **CANONICAL CHARACTER LOCK**
> 
> The character design and expression identity of Meli are finalized and approved. 
> Under no circumstances should Meli be redesigned or stylistically altered.

---

## 2. Inviolable Visual Attributes & Persona Metadata
All downstream asset production must strictly preserve:
- **Demographic / Persona Metadata**: **"Young Adult — 18+"**. Empathetic, quiet, intelligent, observant, and gently respectful.
- **Face & Expressions**: Soft oval jawline, gentle micro-blush, refined almond eyes with warm coral irises and clean white glints. Expression identities are canonical and locked.
- **Hair**: Medium-length layered cut in dusty-rose / muted coral-pink (`#FFB6C1`) with natural soft parted bangs, layered tips, signature Signal Clip, and subtle organic bounce.
- **Proportions**: Petite desktop companion form factor designed for unobtrusive, comfortable coexistence.
- **Attire**: Oversized deep charcoal cotton hoodie (`#171824`) with relaxed dropped shoulders, deep cozy hood, elongated sleeves, and soft blush drawstrings (`#FFD6E7`).
- **Signature Accessories**:
  - **Signal Clip**: Accent hair accessory maintaining exact placement and color.
  - **Signal Heart**: Chest-mounted ambient light indicator centered at coordinate `[256, 294]`.
- **Color Palette**: Standardized token palette locked to sRGB:
  - `Rose`: `#FFB6C1`
  - `Accent Rose`: `#FF7AA2`
  - `Deep Charcoal`: `#171824`
  - `Soft Navy`: `#262A3A`
  - `Soft Blush`: `#FFD6E7`
  - `Pure White`: `#FFFFFF`
- **Footwear**: Low-profile minimalist geometric sneakers in matte charcoal with clean rose accent piping.
- **Silhouette & Posture**: Instantly identifiable cozy oversized silhouette with relaxed, grounded stance.

---

## 3. Canonical Motion Envelope & Usage Guidelines
- **Global Motion Envelope Limits**:
  - Maximum Global Translation: $\mathbf{\le 4.0\text{px}}$
  - Maximum Global Rotation: $\mathbf{\le 2.0^\circ}$
  - Perimeter Safety Inset: $\mathbf{16\text{px}}$
- `design/meli_canonical_character_sheet2.png` is a **non-runtime design reference**.
- Runtime engines consume modular sprite layers registered in `assets/meli/metadata/character_asset_manifest.json`.
- Procedural transforms (such as the SINK/POP micro-animation) operate on the canonical sprite via GPU matrix transforms without altering canonical base assets.
