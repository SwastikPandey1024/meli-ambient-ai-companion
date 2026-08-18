/**
 * NativeResponsiveLayout.test.ts - Unit Tests for Native Responsive Layout & Signal Heart
 */

import { describe, it, expect } from 'vitest';
import { ASSET_CATALOG } from '../components/AssetShowcaseModal';
import { STATE_HEART_ANCHORS, SignalHeart } from '../components/SignalHeart';
import { SIZE_DIMENSIONS } from '../platform';
import { getPerformanceAssetPath } from '../enrichment/PerformanceAssetManager';

describe('Meli Native Tauri — Responsive Layout & Safe Framing Verification', () => {
  describe('1. Canonical Window Dimensions & Size Presets', () => {
    it('provides valid responsive window dimensions for compact, default, large', () => {
      expect(SIZE_DIMENSIONS.compact).toEqual({ width: 280, height: 420 });
      expect(SIZE_DIMENSIONS.default).toEqual({ width: 360, height: 520 });
      expect(SIZE_DIMENSIONS.large).toEqual({ width: 460, height: 640 });
    });
  });

  describe('2. All 16 Performance States Anchor Mapping', () => {
    it('has Signal Heart chest anchor coordinates defined for all 16 states', () => {
      for (const item of ASSET_CATALOG) {
        const anchor = STATE_HEART_ANCHORS[item.key] || STATE_HEART_ANCHORS[item.key.toUpperCase()];
        expect(anchor, `Missing anchor for state ${item.key}`).toBeDefined();
        expect(anchor.xPct).toBeGreaterThan(40);
        expect(anchor.xPct).toBeLessThan(60);
        expect(anchor.yPct).toBeGreaterThan(20);
        expect(anchor.yPct).toBeLessThan(55);
      }
    });

    it('resolves valid PNG paths for all 16 states', () => {
      for (const item of ASSET_CATALOG) {
        const path = getPerformanceAssetPath(item.key);
        expect(path).toBeDefined();
        expect(path).toMatch(/\.png$/i);
      }
    });
  });

  describe('3. Signal Heart Component Integration', () => {
    it('exports SignalHeart React component', () => {
      expect(SignalHeart).toBeDefined();
    });
  });
});
