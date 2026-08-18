/**
 * types.ts - Canonical 512x512 Coordinate Frame & Visual Enrichment Contracts
 *
 * Coordinate Contract:
 * - Canonical coordinate space: 512 × 512 pixels
 * - Normalized percentage anchors: (x: 0..100%, y: 0..100%)
 * - Transform Origin: 50% 96.88% (Grounded shoe baseline)
 * - All enrichment layers transform synchronously with the character transform node.
 */

import { MeliMoodState } from '../state/CharacterStateMachine';

/**
 * 2D normalized anchor within 512x512 canvas
 */
export interface CoordinateAnchor {
  readonly xPercent: number; // 0.0 to 100.0 (e.g. 50.67)
  readonly yPercent: number; // 0.0 to 100.0 (e.g. 29.5)
  readonly widthPercent?: number;
  readonly heightPercent?: number;
  readonly scale?: number;
  readonly rotationDeg?: number;
  readonly origin?: string; // e.g. 'center center' or '50% 50%'
}

/**
 * Canonical landmark coordinates on the 512x512 sprite canvas
 */
export const CANONICAL_LANDMARKS = {
  CANVAS_SIZE: 512,
  GROUNDING_ORIGIN: '50% 96.88%',
  CHEST_SIGNAL_HEART: { xPercent: 50.67, yPercent: 36.04 },
  HEAD_CENTER: { xPercent: 50.67, yPercent: 26.5 },
  FACE_CENTER: { xPercent: 50.67, yPercent: 28.5 },
  EYES_BRIDGE: { xPercent: 50.67, yPercent: 29.2 },
  EYE_LEFT: { xPercent: 44.5, yPercent: 28.6 },
  EYE_RIGHT: { xPercent: 56.8, yPercent: 28.6 },
  CHEEK_BLUSH_LEFT: { xPercent: 42.2, yPercent: 30.8 },
  CHEEK_BLUSH_RIGHT: { xPercent: 59.1, yPercent: 30.8 },
  MOUTH_CENTER: { xPercent: 50.67, yPercent: 32.4 },
  BUBBLE_TOP_ANCHOR: { xPercent: 50.67, yPercent: 4.0 },
  FOREGROUND_LAPTOP: { xPercent: 50.67, yPercent: 68.0 },
} as const;

/**
 * Visual Layer Depth (Z-Index hierarchy inside character transform node)
 */
export const ENRICHMENT_Z_INDEX = {
  SINK_PORTAL_BACKGROUND: 1,
  CANONICAL_BODY_SPRITE: 5,
  SIGNAL_HEART: 10,
  EXPRESSION_LAYER: 25,
  ACCESSORY_FACE: 30,
  ACCESSORY_HEAD: 35,
  ACCESSORY_FOREGROUND: 40,
  DIALOGUE_BUBBLE: 50,
} as const;

export type LayerDepth = typeof ENRICHMENT_Z_INDEX[keyof typeof ENRICHMENT_Z_INDEX];

/**
 * Generic Enrichment Layer Definition
 */
export interface LayerDefinition {
  id: string;
  name: string;
  zIndex: number;
  visible: boolean;
  opacity?: number;
  anchor: CoordinateAnchor;
}

/**
 * Transform state inherited from character motion pipeline
 */
export interface EnrichmentTransform {
  mood: MeliMoodState;
  isNear: boolean;
  gazeOffsetX: number;
  gazeOffsetY: number;
  gazeRotationDeg: number;
}
