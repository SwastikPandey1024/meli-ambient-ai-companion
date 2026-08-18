/**
 * FaceAnchorMap.ts - Canonical Face Geometry & Anchor Registry for Meli Expression Overlays
 *
 * Direct pixel measurements on assets/meli/character/meli_body_base.png (512x512 canvas)
 */

export interface PointAnchor {
  x: number;
  y: number;
  normalizedX: number; // 0.0 - 1.0
  normalizedY: number; // 0.0 - 1.0
}

export interface RectAnchor {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
}

export const CANONICAL_FACE_GEOMETRY = {
  canvas: { width: 512, height: 512 },
  faceBBox: {
    minX: 204,
    minY: 138,
    maxX: 312,
    maxY: 216,
    width: 108,
    height: 78,
  } as RectAnchor,
  anchors: {
    leftEye: { x: 234.4, y: 168.6, normalizedX: 0.4578, normalizedY: 0.3293 } as PointAnchor,
    rightEye: { x: 283.8, y: 167.5, normalizedX: 0.5543, normalizedY: 0.3271 } as PointAnchor,
    leftBrow: { x: 236.9, y: 147.2, normalizedX: 0.4627, normalizedY: 0.2875 } as PointAnchor,
    rightBrow: { x: 289.0, y: 147.7, normalizedX: 0.5645, normalizedY: 0.2885 } as PointAnchor,
    nose: { x: 256.0, y: 184.0, normalizedX: 0.5000, normalizedY: 0.3594 } as PointAnchor,
    mouth: { x: 254.0, y: 199.0, normalizedX: 0.4961, normalizedY: 0.3887 } as PointAnchor,
    leftCheek: { x: 216.0, y: 180.0, normalizedX: 0.4219, normalizedY: 0.3516 } as PointAnchor,
    rightCheek: { x: 298.0, y: 180.0, normalizedX: 0.5820, normalizedY: 0.3516 } as PointAnchor,
    signalHeart: { x: 259.42, y: 184.55, normalizedX: 0.5067, normalizedY: 0.3604 } as PointAnchor,
  },
} as const;
