/**
 * accessories/types.ts - Typed contracts for Meli Accessory System
 */

import React from 'react';
import { CoordinateAnchor } from '../types';
import { MeliMoodState } from '../../state/CharacterStateMachine';

export type AccessoryCategory = 'face' | 'head' | 'foreground' | 'chest';
export type AccessoryStatus = 'active' | 'planned';
export type AccessoryRenderType = 'svg' | 'image' | 'component';

export interface AccessoryStateModulation {
  offsetYPx?: number;
  rotationDeg?: number;
  scaleFactor?: number;
  opacity?: number;
}

export interface AccessoryConfig {
  id: string;
  name: string;
  category: AccessoryCategory;
  status: AccessoryStatus;
  zIndex: number;
  anchor: CoordinateAnchor;
  renderType: AccessoryRenderType;
  assetUrl?: string; // Optional transparent PNG/WebP path when available
  stateTriggers?: Partial<Record<MeliMoodState, AccessoryStateModulation>>;
  component?: React.FC<AccessoryRenderProps>;
}

export interface AccessoryRenderProps {
  config: AccessoryConfig;
  mood: MeliMoodState;
  enabled: boolean;
}
