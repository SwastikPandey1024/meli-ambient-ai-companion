/**
 * expressions/presets.ts - Canonical Expression Presets & Transition Timing
 */

import { FacialExpressionConfig } from './types';

export const EXPRESSION_PRESETS: Record<string, FacialExpressionConfig> = {
  neutral: {
    id: 'neutral',
    name: 'Neutral Calm Resting',
    eyes: 'neutral',
    mouth: 'neutral',
    brows: 'neutral',
    blushOpacity: 0.12,
    aegyoSal: false,
  },

  curious: {
    id: 'curious',
    name: 'Curious Wonder',
    eyes: 'curious',
    mouth: 'small-o',
    brows: 'raised',
    blushOpacity: 0.35,
    aegyoSal: true,
  },

  focused: {
    id: 'focused',
    name: 'Focused Thinking',
    eyes: 'focused',
    mouth: 'flat',
    brows: 'furrowed',
    blushOpacity: 0.10,
    aegyoSal: false,
  },

  nervous: {
    id: 'nervous',
    name: 'Nervous Apologetic',
    eyes: 'nervous',
    mouth: 'small-wave',
    brows: 'asymmetric',
    blushOpacity: 0.45,
    aegyoSal: false,
  },

  surprised: {
    id: 'surprised',
    name: 'Surprised Alert',
    eyes: 'surprised',
    mouth: 'small-o',
    brows: 'raised',
    blushOpacity: 0.40,
    aegyoSal: true,
  },

  happy: {
    id: 'happy',
    name: 'Happy Joyful Smile',
    eyes: 'happy',
    mouth: 'smile',
    brows: 'raised',
    blushOpacity: 0.60,
    aegyoSal: true,
    sparkles: true,
  },
};

/**
 * Canonical transition timing configs (in milliseconds)
 */
export const EXPRESSION_TRANSITION_TIMING = {
  crossfadeDurationMs: 220,
  blushTransitionMs: 280,
  defaultDecayMs: 3000,
  presetDecays: {
    happy: 3200,
    curious: 2600,
    focused: 0, // Held until release
    nervous: 3000,
    surprised: 2400,
    neutral: 0,
  } as Record<string, number>,
} as const;

export function getExpressionPreset(id: string): FacialExpressionConfig {
  return EXPRESSION_PRESETS[id] || EXPRESSION_PRESETS.neutral;
}

export function getAllExpressionPresetIds(): string[] {
  return Object.keys(EXPRESSION_PRESETS);
}

export function getTransitionDecayMs(presetId: string): number {
  return EXPRESSION_TRANSITION_TIMING.presetDecays[presetId] ?? EXPRESSION_TRANSITION_TIMING.defaultDecayMs;
}
