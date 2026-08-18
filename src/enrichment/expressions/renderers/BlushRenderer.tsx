/**
 * BlushRenderer.tsx - Soft Radial Gradient Pink Cheek Blush
 */

import React from 'react';

interface BlushRendererProps {
  opacity?: number; // 0.0 to 1.0
}

export const BlushRenderer: React.FC<BlushRendererProps> = ({ opacity = 0.55 }) => {
  if (opacity <= 0.01) return null;

  return (
    <div
      className="blush-layer-container"
      style={{
        position: 'absolute',
        top: '30.8%',
        left: '50.67%',
        width: '110px',
        height: '32px',
        transform: 'translate(-50%, -50%)',
        pointerEvents: 'none',
        opacity: Math.min(1.0, Math.max(0.0, opacity)),
        transition: 'opacity 0.25s ease-out',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0 4px',
      }}
    >
      {/* Left Cheek Blush */}
      <div
        style={{
          width: '28px',
          height: '18px',
          borderRadius: '50%',
          background: 'radial-gradient(ellipse at center, rgba(255, 122, 162, 0.75) 0%, rgba(255, 182, 193, 0.35) 55%, transparent 100%)',
          filter: 'blur(2.5px)',
        }}
      />

      {/* Right Cheek Blush */}
      <div
        style={{
          width: '28px',
          height: '18px',
          borderRadius: '50%',
          background: 'radial-gradient(ellipse at center, rgba(255, 122, 162, 0.75) 0%, rgba(255, 182, 193, 0.35) 55%, transparent 100%)',
          filter: 'blur(2.5px)',
        }}
      />
    </div>
  );
};
