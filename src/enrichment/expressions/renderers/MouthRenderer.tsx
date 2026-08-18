/**
 * MouthRenderer.tsx - Composable Vector SVG Mouth Overlays
 */

import React from 'react';
import { MouthType } from '../types';

interface MouthRendererProps {
  mouth: MouthType;
}

export const MouthRenderer: React.FC<MouthRendererProps> = ({ mouth }) => {
  if (mouth === 'neutral') {
    return null; // Natural sprite mouth shows through cleanly
  }

  const renderMouthShape = () => {
    switch (mouth) {
      case 'smile':
        return (
          // Joyful gentle open smile with warm rosy inner tint and dimples
          <>
            <path
              d="M10 8 C16 21, 32 21, 38 8"
              stroke="#2E202C"
              strokeWidth="2.8"
              strokeLinecap="round"
              fill="#FF8CAE"
            />
            {/* Smile dimple accents */}
            <circle cx="8" cy="8" r="1.2" fill="#FF7AA2" />
            <circle cx="40" cy="8" r="1.2" fill="#FF7AA2" />
          </>
        );

      case 'small-o':
        return (
          // Inquisitive / surprised cute round "o"
          <ellipse
            cx="24"
            cy="12"
            rx="5.5"
            ry="7.5"
            fill="#FF8CAE"
            stroke="#2E202C"
            strokeWidth="2.2"
          />
        );

      case 'small-wave':
        return (
          // Nervous trembly wavy mouth line
          <path
            d="M11 12 Q17 7, 24 12 T37 12"
            stroke="#2E202C"
            strokeWidth="2.4"
            strokeLinecap="round"
            fill="none"
          />
        );

      case 'flat':
        return (
          // Focused concentrated flat line
          <path
            d="M14 12 L34 12"
            stroke="#2E202C"
            strokeWidth="2.4"
            strokeLinecap="round"
            fill="none"
          />
        );

      case 'pout':
        return (
          // Cute slight downward pout arc
          <path
            d="M13 14 C18 10, 30 10, 35 14"
            stroke="#2E202C"
            strokeWidth="2.4"
            strokeLinecap="round"
            fill="none"
          />
        );

      default:
        return null;
    }
  };

  return (
    <div
      style={{
        position: 'absolute',
        top: '32.4%',
        left: '50.67%',
        transform: 'translate(-50%, -50%)',
        width: '48px',
        height: '24px',
        pointerEvents: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg
        viewBox="0 0 48 24"
        width="100%"
        height="100%"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {renderMouthShape()}
      </svg>
    </div>
  );
};
