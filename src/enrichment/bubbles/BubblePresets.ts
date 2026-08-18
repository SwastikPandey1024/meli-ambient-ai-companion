/**
 * bubbles/BubblePresets.ts - Motion Variants & Timing Presets for Companion Bubbles
 */

import { BubbleMotionPreset, BubbleEmotion } from './types';

export const DEFAULT_BUBBLE_DURATION_MS = 2500;

export interface BubbleVisualConfig {
  preset: BubbleMotionPreset;
  durationMs: number;
  textColor: string;
  borderColor: string;
  bgGradient: string;
}

export const BUBBLE_EMOTION_CONFIGS: Record<BubbleEmotion, BubbleVisualConfig> = {
  CALM: {
    preset: 'pop_fade',
    durationMs: 2400,
    textColor: '#FFD6E7',
    borderColor: 'rgba(255, 182, 193, 0.35)',
    bgGradient: 'linear-gradient(135deg, rgba(23, 24, 36, 0.92) 0%, rgba(38, 28, 44, 0.92) 100%)',
  },
  NERVOUS: {
    preset: 'nervous_jitter',
    durationMs: 2200,
    textColor: '#FFB6C1',
    borderColor: 'rgba(255, 122, 162, 0.50)',
    bgGradient: 'linear-gradient(135deg, rgba(30, 20, 32, 0.95) 0%, rgba(45, 25, 38, 0.95) 100%)',
  },
  PLAYFUL: {
    preset: 'gentle_breathe',
    durationMs: 2800,
    textColor: '#FFFFFF',
    borderColor: 'rgba(255, 122, 162, 0.65)',
    bgGradient: 'linear-gradient(135deg, rgba(42, 22, 45, 0.95) 0%, rgba(28, 18, 38, 0.95) 100%)',
  },
  DELIGHTED: {
    preset: 'delighted_float',
    durationMs: 2600,
    textColor: '#FFFFFF',
    borderColor: 'rgba(105, 240, 174, 0.55)',
    bgGradient: 'linear-gradient(135deg, rgba(20, 35, 30, 0.95) 0%, rgba(23, 24, 36, 0.95) 100%)',
  },
  SHY: {
    preset: 'pop_fade',
    durationMs: 2400,
    textColor: '#FFD6E7',
    borderColor: 'rgba(255, 182, 193, 0.40)',
    bgGradient: 'linear-gradient(135deg, rgba(28, 18, 30, 0.92) 0%, rgba(23, 24, 36, 0.92) 100%)',
  },
  SURPRISED: {
    preset: 'pop_fade',
    durationMs: 2000,
    textColor: '#FFFFFF',
    borderColor: 'rgba(179, 136, 255, 0.65)',
    bgGradient: 'linear-gradient(135deg, rgba(32, 24, 48, 0.95) 0%, rgba(23, 24, 36, 0.95) 100%)',
  },
};

export const BUBBLE_MOTION_VARIANTS = {
  pop_fade: {
    initial: { opacity: 0, scale: 0.75, y: 8 },
    animate: {
      opacity: [0, 1, 1, 0],
      scale: [0.75, 1.06, 1.0, 0.95],
      y: [8, 0, -8, -16],
      transition: {
        duration: 2.4,
        times: [0, 0.12, 0.80, 1.0],
        ease: 'easeOut',
      },
    },
  },

  nervous_jitter: {
    initial: { opacity: 0, scale: 0.85, y: 4, x: 0 },
    animate: {
      opacity: [0, 1, 1, 0],
      scale: [0.85, 1.04, 1.0, 0.92],
      x: [0, -3, 3, -2, 2, 0],
      y: [4, 0, -4, -10],
      transition: {
        duration: 2.2,
        times: [0, 0.15, 0.78, 1.0],
        ease: 'easeInOut',
      },
    },
  },

  gentle_breathe: {
    initial: { opacity: 0, scale: 0.8, y: 6 },
    animate: {
      opacity: [0, 1, 1, 0],
      scale: [0.8, 1.05, 0.98, 1.02, 0.95],
      y: [6, 0, -3, -6, -14],
      transition: {
        duration: 2.8,
        times: [0, 0.12, 0.45, 0.82, 1.0],
        ease: 'easeInOut',
      },
    },
  },

  delighted_float: {
    initial: { opacity: 0, scale: 0.7, y: 10 },
    animate: {
      opacity: [0, 1, 1, 0],
      scale: [0.7, 1.10, 1.0, 1.02, 0.9],
      y: [10, 0, -6, -12, -22],
      transition: {
        duration: 2.6,
        times: [0, 0.14, 0.5, 0.82, 1.0],
        ease: 'easeOut',
      },
    },
  },
};
