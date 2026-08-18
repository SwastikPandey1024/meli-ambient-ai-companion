import { describe, it, expect } from 'vitest';
import {
  PERFORMANCE_ASSET_MAP,
  resolvePerformanceState,
  getPerformanceAssetPath,
  MeliPerformanceState,
} from '../enrichment/PerformanceAssetManager';

describe('PerformanceAssetManager Runtime Integration Tests', () => {
  it('contains all 16 canonical standalone performance assets', () => {
    const expectedKeys: MeliPerformanceState[] = [
      'idle',
      'curious',
      'happy',
      'thinking',
      'working',
      'focused',
      'sleepy',
      'confused',
      'surprised',
      'error',
      'complete',
      'greeting',
      'celebration',
      'proximity',
      'hover',
      'click_pet',
    ];

    expect(Object.keys(PERFORMANCE_ASSET_MAP)).toHaveLength(16);
    expectedKeys.forEach((key) => {
      expect(PERFORMANCE_ASSET_MAP[key]).toBeDefined();
      expect(PERFORMANCE_ASSET_MAP[key]).toMatch(/\.png$/);
    });
  });

  it('maps all 12 core performance events accurately', () => {
    expect(resolvePerformanceState('IDLE')).toBe('idle');
    expect(resolvePerformanceState('THINKING')).toBe('thinking');
    expect(resolvePerformanceState('MEMORY_RETRIEVED')).toBe('curious');
    expect(resolvePerformanceState('RESPONSE_STREAM')).toBe('focused');
    expect(resolvePerformanceState('RESPONSE_COMPLETED')).toBe('complete');
    expect(resolvePerformanceState('ERROR')).toBe('error');
    expect(resolvePerformanceState('APP_LAUNCH')).toBe('greeting');
    expect(resolvePerformanceState('WORKING')).toBe('working');
    expect(resolvePerformanceState('SLEEP')).toBe('sleepy');
    expect(resolvePerformanceState('CONFUSED')).toBe('confused');
    expect(resolvePerformanceState('SURPRISED')).toBe('surprised');
    expect(resolvePerformanceState('HAPPY')).toBe('happy');
  });

  it('maps all 4 special performance events accurately', () => {
    expect(resolvePerformanceState('PROXIMITY')).toBe('proximity');
    expect(resolvePerformanceState('HOVER')).toBe('hover');
    expect(resolvePerformanceState('CLICK_PET')).toBe('click_pet');
    expect(resolvePerformanceState('CELEBRATION')).toBe('celebration');
  });

  it('resolves correct file paths for all events', () => {
    expect(getPerformanceAssetPath('IDLE')).toBe('/states/meli_idle.png');
    expect(getPerformanceAssetPath('THINKING')).toBe('/states/meli_thinking.png');
    expect(getPerformanceAssetPath('RESPONSE_STREAM')).toBe('/states/meli_focused.png');
    expect(getPerformanceAssetPath('RESPONSE_COMPLETED')).toBe('/states/meli_complete.png');
    expect(getPerformanceAssetPath('CELEBRATION')).toBe('/special/meli_celebration.png');
    expect(getPerformanceAssetPath('CLICK_PET')).toBe('/special/meli_click_pet.png');
    expect(getPerformanceAssetPath('HOVER')).toBe('/special/meli_hover.png');
    expect(getPerformanceAssetPath('PROXIMITY')).toBe('/special/meli_proximity.png');
  });
});
