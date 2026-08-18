/**
 * tts/factory.ts - Text-To-Speech (TTS) Provider Factory
 * Dynamically instantiates OrpheusTTSAdapter (with autumn/diana/hannah) or WebSpeechTTSAdapter.
 */

import { ITTSAdapter, VoiceConfig } from '../types';
import { WebSpeechTTSAdapter } from './web_speech_tts';
import { OrpheusTTSAdapter, OrpheusFemaleVoice } from './orpheus_tts';

export type TTSProviderType = 'orpheus' | 'webspeech' | 'auto';

export interface TTSFactoryOptions {
  provider?: TTSProviderType;
  voice?: OrpheusFemaleVoice;
  model?: string;
  backendUrl?: string;
  config?: Partial<VoiceConfig>;
}

export class TTSProviderFactory {
  static create(options?: TTSFactoryOptions): ITTSAdapter {
    const provider = options?.provider || 'auto';
    const model = options?.model || 'canopylabs/orpheus-v1-english';
    const backendUrl = options?.backendUrl || 'http://127.0.0.1:8000';

    if (provider === 'webspeech') {
      const adapter = new WebSpeechTTSAdapter();
      if (options?.config) adapter.setConfig(options.config);
      return adapter;
    }

    const chosenVoice: OrpheusFemaleVoice =
      options?.voice || (options?.config?.voice as OrpheusFemaleVoice) || 'autumn';

    // Default 'auto' or 'orpheus': uses Orpheus adapter with automatic WebSpeech fallback
    return new OrpheusTTSAdapter({
      model,
      voice: chosenVoice,
      backendUrl,
      volume: options?.config?.volume,
      muted: options?.config?.muted,
      rate: options?.config?.rate,
      pitch: options?.config?.pitch,
      language: options?.config?.language,
      autoSpeak: options?.config?.autoSpeak,
    });
  }
}
