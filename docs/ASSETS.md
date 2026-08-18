# Meli Asset Manifest & Visual Policy

This document catalogs the 16 approved, frozen standalone illustrations and defines the immutable asset policy for Meli.

---

## 1. Immutable Asset Policy

> **CRITICAL RULE**: All 16 standalone PNG illustrations in `public/states/`, `public/special/`, and the base character sprite `assets/meli/character/meli_body_base.png` are **100% frozen and immutable**.
> Under no circumstances should runtime code modify, resize, recolor, crop, or regenerate these image files.

---

## 2. 16 Performance Assets Catalog

### Core Performance States (`public/states/`)

| # | File Name | Canonical State | Resolution | Description |
| :- | :--- | :--- | :--- | :--- |
| **01** | `meli_idle.png` | `IDLE` | 512x512 | Default ambient resting pose. |
| **02** | `meli_curious.png` | `CURIOUS` | 512x512 | Attentive curiosity upon question or memory recall. |
| **03** | `meli_happy.png` | `HAPPY` | 512x512 | Warm smile upon praise or friendly interaction. |
| **04** | `meli_thinking.png` | `THINKING` | 512x512 | Concentrated reasoning during LLM query stream. |
| **05** | `meli_working.png` | `WORKING` | 512x512 | Active engagement during tool execution. |
| **06** | `meli_focused.png` | `FOCUSED` | 512x512 | Intense focus during enterprise search & analysis. |
| **07** | `meli_sleepy.png` | `SLEEPY` | 512x512 | Resting/sleepy state during extended user inactivity. |
| **08** | `meli_confused.png` | `CONFUSED` | 512x512 | Perplexed expression upon ambiguous requests. |
| **09** | `meli_surprised.png`| `SURPRISED` | 512x512 | Sudden discovery or return from absence. |
| **10** | `meli_error.png` | `ERROR` | 512x512 | Concern / apology upon tool failure or blocked action. |
| **11** | `meli_complete.png` | `COMPLETE` | 512x512 | Satisfied smile upon successful task completion. |
| **12** | `meli_greeting.png` | `GREETING` | 512x512 | Cheerful wave on initial boot or window unhide. |

### Special Interaction States (`public/special/`)

| # | File Name | Canonical State | Resolution | Description |
| :- | :--- | :--- | :--- | :--- |
| **13** | `meli_click_pet.png` | `CLICK_PET` | 512x512 | Tactile single-click reaction pose. |
| **14** | `meli_hover.png` | `HOVER` | 512x512 | Light hovering posture upon cursor contact. |
| **15** | `meli_proximity.png`| `PROXIMITY` | 512x512 | Subtle gaze tracking towards mouse position. |
| **16** | `meli_celebration.png`| `CELEBRATION` | 512x512 | Fist-pump celebration with confetti particles. |

---

## 3. Canonical Composition & Grounding Baseline

- **Canvas Size**: 512x512 pixels (Aspect Ratio: 1 / 1).
- **Grounding Baseline**: `Y = 496.0px` (`96.88%` of canvas height).
- **Signal Heart Centroid**: `X = 273.92px` (`53.50%`), `Y = 240.64px` (`47.00%`).
