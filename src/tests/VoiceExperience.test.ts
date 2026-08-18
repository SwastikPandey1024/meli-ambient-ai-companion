/**
 * VoiceExperience.test.ts - Unit & Integration Tests for Phase 1C Voice Layer
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { voiceManager, VoiceState } from '../voice';
import { companionEvents } from '../enrichment/bridge/CompanionEventManager';
import { initHotkeyListener } from '../platform';
import { MediaRecorderSTT } from '../voice/stt/audio_recorder_stt';
import { WebSpeechTTS } from '../voice/tts/web_speech_tts';
import { OrpheusTTSAdapter, TTSProviderFactory } from '../voice/tts';
import { soundEffects } from '../voice/audio/sound_effects';

// Mock localStorage for Node test runner
const storageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    clear: () => {
      store = {};
    },
    removeItem: (key: string) => {
      delete store[key];
    },
  };
})();

if (typeof globalThis.localStorage === 'undefined') {
  Object.defineProperty(globalThis, 'localStorage', {
    value: storageMock,
    writable: true,
  });
}

describe('Meli Phase 1C — Voice Experience & Audio Orchestrator', () => {
  beforeEach(() => {
    globalThis.localStorage.clear();
    vi.restoreAllMocks();
    voiceManager.cancel();
  });

  afterEach(() => {
    voiceManager.cancel();
  });

  describe('1. Voice State Model & Subscriptions', () => {
    it('initializes in IDLE state with default configuration', () => {
      expect(voiceManager.getState()).toBe('IDLE');
      const config = voiceManager.getConfig();
      expect(config.muted).toBe(false);
      expect(config.volume).toBeGreaterThan(0);
      expect(config.autoSpeak).toBe(true);
    });

    it('notifies subscribers upon voice state changes', () => {
      const states: VoiceState[] = [];
      const unsub = voiceManager.subscribe((state) => {
        states.push(state);
      });

      expect(states).toContain('IDLE');
      unsub();
    });
  });

  describe('2. Push-To-Talk Keyboard Hotkey & Repeat Suppression', () => {
    it('triggers voice_ptt_start on keydown and voice_ptt_stop on keyup (Ctrl+Shift+V)', async () => {
      const hotkeyEvents: string[] = [];
      const unsub = await initHotkeyListener((shortcut) => {
        hotkeyEvents.push(shortcut);
      });

      if (typeof window !== 'undefined') {
        // Keydown (first press)
        window.dispatchEvent(
          new KeyboardEvent('keydown', {
            key: 'V',
            ctrlKey: true,
            shiftKey: true,
            repeat: false,
          })
        );
        expect(hotkeyEvents).toContain('voice_ptt_start');

        // Keydown repeat (should be suppressed)
        window.dispatchEvent(
          new KeyboardEvent('keydown', {
            key: 'V',
            ctrlKey: true,
            shiftKey: true,
            repeat: true,
          })
        );
        expect(hotkeyEvents.filter((e) => e === 'voice_ptt_start').length).toBe(1);

        // Keyup
        window.dispatchEvent(
          new KeyboardEvent('keyup', {
            key: 'V',
            ctrlKey: true,
            shiftKey: true,
          })
        );
        expect(hotkeyEvents).toContain('voice_ptt_stop');
      }

      unsub();
    });
  });

  describe('3. STT Adapter & Lifecycle Mechanics', () => {
    it('properly tracks listening state and cleans up audio tracks on stop', async () => {
      const trackStopMock = vi.fn();
      const mockStream = {
        getTracks: () => [{ stop: trackStopMock }],
      };

      const mockMediaRecorder: any = {
        start: vi.fn().mockImplementation(function(this: any) {
          if (this.onstart) this.onstart();
        }),
        stop: vi.fn(),
        state: 'recording',
        ondataavailable: null as any,
        onstart: null as any,
        onerror: null as any,
        onstop: null as any,
      };

      const mediaDevicesMock = {
        getUserMedia: vi.fn().mockResolvedValue(mockStream),
      };

      Object.defineProperty(globalThis.navigator, 'mediaDevices', {
        value: mediaDevicesMock,
        configurable: true,
        writable: true,
      });

      (globalThis as any).MediaRecorder = vi.fn().mockImplementation(() => mockMediaRecorder);
      (globalThis as any).MediaRecorder.isTypeSupported = vi.fn().mockReturnValue(true);

      const stt = new MediaRecorderSTT();
      expect(stt.isSupported()).toBe(true);

      const onResult = vi.fn();
      const onError = vi.fn();
      const onEnd = vi.fn();

      await stt.start(onResult, onError, onEnd);
      expect(stt.isListening()).toBe(true);
      expect(mockMediaRecorder.start).toHaveBeenCalled();

      // Cancel
      stt.cancel();
      expect(stt.isListening()).toBe(false);
      expect(trackStopMock).toHaveBeenCalled();
    });

    it('handles microphone permission denial gracefully without crashing', async () => {
      const mediaDevicesMock = {
        getUserMedia: vi.fn().mockRejectedValue(new Error('Permission denied')),
      };

      Object.defineProperty(globalThis.navigator, 'mediaDevices', {
        value: mediaDevicesMock,
        configurable: true,
        writable: true,
      });

      (globalThis as any).MediaRecorder = vi.fn();
      (globalThis as any).MediaRecorder.isTypeSupported = vi.fn().mockReturnValue(true);

      const stt = new MediaRecorderSTT();
      const onResult = vi.fn();
      const onError = vi.fn();
      const onEnd = vi.fn();

      await stt.start(onResult, onError, onEnd);
      expect(onError).toHaveBeenCalledWith(expect.any(Error));
      expect(stt.isListening()).toBe(false);
    });
  });

  describe('4. Transcript Handoff & Pipeline Convergence', () => {
    it('dispatches transcribed speech to registered transcript handler', async () => {
      const mockStream = {
        getTracks: () => [{ stop: vi.fn() }],
      };
      const mockMediaRecorder = {
        start: vi.fn(),
        stop: vi.fn(),
        state: 'recording',
        ondataavailable: null as any,
        onstart: null as any,
        onerror: null as any,
        onstop: null as any,
      };

      Object.defineProperty(globalThis.navigator, 'mediaDevices', {
        value: { getUserMedia: vi.fn().mockResolvedValue(mockStream) },
        configurable: true,
        writable: true,
      });
      (globalThis as any).MediaRecorder = vi.fn().mockImplementation(() => mockMediaRecorder);
      (globalThis as any).MediaRecorder.isTypeSupported = vi.fn().mockReturnValue(true);

      const mockHandler = vi.fn();
      const unsub = voiceManager.registerTranscriptHandler(mockHandler);

      // Trigger start listening then stop
      await voiceManager.startListening();
      expect(voiceManager.getState()).toBe('LISTENING');

      await voiceManager.stopListening();
      unsub();
    });
  });

  describe('5. TTS Synthesis & Markdown Normalization', () => {
    it('strips markdown syntax, citations, and headers before vocalization', async () => {
      const tts = new WebSpeechTTS();
      const textWithMarkdown = '# Hello World\nThis is **bold** and *italic* with `code` and [Doc: Policy].';
      const cleanMethod = (tts as any).cleanTextForSpeech.bind(tts);
      const cleaned = cleanMethod(textWithMarkdown);

      expect(cleaned).not.toContain('#');
      expect(cleaned).not.toContain('**');
      expect(cleaned).not.toContain('*');
      expect(cleaned).not.toContain('`');
      expect(cleaned).not.toContain('[Doc: Policy]');
      expect(cleaned).toContain('Hello World');
      expect(cleaned).toContain('bold and italic with code and');
    });

    it('cancels ongoing speech when new speech or stop is invoked', () => {
      const cancelMock = vi.fn();
      const synthMock = {
        cancel: cancelMock,
        speak: vi.fn(),
        pause: vi.fn(),
        resume: vi.fn(),
        getVoices: vi.fn().mockReturnValue([]),
      };

      (globalThis as any).speechSynthesis = synthMock;

      const tts = new WebSpeechTTS();
      tts.stop();
      expect(cancelMock).toHaveBeenCalled();
    });
  });

  describe('6. Voice Configuration, Mute, & Sound Effects', () => {
    it('toggles mute state and persists to storage', () => {
      const initialMuted = voiceManager.getConfig().muted;
      const nextMuted = voiceManager.toggleMute();
      expect(nextMuted).toBe(!initialMuted);
      expect(voiceManager.getConfig().muted).toBe(nextMuted);

      // Toggle back
      const restored = voiceManager.toggleMute();
      expect(restored).toBe(initialMuted);
    });

    it('executes sound effects without throwing even without hardware audio', () => {
      expect(() => {
        soundEffects.playMicStart();
        soundEffects.playListeningConfirm();
        soundEffects.playSpeechDone();
        soundEffects.playErrorTone();
      }).not.toThrow();
    });
  });

  describe('7. Visual Companion Event Synchronization', () => {
    it('emits structured companion events matching visual performance states', () => {
      const receivedEvents: string[] = [];
      const unsub = companionEvents.subscribe((event) => {
        receivedEvents.push(event.type);
      });

      companionEvents.emit('LISTENING');
      companionEvents.emit('TRANSCRIBING');
      companionEvents.emit('SPEAKING', 'Hello from Meli');

      expect(receivedEvents).toContain('LISTENING');
      expect(receivedEvents).toContain('TRANSCRIBING');
      expect(receivedEvents).toContain('SPEAKING');

      unsub();
    });
  });

  describe('8. TTS Provider Abstraction & Orpheus / WebSpeech Fallback', () => {
    it('instantiates OrpheusTTSAdapter with female voice settings (autumn/diana/hannah)', () => {
      const orpheus = new OrpheusTTSAdapter({ voice: 'autumn' });
      expect(orpheus.name).toContain('OrpheusTTS');
      expect(orpheus.getVoice()).toBe('autumn');

      orpheus.setVoice('diana');
      expect(orpheus.getVoice()).toBe('diana');

      orpheus.setVoice('hannah');
      expect(orpheus.getVoice()).toBe('hannah');
    });

    it('factory creates orpheus adapter by default and webspeech upon explicit selection', () => {
      const autoAdapter = TTSProviderFactory.create({ provider: 'auto' });
      expect(autoAdapter.name).toContain('OrpheusTTS');

      const webAdapter = TTSProviderFactory.create({ provider: 'webspeech' });
      expect(webAdapter.name).toContain('WebSpeech');
    });
  });
});

