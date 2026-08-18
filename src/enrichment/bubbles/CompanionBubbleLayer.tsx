/**
 * CompanionBubbleLayer.tsx - Floating Reactive Companion Dialogue Bubbles
 */

import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CompanionBubble } from './types';
import { BUBBLE_EMOTION_CONFIGS, BUBBLE_MOTION_VARIANTS, DEFAULT_BUBBLE_DURATION_MS } from './BubblePresets';
import { ENRICHMENT_Z_INDEX } from '../types';

interface CompanionBubbleLayerProps {
  bubbles: CompanionBubble[];
  onDismiss: (id: string) => void;
}

export const CompanionBubbleLayer: React.FC<CompanionBubbleLayerProps> = ({
  bubbles,
  onDismiss,
}) => {
  return (
    <div
      className="companion-bubble-layer"
      style={{
        position: 'absolute',
        top: '6.0%',
        left: '50.67%',
        transform: 'translateX(-50%)',
        width: 'max-content',
        maxWidth: '85%',
        pointerEvents: 'none',
        zIndex: ENRICHMENT_Z_INDEX.DIALOGUE_BUBBLE,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '6px',
      }}
    >
      <AnimatePresence>
        {bubbles.map((bubble) => (
          <SingleBubbleItem
            key={bubble.id}
            bubble={bubble}
            onDismiss={onDismiss}
          />
        ))}
      </AnimatePresence>
    </div>
  );
};

const SingleBubbleItem: React.FC<{
  bubble: CompanionBubble;
  onDismiss: (id: string) => void;
}> = ({ bubble, onDismiss }) => {
  const emotion = bubble.emotion || 'CALM';
  const visualConfig = BUBBLE_EMOTION_CONFIGS[emotion] || BUBBLE_EMOTION_CONFIGS.CALM;
  const motionPreset = bubble.motionPreset || visualConfig.preset;
  const duration = bubble.durationMs || visualConfig.durationMs || DEFAULT_BUBBLE_DURATION_MS;

  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(bubble.id);
    }, duration);

    return () => clearTimeout(timer);
  }, [bubble.id, duration, onDismiss]);

  const variants = BUBBLE_MOTION_VARIANTS[motionPreset] || BUBBLE_MOTION_VARIANTS.pop_fade;

  return (
    <motion.div
      initial={variants.initial}
      animate={variants.animate}
      exit={{ opacity: 0, scale: 0.8, y: -15, transition: { duration: 0.25 } }}
      style={{
        position: 'relative',
        background: visualConfig.bgGradient,
        backdropFilter: 'blur(10px)',
        border: `1px solid ${visualConfig.borderColor}`,
        borderRadius: '14px',
        padding: '5px 12px',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.45)',
        color: visualConfig.textColor,
        fontSize: '12px',
        fontWeight: 600,
        letterSpacing: '0.3px',
        display: 'flex',
        alignItems: 'center',
        gap: '5px',
        whiteSpace: 'nowrap',
      }}
    >
      <span>{bubble.text}</span>

      {/* Downward pointing speech bubble tail */}
      <div
        style={{
          position: 'absolute',
          bottom: '-5px',
          left: '50%',
          transform: 'translateX(-50%) rotate(45deg)',
          width: '8px',
          height: '8px',
          background: visualConfig.bgGradient,
          borderRight: `1px solid ${visualConfig.borderColor}`,
          borderBottom: `1px solid ${visualConfig.borderColor}`,
        }}
      />
    </motion.div>
  );
};
