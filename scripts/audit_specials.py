#!/usr/bin/env python3
"""Phase A: Full audit of special performance assets and their visual quality."""

import hashlib
import os
import json
import numpy as np
from pathlib import Path
from PIL import Image

def sha256(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def inspect_png(path):
    img = Image.open(path).convert('RGBA')
    arr = np.array(img)
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 20)
    if len(ys) == 0:
        return img.size, img.mode, None, None, [int(alpha[0,0]), int(alpha[0,-1]), int(alpha[-1,0]), int(alpha[-1,-1])]
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    height = int(ys.max() - ys.min())
    corners = [int(alpha[0,0]), int(alpha[0,-1]), int(alpha[-1,0]), int(alpha[-1,-1])]
    return img.size, img.mode, bbox, height, corners

def pairwise_mad(paths):
    imgs = {}
    for p in paths:
        arr = np.array(Image.open(p).convert('RGBA')).astype(float)
        imgs[Path(p).name] = arr
    
    names = list(imgs.keys())
    print("Pairwise MAD:")
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            mad = float(np.mean(np.abs(imgs[names[i]] - imgs[names[j]])))
            print(f"  {names[i]} vs {names[j]}: {mad:.2f}")

print("=" * 70)
print("PHASE A: FULL SPECIAL PERFORMANCE ASSET AUDIT")
print("=" * 70)

# 1. Core states audit
core_dir = Path("assets/meli/character/states")
print(f"\n[CORE STATES] {core_dir}")
core_files = sorted(core_dir.glob("*.png"))
for f in core_files:
    sz, mode, bbox, h, corners = inspect_png(f)
    print(f"  {f.name}: {sz} {mode} BBox={bbox} H={h} corners={corners} SHA={sha256(f)[:12]}")

print(f"\n[CORE STATE COUNT]: {len(core_files)} / 12 expected")

# 2. Special assets audit
special_dir = Path("assets/meli/character/special")
print(f"\n[SPECIAL ASSETS] {special_dir}")
special_files = sorted(special_dir.glob("*.png"))
for f in special_files:
    sz, mode, bbox, h, corners = inspect_png(f)
    print(f"  {f.name}: {sz} {mode} BBox={bbox} H={h} corners={corners} SHA={sha256(f)[:12]}")

if len(special_files) >= 2:
    pairwise_mad([str(f) for f in special_files])

# 3. Design reference audit
print(f"\n[DESIGN REFERENCES]")
for ref in [
    "design/artifacts/meli_proximity_review.png",
    "design/artifacts/meli_hover_review.png",
    "design/artifacts/meli_celebration_preview.png",
    "design/meli_canonical_character_sheet.png",
]:
    p = Path(ref)
    if p.exists():
        sz, mode, bbox, h, corners = inspect_png(p)
        print(f"  {p.name}: {sz} {mode} BBox={bbox}")
    else:
        print(f"  MISSING: {ref}")

# 4. Manifest
manifest_path = Path("assets/meli/metadata/character_asset_manifest.json")
if manifest_path.exists():
    with open(manifest_path) as f:
        manifest = json.load(f)
    print(f"\n[MANIFEST] character_asset_manifest.json loaded")
    # Find special state entries
    for item in manifest.get("assets", []):
        if item.get("category") in ["special_performance", "special"]:
            print(f"  Manifest entry: id={item.get('id')} path={item.get('path')} state={item.get('state_trigger')}")
else:
    print("\n[MANIFEST] NOT FOUND")

# 5. Runtime references
print(f"\n[RUNTIME REFERENCES]")
for p in Path("src").rglob("*.ts"):
    content = p.read_text(encoding='utf-8', errors='ignore')
    for kw in ['proximity', 'hover', 'click_pet', 'celebration', 'PROXIMITY', 'HOVER']:
        if kw.lower() in content.lower() and 'import' not in content[:100]:
            pass  # Just noting
    if any(kw in content for kw in ['meli_proximity', 'meli_hover', 'meli_click_pet', 'meli_celebration']):
        print(f"  {p}: contains special asset references")

for p in Path("src").rglob("*.tsx"):
    content = p.read_text(encoding='utf-8', errors='ignore')
    if any(kw in content for kw in ['meli_proximity', 'meli_hover', 'meli_click_pet', 'meli_celebration']):
        print(f"  {p}: contains special asset references")

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)
