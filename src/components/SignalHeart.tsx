import React from 'react';
import { motion } from 'framer-motion';
import { MeliMoodState } from '../state/CharacterStateMachine';

// Precise Left-Chest Emblem Anchor from Artwork (X=273.92 / 512 = 53.50%, Y=240.64 / 512 = 47.00%)
export const STATE_HEART_ANCHORS: Record<string, { xPct: number; yPct: number }> = {
  IDLE: { xPct: 53.50, yPct: 47.00 },
  idle: { xPct: 53.50, yPct: 47.00 },
  meli_body_base: { xPct: 53.50, yPct: 47.00 },
  CELEBRATION: { xPct: 53.50, yPct: 47.00 },
  celebration: { xPct: 53.50, yPct: 47.00 },
  THINKING: { xPct: 53.50, yPct: 47.00 },
  thinking: { xPct: 53.50, yPct: 47.00 },
  COMPLETE: { xPct: 53.50, yPct: 47.00 },
  complete: { xPct: 53.50, yPct: 47.00 },
  ERROR: { xPct: 53.50, yPct: 47.00 },
  error: { xPct: 53.50, yPct: 47.00 },
  CLICK: { xPct: 53.50, yPct: 47.00 },
  CLICK_PET: { xPct: 53.50, yPct: 47.00 },
  click_pet: { xPct: 53.50, yPct: 47.00 },
  HOVER: { xPct: 53.50, yPct: 47.00 },
  hover: { xPct: 53.50, yPct: 47.00 },
  PROXIMITY: { xPct: 53.50, yPct: 47.00 },
  proximity: { xPct: 53.50, yPct: 47.00 },
  SINK_POP: { xPct: 53.50, yPct: 47.00 },
  sink_pop: { xPct: 53.50, yPct: 47.00 },
  HAPPY: { xPct: 53.50, yPct: 47.00 },
  happy: { xPct: 53.50, yPct: 47.00 },
  FOCUSED: { xPct: 53.50, yPct: 47.00 },
  focused: { xPct: 53.50, yPct: 47.00 },
  CONFUSED: { xPct: 53.50, yPct: 47.00 },
  confused: { xPct: 53.50, yPct: 47.00 },
  CURIOUS: { xPct: 53.50, yPct: 47.00 },
  curious: { xPct: 53.50, yPct: 47.00 },
  SLEEPY: { xPct: 53.50, yPct: 47.00 },
  sleepy: { xPct: 53.50, yPct: 47.00 },
  SURPRISED: { xPct: 53.50, yPct: 47.00 },
  surprised: { xPct: 53.50, yPct: 47.00 },
  GREETING: { xPct: 53.50, yPct: 47.00 },
  greeting: { xPct: 53.50, yPct: 47.00 },
  WORKING: { xPct: 53.50, yPct: 47.00 },
  working: { xPct: 53.50, yPct: 47.00 },
};

interface SignalHeartProps {
  mood: MeliMoodState;
  activeState?: string;
}

export const SignalHeart: React.FC<SignalHeartProps> = ({ mood, activeState }) => {
  const currentKey = (activeState || mood || 'IDLE').toLowerCase();
  const anchor =
    STATE_HEART_ANCHORS[activeState || ''] ||
    STATE_HEART_ANCHORS[mood] ||
    STATE_HEART_ANCHORS[currentKey] ||
    STATE_HEART_ANCHORS.IDLE;

  // Rich chromatic appearance mapping for all 16 states & mood triggers
  const getHeartConfig = () => {
    switch (currentKey) {
      case 'thinking':
        return {
          fill: '#B388FF', // Soft Violet
          glowColor: 'rgba(179, 136, 255, 0.90)',
          scale: [1, 1.15, 0.95, 1.12, 1],
          opacity: [0.85, 1.0, 0.85],
          transition: { duration: 1.8, repeat: Infinity, ease: 'easeInOut' },
        };
      case 'working':
        return {
          fill: '#FFD54F', // Warm Golden Amber
          glowColor: 'rgba(255, 213, 79, 0.92)',
          scale: [1, 1.14, 1],
          opacity: [0.85, 1.0, 0.85],
          transition: { duration: 1.2, repeat: Infinity, ease: 'easeInOut' },
        };
      case 'focused':
        return {
          fill: '#7C4DFF', // Deep Electric Indigo / Blue
          glowColor: 'rgba(124, 77, 255, 0.92)',
          scale: [1, 1.08, 1],
          opacity: 1.0,
          transition: { duration: 2.0, repeat: Infinity, ease: 'easeInOut' },
        };
      case 'curious':
        return {
          fill: '#FFAB91', // Warm Peach / Coral
          glowColor: 'rgba(255, 171, 145, 0.90)',
          scale: [1, 1.15, 1],
          opacity: 1.0,
          transition: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' },
        };
      case 'surprised':
        return {
          fill: '#FFE082', // Radiant Sun Yellow
          glowColor: 'rgba(255, 224, 130, 0.95)',
          scale: [1, 1.25, 1],
          opacity: 1.0,
          transition: { duration: 0.8, repeat: 1, ease: 'easeOut' },
        };
      case 'confused':
        return {
          fill: '#FF9800', // Warning Amber / Orange
          glowColor: 'rgba(255, 152, 0, 0.90)',
          scale: [1, 1.12, 0.94, 1.10, 1],
          opacity: [0.8, 1.0, 0.8],
          transition: { duration: 1.6, repeat: Infinity, ease: 'easeInOut' },
        };
      case 'sleepy':
        return {
          fill: '#9FA8DA', // Soft Twilight Lavender / Indigo
          glowColor: 'rgba(159, 168, 218, 0.70)',
          scale: [1, 1.05, 1],
          opacity: [0.55, 0.80, 0.55],
          transition: { duration: 4.0, repeat: Infinity, ease: 'easeInOut' },
        };
      case 'greeting':
        return {
          fill: '#FF80AB', // Sunny Rose Pink
          glowColor: 'rgba(255, 128, 171, 0.92)',
          scale: [1, 1.22, 1],
          opacity: 1.0,
          transition: { duration: 0.6, ease: 'easeOut' },
        };
      case 'happy':
        return {
          fill: '#FF80AB', // Bright Warm Pink
          glowColor: 'rgba(255, 128, 171, 0.90)',
          scale: [1, 1.18, 1],
          opacity: 1.0,
          transition: { duration: 1.6, repeat: Infinity, ease: 'easeInOut' },
        };
      case 'celebration':
        return {
          fill: '#FFD700', // Sparkling Brilliant Gold
          glowColor: 'rgba(255, 215, 0, 0.98)',
          scale: [1, 1.32, 0.92, 1.25, 1],
          opacity: [0.9, 1.0, 0.9],
          transition: { duration: 0.9, repeat: Infinity, ease: 'easeInOut' },
        };
      case 'complete':
        return {
          fill: '#69F0AE', // Soft Spring Green
          glowColor: 'rgba(105, 240, 174, 0.95)',
          scale: [1, 1.25, 1],
          opacity: 1.0,
          transition: { duration: 0.6, ease: 'easeOut' },
        };
      case 'error':
        return {
          fill: '#FF5252', // Crimson Red
          glowColor: 'rgba(255, 82, 82, 0.95)',
          scale: [1, 1.20, 0.94, 1.12, 1],
          opacity: 0.95,
          transition: { duration: 0.8, repeat: 1, ease: 'easeInOut' },
        };
      case 'click':
      case 'click_pet':
        return {
          fill: '#FF4D88', // Radiant Magenta
          glowColor: 'rgba(255, 77, 136, 0.98)',
          scale: [1, 1.30, 1],
          opacity: 1.0,
          transition: { duration: 0.45, repeat: 1, ease: 'easeOut' },
        };
      case 'sink_pop':
        return {
          fill: '#FF7AA2',
          glowColor: 'rgba(255, 122, 162, 0.90)',
          scale: [1, 1.22, 0.92, 1.18, 1],
          opacity: 1.0,
          transition: { duration: 0.55, ease: 'easeInOut' },
        };
      case 'hover':
        return {
          fill: '#FF7AA2', // Brighter Rose
          glowColor: 'rgba(255, 122, 162, 0.90)',
          scale: 1.14,
          opacity: 0.95,
          transition: { duration: 0.25, ease: 'easeOut' },
        };
      case 'proximity':
        return {
          fill: '#FFB6C1',
          glowColor: 'rgba(255, 182, 193, 0.80)',
          scale: 1.06,
          opacity: 0.88,
          transition: { duration: 0.3, ease: 'easeOut' },
        };
      case 'idle':
      default:
        return {
          fill: '#FFB6C1', // Soft Pink
          glowColor: 'rgba(255, 182, 193, 0.70)',
          scale: [1, 1.08, 1],
          opacity: [0.75, 0.95, 0.75],
          transition: { duration: 3.2, repeat: Infinity, ease: 'easeInOut' },
        };
    }
  };

  const config = getHeartConfig();

  return (
    <motion.div
      id="signal-heart"
      className="signal-heart-container"
      animate={{
        top: `${anchor.yPct}%`,
        left: `${anchor.xPct}%`,
      }}
      transition={{
        duration: 0.25,
        ease: 'easeInOut',
      }}
      style={{
        position: 'absolute',
        transform: 'translate(-50%, -50%)',
        pointerEvents: 'none',
        zIndex: 10,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <motion.svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        animate={{
          scale: config.scale,
          opacity: config.opacity,
        }}
        transition={config.transition}
        style={{
          filter: `drop-shadow(0 0 5px ${config.glowColor}) drop-shadow(0 0 10px ${config.glowColor})`,
          transition: 'filter 0.35s ease',
        }}
      >
        <motion.path
          d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
          animate={{ fill: config.fill }}
          transition={{ duration: 0.35, ease: 'easeInOut' }}
        />
      </motion.svg>
    </motion.div>
  );
};
