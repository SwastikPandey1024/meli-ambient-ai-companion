/**
 * tts/orpheus_tts.ts - Remote Orpheus TTS Provider Adapter (canopylabs/orpheus-v1-english)
 * Supports female voice evaluations: 'autumn' (default), 'diana', 'hannah'.
 * Falls back seamlessly to WebSpeechTTSAdapter if remote backend synthesis is offline or in evaluation.
 */

import {
  ITTSAdapter,
  TTSStartCallback,
  TTSEndCallback,
  TTSErrorCallback,
  VoiceConfig,
} from '../types';
import { WebSpeechTTS } from './web_speech_tts';

export type OrpheusFemaleVoice = 'autumn' | 'diana' | 'hannah';

export interface OrpheusTTSConfig extends Partial<VoiceConfig> {
  model?: string;
  voice?: OrpheusFemaleVoice;
  backendUrl?: string;
}

export class OrpheusTTSAdapter implements ITTSAdapter {
  readonly name = 'OrpheusTTS (canopylabs/orpheus-v1-english)';
  private fallbackAdapter: WebSpeechTTS;
  private currentAudio: HTMLAudioElement | null = null;
  private speaking = false;
  private model: string = 'canopylabs/orpheus-v1-english';
  private voice: OrpheusFemaleVoice = 'autumn';
  private backendUrl: string = 'http://127.0.0.1:8000';
  private volume: number = 0.88;
  private muted: boolean = false;

  constructor(config?: OrpheusTTSConfig) {
    this.fallbackAdapter = new WebSpeechTTS();
    if (config) {
      if (config.model) this.model = config.model;
      if (config.voice) this.voice = config.voice;
      if (config.backendUrl) this.backendUrl = config.backendUrl;
      if (config.volume !== undefined) this.volume = config.volume;
      if (config.muted !== undefined) this.muted = config.muted;
      this.fallbackAdapter.setConfig(config);
    }
  }

  isSupported(): boolean {
    return true;
  }

  isSpeaking(): boolean {
    return this.speaking || this.fallbackAdapter.isSpeaking();
  }

  getVoice(): OrpheusFemaleVoice {
    return this.voice;
  }

  setVoice(voice: OrpheusFemaleVoice): void {
    this.voice = voice;
    this.fallbackAdapter.setConfig({ voice } as any);
  }

  setConfig(config: Partial<VoiceConfig> & { voice?: OrpheusFemaleVoice; model?: string }): void {
    if (config.volume !== undefined) this.volume = config.volume;
    if (config.muted !== undefined) this.muted = config.muted;
    if (config.voice) this.voice = config.voice;
    if (config.model) this.model = config.model;
    this.fallbackAdapter.setConfig(config);
  }

  async speak(
    text: string,
    onStart?: TTSStartCallback,
    onEnd?: TTSEndCallback,
    onError?: TTSErrorCallback
  ): Promise<void> {
    if (this.muted) {
      onEnd?.();
      return;
    }

    const cleanText = text.trim();
    if (!cleanText) {
      onEnd?.();
      return;
    }

    try {
      const resp = await fetch(`${this.backendUrl}/api/companion/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: cleanText,
          model: this.model,
          voice: this.voice,
        }),
      });

      if (!resp.ok) {
        throw new Error(`Synthesis HTTP ${resp.status}`);
      }

      const contentType = resp.headers.get('content-type') || '';
      if (contentType.includes('audio/')) {
        const audioBlob = await resp.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        this.currentAudio = audio;
        audio.volume = this.volume;

        audio.onplay = () => {
          this.speaking = true;
          onStart?.();
        };

        audio.onended = () => {
          this.speaking = false;
          URL.revokeObjectURL(audioUrl);
          this.currentAudio = null;
          onEnd?.();
        };

        audio.onerror = (e) => {
          this.speaking = false;
          URL.revokeObjectURL(audioUrl);
          this.currentAudio = null;
          console.warn('[OrpheusTTS] Audio playback error, falling back to WebSpeech:', e);
          this.fallbackAdapter.speak(cleanText, onStart, onEnd, onError);
        };

        await audio.play();
      } else {
        // Fallback JSON returned by backend
        const data = await resp.json();
        if (data.fallback === 'web_speech') {
          await this.fallbackAdapter.speak(cleanText, onStart, onEnd, onError);
        } else {
          onEnd?.();
        }
      }
    } catch (err) {
      console.info('[OrpheusTTS] Remote synthesis fallback to local WebSpeech adapter:', err);
      await this.fallbackAdapter.speak(cleanText, onStart, onEnd, onError);
    }
  }

  stop(): void {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    this.speaking = false;
    this.fallbackAdapter.stop();
  }

  pause(): void {
    if (this.currentAudio) {
      this.currentAudio.pause();
    }
    this.fallbackAdapter.pause();
  }

  resume(): void {
    if (this.currentAudio) {
      this.currentAudio.play().catch(() => {});
    }
    this.fallbackAdapter.resume();
  }
}
