import { useState, useEffect, useCallback, useRef } from 'react';

export interface ProximityVector {
  isNear: boolean;
  distance: number;
  normalizedX: number; // -1 (far left) to +1 (far right)
  normalizedY: number; // -1 (far top) to +1 (far bottom)
  offsetX: number;     // Clamped px translation (max 2px)
  offsetY: number;     // Clamped px translation (max 2px)
  rotationDeg: number; // Clamped rotation deg (max 2°)
}

const PROXIMITY_THRESHOLD_PX = 180;
const MAX_TRANSLATION_PX = 2.0;
const MAX_ROTATION_DEG = 1.8;

export function useProximityTracker(containerRef: React.RefObject<HTMLElement>) {
  const [proximity, setProximity] = useState<ProximityVector>({
    isNear: false,
    distance: 999,
    normalizedX: 0,
    normalizedY: 0,
    offsetX: 0,
    offsetY: 0,
    rotationDeg: 0,
  });

  const rafRef = useRef<number | null>(null);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!containerRef.current) return;

    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }

    rafRef.current = requestAnimationFrame(() => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height * 0.33; // Gaze anchor center

      const dx = e.clientX - centerX;
      const dy = e.clientY - centerY;
      const dist = Math.sqrt(dx * dx + dy * dy);

      const isNear = dist <= PROXIMITY_THRESHOLD_PX;
      const factor = isNear ? (1 - dist / PROXIMITY_THRESHOLD_PX) : 0;

      const normX = Math.max(-1, Math.min(1, dx / PROXIMITY_THRESHOLD_PX));
      const normY = Math.max(-1, Math.min(1, dy / PROXIMITY_THRESHOLD_PX));

      const offsetX = normX * MAX_TRANSLATION_PX * factor;
      const offsetY = normY * (MAX_TRANSLATION_PX * 0.6) * factor;
      const rotationDeg = normX * MAX_ROTATION_DEG * factor;

      setProximity({
        isNear,
        distance: dist,
        normalizedX: normX,
        normalizedY: normY,
        offsetX,
        offsetY,
        rotationDeg,
      });
    });
  }, [containerRef]);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [handleMouseMove]);

  return proximity;
}
