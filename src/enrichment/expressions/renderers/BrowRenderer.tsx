/**
 * BrowRenderer.tsx - Composable Vector SVG Eyebrows
 */

import React from 'react';
import { BrowType } from '../types';

interface BrowRendererProps {
  brows: BrowType;
}

export const BrowRenderer: React.FC<BrowRendererProps> = ({ brows }) => {
  if (brows === 'neutral') {
    return null;
  }

  const renderBrowPaths = () => {
    switch (brows) {
      case 'raised':
        return (
          <>
            {/* Left Brow - High arched curve */}
            <path
              d="M30 20 C38 15, 48 15, 56 19"
              stroke="#3D303B"
              strokeWidth="2.4"
              strokeLinecap="round"
              fill="none"
            />
            {/* Right Brow - High arched curve */}
            <path
              d="M94 19 C102 15, 112 15, 120 20"
              stroke="#3D303B"
              strokeWidth="2.4"
              strokeLinecap="round"
              fill="none"
            />
          </>
        );

      case 'furrowed':
        return (
          <>
            {/* Left Brow - Inward slanting down (Concentrated / Focused) */}
            <path
              d="M32 18 C40 19, 48 23, 56 25"
              stroke="#3D303B"
              strokeWidth="2.4"
              strokeLinecap="round"
              fill="none"
            />
            {/* Right Brow - Inward slanting down */}
            <path
              d="M94 25 C102 23, 110 19, 118 18"
              stroke="#3D303B"
              strokeWidth="2.4"
              strokeLinecap="round"
              fill="none"
            />
          </>
        );

      case 'asymmetric':
        return (
          <>
            {/* Left Brow - Questioning lift */}
            <path
              d="M30 18 C38 14, 48 14, 56 18"
              stroke="#3D303B"
              strokeWidth="2.4"
              strokeLinecap="round"
              fill="none"
            />
            {/* Right Brow - Mild worried slant */}
            <path
              d="M94 24 C102 25, 112 25, 120 23"
              stroke="#3D303B"
              strokeWidth="2.4"
              strokeLinecap="round"
              fill="none"
            />
          </>
        );

      default:
        return null;
    }
  };

  return (
    <svg
      viewBox="0 0 150 70"
      width="100%"
      height="100%"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
    >
      {renderBrowPaths()}
    </svg>
  );
};
