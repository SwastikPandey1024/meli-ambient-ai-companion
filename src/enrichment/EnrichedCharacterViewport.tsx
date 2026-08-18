/**
 * EnrichedCharacterViewport.tsx - Modular Character Compositor with Visual Enrichment Overlays
 *
 * Phase 0 Strict Preservation:
 * - Inherits canonical motion pipeline, SINK_POP sequence, SignalHeart chest centroid, and proximity gaze math.
 * - Composites ExpressionLayer, AccessoryLayer, SignalHeart, and CompanionBubbleLayer in the canonical 512x512 coordinate space.
 */

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CharacterStateMachine, MeliMoodState } from '../state/CharacterStateMachine';
import { useProximityTracker } from '../hooks/useProximityTracker';
import { ParticleEmitter, Particle } from '../components/ParticleEmitter';
import { SignalHeart } from '../components/SignalHeart';
import { CompanionBubbleLayer } from './bubbles/CompanionBubbleLayer';
import { CompanionBubble } from './bubbles/types';
import { MeliPerformanceState, getPerformanceAssetPath } from './PerformanceAssetManager';

export type CompanionSize = 'compact' | 'default' | 'large';

interface EnrichedCharacterViewportProps {
  stateMachine: CharacterStateMachine;
  size?: CompanionSize;
  activePerformanceState?: MeliPerformanceState;
  activeExpression?: string;
  equippedAccessories?: string[];
  bubbles?: CompanionBubble[];
  onDismissBubble?: (id: string) => void;
}

export const EnrichedCharacterViewport: React.FC<EnrichedCharacterViewportProps> = ({
  stateMachine,
  size = 'default',
  activePerformanceState = 'idle',
  activeExpression = 'idle',
  equippedAccessories: _equippedAccessories = [],
  bubbles = [],
  onDismissBubble = () => { },
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [mood, setMood] = useState<MeliMoodState>(stateMachine.getState());
  const [particles, setParticles] = useState<Particle[]>([]);
  const clickCountRef = useRef<number>(0);
  const clickTimerRef = useRef<number | null>(null);
  const proximity = useProximityTracker(containerRef);

  // Determine current active performance image asset with strict precedence:
  // Active Companion Event > Custom Override > StateMachine Mood > Ambient IDLE
  let resolvedKey = 'IDLE';
  if (activePerformanceState && activePerformanceState !== 'idle') {
    resolvedKey = activePerformanceState;
  } else if (activeExpression && activeExpression !== 'idle' && activeExpression !== 'neutral') {
    resolvedKey = activeExpression;
  } else if (mood && mood !== 'IDLE') {
    resolvedKey = mood === 'CLICK' ? 'CLICK_PET' : mood;
  }
  const performanceAssetSrc = getPerformanceAssetPath(resolvedKey);

  // Max dimension bounds for S/M/L profiles while respecting viewport containment
  const sizeMap: Record<CompanionSize, { maxDim: number }> = {
    compact: { maxDim: 280 },
    default: { maxDim: 380 },
    large: { maxDim: 480 },
  };

  const currentDim = sizeMap[size] || sizeMap.default;

  // Subscribe to state machine
  useEffect(() => {
    return stateMachine.subscribe((nextMood) => {
      setMood(nextMood);
    });
  }, [stateMachine]);

  // Feed proximity
  useEffect(() => {
    stateMachine.onProximityUpdate(proximity.isNear);
  }, [proximity.isNear, stateMachine]);

  // Single Click Trigger (Pet Meli)
  const handleSingleClick = useCallback(() => {
    stateMachine.triggerClick();

    // Spawn subtle heart/sparkle particles around Chest Signal Heart area
    const rect = containerRef.current?.getBoundingClientRect();
    if (rect) {
      const heartX = rect.width * 0.5067;
      const heartY = rect.height * 0.3604;
      const newParticles: Particle[] = Array.from({ length: 6 }).map((_, i) => ({
        id: Date.now() + i,
        x: heartX + (Math.random() * 20 - 10),
        y: heartY + (Math.random() * 20 - 10),
        vx: (Math.random() - 0.5) * 60,
        vy: -20 - Math.random() * 45,
        size: 5 + Math.random() * 6,
        color: ['#FFB6C1', '#FF7AA2', '#FFD6E7', '#FFFFFF'][i % 4],
      }));
      setParticles((prev) => [...prev, ...newParticles]);

      setTimeout(() => {
        setParticles((prev) => prev.filter((p) => !newParticles.includes(p)));
      }, 700);
    }
  }, [stateMachine]);

  // Double Click Trigger (SINK / POP)
  const handleDoubleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (clickTimerRef.current !== null) {
        clearTimeout(clickTimerRef.current);
        clickTimerRef.current = null;
      }
      clickCountRef.current = 0;
      stateMachine.triggerSinkPop();
    },
    [stateMachine]
  );

  // Reliable click & double click dispatcher
  const handleClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.control-capsule') || (e.target as HTMLElement).closest('.meli-chat-panel')) return;

    clickCountRef.current += 1;
    if (clickCountRef.current === 1) {
      clickTimerRef.current = window.setTimeout(() => {
        clickCountRef.current = 0;
        clickTimerRef.current = null;
        handleSingleClick();
      }, 280);
    } else if (clickCountRef.current >= 2) {
      if (clickTimerRef.current !== null) {
        clearTimeout(clickTimerRef.current);
        clickTimerRef.current = null;
      }
      clickCountRef.current = 0;
      stateMachine.triggerSinkPop();
    }
  };

  // Motion variants with deep SINK / POP sequence (1200ms) - strictly matches Phase 0
  const getMotionVariants = () => {
    switch (mood) {
      case 'SINK_POP':
        return {
          animate: {
            y: [0, 2, 45, 65, 65, -12, 0],
            scaleY: [1.0, 0.96, 0.38, 0.10, 0.10, 1.08, 1.0],
            scaleX: [1.0, 1.03, 0.72, 0.35, 0.35, 1.08, 1.0],
            rotate: [0, 0, -1.0, 0, 0, 1.5, 0],
            opacity: [1.0, 1.0, 0.85, 0.0, 0.0, 1.0, 1.0],
            transition: {
              duration: 1.20,
              times: [0, 0.10, 0.42, 0.52, 0.58, 0.75, 1.0],
              ease: 'easeInOut',
            },
          },
        };
      case 'CLICK':
        return {
          animate: {
            y: [0, -4, 1.5, 0],
            scaleY: [1, 1.025, 0.98, 1],
            scaleX: [1, 0.98, 1.02, 1],
            rotate: [0, -1.5, 1.0, 0],
            opacity: 1,
            transition: { duration: 0.65, ease: 'easeOut' },
          },
        };
      case 'HOVER':
        return {
          animate: {
            y: -3.5,
            scaleY: 1.015,
            scaleX: 0.99,
            rotate: proximity.rotationDeg,
            opacity: 1,
            transition: { duration: 0.22, ease: 'easeOut' },
          },
        };
      case 'PROXIMITY':
        return {
          animate: {
            x: proximity.offsetX,
            y: proximity.offsetY,
            rotate: proximity.rotationDeg,
            scaleY: 1.005,
            scaleX: 0.995,
            opacity: 1,
            transition: { type: 'spring', damping: 15, stiffness: 120 },
          },
        };
      case 'IDLE':
      default:
        return {
          animate: {
            y: [0, -1.5, 0],
            scaleY: [1, 1.004, 1],
            scaleX: [1, 0.998, 1],
            rotate: 0,
            opacity: 1,
            transition: {
              duration: 3.2,
              repeat: Infinity,
              ease: 'easeInOut',
            },
          },
        };
    }
  };

  const variants = getMotionVariants();

  return (
    <div
      ref={containerRef}
      className={`character-root size-${size}`}
      style={{
        width: '100%',
        maxWidth: `min(${currentDim.maxDim}px, 94vw, calc(100vh - 40px))`,
        aspectRatio: '1 / 1',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
      }}
      onMouseEnter={() => stateMachine.onHoverStart()}
      onMouseLeave={() => stateMachine.onHoverEnd()}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
    >
      <ParticleEmitter particles={particles} />

      {/* Floating Companion Bubble Layer (Z: 50) */}
      <CompanionBubbleLayer bubbles={bubbles} onDismiss={onDismissBubble} />

      {/* Canonical 1:1 Composition Root: Locks SinkPortal and CharacterTransformNode to identical coordinate space */}
      <div
        className="character-composition-root"
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          aspectRatio: '1 / 1',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'visible',
        }}
      >
        {/* Grounded Sink Portal (Z: 1) - Rendered strictly and exclusively during SINK_POP */}
        <AnimatePresence>
          {mood === 'SINK_POP' && (
            <motion.div
              key="sink-portal"
              className="sink-portal"
              initial={{ opacity: 0, x: '-50%', y: '-50%', scaleX: 0.3, scaleY: 0.1 }}
              animate={{
                opacity: [0, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85],
                scaleX: [0.3, 1.0, 0.92, 0.80, 0.80, 1.15, 1.0],
                scaleY: [0.15, 0.45, 0.60, 0.70, 0.70, 0.55, 0.45],
                x: '-50%',
                y: '-50%',
                transition: {
                  duration: 1.20,
                  times: [0, 0.08, 0.42, 0.52, 0.58, 0.85, 1.0],
                  ease: 'easeInOut',
                },
              }}
              exit={{
                opacity: 0,
                scaleX: 0.3,
                scaleY: 0.1,
                x: '-50%',
                y: '-50%',
                transition: { duration: 0.15, ease: 'easeOut' },
              }}
            >
              <div className="sink-portal-inner" />
              <div className="sink-portal-glow" />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Canonical CharacterTransformNode (Z: 5) */}
        <motion.div
          className="character-transform-node"
          animate={variants.animate}
          style={{
            width: '100%',
            height: '100%',
            position: 'relative',
            transformOrigin: '50% 96.88%',
          }}
        >
          {/* Signal Heart Component (Z: 10) - Glowing Chest Centroid */}
          <SignalHeart
            mood={mood}
            activeState={activePerformanceState || activeExpression || mood}
          />

          {/* Standalone Complete Performance Illustration (Z: 5) */}
          <AnimatePresence mode="wait">
            <motion.img
              key={performanceAssetSrc}
              src={performanceAssetSrc}
              alt="Meli"
              className="meli-sprite-img"
              draggable={false}
              initial={{ opacity: 0.85 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0.85 }}
              transition={{ duration: 0.2, ease: 'easeInOut' }}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                objectPosition: 'center bottom',
                display: 'block',
                userSelect: 'none',
                pointerEvents: 'none',
              }}
            />
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
};
