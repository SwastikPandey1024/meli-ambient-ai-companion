/**
 * ExpressionLayer.tsx - Composable Facial Expression Overlay Container
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FacialExpressionConfig } from './types';
import { getExpressionPreset, EXPRESSION_TRANSITION_TIMING } from './presets';
import { EyeRenderer } from './renderers/EyeRenderer';
import { BrowRenderer } from './renderers/BrowRenderer';
import { MouthRenderer } from './renderers/MouthRenderer';
import { BlushRenderer } from './renderers/BlushRenderer';
import { ENRICHMENT_Z_INDEX } from '../types';

interface ExpressionLayerProps {
  expression?: string | FacialExpressionConfig;
}

export const ExpressionLayer: React.FC<ExpressionLayerProps> = ({ expression = 'neutral' }) => {
  const config = typeof expression === 'string' ? getExpressionPreset(expression) : expression;

  return (
    <div
      className="character-expression-layer"
      style={{
        position: 'absolute',
        top: '28.5%',
        left: '50.67%',
        width: '130px',
        height: '65px',
        transform: 'translate(-50%, -50%)',
        pointerEvents: 'none',
        zIndex: ENRICHMENT_Z_INDEX.EXPRESSION_LAYER,
      }}
    >
      {/* Blush Layer with smooth opacity transition */}
      <BlushRenderer opacity={config.blushOpacity} />

      {/* Composable Eye, Brow, and Mouth overlays with deterministic cross-fade */}
      <AnimatePresence mode="wait">
        <motion.div
          key={config.id || 'expression'}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{
            duration: EXPRESSION_TRANSITION_TIMING.crossfadeDurationMs / 1000,
            ease: 'easeInOut',
          }}
          style={{ position: 'absolute', inset: 0 }}
        >
          <BrowRenderer brows={config.brows || 'neutral'} />
          <EyeRenderer
            eyes={config.eyes || 'neutral'}
            aegyoSal={config.aegyoSal}
          />
          <MouthRenderer mouth={config.mouth || 'neutral'} />
        </motion.div>
      </AnimatePresence>
    </div>
  );
};
