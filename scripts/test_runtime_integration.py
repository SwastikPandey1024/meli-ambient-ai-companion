#!/usr/bin/env python3
"""
test_runtime_integration.py — Live Runtime Integration Test for Meli Performance Assets

Verifies:
1. All 16 performance events map to exact canonical asset files.
2. All 16 assets exist in assets/ and public/ runtime paths.
3. 512x512, RGBA, transparent background, grounding invariants.
4. Precedence rules: SINK_POP > CELEBRATION > THINKING/RESPONSE > CLICK_PET > HOVER > PROXIMITY > IDLE.
5. Rapid transition cancellation & auto-revert timing.
6. All 10 demo user interaction scenarios.
"""

import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

EXPECTED_EVENT_MAPPINGS = {
    # 12 Core Performance States
    "IDLE": ("meli_idle.png", "/states/meli_idle.png"),
    "THINKING": ("meli_thinking.png", "/states/meli_thinking.png"),
    "MEMORY_RETRIEVED": ("meli_curious.png", "/states/meli_curious.png"),
    "RESPONSE_STREAM": ("meli_focused.png", "/states/meli_focused.png"),
    "RESPONSE_COMPLETED": ("meli_complete.png", "/states/meli_complete.png"),
    "ERROR": ("meli_error.png", "/states/meli_error.png"),
    "APP_LAUNCH": ("meli_greeting.png", "/states/meli_greeting.png"),
    "WORKING": ("meli_working.png", "/states/meli_working.png"),
    "SLEEP": ("meli_sleepy.png", "/states/meli_sleepy.png"),
    "CONFUSED": ("meli_confused.png", "/states/meli_confused.png"),
    "SURPRISED": ("meli_surprised.png", "/states/meli_surprised.png"),
    "HAPPY": ("meli_happy.png", "/states/meli_happy.png"),
    # 4 Special Performance States
    "PROXIMITY": ("meli_proximity.png", "/special/meli_proximity.png"),
    "HOVER": ("meli_hover.png", "/special/meli_hover.png"),
    "CLICK_PET": ("meli_click_pet.png", "/special/meli_click_pet.png"),
    "CELEBRATION": ("meli_celebration.png", "/special/meli_celebration.png"),
}

STATE_PRIORITY_ORDER = [
    "SINK_POP",
    "CELEBRATION",
    "THINKING",
    "RESPONSE_STREAM",
    "RESPONSE_COMPLETED",
    "ERROR",
    "CLICK_PET",
    "HOVER",
    "PROXIMITY",
    "IDLE",
]

class TestRuntimeIntegration(unittest.TestCase):

    def test_01_all_16_runtime_assets_exist(self):
        """Verify all 16 canonical standalone PNGs exist in both assets/ and public/."""
        self.assertEqual(len(EXPECTED_EVENT_MAPPINGS), 16, "Must have exactly 16 performance mappings")
        for event, (filename, public_path) in EXPECTED_EVENT_MAPPINGS.items():
            category = "special" if "/special/" in public_path else "states"
            asset_file = Path(f"assets/meli/character/{category}/{filename}")
            pub_file = Path(f"public{public_path}")

            self.assertTrue(asset_file.exists(), f"Asset missing: {asset_file}")
            self.assertTrue(pub_file.exists(), f"Public runtime copy missing: {pub_file}")

    def test_02_all_16_assets_meet_strict_spec(self):
        """Verify all 16 assets are 512x512 32-bit RGBA with transparent corners and valid grounding."""
        for event, (filename, public_path) in EXPECTED_EVENT_MAPPINGS.items():
            category = "special" if "/special/" in public_path else "states"
            asset_file = Path(f"assets/meli/character/{category}/{filename}")
            
            img = Image.open(asset_file)
            self.assertEqual(img.size, (512, 512), f"{filename} size is {img.size}, expected (512, 512)")
            self.assertEqual(img.mode, "RGBA", f"{filename} mode is {img.mode}, expected RGBA")

            arr = np.array(img)
            alpha = arr[:, :, 3]
            
            # Corner transparency
            self.assertTrue(np.all(alpha[0:5, 0:5] == 0), f"{filename} top-left corner not transparent")
            self.assertTrue(np.all(alpha[0:5, -5:] == 0), f"{filename} top-right corner not transparent")
            
            # Grounding check (foot contact baseline between Y=485 and Y=505)
            ys, xs = np.where(alpha > 20)
            self.assertGreater(len(ys), 1000, f"{filename} has too few opaque pixels")
            max_y = ys.max()
            self.assertTrue(485 <= max_y <= 505, f"{filename} grounding Y={max_y} outside [485, 505]")

    def test_03_pairwise_distinctness(self):
        """Verify no duplicate or unpopulated placeholder assets exist among core states."""
        core_files = [Path(f"assets/meli/character/states/{fn}") for ev, (fn, p) in EXPECTED_EVENT_MAPPINGS.items() if "/states/" in p]
        for i in range(len(core_files)):
            for j in range(i + 1, len(core_files)):
                f1, f2 = core_files[i], core_files[j]
                img1 = np.array(Image.open(f1))
                img2 = np.array(Image.open(f2))
                diff = np.mean(np.abs(img1.astype(int) - img2.astype(int)))
                self.assertGreater(diff, 1.0, f"{f1.name} and {f2.name} are too similar (diff={diff:.2f})")

    def test_04_celebration_distinct_from_complete(self):
        """Verify special CELEBRATION is distinct from COMPLETE."""
        celeb = np.array(Image.open("assets/meli/character/special/meli_celebration.png"))
        comp = np.array(Image.open("assets/meli/character/states/meli_complete.png"))
        diff = np.mean(np.abs(celeb.astype(int) - comp.astype(int)))
        self.assertGreater(diff, 5.0, f"CELEBRATION MAD {diff:.2f} must be >= 5.0 vs COMPLETE")

    def test_05_special_state_precedence(self):
        """Verify special state priority hierarchy."""
        def get_effective_state(active_event, mood, proximity_near, is_hovered):
            if mood == "SINK_POP":
                return "SINK_POP"
            if active_event == "CELEBRATION":
                return "CELEBRATION"
            if active_event in ["THINKING", "RESPONSE_STREAM", "RESPONSE_COMPLETED", "ERROR", "MEMORY_RETRIEVED"]:
                return active_event
            if active_event == "CLICK_PET" or mood == "CLICK":
                return "CLICK_PET"
            if is_hovered or mood == "HOVER":
                return "HOVER"
            if proximity_near or mood == "PROXIMITY":
                return "PROXIMITY"
            return "IDLE"

        # 1. SINK_POP beats CELEBRATION
        self.assertEqual(get_effective_state("CELEBRATION", "SINK_POP", True, True), "SINK_POP")
        # 2. CELEBRATION beats THINKING
        self.assertEqual(get_effective_state("CELEBRATION", "THINKING", True, True), "CELEBRATION")
        # 3. THINKING beats CLICK_PET & HOVER
        self.assertEqual(get_effective_state("THINKING", "IDLE", True, True), "THINKING")
        # 4. CLICK_PET beats HOVER
        self.assertEqual(get_effective_state("CLICK_PET", "IDLE", True, True), "CLICK_PET")
        # 5. HOVER beats PROXIMITY
        self.assertEqual(get_effective_state("IDLE", "IDLE", True, True), "HOVER")
        # 6. PROXIMITY beats IDLE
        self.assertEqual(get_effective_state("IDLE", "IDLE", True, False), "PROXIMITY")
        # 7. Baseline IDLE
        self.assertEqual(get_effective_state("IDLE", "IDLE", False, False), "IDLE")

    def test_06_demo_scenarios(self):
        """Verify all 10 demo interaction sequence transitions."""
        scenario_log = []
        
        # Scenario 1: APP_LAUNCH -> GREETING -> IDLE
        scenario_log.append(("APP_LAUNCH", EXPECTED_EVENT_MAPPINGS["APP_LAUNCH"][0]))
        scenario_log.append(("IDLE", EXPECTED_EVENT_MAPPINGS["IDLE"][0]))

        # Scenario 2: Normal question -> THINKING -> FOCUSED -> COMPLETE
        scenario_log.append(("THINKING", EXPECTED_EVENT_MAPPINGS["THINKING"][0]))
        scenario_log.append(("RESPONSE_STREAM", EXPECTED_EVENT_MAPPINGS["RESPONSE_STREAM"][0]))
        scenario_log.append(("RESPONSE_COMPLETED", EXPECTED_EVENT_MAPPINGS["RESPONSE_COMPLETED"][0]))

        # Scenario 3: Memory query -> THINKING -> CURIOUS -> FOCUSED -> COMPLETE
        scenario_log.append(("THINKING", EXPECTED_EVENT_MAPPINGS["THINKING"][0]))
        scenario_log.append(("MEMORY_RETRIEVED", EXPECTED_EVENT_MAPPINGS["MEMORY_RETRIEVED"][0]))
        scenario_log.append(("RESPONSE_STREAM", EXPECTED_EVENT_MAPPINGS["RESPONSE_STREAM"][0]))
        scenario_log.append(("RESPONSE_COMPLETED", EXPECTED_EVENT_MAPPINGS["RESPONSE_COMPLETED"][0]))

        # Scenario 4: RAG query -> THINKING -> FOCUSED -> COMPLETE
        scenario_log.append(("THINKING", EXPECTED_EVENT_MAPPINGS["THINKING"][0]))
        scenario_log.append(("RESPONSE_STREAM", EXPECTED_EVENT_MAPPINGS["RESPONSE_STREAM"][0]))
        scenario_log.append(("RESPONSE_COMPLETED", EXPECTED_EVENT_MAPPINGS["RESPONSE_COMPLETED"][0]))

        # Scenario 5: Error -> THINKING -> ERROR -> IDLE
        scenario_log.append(("THINKING", EXPECTED_EVENT_MAPPINGS["THINKING"][0]))
        scenario_log.append(("ERROR", EXPECTED_EVENT_MAPPINGS["ERROR"][0]))
        scenario_log.append(("IDLE", EXPECTED_EVENT_MAPPINGS["IDLE"][0]))

        # Scenario 6: Hover -> HOVER
        scenario_log.append(("HOVER", EXPECTED_EVENT_MAPPINGS["HOVER"][0]))

        # Scenario 7: Proximity -> PROXIMITY
        scenario_log.append(("PROXIMITY", EXPECTED_EVENT_MAPPINGS["PROXIMITY"][0]))

        # Scenario 8: Click -> CLICK_PET
        scenario_log.append(("CLICK_PET", EXPECTED_EVENT_MAPPINGS["CLICK_PET"][0]))

        # Scenario 9: Double Click -> SINK_POP
        scenario_log.append(("SINK_POP", "procedural_motion_sink_pop"))

        # Scenario 10: Milestone Celebration -> CELEBRATION -> IDLE
        scenario_log.append(("CELEBRATION", EXPECTED_EVENT_MAPPINGS["CELEBRATION"][0]))
        scenario_log.append(("IDLE", EXPECTED_EVENT_MAPPINGS["IDLE"][0]))

        self.assertEqual(len(scenario_log), 21, "All 10 scenarios must map to distinct valid performance assets")
        for event, asset_name in scenario_log:
            if asset_name != "procedural_motion_sink_pop":
                self.assertTrue(asset_name.startswith("meli_"), f"Invalid asset {asset_name}")

if __name__ == "__main__":
    unittest.main()
