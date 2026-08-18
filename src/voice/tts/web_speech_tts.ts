/**
 * tts/web_speech_tts.ts - SpeechSynthesis TTS Engine for Meli Voice
 *
 * Provides strictly feminine voice selection (Autumn, Diana, Hannah), text normalization
 * (stripping Markdown, JSON, URLs, internal IDs), utterance lifecycle safety, and sentence-aware chunking.
 */

import {
  ITTSAdapter,
  TTSStartCallback,
  TTSEndCallback,
  TTSErrorCallback,
} from './tts_adapter';
import { VoiceConfig } from '../types';

// Known male name tokens to blacklist from companion synthesis
const MALE_NAME_BLACKLIST = [
  'david', 'mark', 'george', 'richard', 'james', 'male', 'guy',
  'paul', 'stefan', 'brian', 'daniel', 'tom', 'eric', 'alex', 'fred',
  'junior', 'albert', 'oliver', 'rishi', 'cosmo', 'stephen', 'thomas',
  'lee', 'michael', 'christopher', 'matthew', 'anthony', 'andrew',
  'joseph', 'joshua', 'kevin', 'justin', 'ryan', 'brandon', 'gary',
  'steve', 'charles', 'robert', 'john', 'william', 'frank', 'edward'
];

export class WebSpeechTTS implements ITTSAdapter {
  public readonly name = 'WebSpeechTTS';
  private synth: SpeechSynthesis | null = null;
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private speaking: boolean = false;
  private config: VoiceConfig = {
    volume: 0.88,
    muted: false,
    rate: 0.94,
    pitch: 1.15,
    language: 'en-US',
    autoSpeak: true,
  };

  constructor(initialConfig?: Partial<VoiceConfig>) {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      this.synth = window.speechSynthesis;
    } else if (typeof globalThis !== 'undefined' && (globalThis as any).speechSynthesis) {
      this.synth = (globalThis as any).speechSynthesis;
    }
    if (initialConfig) {
      this.setConfig(initialConfig);
    }
  }

  public isSupported(): boolean {
    return (
      (typeof window !== 'undefined' && !!window.speechSynthesis) ||
      (typeof globalThis !== 'undefined' && !!(globalThis as any).speechSynthesis)
    );
  }

  public isSpeaking(): boolean {
    return this.speaking || this.currentUtterance !== null;
  }

  public setConfig(newConfig: Partial<VoiceConfig>): void {
    this.config = { ...this.config, ...newConfig };
    if (this.config.muted && this.speaking) {
      this.stop();
    }
  }

  /**
   * Cleans up markdown, URLs, JSON, bracketed voice directives, citations, and error traces for natural speech synthesis
   */
  public cleanTextForSpeech(rawText: string): string {
    return rawText
      // Remove bracketed voice stage directions (e.g. [Hannah voice, friendly and steady], [Voice: HANNAH])
      .replace(/\[(autumn|diana|hannah)\s+voice[^\]]*\]/gi, '')
      .replace(/\[voice:[^\]]+\]/gi, '')
      .replace(/\[(friendly|calm|steady|soft|gentle|warm|expressive|cheerful)[^\]]*\]/gi, '')
      .replace(/\((autumn|diana|hannah)\s+voice[^)]*\)/gi, '')
      // Remove code blocks
      .replace(/```[\s\S]*?```/g, '')
      // Remove JSON objects
      .replace(/\{[\s\S]*?\}/g, '')
      // Remove internal event / confirmation tokens
      .replace(/tool-confirm-[a-zA-Z0-9_-]+/gi, '')
      .replace(/call_[a-zA-Z0-9_-]+/gi, '')
      .replace(/TOOL_[A-Z_]+/g, '')
      // Remove raw URLs
      .replace(/https?:\/\/\S+/gi, 'the website')
      // Remove inline code
      .replace(/`([^`]+)`/g, '$1')
      // Remove enterprise doc citations like [Doc: Engineering Policy] or [1], [2]
      .replace(/\[Doc:[^\]]+\]/gi, '')
      .replace(/\[\d+\]/g, '')
      // Remove markdown links [text](url) -> text
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      // Remove markdown headers #, ##, etc.
      .replace(/^#{1,6}\s+/gm, '')
      // Remove bold/italics * and _
      .replace(/[*_~]+/g, '')
      // Remove bullet dashes
      .replace(/^[\s-•*]+\s+/gm, '')
      // Remove debug / stack trace snippets
      .replace(/(?:Traceback|RuntimeError|Exception|Error:).*$/gm, '')
      // Collapse whitespace
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Evaluates if a given speech synthesis voice is strictly NOT male
   */
  private isNotMaleVoice(v: SpeechSynthesisVoice): boolean {
    const fullDesc = `${v.name} ${v.voiceURI}`.toLowerCase();
    for (const maleName of MALE_NAME_BLACKLIST) {
      const regex = new RegExp(`\\b${maleName}\\b`, 'i');
      if (regex.test(fullDesc)) {
        return false;
      }
    }
    return true;
  }

  /**
   * Selects best available strictly feminine English voice mapped to logical voice preset (autumn/diana/hannah)
   */
  public getBestVoice(): SpeechSynthesisVoice | null {
    if (!this.synth) return null;
    const voices = this.synth.getVoices();
    if (!voices || voices.length === 0) return null;

    const logicalVoice = ((this.config as any).voice || 'autumn').toLowerCase();

    // Filter available voices to non-male English voices first
    const safeFemaleEnglishVoices = voices.filter(
      (v) => v.lang.toLowerCase().startsWith('en') && this.isNotMaleVoice(v)
    );

    // Prioritized specific candidate feminine voice names per preset
    let targetPicks: string[] = [];
    if (logicalVoice === 'diana') {
      // Diana: Crisp, calm, articulate feminine voice
      targetPicks = [
        'Microsoft Aria Online (Natural)',
        'Microsoft Aria',
        'Microsoft Zira Desktop',
        'Microsoft Zira',
        'Victoria',
        'Karen',
        'Samantha',
        'en-US-AriaNeural',
        'en-US-SaraNeural',
      ];
    } else if (logicalVoice === 'hannah') {
      // Hannah: Gentle, expressive, friendly feminine voice
      targetPicks = [
        'Microsoft Michelle Online (Natural)',
        'Microsoft Michelle',
        'Microsoft Jenny Online (Natural)',
        'Google US English',
        'Samantha',
        'Microsoft Jenny',
        'Microsoft Zira',
        'Karen',
        'en-US-MichelleNeural',
        'en-US-AnaNeural',
      ];
    } else {
      // Autumn (Default): Warm, natural, soft, companion-like feminine voice
      targetPicks = [
        'Microsoft Jenny Online (Natural)',
        'Microsoft Jenny',
        'Microsoft Zira Desktop',
        'Microsoft Zira',
        'Google US English Female',
        'Google UK English Female',
        'Samantha',
        'Victoria',
        'Karen',
        'Moira',
        'Tessa',
        'Fiona',
        'Microsoft Aria Online (Natural)',
        'en-US-JennyNeural',
        'en-US-AriaNeural',
        'en-US-AvaNeural',
        'en-US-EmmaNeural',
      ];
    }

    // 1. First priority: match exact desired feminine voices
    for (const name of targetPicks) {
      const match = voices.find(
        (v) =>
          this.isNotMaleVoice(v) &&
          (v.name.toLowerCase().includes(name.toLowerCase()) ||
            v.voiceURI.toLowerCase().includes(name.toLowerCase()))
      );
      if (match) return match;
    }

    // 2. Second priority: any verified female English voice
    if (safeFemaleEnglishVoices.length > 0) {
      return safeFemaleEnglishVoices[0];
    }

    // 3. Fallback: Any non-male voice
    const anySafe = voices.find((v) => this.isNotMaleVoice(v));
    return anySafe || voices[0] || null;
  }

  /**
   * Splits long text into natural sentence chunks
   */
  private splitIntoSentences(text: string): string[] {
    const rawMatches = text.match(/[^.!?]+[.!?]+|[^.!?]+$/g);
    if (!rawMatches) return [text];
    return rawMatches.map((s) => s.trim()).filter(Boolean);
  }

  public async speak(
    rawText: string,
    onStart?: TTSStartCallback,
    onEnd?: TTSEndCallback,
    onError?: TTSErrorCallback
  ): Promise<void> {
    if (!this.isSupported() || !this.synth) {
      if (onEnd) onEnd();
      return;
    }

    if (this.config.muted) {
      if (onEnd) onEnd();
      return;
    }

    const textToSpeak = this.cleanTextForSpeech(rawText);
    if (!textToSpeak) {
      if (onEnd) onEnd();
      return;
    }

    // Cancel any ongoing utterance before starting new speech
    this.stop();

    try {
      const sentences = this.splitIntoSentences(textToSpeak);
      const voice = this.getBestVoice();
      const logicalVoice = ((this.config as any).voice || 'autumn').toLowerCase();
      let currentIndex = 0;

      // Fine-tune feminine pitch & companion cadence per voice preset
      let tunedPitch = 1.15;
      let tunedRate = 0.94;
      if (logicalVoice === 'diana') {
        tunedPitch = 1.10;
        tunedRate = 0.98;
      } else if (logicalVoice === 'hannah') {
        tunedPitch = 1.20;
        tunedRate = 0.96;
      }

      const speakNextChunk = () => {
        if (!this.synth || currentIndex >= sentences.length) {
          this.speaking = false;
          this.currentUtterance = null;
          if (onEnd) onEnd();
          return;
        }

        const chunk = sentences[currentIndex];
        currentIndex += 1;

        const utterance = new SpeechSynthesisUtterance(chunk);
        if (voice) {
          utterance.voice = voice;
          utterance.lang = voice.lang || 'en-US';
        } else {
          utterance.lang = this.config.language || 'en-US';
        }

        utterance.volume = this.config.volume ?? 0.88;
        utterance.rate = this.config.rate ? this.config.rate * tunedRate : tunedRate;
        utterance.pitch = this.config.pitch ? this.config.pitch * tunedPitch : tunedPitch;

        utterance.onstart = () => {
          this.speaking = true;
          if (currentIndex === 1 && onStart) {
            onStart();
          }
        };

        utterance.onend = () => {
          speakNextChunk();
        };

        utterance.onerror = (e) => {
          if (e.error === 'canceled' || e.error === 'interrupted') {
            this.speaking = false;
            this.currentUtterance = null;
            if (onEnd) onEnd();
            return;
          }
          console.warn('[WebSpeechTTS] Synthesis chunk warning:', e);
          this.speaking = false;
          this.currentUtterance = null;
          if (onError) onError(new Error(`SpeechSynthesis error: ${e.error}`));
          if (onEnd) onEnd();
        };

        this.currentUtterance = utterance;
        this.synth.speak(utterance);
      };

      speakNextChunk();
    } catch (err: any) {
      console.warn('[WebSpeechTTS] Exception during speak execution:', err);
      this.speaking = false;
      this.currentUtterance = null;
      if (onError) onError(err);
      if (onEnd) onEnd();
    }
  }

  public stop(): void {
    if (this.synth) {
      try {
        this.synth.cancel();
      } catch {}
    }
    this.speaking = false;
    this.currentUtterance = null;
  }

  public pause(): void {
    if (this.synth) {
      try {
        this.synth.pause();
      } catch {}
    }
  }

  public resume(): void {
    if (this.synth) {
      try {
        this.synth.resume();
      } catch {}
    }
  }
}

export const WebSpeechTTSAdapter = WebSpeechTTS;
export type WebSpeechTTSAdapter = WebSpeechTTS;
