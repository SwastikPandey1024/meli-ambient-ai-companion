#!/usr/bin/env python3
"""
test_special_visual_uniqueness.py — Final Visual Authority QA for 4 Special Performance States

Validates:
1. All 4 special assets exist in assets/ and public/:
   - meli_proximity.png
   - meli_hover.png
   - meli_click_pet.png
   - meli_celebration.png
2. All technical contracts pass:
   - 512x512 canvas size
   - RGBA mode (32-bit)
   - 100% transparent corners (alpha=0)
   - Grounding baseline Y in [485, 505]
   - Non-empty opaque body silhouette
3. Pairwise distinctness & semantic uniqueness:
   - PROXIMITY != HOVER (assert Mean Absolute Difference >= 3.5)
   - HOVER != CLICK_PET (assert Mean Absolute Difference >= 4.0)
   - ALL 4 Special pairs pairwise distinct (MAD >= 3.5)
4. Runtime mappings in PerformanceAssetManager point directly to canonical special files.
"""

import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

SPECIAL_ASSETS = {
    "PROXIMITY": {
        "file": "meli_proximity.png",
        "asset_path": Path("assets/meli/character/special/meli_proximity.png"),
        "public_path": Path("public/special/meli_proximity.png"),
        "intent": "Subtle cursor awareness / attentive gaze",
    },
    "HOVER": {
        "file": "meli_hover.png",
        "asset_path": Path("assets/meli/character/special/meli_hover.png"),
        "public_path": Path("public/special/meli_hover.png"),
        "intent": "Active engagement / cheerful open smile & micro-sparkles",
    },
    "CLICK_PET": {
        "file": "meli_click_pet.png",
        "asset_path": Path("assets/meli/character/special/meli_click_pet.png"),
        "public_path": Path("public/special/meli_click_pet.png"),
        "intent": "Tactile response / sweet blush reaction",
    },
    "CELEBRATION": {
        "file": "meli_celebration.png",
        "asset_path": Path("assets/meli/character/special/meli_celebration.png"),
        "public_path": Path("public/special/meli_celebration.png"),
        "intent": "Milestone victory / high-energy fist pump",
    },
}


class TestSpecialVisualUniqueness(unittest.TestCase):

    def test_01_all_4_special_assets_exist(self):
        """Verify all 4 special assets exist in both assets/ and public/ directories."""
        self.assertEqual(len(SPECIAL_ASSETS), 4)
        for name, data in SPECIAL_ASSETS.items():
            self.assertTrue(
                data["asset_path"].exists(), f"Asset path missing: {data['asset_path']}"
            )
            self.assertTrue(
                data["public_path"].exists(),
                f"Public path missing: {data['public_path']}",
            )

    def test_02_technical_contracts(self):
        """Verify 512x512, 32-bit RGBA, transparent corners, and grounding contact."""
        for name, data in SPECIAL_ASSETS.items():
            img = Image.open(data["asset_path"])
            self.assertEqual(
                img.size, (512, 512), f"{name} size is {img.size}, expected (512, 512)"
            )
            self.assertEqual(
                img.mode, "RGBA", f"{name} mode is {img.mode}, expected RGBA"
            )

            arr = np.array(img)
            alpha = arr[:, :, 3]

            # 4 Corners must be 100% transparent
            self.assertTrue(
                np.all(alpha[0:5, 0:5] == 0), f"{name} top-left corner not transparent"
            )
            self.assertTrue(
                np.all(alpha[0:5, -5:] == 0), f"{name} top-right corner not transparent"
            )
            self.assertTrue(
                np.all(alpha[-5:, 0:5] == 0),
                f"{name} bottom-left corner not transparent",
            )
            self.assertTrue(
                np.all(alpha[-5:, -5:] == 0),
                f"{name} bottom-right corner not transparent",
            )

            # Grounding check
            ys, xs = np.where(alpha > 20)
            self.assertGreater(len(ys), 1000, f"{name} has too few opaque pixels")
            max_y = ys.max()
            self.assertTrue(
                485 <= max_y <= 505, f"{name} grounding Y={max_y} outside [485, 505]"
            )

    def test_03_proximity_vs_hover_uniqueness(self):
        """Verify PROXIMITY and HOVER are NOT identical or near-duplicates."""
        prox = np.array(Image.open(SPECIAL_ASSETS["PROXIMITY"]["asset_path"]))
        hover = np.array(Image.open(SPECIAL_ASSETS["HOVER"]["asset_path"]))

        diff = np.mean(np.abs(prox.astype(int) - hover.astype(int)))
        print(f"\n[Visual QA] PROXIMITY vs HOVER MAD: {diff:.2f}")
        self.assertGreater(
            diff,
            3.5,
            f"PROXIMITY and HOVER are too visually similar (MAD={diff:.2f}, expected >= 3.5)",
        )

    def test_04_hover_vs_click_pet_uniqueness(self):
        """Verify HOVER and CLICK_PET are dramatically distinct in pose, expression, and effects."""
        hover = np.array(Image.open(SPECIAL_ASSETS["HOVER"]["asset_path"]))
        click = np.array(Image.open(SPECIAL_ASSETS["CLICK_PET"]["asset_path"]))

        diff = np.mean(np.abs(hover.astype(int) - click.astype(int)))
        print(f"[Visual QA] HOVER vs CLICK_PET MAD: {diff:.2f}")
        self.assertGreater(
            diff,
            4.0,
            f"HOVER and CLICK_PET are too visually similar (MAD={diff:.2f}, expected >= 4.0)",
        )

    def test_05_all_special_pairwise_distinctness(self):
        """Verify all 4 special assets are pairwise distinct from each other."""
        special_names = list(SPECIAL_ASSETS.keys())
        for i in range(len(special_names)):
            for j in range(i + 1, len(special_names)):
                n1, n2 = special_names[i], special_names[j]
                img1 = np.array(Image.open(SPECIAL_ASSETS[n1]["asset_path"]))
                img2 = np.array(Image.open(SPECIAL_ASSETS[n2]["asset_path"]))
                diff = np.mean(np.abs(img1.astype(int) - img2.astype(int)))
                self.assertGreater(
                    diff, 3.5, f"{n1} and {n2} are too similar (MAD={diff:.2f})"
                )

    def test_06_runtime_asset_manifest_and_mappings(self):
        """Verify runtime PerformanceAssetManager maps special events to exact paths."""
        pam_file = Path("src/enrichment/PerformanceAssetManager.ts")
        self.assertTrue(pam_file.exists())
        content = pam_file.read_text(encoding="utf-8")

        self.assertIn("proximity: '/special/meli_proximity.png'", content)
        self.assertIn("hover: '/special/meli_hover.png'", content)
        self.assertIn("click_pet: '/special/meli_click_pet.png'", content)
        self.assertIn("celebration: '/special/meli_celebration.png'", content)


if __name__ == "__main__":
    unittest.main()
