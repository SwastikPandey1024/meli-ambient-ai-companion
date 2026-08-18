/**
 * voice_manager.ts - Central Voice & Audio Lifecycle Orchestrator for Meli Companion
 *
 * Single frontend authority for Push-to-Talk, STT, TTS, Audio Feedback, and
 * bridge integration with companion events.
 */

import { VoiceState, VoiceConfig, VoiceStateListener, ISTTAdapter, ITTSAdapter } from './types';
import { createSTTAdapter } from './stt';
import { createTTSAdapter, OrpheusFemaleVoice } from './tts';
import { soundEffects } from './audio/sound_effects';
import { companionEvents } from '../enrichment/bridge/CompanionEventManager';

const STORAGE_KEY = 'meli_voice_config';
const VOICE_STORAGE_KEY = 'meli_selected_voice';

const DEFAULT_CONFIG: VoiceConfig = {
  volume: 0.85,
  muted: false,
  rate: 1.0,
  pitch: 1.05,
  language: 'en-US',
  autoSpeak: true,
};

export class VoiceManager {
  private static instance: VoiceManager | null = null;
  private state: VoiceState = 'IDLE';
  private config: VoiceConfig = DEFAULT_CONFIG;
  private currentVoice: OrpheusFemaleVoice = 'autumn';
  private sttAdapter: ISTTAdapter;
  private ttsAdapter: ITTSAdapter;
  private listeners: Set<VoiceStateListener> = new Set();
  private voiceListeners: Set<(voice: OrpheusFemaleVoice) => void> = new Set();
  private transcriptHandler: ((text: string) => Promise<void> | void) | null = null;
  private errorTimer: number | null = null;
  private isPttActive: boolean = false;

  private constructor() {
    this.loadPersistedConfig();
    this.sttAdapter = createSTTAdapter();
    this.ttsAdapter = createTTSAdapter(this.config, { voice: this.currentVoice });
    soundEffects.setMuted(this.config.muted);
    soundEffects.setVolume(this.config.volume);
  }

  public static getInstance(): VoiceManager {
    if (!VoiceManager.instance) {
      VoiceManager.instance = new VoiceManager();
    }
    return VoiceManager.instance;
  }

  public getState(): VoiceState {
    return this.state;
  }

  public getConfig(): VoiceConfig {
    return { ...this.config };
  }

  public getVoice(): OrpheusFemaleVoice {
    return this.currentVoice;
  }

  public setVoice(voice: OrpheusFemaleVoice): void {
    this.currentVoice = voice;
    this.ttsAdapter.setConfig({ voice });
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem(VOICE_STORAGE_KEY, voice);
      } catch {}
    }
    this.voiceListeners.forEach((l) => l(voice));
    this.listeners.forEach((l) => l(this.state, { voice }));
  }

  public subscribeVoice(listener: (voice: OrpheusFemaleVoice) => void): () => void {
    this.voiceListeners.add(listener);
    listener(this.currentVoice);
    return () => {
      this.voiceListeners.delete(listener);
    };
  }

  public setConfig(newConfig: Partial<VoiceConfig>) {
    this.config = { ...this.config, ...newConfig };
    this.ttsAdapter.setConfig({ ...this.config, voice: this.currentVoice });
    soundEffects.setMuted(this.config.muted);
    soundEffects.setVolume(this.config.volume);
    this.savePersistedConfig();
  }

  public toggleMute(): boolean {
    const nextMuted = !this.config.muted;
    this.setConfig({ muted: nextMuted });
    if (nextMuted && this.state === 'SPEAKING') {
      this.ttsAdapter.stop();
      this.setState('IDLE');
    }
    return nextMuted;
  }

  public async speak(
    text: string,
    onStart?: () => void,
    onEnd?: () => void,
    onError?: (err: Error | string) => void
  ): Promise<void> {
    if (this.config.muted) return;
    this.setState('SPEAKING');
    companionEvents.emit('SPEAKING', text);
    try {
      await this.ttsAdapter.speak(
        text,
        () => {
          onStart?.();
        },
        () => {
          this.setState('IDLE');
          companionEvents.emit('IDLE');
          onEnd?.();
        },
        (err) => {
          this.setState('IDLE');
          companionEvents.emit('IDLE');
          onError?.(err);
        }
      );
    } catch (err) {
      this.setState('IDLE');
      companionEvents.emit('IDLE');
    }
  }

  public registerTranscriptHandler(handler: (text: string) => Promise<void> | void): () => void {
    this.transcriptHandler = handler;
    return () => {
      if (this.transcriptHandler === handler) {
        this.transcriptHandler = null;
      }
    };
  }

  public subscribe(listener: VoiceStateListener): () => void {
    this.listeners.add(listener);
    listener(this.state);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private setState(newState: VoiceState, metadata?: Record<string, any>) {
    this.state = newState;
    this.listeners.forEach((fn) => {
      try {
        fn(this.state, metadata);
      } catch (err) {
        console.warn('[VoiceManager] Listener error:', err);
      }
    });
  }

  /**
   * Push-To-Talk Start (Keydown or Mic Button Press)
   */
  public async startListening(): Promise<void> {
    if (this.isPttActive || this.state === 'LISTENING') return;

    this.isPttActive = true;

    // Interrupt previous TTS speech before listening
    if (this.ttsAdapter.isSpeaking() || this.state === 'SPEAKING') {
      this.ttsAdapter.stop();
    }

    if (this.errorTimer !== null) {
      clearTimeout(this.errorTimer);
      this.errorTimer = null;
    }

    soundEffects.playMicStart();
    this.setState('LISTENING');
    companionEvents.emit('LISTENING');

    try {
      await this.sttAdapter.start(
        // On Result
        (result) => {
          if (result.isFinal && result.text.trim()) {
            this.handleTranscriptionSuccess(result.text.trim());
          }
        },
        // On Error
        (error) => {
          this.handleVoiceError(error instanceof Error ? error.message : String(error));
        },
        // On End
        () => {
          if (this.state === 'LISTENING' || this.state === 'TRANSCRIBING') {
            if (this.state === 'LISTENING') {
              this.setState('IDLE');
              companionEvents.emit('IDLE');
            }
          }
        }
      );
    } catch (err) {
      this.handleVoiceError(err instanceof Error ? err.message : String(err));
    }
  }

  /**
   * Push-To-Talk Stop (Keyup or Mic Button Release)
   */
  public async stopListening(): Promise<void> {
    if (!this.isPttActive && this.state !== 'LISTENING') return;
    this.isPttActive = false;

    if (this.state === 'LISTENING') {
      this.setState('TRANSCRIBING');
      companionEvents.emit('TRANSCRIBING');

      try {
        const transcript = await this.sttAdapter.stop();
        if (typeof transcript === 'string' && transcript.trim()) {
          this.handleTranscriptionSuccess(transcript.trim());
        }
      } catch (err) {
        this.handleVoiceError(err instanceof Error ? err.message : String(err));
      }
    }
  }

  /**
   * Cancel active voice recording / TTS playback
   */
  public cancel(): void {
    this.isPttActive = false;
    this.sttAdapter.cancel();
    this.ttsAdapter.stop();

    if (this.errorTimer !== null) {
      clearTimeout(this.errorTimer);
      this.errorTimer = null;
    }

    this.setState('IDLE');
    companionEvents.emit('IDLE');
  }

  /**
   * Process completed transcription and forward to unified companion pipeline
   */
  private async handleTranscriptionSuccess(transcript: string) {
    if (!transcript) {
      this.setState('IDLE');
      companionEvents.emit('IDLE');
      return;
    }

    soundEffects.playListeningConfirm();
    this.setState('THINKING');
    companionEvents.emit('THINKING');

    if (this.transcriptHandler) {
      try {
        await this.transcriptHandler(transcript);
      } catch (err) {
        console.warn('[VoiceManager] Transcript handoff error:', err);
      }
    }
  }

  /**
   * Vocalize AI response text via TTS
   */
  public async speakText(text: string, visualHint?: string): Promise<void> {
    if (this.config.muted || !this.config.autoSpeak) {
      this.setState('IDLE');
      return;
    }

    if (!text || !text.trim()) {
      this.setState('IDLE');
      return;
    }

    this.setState('SPEAKING');
    companionEvents.emit('SPEAKING', text, undefined, { visual_hint: visualHint });

    await this.ttsAdapter.speak(
      text,
      // onStart
      () => {
        this.setState('SPEAKING');
      },
      // onEnd
      () => {
        soundEffects.playSpeechDone();
        this.setState('IDLE');
        companionEvents.emit('IDLE');
      },
      // onError
      (err) => {
        console.debug('[VoiceManager] TTS speech error or cancellation:', err);
        this.setState('IDLE');
        companionEvents.emit('IDLE');
      }
    );
  }

  /**
   * Handle errors gracefully with soft acoustic feedback and auto-revert
   */
  private handleVoiceError(errorMsg: string) {
    this.isPttActive = false;
    soundEffects.playErrorTone();
    this.setState('ERROR', { error: errorMsg });
    companionEvents.emit('ERROR', errorMsg);

    if (this.errorTimer !== null) {
      clearTimeout(this.errorTimer);
    }

    const scheduleTimer = typeof window !== 'undefined' ? window.setTimeout : setTimeout;
    this.errorTimer = scheduleTimer(() => {
      this.setState('IDLE');
      companionEvents.emit('IDLE');
      this.errorTimer = null;
    }, 2800) as unknown as number;
  }

  private loadPersistedConfig() {
    if (typeof localStorage === 'undefined') return;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        this.config = { ...DEFAULT_CONFIG, ...parsed };
      }
      const savedVoice = localStorage.getItem(VOICE_STORAGE_KEY) as OrpheusFemaleVoice | null;
      if (savedVoice && ['autumn', 'diana', 'hannah'].includes(savedVoice)) {
        this.currentVoice = savedVoice;
      }
    } catch {}
  }

  private savePersistedConfig() {
    if (typeof localStorage === 'undefined') return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.config));
      localStorage.setItem(VOICE_STORAGE_KEY, this.currentVoice);
    } catch {}
  }
}

export const voiceManager = VoiceManager.getInstance();
