/**
 * VoiceCommandParser.test.ts - Unit Tests for Voice Selection & Command Parsing
 */

import { describe, it, expect } from 'vitest';
import { parseVoiceCommand } from '../voice/voice_command_parser';
import { WebSpeechTTS } from '../voice/tts/web_speech_tts';
import { voiceManager } from '../voice';

describe('Meli Phase 1D — Voice Command Parser & Voice Selection Subsystem', () => {
  describe('1. Voice Selection Directives Parsing', () => {
    it('detects "use Hannah voice and introduce yourself"', () => {
      const res = parseVoiceCommand('use Hannah voice and introduce yourself');
      expect(res.isVoiceCommand).toBe(true);
      expect(res.voice).toBe('hannah');
      expect(res.remainingText).toBe('introduce yourself');
    });

    it('detects "Switch to Diana"', () => {
      const res = parseVoiceCommand('Switch to Diana');
      expect(res.isVoiceCommand).toBe(true);
      expect(res.voice).toBe('diana');
      expect(res.remainingText).toBeUndefined();
    });

    it('detects "speak in Autumn voice"', () => {
      const res = parseVoiceCommand('speak in Autumn voice');
      expect(res.isVoiceCommand).toBe(true);
      expect(res.voice).toBe('autumn');
      expect(res.remainingText).toBeUndefined();
    });

    it('detects "now give intro in hannah voice"', () => {
      const res = parseVoiceCommand('now give intro in hannah voice');
      expect(res.isVoiceCommand).toBe(true);
      expect(res.voice).toBe('hannah');
      expect(res.remainingText).toBe('now give intro');
    });

    it('detects "change to Diana voice and summarize notes"', () => {
      const res = parseVoiceCommand('change to Diana voice and summarize notes');
      expect(res.isVoiceCommand).toBe(true);
      expect(res.voice).toBe('diana');
      expect(res.remainingText).toBe('summarize notes');
    });

    it('returns isVoiceCommand=false for regular queries', () => {
      const res = parseVoiceCommand('What is the capital of France?');
      expect(res.isVoiceCommand).toBe(false);
      expect(res.voice).toBeUndefined();
    });
  });

  describe('2. Voice Manager Voice State & Persistence', () => {
    it('sets and retrieves active voice selection', () => {
      voiceManager.setVoice('diana');
      expect(voiceManager.getVoice()).toBe('diana');

      voiceManager.setVoice('hannah');
      expect(voiceManager.getVoice()).toBe('hannah');

      voiceManager.setVoice('autumn');
      expect(voiceManager.getVoice()).toBe('autumn');
    });
  });

  describe('3. TTS Text Sanitization', () => {
    it('strips bracketed voice directives like [Hannah voice, friendly and steady]', () => {
      const tts = new WebSpeechTTS();
      const raw = "[Hannah voice, friendly and steady] I'm Meli, your desktop companion!";
      const cleaned = tts.cleanTextForSpeech(raw);
      expect(cleaned).toBe("I'm Meli, your desktop companion!");
      expect(cleaned).not.toContain('Hannah voice');
      expect(cleaned).not.toContain('[');
    });

    it('strips internal tool IDs, confirmation IDs, and citations', () => {
      const tts = new WebSpeechTTS();
      const raw = "I executed tool-confirm-abc12345 and call_0987f4 for [Doc: Engineering Policy] [1].";
      const cleaned = tts.cleanTextForSpeech(raw);
      expect(cleaned).not.toContain('tool-confirm-');
      expect(cleaned).not.toContain('call_');
      expect(cleaned).not.toContain('[Doc:');
      expect(cleaned).not.toContain('[1]');
    });
  });
});
