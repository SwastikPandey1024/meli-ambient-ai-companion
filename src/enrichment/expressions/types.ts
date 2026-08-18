/**
 * expressions/types.ts - Typed contracts for Composable Facial Expression Overlays
 */

export type EyeType =
  | 'neutral'
  | 'happy'
  | 'curious'
  | 'blink'
  | 'sleepy'
  | 'focused'
  | 'nervous'
  | 'surprised'
  | 'sparkle';

export type MouthType =
  | 'neutral'
  | 'smile'
  | 'small-o'
  | 'small-wave'
  | 'pout'
  | 'flat';

export type BrowType =
  | 'neutral'
  | 'raised'
  | 'furrowed'
  | 'asymmetric';

export interface FacialExpressionConfig {
  id: string;
  name: string;
  eyes?: EyeType;
  mouth?: MouthType;
  brows?: BrowType;
  blushOpacity?: number; // 0.0 to 1.0
  aegyoSal?: boolean;
  sparkles?: boolean;
  tears?: boolean;
}
