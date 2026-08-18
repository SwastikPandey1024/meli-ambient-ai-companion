import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  CharacterStateMachine,
  STATE_PRIORITY,
  SINK_POP_TIMING,
  STATE_MOTION_LIMITS,
} from '../state/CharacterStateMachine';

describe('CharacterStateMachine Phase 0 Strict Precedence & Motion Engine', () => {
  let sm: CharacterStateMachine;

  beforeEach(() => {
    sm = new CharacterStateMachine();
    vi.useFakeTimers();
  });

  it('initializes in IDLE mood', () => {
    expect(sm.getState()).toBe('IDLE');
  });

  it('switches to PROXIMITY on cursor proximity and returns to IDLE when leaving', () => {
    sm.onProximityUpdate(true);
    expect(sm.getState()).toBe('PROXIMITY');

    sm.onProximityUpdate(false);
    expect(sm.getState()).toBe('IDLE');
  });

  it('switches to HOVER on hover start and returns to IDLE on hover end', () => {
    sm.onHoverStart();
    expect(sm.getState()).toBe('HOVER');

    sm.onHoverEnd();
    expect(sm.getState()).toBe('IDLE');
  });

  it('triggers CLICK tactile bounce and reverts to ambient state after duration', () => {
    sm.triggerClick();
    expect(sm.getState()).toBe('CLICK');

    vi.advanceTimersByTime(700);
    expect(sm.getState()).toBe('IDLE');
  });

  it('triggers SINK_POP procedural micro-motion and locks state from lower-priority events', () => {
    const ok = sm.triggerSinkPop();
    expect(ok).toBe(true);
    expect(sm.getState()).toBe('SINK_POP');

    // Attempt lower priority events during SINK_POP - ALL MUST BE REJECTED
    sm.onHoverStart();
    expect(sm.getState()).toBe('SINK_POP');

    sm.onProximityUpdate(true);
    expect(sm.getState()).toBe('SINK_POP');

    const clickOk = sm.triggerClick();
    expect(clickOk).toBe(false);
    expect(sm.getState()).toBe('SINK_POP');

    // Verify SINK_POP completes full timing sequence and reverts cleanly
    vi.advanceTimersByTime(SINK_POP_TIMING.totalMs + 50);
    expect(sm.getState()).toBe('IDLE');
  });

  it('strictly enforces state priority table (SINK_POP > CLICK > HOVER > PROXIMITY > IDLE)', () => {
    expect(STATE_PRIORITY.SINK_POP).toBeGreaterThan(STATE_PRIORITY.CLICK);
    expect(STATE_PRIORITY.CLICK).toBeGreaterThan(STATE_PRIORITY.HOVER);
    expect(STATE_PRIORITY.HOVER).toBeGreaterThan(STATE_PRIORITY.PROXIMITY);
    expect(STATE_PRIORITY.PROXIMITY).toBeGreaterThan(STATE_PRIORITY.IDLE);
  });

  it('strictly adheres to global motion limits across all states (<= 4.0px, <= 2.0°)', () => {
    expect(STATE_MOTION_LIMITS.GLOBAL.maxTranslationPx).toBeLessThanOrEqual(4.0);
    expect(STATE_MOTION_LIMITS.GLOBAL.maxRotationDeg).toBeLessThanOrEqual(2.0);
    expect(STATE_MOTION_LIMITS.SINK_POP.anticipate.translateY).toBeLessThanOrEqual(4.0);
    expect(STATE_MOTION_LIMITS.SINK_POP.pop.translateY).toBeLessThanOrEqual(0.0);
    expect(STATE_MOTION_LIMITS.SINK_POP.pop.rotate).toBeLessThanOrEqual(2.0);
  });

  it('preserves volume during SINK_POP compression and pop overshoot', () => {
    const anticipateVol =
      STATE_MOTION_LIMITS.SINK_POP.anticipate.scaleX * STATE_MOTION_LIMITS.SINK_POP.anticipate.scaleY;
    const popVol =
      STATE_MOTION_LIMITS.SINK_POP.pop.scaleX * STATE_MOTION_LIMITS.SINK_POP.pop.scaleY;
    expect(anticipateVol).toBeCloseTo(0.9888, 3);
    expect(popVol).toBeGreaterThanOrEqual(1.0);
  });
});
