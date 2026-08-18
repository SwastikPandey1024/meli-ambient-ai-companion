/**
 * voice/types.ts - Type Contracts for Meli Phase 1C Voice & Audio Subsystem
 */

export type VoiceState =
  | 'IDLE'
  | 'LISTENING'
  | 'TRANSCRIBING'
  | 'THINKING'
  | 'SPEAKING'
  | 'ERROR';

export interface VoiceConfig {
  volume: number;      // 0.0 to 1.0 (default: 0.8)
  muted: boolean;       // boolean (default: false)
  rate: number;        // 0.5 to 2.0 (default: 1.0)
  pitch: number;       // 0.5 to 1.5 (default: 1.05)
  language: string;    // e.g. "en-US"
  autoSpeak: boolean;  // whether companion replies aloud automatically (default: true)
  voice?: string;      // selected voice preset (autumn | diana | hannah)
}

export interface TranscriptResult {
  text: string;
  isFinal: boolean;
  confidence?: number;
}

export type STTResultCallback = (result: TranscriptResult) => void;
export type STTErrorCallback = (error: Error | string) => void;
export type STTEndCallback = () => void;

export interface ISTTAdapter {
  readonly name: string;
  isSupported(): boolean;
  isListening(): boolean;
  start(
    onResult: STTResultCallback,
    onError: STTErrorCallback,
    onEnd: STTEndCallback
  ): Promise<void>;
  stop(): Promise<string | void>;
  cancel(): void;
}

export type TTSStartCallback = () => void;
export type TTSEndCallback = () => void;
export type TTSErrorCallback = (error: Error | string) => void;

export interface ITTSAdapter {
  readonly name: string;
  isSupported(): boolean;
  isSpeaking(): boolean;
  speak(
    text: string,
    onStart?: TTSStartCallback,
    onEnd?: TTSEndCallback,
    onError?: TTSErrorCallback
  ): Promise<void>;
  stop(): void;
  pause(): void;
  resume(): void;
  setConfig(config: Partial<VoiceConfig>): void;
}

export type VoiceStateListener = (state: VoiceState, metadata?: Record<string, any>) => void;
