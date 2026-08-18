import React from 'react';
import { MeliExpressionId, EXPRESSION_REGISTRY } from './ExpressionRegistry';

export interface ExpressionOverlayProps {
  expression: MeliExpressionId;
  opacity?: number;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * ExpressionOverlay component.
 *
 * Renders a lightweight, high-resolution SVG overlay precisely positioned inside
 * Meli's CharacterTransformNode (Z-Index 25).
 * The underlying canonical face (Z-Index 5) is 100% preserved.
 */
export const ExpressionOverlay: React.FC<ExpressionOverlayProps> = ({
  expression,
  opacity = 1.0,
  className = '',
  style = {},
}) => {
  const def = EXPRESSION_REGISTRY[expression] || EXPRESSION_REGISTRY.idle;

  if (expression === 'idle') {
    return null;
  }

  return (
    <div
      className={`expression-overlay-layer ${className}`}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 25,
        opacity,
        transition: 'opacity 180ms ease-out',
        ...style,
      }}
      data-testid={`expression-overlay-${expression}`}
    >
      <img
        src={def.svgUrl}
        alt={`Expression overlay: ${def.name}`}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          display: 'block',
        }}
      />
    </div>
  );
};
