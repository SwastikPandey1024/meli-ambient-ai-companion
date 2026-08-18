import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface Particle {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
}

interface ParticleEmitterProps {
  particles: Particle[];
}

export const ParticleEmitter: React.FC<ParticleEmitterProps> = ({ particles }) => {
  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        overflow: 'hidden',
        zIndex: 20,
      }}
    >
      <AnimatePresence>
        {particles.map((p) => (
          <motion.div
            key={p.id}
            initial={{
              opacity: 1,
              scale: 0.4,
              x: p.x,
              y: p.y,
            }}
            animate={{
              opacity: 0,
              scale: 1.2,
              x: p.x + p.vx,
              y: p.y + p.vy,
            }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.65, ease: 'easeOut' }}
            style={{
              position: 'absolute',
              width: p.size,
              height: p.size,
              borderRadius: '50%',
              backgroundColor: p.color,
              boxShadow: `0 0 8px ${p.color}`,
            }}
          />
        ))}
      </AnimatePresence>
    </div>
  );
};
