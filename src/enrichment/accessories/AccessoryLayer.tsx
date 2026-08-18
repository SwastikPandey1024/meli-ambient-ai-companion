/**
 * AccessoryLayer.tsx - Compositor Layer for Active Character Accessories
 */

import React from 'react';
import { MeliMoodState } from '../../state/CharacterStateMachine';
import { getAccessory } from './registry';

interface AccessoryLayerProps {
  equippedAccessoryIds: string[];
  mood: MeliMoodState;
}

export const AccessoryLayer: React.FC<AccessoryLayerProps> = ({
  equippedAccessoryIds,
  mood,
}) => {
  if (!equippedAccessoryIds || equippedAccessoryIds.length === 0) {
    return null;
  }

  return (
    <>
      {equippedAccessoryIds.map((id) => {
        const config = getAccessory(id);
        if (!config || config.status !== 'active' || !config.component) {
          return null;
        }

        const Component = config.component;
        return (
          <Component
            key={config.id}
            config={config}
            mood={mood}
            enabled={true}
          />
        );
      })}
    </>
  );
};
