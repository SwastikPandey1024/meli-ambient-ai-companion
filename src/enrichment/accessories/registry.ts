/**
 * accessories/registry.ts - Canonical Accessory Registry
 */

import { AccessoryConfig } from './types';
import { CANONICAL_LANDMARKS, ENRICHMENT_Z_INDEX } from '../types';
import { GlassesRenderer } from './renderers/GlassesRenderer';

export const ACCESSORY_REGISTRY: Record<string, AccessoryConfig> = {
  glasses: {
    id: 'glasses',
    name: 'Oversized Wireframe Glasses',
    category: 'face',
    status: 'active',
    zIndex: ENRICHMENT_Z_INDEX.ACCESSORY_FACE,
    anchor: {
      xPercent: CANONICAL_LANDMARKS.EYES_BRIDGE.xPercent,
      yPercent: CANONICAL_LANDMARKS.EYES_BRIDGE.yPercent,
      widthPercent: 34.0,
      heightPercent: 15.0,
      scale: 1.0,
      rotationDeg: 0,
      origin: '50% 50%',
    },
    renderType: 'svg',
    component: GlassesRenderer,
    stateTriggers: {
      CLICK: {
        offsetYPx: -2.0,
        scaleFactor: 1.02,
      },
      HOVER: {
        offsetYPx: -1.0,
        scaleFactor: 1.01,
      },
      SINK_POP: {
        offsetYPx: 0.0,
        scaleFactor: 1.0,
      },
      THINKING: {
        offsetYPx: 0.5,
        rotationDeg: -0.5,
      },
    },
  },

  headphones: {
    id: 'headphones',
    name: 'Cat-Ear Asymmetric Headphones',
    category: 'head',
    status: 'planned',
    zIndex: ENRICHMENT_Z_INDEX.ACCESSORY_HEAD,
    anchor: {
      xPercent: CANONICAL_LANDMARKS.HEAD_CENTER.xPercent,
      yPercent: CANONICAL_LANDMARKS.HEAD_CENTER.yPercent,
      widthPercent: 44.0,
      heightPercent: 24.0,
      scale: 1.0,
      rotationDeg: 0,
      origin: '50% 80%',
    },
    renderType: 'svg',
  },

  laptop: {
    id: 'laptop',
    name: 'Foreground Development Laptop',
    category: 'foreground',
    status: 'planned',
    zIndex: ENRICHMENT_Z_INDEX.ACCESSORY_FOREGROUND,
    anchor: {
      xPercent: CANONICAL_LANDMARKS.FOREGROUND_LAPTOP.xPercent,
      yPercent: CANONICAL_LANDMARKS.FOREGROUND_LAPTOP.yPercent,
      widthPercent: 48.0,
      heightPercent: 26.0,
      scale: 1.0,
      rotationDeg: 0,
      origin: '50% 50%',
    },
    renderType: 'component',
  },
};

export function getAccessory(id: string): AccessoryConfig | undefined {
  return ACCESSORY_REGISTRY[id];
}

export function getAllAccessories(): AccessoryConfig[] {
  return Object.values(ACCESSORY_REGISTRY);
}

export function getActiveAccessories(): AccessoryConfig[] {
  return Object.values(ACCESSORY_REGISTRY).filter((acc) => acc.status === 'active');
}
