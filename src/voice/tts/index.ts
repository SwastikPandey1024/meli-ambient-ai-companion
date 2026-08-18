/**
 * tts/index.ts - Text-to-Speech Subsystem Exports
 */

import { TTSProviderFactory, TTSFactoryOptions } from './factory';
import { ITTSAdapter, VoiceConfig } from '../types';

export * from './tts_adapter';
export * from './web_speech_tts';
export * from './orpheus_tts';
export * from './factory';

export function createTTSAdapter(config?: Partial<VoiceConfig>, options?: TTSFactoryOptions): ITTSAdapter {
  return TTSProviderFactory.create({
    provider: 'auto',
    voice: 'autumn',
    model: 'canopylabs/orpheus-v1-english',
    config,
    ...options,
  });
}
