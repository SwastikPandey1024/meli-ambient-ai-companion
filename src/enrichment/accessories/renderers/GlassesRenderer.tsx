/**
 * GlassesRenderer.tsx - Procedural SVG Oversized Wireframe Glasses (Proof of Concept)
 *
 * Design Spec:
 * - Oversized rounded wireframe frame with delicate double bridge
 * - Soft rose-gold & charcoal finish (#FFB6C1 / #2D2230 / #FF7AA2)
 * - Subtle anti-glare reflection lens sheen
 * - Anchored at the nasal bridge / eye line (X: 50.67%, Y: 29.2%)
 * - 100% vector SVG, zero layout shift, seamless S/M/L scaling
 */

import React from 'react';
import { motion } from 'framer-motion';
import { AccessoryRenderProps } from '../types';

export const GlassesRenderer: React.FC<AccessoryRenderProps> = ({ config, mood, enabled }) => {
  if (!enabled) return null;

  const { anchor } = config;
  const mod = config.stateTriggers?.[mood] || {};
  const yShift = mod.offsetYPx ?? 0;
  const rotMod = mod.rotationDeg ?? 0;
  const scaleMod = mod.scaleFactor ?? 1.0;

  return (
    <motion.div
      className="accessory-glasses-container"
      style={{
        position: 'absolute',
        top: `${anchor.yPercent}%`,
        left: `${anchor.xPercent}%`,
        width: `${anchor.widthPercent ?? 34}%`,
        height: `${anchor.heightPercent ?? 15}%`,
        transform: 'translate(-50%, -50%)',
        transformOrigin: anchor.origin || '50% 50%',
        zIndex: config.zIndex,
        pointerEvents: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      animate={{
        y: yShift,
        rotate: rotMod,
        scale: scaleMod,
        opacity: mod.opacity ?? 1.0,
      }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      <svg
        viewBox="0 0 174 76"
        width="100%"
        height="100%"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ filter: 'drop-shadow(0 2px 5px rgba(23, 24, 36, 0.45))' }}
      >
        <defs>
          <linearGradient id="roseGoldFrame" x1="0" y1="0" x2="174" y2="76" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#FFD6E7" />
            <stop offset="45%" stopColor="#FF7AA2" />
            <stop offset="80%" stopColor="#E284A5" />
            <stop offset="100%" stopColor="#FFD6E7" />
          </linearGradient>

          <linearGradient id="lensSheen" x1="10" y1="10" x2="60" y2="60" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.40" />
            <stop offset="40%" stopColor="#FFFFFF" stopOpacity="0.10" />
            <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0.0" />
          </linearGradient>

          <linearGradient id="lensSheenRight" x1="110" y1="10" x2="160" y2="60" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.40" />
            <stop offset="40%" stopColor="#FFFFFF" stopOpacity="0.10" />
            <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Left Lens Glass Sheen */}
        <rect
          x="12"
          y="11"
          width="64"
          height="54"
          rx="22"
          fill="rgba(255, 255, 255, 0.08)"
          stroke="rgba(255, 214, 231, 0.15)"
          strokeWidth="1"
        />
        {/* Left Lens Glare Reflection Line */}
        <path
          d="M24 16 L56 48"
          stroke="url(#lensSheen)"
          strokeWidth="3.5"
          strokeLinecap="round"
        />
        <path
          d="M40 16 L58 34"
          stroke="url(#lensSheen)"
          strokeWidth="1.8"
          strokeLinecap="round"
        />

        {/* Right Lens Glass Sheen */}
        <rect
          x="98"
          y="11"
          width="64"
          height="54"
          rx="22"
          fill="rgba(255, 255, 255, 0.08)"
          stroke="rgba(255, 214, 231, 0.15)"
          strokeWidth="1"
        />
        {/* Right Lens Glare Reflection Line */}
        <path
          d="M110 16 L142 48"
          stroke="url(#lensSheenRight)"
          strokeWidth="3.5"
          strokeLinecap="round"
        />
        <path
          d="M126 16 L144 34"
          stroke="url(#lensSheenRight)"
          strokeWidth="1.8"
          strokeLinecap="round"
        />

        {/* Left Wireframe Rim */}
        <rect
          x="10"
          y="9"
          width="68"
          height="58"
          rx="24"
          stroke="url(#roseGoldFrame)"
          strokeWidth="2.8"
          fill="none"
        />
        <rect
          x="12"
          y="11"
          width="64"
          height="54"
          rx="22"
          stroke="rgba(40, 20, 35, 0.65)"
          strokeWidth="1.2"
          fill="none"
        />

        {/* Right Wireframe Rim */}
        <rect
          x="96"
          y="9"
          width="68"
          height="58"
          rx="24"
          stroke="url(#roseGoldFrame)"
          strokeWidth="2.8"
          fill="none"
        />
        <rect
          x="98"
          y="11"
          width="64"
          height="54"
          rx="22"
          stroke="rgba(40, 20, 35, 0.65)"
          strokeWidth="1.2"
          fill="none"
        />

        {/* Bridge (Nose arch with double wireframe style) */}
        <path
          d="M78 28 C82 24, 92 24, 96 28"
          stroke="url(#roseGoldFrame)"
          strokeWidth="2.4"
          strokeLinecap="round"
          fill="none"
        />
        <path
          d="M79 34 C83 31, 91 31, 95 34"
          stroke="url(#roseGoldFrame)"
          strokeWidth="1.8"
          strokeLinecap="round"
          fill="none"
        />

        {/* Left & Right Temples / Hinges */}
        <path
          d="M10 26 L2 24"
          stroke="url(#roseGoldFrame)"
          strokeWidth="2.4"
          strokeLinecap="round"
        />
        <path
          d="M164 26 L172 24"
          stroke="url(#roseGoldFrame)"
          strokeWidth="2.4"
          strokeLinecap="round"
        />

        {/* Nose Pads */}
        <ellipse cx="76" cy="38" rx="2.2" ry="4" fill="#FFB6C1" opacity="0.85" />
        <ellipse cx="98" cy="38" rx="2.2" ry="4" fill="#FFB6C1" opacity="0.85" />
      </svg>
    </motion.div>
  );
};
