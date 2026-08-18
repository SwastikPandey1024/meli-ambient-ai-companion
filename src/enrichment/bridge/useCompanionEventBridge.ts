import { useState, useEffect, useCallback, useRef } from 'react';
import { CompanionEventManager, companionEvents } from './CompanionEventManager';
import { CompanionEventPayload } from './types';
import { CompanionBubble } from '../bubbles/types';
import { FacialExpressionConfig } from '../expressions/types';
import { getExpressionPreset, getTransitionDecayMs } from '../expressions/presets';
import { CharacterStateMachine } from '../../state/CharacterStateMachine';
import { MeliPerformanceState, resolvePerformanceState } from '../PerformanceAssetManager';

interface UseCompanionEventBridgeOptions {
  enableAutoBubbles?: boolean;
  eventManager?: CompanionEventManager;
  stateMachine?: CharacterStateMachine;
}

export function useCompanionEventBridge(options: UseCompanionEventBridgeOptions = {}) {
  const { enableAutoBubbles = true, eventManager = companionEvents, stateMachine } = options;

  const [activePerformanceState, setActivePerformanceState] = useState<MeliPerformanceState>('idle');
  const [activeExpression, setActiveExpression] = useState<FacialExpressionConfig>(
    getExpressionPreset('neutral')
  );
  const [bubbles, setBubbles] = useState<CompanionBubble[]>([]);
  const [equippedAccessories, setEquippedAccessories] = useState<string[]>(['glasses']);
  const decayTimerRef = useRef<number | null>(null);

  // Set transient performance state with deterministic auto-revert to ambient baseline
  const setPerformanceWithDecay = useCallback((state: MeliPerformanceState, durationMs: number = 0) => {
    // Stale transition cancellation: safely clear pending timer
    if (decayTimerRef.current !== null) {
      clearTimeout(decayTimerRef.current);
      decayTimerRef.current = null;
    }

    setActivePerformanceState(state);

    if (durationMs > 0) {
      decayTimerRef.current = window.setTimeout(() => {
        setActivePerformanceState('idle');
        decayTimerRef.current = null;
      }, durationMs);
    }
  }, []);

  // Backward compatible preset helper
  const setExpressionWithDecay = useCallback((presetName: string, durationMs?: number) => {
    const resolvedDuration = durationMs !== undefined ? durationMs : getTransitionDecayMs(presetName);
    setActiveExpression(getExpressionPreset(presetName));
    const perfState = resolvePerformanceState(presetName);
    setPerformanceWithDecay(perfState, resolvedDuration);
  }, [setPerformanceWithDecay]);

  // Spawn companion bubble
  const spawnBubble = useCallback((bubble: Omit<CompanionBubble, 'id' | 'createdAt'>) => {
    const newBubble: CompanionBubble = {
      ...bubble,
      id: `bubble-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      createdAt: Date.now(),
    };
    setBubbles((prev) => [...prev.slice(-2), newBubble]); // Max 3 concurrent bubbles
    return newBubble.id;
  }, []);

  // Dismiss single bubble
  const dismissBubble = useCallback((id: string) => {
    setBubbles((prev) => prev.filter((b) => b.id !== id));
  }, []);

  // Toggle accessory equipped state
  const toggleAccessory = useCallback((accessoryId: string) => {
    setEquippedAccessories((prev) =>
      prev.includes(accessoryId) ? prev.filter((id) => id !== accessoryId) : [...prev, accessoryId]
    );
  }, []);

  // Process structured companion events with strict special-state priority
  useEffect(() => {
    return eventManager.subscribe((event: CompanionEventPayload) => {
      switch (event.type) {
        case 'THINKING':
          stateMachine?.setThinking();
          setPerformanceWithDecay('thinking', 0); // Held until response or completed
          if (enableAutoBubbles) {
            spawnBubble({
              text: '...',
              emotion: 'CALM',
              durationMs: 2000,
            });
          }
          break;

        case 'MEMORY_RETRIEVED':
          setPerformanceWithDecay('curious', 2200);
          if (enableAutoBubbles && event.message) {
            spawnBubble({
              text: event.message,
              emotion: 'SURPRISED',
              durationMs: 2200,
            });
          }
          break;

        case 'TOOL_REQUESTED':
          setPerformanceWithDecay('focused', 2000);
          break;

        case 'TOOL_CONFIRMATION_REQUIRED':
          setPerformanceWithDecay('curious', 3500);
          if (enableAutoBubbles && event.message) {
            spawnBubble({
              text: event.message,
              emotion: 'SURPRISED',
              durationMs: 3500,
            });
          }
          break;

        case 'TOOL_STARTED':
          setPerformanceWithDecay('focused', 0);
          if (enableAutoBubbles && event.message) {
            spawnBubble({
              text: event.message,
              emotion: 'CALM',
              durationMs: 2200,
            });
          }
          break;

        case 'TOOL_COMPLETED':
          stateMachine?.setComplete();
          setPerformanceWithDecay('complete', 2200);
          break;

        case 'TOOL_FAILED':
          stateMachine?.setError();
          setPerformanceWithDecay('error', 2500);
          break;

        case 'RESPONSE_STREAM':
          setPerformanceWithDecay('focused', 0);
          break;

        case 'RESPONSE_COMPLETED':
          stateMachine?.setComplete();
          setPerformanceWithDecay('complete', 2400);
          if (enableAutoBubbles && event.message && event.message !== 'Response completed') {
            spawnBubble({
              text: event.message,
              emotion: 'DELIGHTED',
              durationMs: 2600,
            });
          }
          break;

        case 'ERROR':
          stateMachine?.setError();
          setPerformanceWithDecay('error', 3000);
          if (enableAutoBubbles) {
            spawnBubble({
              text: event.message || 'eeh...',
              emotion: 'NERVOUS',
              durationMs: 2400,
            });
          }
          break;

        case 'APP_LAUNCH':
          setPerformanceWithDecay('greeting', 2500);
          break;

        case 'WORKING':
          setPerformanceWithDecay('working', 2500);
          break;

        case 'SLEEP':
          setPerformanceWithDecay('sleepy', 3000);
          break;

        case 'CONFUSED':
          setPerformanceWithDecay('confused', 2500);
          break;

        case 'SURPRISED':
          setPerformanceWithDecay('surprised', 2500);
          break;

        case 'SHOWCASE_PREVIEW':
          if (event.visual_hint) {
            setPerformanceWithDecay(event.visual_hint as any, 3500);
          }
          break;

        case 'HAPPY':
          setPerformanceWithDecay('happy', 2200);
          break;

        case 'CLICK_PET':
          stateMachine?.triggerClick();
          setPerformanceWithDecay('click_pet', 650);
          break;

        case 'HOVER':
          setPerformanceWithDecay('hover', 0);
          break;

        case 'PROXIMITY':
          setPerformanceWithDecay('proximity', 0);
          break;

        case 'CELEBRATION':
          setPerformanceWithDecay('celebration', 3200);
          if (enableAutoBubbles && event.message) {
            spawnBubble({
              text: event.message || 'Yay! We did it! 🎉',
              emotion: 'DELIGHTED',
              durationMs: 3000,
            });
          }
          break;

        case 'LISTENING':
          setPerformanceWithDecay('curious', 0);
          break;

        case 'TRANSCRIBING':
          setPerformanceWithDecay('thinking', 0);
          break;

        case 'SPEAKING':
          // Choose happy or focused depending on visual hint/message
          if (event.visual_hint === 'focused') {
            setPerformanceWithDecay('focused', 0);
          } else {
            setPerformanceWithDecay('happy', 0);
          }
          break;

        case 'IDLE':
        default:
          setPerformanceWithDecay('idle', 0);
          break;
      }
    });
  }, [eventManager, stateMachine, enableAutoBubbles, setPerformanceWithDecay, spawnBubble]);

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      if (decayTimerRef.current !== null) {
        clearTimeout(decayTimerRef.current);
      }
    };
  }, []);

  return {
    activePerformanceState,
    setPerformanceState: setPerformanceWithDecay,
    activeExpression,
    setExpression: setActiveExpression,
    setExpressionPreset: setExpressionWithDecay,
    bubbles,
    spawnBubble,
    dismissBubble,
    equippedAccessories,
    setEquippedAccessories,
    toggleAccessory,
  };
}

