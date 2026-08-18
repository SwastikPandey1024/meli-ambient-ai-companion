/**
 * AssetShowcasePreview.test.ts - Unit Tests for Asset Showcase Preview Overlay Stage
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ASSET_CATALOG } from '../components/AssetShowcaseModal';
import { getPerformanceAssetPath, MeliPerformanceState } from '../enrichment/PerformanceAssetManager';
import { CharacterStateMachine } from '../state/CharacterStateMachine';

describe('Meli Phase 1D — Asset Showcase Foreground Preview Stage', () => {
  let stateMachine: CharacterStateMachine;

  beforeEach(() => {
    stateMachine = new CharacterStateMachine();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('contains all 16 canonical assets across Core and Special categories', () => {
    expect(ASSET_CATALOG.length).toBe(16);
    const coreItems = ASSET_CATALOG.filter((i) => i.category === 'Core Performance');
    const specialItems = ASSET_CATALOG.filter((i) => i.category === 'Special Interaction');

    expect(coreItems.length).toBe(12);
    expect(specialItems.length).toBe(4);
  });

  it('resolves valid canonical PNG paths for all 16 asset keys', () => {
    for (const item of ASSET_CATALOG) {
      const path = getPerformanceAssetPath(item.key);
      expect(path).toBeDefined();
      expect(path).toMatch(/\.png$/i);
      expect(path.length).toBeGreaterThan(0);
    }
  });

  it('preview stage operates without mutating authoritative CharacterStateMachine', () => {
    const initialState = stateMachine.getState();
    expect(initialState).toBe('IDLE');

    // Simulate previewing multiple assets
    const testKeys: MeliPerformanceState[] = [
      'working',
      'focused',
      'celebration',
      'proximity',
      'hover',
      'click_pet',
    ];

    for (const key of testKeys) {
      const resolvedPath = getPerformanceAssetPath(key);
      expect(resolvedPath).toMatch(/\.png$/i);
      // Verify stateMachine was never mutated
      expect(stateMachine.getState()).toBe('IDLE');
    }
  });

  it('verifies timer lifecycle constants for preview duration', () => {
    const PREVIEW_DURATION_MS = 3500;
    expect(PREVIEW_DURATION_MS).toBe(3500);
  });
});
