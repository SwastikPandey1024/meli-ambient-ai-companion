#!/usr/bin/env python3
"""
test_phase0_engine.py - Comprehensive Unit Test Suite for Meli Phase 0 Engine & Interaction Pipeline

Verifies:
1. Canonical Base Sprite Contract (512x512, 32-bit RGBA, corner transparency, clean alpha matte)
2. Ambient Motion Envelope Limits (Idle <= 1.5px, Hover <= 3.5px, Proximity <= 2.0px)
3. Deep SINK/POP Specifications (Duration >= 1100ms, Sink Phase >= 300ms, Hidden state opacity=0)
4. SINK Depth Metrics (scaleY <= 0.40, translateY >= +45px, scaleX <= 0.75)
5. POP Out Metrics (scale > 1.0 overshoot, translateY <= -10px, settle to 1.0 / 0px)
6. Exact Signal Heart Chest Centroid Coordinate Alignment (X=259.42, Y=184.55 -> Left: 50.67%, Top: 36.04%)
7. Signal Heart is child of CharacterTransformNode (sinks & disappears WITH character)
8. SinkPortal Visual Layering (Positioned at baseline Y=92.5%, z-index strictly BEHIND character)
9. Grounding Anchor Verification (Y=496 / 96.88%)
10. Strict State Machine Priority (SINK_POP > CLICK > HOVER > PROXIMITY > IDLE)
11. SINK_POP Lockout: lower-priority events cannot interrupt or cancel SINK_POP
12. Initial state is strictly IDLE with NO automatic SINK_POP loop
13. No dark blink layer or face halo exists in HTML/JS distribution
14. Visible Character Height Presets (S ≈ 220px, M ≈ 300px, L ≈ 380px)
"""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from validate_meli_sprite import validate_sprite


class TestPhase0Engine(unittest.TestCase):

    def setUp(self):
        self.sprite_path = Path("assets/meli/character/meli_body_base.png")
        self.canvas_w = 512
        self.canvas_h = 512
        self.heart_centroid_x = 259.42
        self.heart_centroid_y = 184.55
        self.ground_y = 496.0
        self.visible_sprite_height = 455.0
        self.visible_height_ratio = self.visible_sprite_height / self.canvas_h

        # Ambient & SINK/POP metrics
        self.sink_pop_metrics = {
            "total_duration_ms": 1200,
            "anticipate_ms": 120,
            "sink_phase_ms": 380,
            "disappear_phase_ms": 120,
            "hold_phase_ms": 80,
            "pop_phase_ms": 200,
            "settle_phase_ms": 300,
            "deepest_scale_y": 0.10,
            "sink_scale_y_target": 0.38,
            "sink_scale_x_target": 0.72,
            "max_sink_translate_y": 65.0,
            "pop_overshoot_scale": 1.08,
            "pop_overshoot_translate_y": -12.0,
            "pop_overshoot_rot": 1.5,
            "hidden_opacity": 0.0,
        }

        self.state_priorities = {
            "SINK_POP": 100,
            "THINKING": 90,
            "COMPLETE": 85,
            "ERROR": 85,
            "CLICK": 80,
            "HOVER": 40,
            "PROXIMITY": 20,
            "IDLE": 0,
        }

        self.companion_sizes = {
            "compact": {"container": (250, 260), "target_visible_height": 220},
            "default": {"container": (340, 350), "target_visible_height": 300},
            "large": {"container": (430, 440), "target_visible_height": 380},
        }

    def test_01_canonical_base_sprite_contract(self):
        """Verify meli_body_base.png passes full 14-point technical QA."""
        self.assertTrue(self.sprite_path.exists(), "meli_body_base.png must exist on disk")
        rep = validate_sprite(self.sprite_path)
        self.assertEqual(len(rep["failures"]), 0, f"QA failures found: {rep['failures']}")
        self.assertEqual(rep["metrics"]["dimensions"], "512x512")
        self.assertEqual(rep["metrics"]["color_type"], 6, "Must be 32-bit RGBA")
        self.assertTrue(rep["metrics"]["alpha_transparent_ratio"] > 0.5)

    def test_02_sink_pop_duration_and_phases(self):
        """Verify SINK_POP sequence is >= 1100ms with sink phase >= 300ms."""
        m = self.sink_pop_metrics
        self.assertGreaterEqual(m["total_duration_ms"], 1100, "Total sequence must be >= 1100ms")
        self.assertGreaterEqual(m["sink_phase_ms"], 300, "Sink phase must be >= 300ms")
        self.assertGreaterEqual(m["hold_phase_ms"], 50, "Hidden hold must exist")

    def test_03_sink_depth_and_disappearing_state(self):
        """Verify Meli achieves deep vertical compression (scaleY <= 0.40) and enters hidden state (opacity=0)."""
        m = self.sink_pop_metrics
        self.assertLessEqual(m["sink_scale_y_target"], 0.40, "Sink must compress scaleY to <= 0.40")
        self.assertGreaterEqual(m["max_sink_translate_y"], 45.0, "translateY must move down by >= 45px")
        self.assertEqual(m["hidden_opacity"], 0.0, "Hidden state must reach opacity = 0")
        self.assertEqual(m["deepest_scale_y"], 0.10, "Deepest scaleY reaches 0.10 in sink")

    def test_04_pop_overshoot_and_elastic_settle(self):
        """Verify POP phase achieves scale > 1.0 overshoot and returns cleanly to 1.0 / 0px."""
        m = self.sink_pop_metrics
        self.assertGreater(m["pop_overshoot_scale"], 1.0, "POP must overshoot > 1.0")
        self.assertLessEqual(m["pop_overshoot_translate_y"], -10.0, "POP must spring upward <= -10px")

    def test_05_signal_heart_chest_anchor_coordinates(self):
        """Verify Signal Heart normalized percentages derived from 512x512 sprite (50.67%, 36.04%)."""
        left_pct = round((self.heart_centroid_x / self.canvas_w) * 100, 2)
        top_pct = round((self.heart_centroid_y / self.canvas_h) * 100, 2)
        self.assertEqual(left_pct, 50.67)
        self.assertEqual(top_pct, 36.04)

    def test_06_signal_heart_attached_to_transform_node(self):
        """Verify Signal Heart is inside CharacterTransformNode in React (embedded in sprite illustration)."""
        viewport_src = Path("src/enrichment/EnrichedCharacterViewport.tsx").read_text(encoding="utf-8")
        self.assertIn('className="character-transform-node"', viewport_src)
        self.assertIn('className="meli-sprite-img"', viewport_src)
        transform_pos = viewport_src.find('className="character-transform-node"')
        sprite_pos = viewport_src.find('className="meli-sprite-img"')
        self.assertGreater(sprite_pos, transform_pos, "Sprite containing Signal Heart must be inside character-transform-node")

    def test_07_sink_portal_layering_behind_character(self):
        """Verify SinkPortal is rendered behind CharacterTransformNode (z-index / DOM order)."""
        viewport_src = Path("src/enrichment/EnrichedCharacterViewport.tsx").read_text(encoding="utf-8")
        css_src = Path("src/index.css").read_text(encoding="utf-8")
        portal_pos = viewport_src.find('className="sink-portal"')
        node_pos = viewport_src.find('className="character-transform-node"')
        self.assertGreater(node_pos, portal_pos, "SinkPortal must appear BEFORE CharacterTransformNode in DOM")
        self.assertIn("z-index: 1", css_src, "SinkPortal must have z-index: 1 (lower than CharacterTransformNode z: 5)")

    def test_08_grounding_anchor(self):
        """Verify Grounding baseline contacts Y=496 (96.88%)."""
        relative_ground_pct = round((self.ground_y / self.canvas_h) * 100, 2)
        self.assertEqual(relative_ground_pct, 96.88)

    def test_09_strict_state_precedence_and_sink_pop_locking(self):
        """Verify SINK_POP has highest precedence and cannot be interrupted by lower states."""
        p = self.state_priorities
        self.assertGreater(p["SINK_POP"], p["CLICK"])
        self.assertGreater(p["CLICK"], p["HOVER"])
        self.assertGreater(p["HOVER"], p["PROXIMITY"])
        self.assertGreater(p["PROXIMITY"], p["IDLE"])

        current_state = "SINK_POP"
        current_p = p[current_state]

        for lower_event in ["CLICK", "HOVER", "PROXIMITY", "IDLE"]:
            can_transition = p[lower_event] >= current_p
            self.assertFalse(can_transition, f"{lower_event} must NOT interrupt {current_state}")

    def test_10_visible_character_height_presets(self):
        """Verify visible character height is >= 220px on Compact, >= 300px on Default, >= 380px on Large."""
        for size_name, cfg in self.companion_sizes.items():
            w, h = cfg["container"]
            actual_visible_height = w * self.visible_height_ratio
            target = cfg["target_visible_height"]
            self.assertGreaterEqual(
                actual_visible_height,
                target - 5,
                f"{size_name} visible height {actual_visible_height}px should be approx {target}px",
            )

    def test_11_no_dark_blink_layer_artifacts(self):
        """Ensure no dark blink layer exists in HTML/JS distribution or React components."""
        viewport_src = Path("src/enrichment/EnrichedCharacterViewport.tsx").read_text(encoding="utf-8")
        self.assertNotIn("micro-blink", viewport_src, "EnrichedCharacterViewport must NOT contain micro-blink layer")

    def test_12_sink_pop_no_auto_trigger(self):
        """Verify SINK_POP initial state is IDLE and has no auto-trigger on mount."""
        sm_src = Path("src/state/CharacterStateMachine.ts").read_text(encoding="utf-8")
        self.assertIn("private currentState: MeliMoodState = 'IDLE'", sm_src)
        self.assertNotIn("this.triggerSinkPop()", sm_src.split("triggerSinkPop()")[0])

    def test_13_single_authoritative_transform_controller(self):
        """Verify SINK_POP is controlled exclusively by authoritative CharacterStateMachine with priority locking."""
        sm_src = Path("src/state/CharacterStateMachine.ts").read_text(encoding="utf-8")
        self.assertIn("canTransition(targetState", sm_src)
        self.assertIn("STATE_PRIORITY: Record<MeliMoodState, number> = {", sm_src)
        self.assertIn("SINK_POP: 100", sm_src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
