import React, { useEffect, useState } from 'react';
import { MeliExpressionId } from './ExpressionRegistry';
import { ExpressionOverlay } from './ExpressionOverlay';

export interface ExpressionRendererProps {
  currentExpression: MeliExpressionId;
  targetExpression?: MeliExpressionId;
  transitionDurationMs?: number;
}

/**
 * ExpressionRenderer handles cross-fading and deterministic state mapping
 * between distinct expression overlay states.
 */
export const ExpressionRenderer: React.FC<ExpressionRendererProps> = ({
  currentExpression,
  targetExpression,
  transitionDurationMs = 200,
}) => {
  const [activeExpr, setActiveExpr] = useState<MeliExpressionId>(currentExpression);
  const [fadeOpacity, setFadeOpacity] = useState<number>(1.0);

  useEffect(() => {
    if (targetExpression && targetExpression !== activeExpr) {
      setFadeOpacity(0.0);
      const timer = setTimeout(() => {
        setActiveExpr(targetExpression);
        setFadeOpacity(1.0);
      }, transitionDurationMs / 2);
      return () => clearTimeout(timer);
    } else if (currentExpression !== activeExpr) {
      setActiveExpr(currentExpression);
      setFadeOpacity(1.0);
    }
  }, [currentExpression, targetExpression, activeExpr, transitionDurationMs]);

  return (
    <ExpressionOverlay
      expression={activeExpr}
      opacity={fadeOpacity}
      style={{ transition: `opacity ${transitionDurationMs / 2}ms ease-in-out` }}
    />
  );
};
