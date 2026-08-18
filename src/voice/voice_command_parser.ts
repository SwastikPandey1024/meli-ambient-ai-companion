/**
 * voice_command_parser.ts - Voice Command & Voice Selection Parser
 *
 * Detects explicit voice-selection instructions such as:
 * - "use Hannah voice" / "use Hannah voice and introduce yourself"
 * - "switch to Diana" / "switch to Diana voice"
 * - "change to Autumn voice" / "speak in Autumn voice"
 * - "now give intro in hannah voice"
 *
 * Extracts the chosen voice (autumn | diana | hannah) and separates the semantic
 * payload so voice commands are never sent to the LLM as normal content.
 */

import { OrpheusFemaleVoice } from './tts/orpheus_tts';

export interface VoiceCommandResult {
  isVoiceCommand: boolean;
  voice?: OrpheusFemaleVoice;
  remainingText?: string;
  confirmationMessage?: string;
}

export const SUPPORTED_VOICES: OrpheusFemaleVoice[] = ['autumn', 'diana', 'hannah'];

export function parseVoiceCommand(rawText: string): VoiceCommandResult {
  if (!rawText || !rawText.trim()) {
    return { isVoiceCommand: false };
  }

  const text = rawText.trim();
  const lower = text.toLowerCase();

  // Regex patterns matching voice selection
  // 1. "use (the)? (autumn|diana|hannah) voice (and|to)? ..."
  // 2. "switch to (the)? (autumn|diana|hannah)( voice)? (and|to)? ..."
  // 3. "change to (the)? (autumn|diana|hannah)( voice)? (and|to)? ..."
  // 4. "speak in (the)? (autumn|diana|hannah)( voice)? (and|to)? ..."
  // 5. "talk in (the)? (autumn|diana|hannah)( voice)? (and|to)? ..."
  // 6. "... in (the)? (autumn|diana|hannah) voice"
  // 7. "now give intro in (autumn|diana|hannah) voice"

  const voicePattern = /\b(autumn|diana|hannah)\b/i;
  const match = lower.match(voicePattern);

  if (!match) {
    return { isVoiceCommand: false };
  }

  const detectedVoice = match[1].toLowerCase() as OrpheusFemaleVoice;

  // Check if sentence structure indicates a voice change directive
  const isDirective =
    /\b(use|switch\s+to|change\s+to|speak\s+in|talk\s+in|set\s+voice\s+to)\b/i.test(lower) ||
    /\bin\s+(the\s+)?(autumn|diana|hannah)\s+voice\b/i.test(lower) ||
    /\b(autumn|diana|hannah)\s+voice\b/i.test(lower);

  if (!isDirective) {
    return { isVoiceCommand: false };
  }

  // Remove the voice command phrase to produce clean remaining semantic text
  let cleaned = text;

  // Pattern A: Lead-in command: "Use Hannah voice and / to ..."
  cleaned = cleaned.replace(
    /^(please\s+)?(use|switch\s+to|change\s+to|speak\s+in|talk\s+in|set\s+voice\s+to)\s+(the\s+)?(autumn|diana|hannah)(\s+voice)?(\s+(and|to|then|,))?\s*/i,
    ''
  );

  // Pattern B: Trailing / inline: "... in (the)? Hannah voice"
  cleaned = cleaned.replace(
    /\s*(,\s*)?(in|using|with)\s+(the\s+)?(autumn|diana|hannah)\s+voice\b/i,
    ''
  );

  // Pattern C: "now give intro in Hannah voice" -> "now give intro"
  cleaned = cleaned.replace(
    /\s*(,\s*)?in\s+(the\s+)?(autumn|diana|hannah)\s+voice\s*/i,
    ''
  );

  // Pattern D: Standalone "<voice> voice" phrase
  cleaned = cleaned.replace(/\b(autumn|diana|hannah)\s+voice\b/i, '');

  cleaned = cleaned.trim().replace(/^,\s*/, '').replace(/^[.!?]\s*/, '').trim();

  // If after cleaning, only filler words remains ("and", "then", "please"), clear it
  if (/^(and|then|please|now)$/i.test(cleaned)) {
    cleaned = '';
  }

  const confirmationMessage = `Switched voice to ${detectedVoice.charAt(0).toUpperCase() + detectedVoice.slice(1)}. ✨`;

  return {
    isVoiceCommand: true,
    voice: detectedVoice,
    remainingText: cleaned.length > 0 ? cleaned : undefined,
    confirmationMessage,
  };
}
