/**
 * CharacterStateMachine.ts - Phase 0 & Phase 1A State Machine with Strict Precedence
 *
 * State Precedence:
 * SINK_POP (100) > THINKING (90) > COMPLETE (85) > ERROR (85) > CLICK (80) > HOVER (40) > PROXIMITY (20) > IDLE (0)
 *
 * During SINK_POP:
 * - Lower-priority events (hover, proximity, idle, click) CANNOT interrupt or cancel the animation.
 * - Deep 1200ms sequence:
 *   Phase A (0-120ms): Anticipation (sX 1.03, sY 0.96, translateY +2px)
 *   Phase B (120-500ms): SINK (sX 0.72, sY 0.38, translateY +45px, op 0.85)
 *   Phase C (500-620ms): Enter / Disappear (sX 0.35, sY 0.10, translateY +65px, op 0.0)
 *   Phase D (620-700ms): Hidden Sink Hold (op 0.0, sY 0.10, sX 0.35)
 *   Phase E (700-900ms): Pop Out Spring (sX 1.08, sY 1.08, translateY -12px, rot 1.5°)
 *   Phase F (900-1200ms): Settle to IDLE
 */

export type MeliMoodState =
  | 'IDLE'
  | 'PROXIMITY'
  | 'HOVER'
  | 'CLICK'
  | 'SINK_POP'
  | 'THINKING'
  | 'COMPLETE'
  | 'ERROR';

export const STATE_PRIORITY: Record<MeliMoodState, number> = {
  SINK_POP: 100,
  THINKING: 90,
  COMPLETE: 85,
  ERROR: 85,
  CLICK: 80,
  HOVER: 40,
  PROXIMITY: 20,
  IDLE: 0,
};

export const SINK_POP_TIMING = {
  anticipateMs: 220,
  sinkMs: 280,
  disappearMs: 180,
  holdMs: 620,
  popMs: 350,
  settleMs: 150,
  totalMs: 1800,
} as const;

export const STATE_MOTION_LIMITS = {
  GLOBAL: {
    maxTranslationPx: 4.0,
    maxRotationDeg: 2.0,
  },
  IDLE: {
    maxTranslationPx: 1.5,
    maxRotationDeg: 0.0,
  },
  PROXIMITY: {
    maxTranslationPx: 2.0,
    maxRotationDeg: 1.8,
  },
  HOVER: {
    maxTranslationPx: 3.5,
    maxRotationDeg: 1.8,
  },
  CLICK: {
    maxTranslationPx: 4.0,
    maxRotationDeg: 2.0,
  },
  THINKING: {
    maxTranslationPx: 1.5,
    maxRotationDeg: 1.0,
  },
  COMPLETE: {
    maxTranslationPx: 2.0,
    maxRotationDeg: 1.0,
  },
  ERROR: {
    maxTranslationPx: 1.5,
    maxRotationDeg: 1.0,
  },
  SINK_POP: {
    anticipate: {
      translateY: 2.0,
      scaleY: 0.96,
      scaleX: 1.03,
      rotate: 0.0,
    },
    deepSink: {
      translateY: 45.0,
      scaleY: 0.38,
      scaleX: 0.72,
      rotate: -1.0,
    },
    disappear: {
      translateY: 65.0,
      scaleY: 0.10,
      scaleX: 0.35,
      rotate: 0.0,
      opacity: 0.0,
    },
    pop: {
      translateY: -12.0,
      scaleY: 1.08,
      scaleX: 1.08,
      rotate: 1.5,
      opacity: 1.0,
    },
  },
} as const;

export class CharacterStateMachine {
  private currentState: MeliMoodState = 'IDLE';
  private subscribers: Set<(state: MeliMoodState) => void> = new Set();
  private autoRevertTimer: number | null = null;
  private isHovered: boolean = false;
  private isNearby: boolean = false;

  public getState(): MeliMoodState {
    return this.currentState;
  }

  public subscribe(callback: (state: MeliMoodState) => void): () => void {
    this.subscribers.add(callback);
    callback(this.currentState);
    return () => this.subscribers.delete(callback);
  }

  private notify() {
    this.subscribers.forEach((cb) => cb(this.currentState));
  }

  private canTransition(targetState: MeliMoodState): boolean {
    const currentPriority = STATE_PRIORITY[this.currentState] ?? 0;
    const targetPriority = STATE_PRIORITY[targetState] ?? 0;
    return targetPriority >= currentPriority;
  }

  private setState(targetState: MeliMoodState, autoRevertMs: number = 0, force: boolean = false): boolean {
    if (!force && !this.canTransition(targetState)) {
      return false;
    }

    if (this.autoRevertTimer !== null) {
      clearTimeout(this.autoRevertTimer);
      this.autoRevertTimer = null;
    }

    this.currentState = targetState;
    this.notify();

    if (autoRevertMs > 0) {
      const scheduleTimer = typeof window !== 'undefined' ? window.setTimeout : setTimeout;
      this.autoRevertTimer = scheduleTimer(() => {
        this.revertToAmbient();
      }, autoRevertMs) as unknown as number;
    }

    return true;
  }

  public isLocked(): boolean {
    return this.currentState === 'SINK_POP';
  }

  private revertToAmbient() {
    this.autoRevertTimer = null;
    if (this.isHovered) {
      this.currentState = 'HOVER';
    } else if (this.isNearby) {
      this.currentState = 'PROXIMITY';
    } else {
      this.currentState = 'IDLE';
    }
    this.notify();
  }

  // Double-Click / QA SINK trigger: Deep 1200ms sequence
  public triggerSinkPop(): boolean {
    return this.setState('SINK_POP', SINK_POP_TIMING.totalMs, true);
  }

  // Single-Click Pet
  public triggerClick(): boolean {
    return this.setState('CLICK', 650);
  }

  public onHoverStart() {
    if (this.canTransition('HOVER')) {
      this.isHovered = true;
      this.setState('HOVER');
    }
  }

  public onHoverEnd() {
    this.isHovered = false;
    if (this.currentState === 'HOVER') {
      this.revertToAmbient();
    }
  }

  public onProximityUpdate(isNear: boolean) {
    if (!this.canTransition('PROXIMITY') && !this.canTransition('IDLE')) {
      return;
    }
    this.isNearby = isNear;
    if (isNear && this.currentState === 'IDLE') {
      this.setState('PROXIMITY');
    } else if (!isNear && this.currentState === 'PROXIMITY') {
      this.revertToAmbient();
    }
  }

  public setThinking(): boolean {
    return this.setState('THINKING', 0, true);
  }

  public setComplete(): boolean {
    return this.setState('COMPLETE', 2400, true);
  }

  public setError(): boolean {
    return this.setState('ERROR', 3000, true);
  }
}
