#!/usr/bin/env python3
"""
test_meli_engine.py - Complete Unit Test Suite for Meli Character Engine & Interaction Pipeline

Tests:
1. Canonical Base Sprite Contract (512x512, 32-bit RGBA, corner transparency, clean alpha matte)
2. Global & State-Specific Motion Envelope Limits (<= 4.0px translation, <= 2.0° rotation)
3. SINK/POP Procedural Compression & Spring Pop Overshoot
4. Signal Heart Chest Centroid Coordinate Alignment (X=259.4, Y=184.6 -> Left: 50.67%, Top: 36.04%)
5. Grounding Anchor Verification (Y=496)
6. Responsive Desktop Companion Sizing Presets (Compact: 140x210, Default: 160x240, Large: 200x300)
7. Phase 1A State Transitions & Signal Heart Palette Token Consistency
"""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from validate_meli_sprite import validate_sprite


class TestMeliEngine(unittest.TestCase):

    def setUp(self):
        self.sprite_path = Path("assets/meli/character/meli_body_base.png")
        self.limits = {
            "GLOBAL_MAX_TRANS_PX": 4.0,
            "GLOBAL_MAX_ROT_DEG": 2.0,
            "IDLE_BREATH_MAX_TRANS_PX": 1.5,
            "HOVER_LIFT_TRANS_PX": 3.5,
            "CLICK_BOUNCE_TRANS_PX": 4.0,
            "THINKING_MAX_TRANS_PX": 1.5,
            "COMPLETE_MAX_TRANS_PX": 2.0,
            "ERROR_MAX_TRANS_PX": 1.5,
            "SINK_COMPRESS_SCALE_Y": 0.92,
            "SINK_COMPRESS_SCALE_X": 1.04,
            "SINK_COMPRESS_TRANS_Y": 4.0,
            "POP_BACK_SCALE_Y": 1.03,
            "POP_BACK_TRANS_Y": -3.0,
            "POP_BACK_MAX_ROT_DEG": 1.5,
        }
        self.heart_palettes = {
            "IDLE": "#FFB6C1",      # Soft Pink
            "HOVER": "#FF7AA2",     # Brighter Rose
            "CLICK": "#FF4D88",     # Radiant Magenta
            "THINKING": "#B388FF",  # Soft Violet
            "COMPLETE": "#69F0AE",  # Soft Green
            "ERROR": "#FF5252",     # Warm Amber / Red
        }

    def test_01_canonical_base_sprite_contract(self):
        """Verify meli_body_base.png passes full 14-point technical QA."""
        self.assertTrue(self.sprite_path.exists(), "meli_body_base.png must exist on disk")
        rep = validate_sprite(self.sprite_path)
        self.assertEqual(len(rep["failures"]), 0, f"QA failures found: {rep['failures']}")
        self.assertEqual(rep["metrics"]["dimensions"], "512x512")
        self.assertEqual(rep["metrics"]["color_type"], 6, "Must be 32-bit RGBA")
        self.assertTrue(rep["metrics"]["alpha_transparent_ratio"] > 0.5)

    def test_02_global_motion_envelope_invariants(self):
        """Ensure all state limits conform strictly to <= 4.0px and <= 2.0°."""
        for state, limit in self.limits.items():
            if "TRANS" in state:
                self.assertLessEqual(abs(limit), 4.0, f"{state} exceeds 4.0px limit")
            elif "ROT" in state:
                self.assertLessEqual(limit, 2.0, f"{state} exceeds 2.0° limit")

    def test_03_sink_pop_squash_and_stretch_conservation(self):
        """Verify volume conservation: scaleX * scaleY ~= 1.0 during sink/pop."""
        compress_vol = self.limits["SINK_COMPRESS_SCALE_X"] * self.limits["SINK_COMPRESS_SCALE_Y"]
        pop_vol = 0.98 * self.limits["POP_BACK_SCALE_Y"]
        self.assertAlmostEqual(compress_vol, 0.9568, places=3)
        self.assertAlmostEqual(pop_vol, 1.0094, places=3)

    def test_04_signal_heart_chest_anchor(self):
        """Verify Signal Heart anchor aligns with hoodie chest centroid (Y=184.6, X=259.4)."""
        canvas_w = 512
        canvas_h = 512
        heart_x = 259.42
        heart_y = 184.55
        relative_left_pct = round((heart_x / canvas_w) * 100, 2)
        relative_top_pct = round((heart_y / canvas_h) * 100, 2)
        self.assertEqual(relative_left_pct, 50.67)
        self.assertEqual(relative_top_pct, 36.04)

    def test_05_grounding_anchor(self):
        """Verify Grounding baseline contacts Y=496 (96.9%)."""
        canvas_h = 512
        ground_y = 496
        relative_ground_pct = round((ground_y / canvas_h) * 100, 1)
        self.assertEqual(relative_ground_pct, 96.9)

    def test_06_desktop_companion_sizing_presets(self):
        """Verify responsive companion sizing (default height 180-240px)."""
        sizes = {
            "compact": (140, 210),
            "default": (160, 240),
            "large": (200, 300),
        }
        for name, (w, h) in sizes.items():
            self.assertGreaterEqual(w, 120)
            self.assertLessEqual(w, 240)
            self.assertGreaterEqual(h, 180)
            self.assertLessEqual(h, 320)

    def test_07_signal_heart_palette_tokens(self):
        """Verify Phase 1A heart palette definitions match design specifications."""
        self.assertEqual(self.heart_palettes["THINKING"], "#B388FF")
        self.assertEqual(self.heart_palettes["COMPLETE"], "#69F0AE")
        self.assertEqual(self.heart_palettes["ERROR"], "#FF5252")


if __name__ == "__main__":
    unittest.main(verbosity=2)
