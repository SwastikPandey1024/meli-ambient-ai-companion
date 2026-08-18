/**
 * bubbles/types.ts - Typed contracts for Floating Companion Dialogue Bubbles
 */

export type BubbleEmotion =
  | 'CALM'
  | 'NERVOUS'
  | 'PLAYFUL'
  | 'SURPRISED'
  | 'SHY'
  | 'DELIGHTED';

export type BubbleMotionPreset =
  | 'pop_fade'
  | 'nervous_jitter'
  | 'gentle_breathe'
  | 'delighted_float';

export type ParticlePreset =
  | 'hearts'
  | 'sparkles'
  | 'sweat_drop'
  | 'question_mark'
  | 'none';

export interface CompanionBubble {
  id: string;
  text: string;
  emotion?: BubbleEmotion;
  motionPreset?: BubbleMotionPreset;
  durationMs?: number;
  particlePreset?: ParticlePreset;
  createdAt?: number;
}
