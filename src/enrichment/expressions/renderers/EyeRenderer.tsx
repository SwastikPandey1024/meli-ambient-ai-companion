/**
 * EyeRenderer.tsx - Composable Vector SVG Eyes
 */

import React from 'react';
import { EyeType } from '../types';

interface EyeRendererProps {
  eyes: EyeType;
  aegyoSal?: boolean;
}

export const EyeRenderer: React.FC<EyeRendererProps> = ({ eyes, aegyoSal = false }) => {
  if (eyes === 'neutral' && !aegyoSal) {
    return null; // Natural sprite eyes shine through
  }

  const renderEyeShapes = () => {
    switch (eyes) {
      case 'happy':
        return (
          // Joyful squint arcs (^ ^)
          <>
            {/* Left Eye Happy Arc */}
            <path
              d="M32 40 C38 27, 52 27, 58 40"
              stroke="#2E202C"
              strokeWidth="3.2"
              strokeLinecap="round"
              fill="none"
            />
            {/* Left Lash Accent */}
            <path
              d="M56 36 L61 32"
              stroke="#2E202C"
              strokeWidth="2.2"
              strokeLinecap="round"
            />

            {/* Right Eye Happy Arc */}
            <path
              d="M92 40 C98 27, 112 27, 118 40"
              stroke="#2E202C"
              strokeWidth="3.2"
              strokeLinecap="round"
              fill="none"
            />
            {/* Right Lash Accent */}
            <path
              d="M116 36 L121 32"
              stroke="#2E202C"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
          </>
        );

      case 'focused':
        return (
          // Determined analytical focus lines
          <>
            <path
              d="M33 38 C41 33, 51 33, 59 36"
              stroke="#2E202C"
              strokeWidth="2.8"
              strokeLinecap="round"
              fill="none"
            />
            <circle cx="46" cy="37" r="1.4" fill="#FFFFFF" opacity="0.9" />

            <path
              d="M91 36 C99 33, 109 33, 117 38"
              stroke="#2E202C"
              strokeWidth="2.8"
              strokeLinecap="round"
              fill="none"
            />
            <circle cx="104" cy="37" r="1.4" fill="#FFFFFF" opacity="0.9" />
          </>
        );

      case 'nervous':
        return (
          // Gentle sloping arcs with apologetic sweat / tear drop accent
          <>
            <path
              d="M33 36 C40 32, 50 32, 57 39"
              stroke="#2E202C"
              strokeWidth="2.8"
              strokeLinecap="round"
              fill="none"
            />
            <path
              d="M93 39 C100 32, 110 32, 117 36"
              stroke="#2E202C"
              strokeWidth="2.8"
              strokeLinecap="round"
              fill="none"
            />
            {/* Sweat drop accent */}
            <path
              d="M125 30 C125 27, 128 24, 128 24 C128 24, 131 27, 131 30 C131 32, 129.5 33.5, 128 33.5 C126.5 33.5, 125 32, 125 30 Z"
              fill="#90CAF9"
              opacity="0.85"
            />
          </>
        );

      case 'curious':
        return (
          // Bright inquisitive eyes looking slightly upward
          <>
            <ellipse cx="45" cy="36" rx="9" ry="11" fill="#2E202C" />
            <circle cx="43" cy="32" r="3.8" fill="#FFFFFF" />
            <circle cx="49" cy="39" r="2.0" fill="#FFFFFF" />

            <ellipse cx="105" cy="36" rx="9" ry="11" fill="#2E202C" />
            <circle cx="103" cy="32" r="3.8" fill="#FFFFFF" />
            <circle cx="109" cy="39" r="2.0" fill="#FFFFFF" />
          </>
        );

      case 'surprised':
        return (
          // Wide open circular alert eyes with prominent catchlights
          <>
            <ellipse cx="45" cy="37" rx="10.5" ry="12.5" fill="#2E202C" />
            <circle cx="42" cy="33" r="4.2" fill="#FFFFFF" />
            <circle cx="49" cy="41" r="2.4" fill="#FFFFFF" />

            <ellipse cx="105" cy="37" rx="10.5" ry="12.5" fill="#2E202C" />
            <circle cx="102" cy="33" r="4.2" fill="#FFFFFF" />
            <circle cx="109" cy="41" r="2.4" fill="#FFFFFF" />
          </>
        );

      case 'blink':
      case 'sleepy':
        return (
          // Gentle resting downward arcs
          <>
            <path
              d="M34 38 C42 45, 52 45, 58 38"
              stroke="#2E202C"
              strokeWidth="2.8"
              strokeLinecap="round"
              fill="none"
            />
            <path
              d="M92 38 C98 45, 108 45, 116 38"
              stroke="#2E202C"
              strokeWidth="2.8"
              strokeLinecap="round"
              fill="none"
            />
          </>
        );

      case 'neutral':
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
      {renderEyeShapes()}

      {/* Aegyo-sal subtle soft under-eye contour */}
      {aegyoSal && (
        <>
          <path
            d="M36 45 C44 48.5, 50 48.5, 56 45"
            stroke="rgba(255, 182, 193, 0.50)"
            strokeWidth="1.6"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M94 45 C100 48.5, 106 48.5, 114 45"
            stroke="rgba(255, 182, 193, 0.50)"
            strokeWidth="1.6"
            strokeLinecap="round"
            fill="none"
          />
        </>
      )}
    </svg>
  );
};
