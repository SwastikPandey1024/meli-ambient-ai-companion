import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  isTauriEnvironment,
  setWindowSize,
  SIZE_DIMENSIONS,
  getPersistedWindowState,
  savePersistedWindowState,
  initTrayListener,
  initHotkeyListener,
  getPlatformInfo,
} from '../platform';

// Mock localStorage for Node environment
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

describe('Desktop Platform & Native Shell Abstraction', () => {
  beforeEach(() => {
    globalThis.localStorage.clear();
    vi.restoreAllMocks();
  });

  describe('1. Environment Detection & Platform Info', () => {
    it('accurately identifies browser runtime fallback when outside Tauri', async () => {
      expect(isTauriEnvironment()).toBe(false);
      const info = await getPlatformInfo();
      expect(info.isTauri).toBe(false);
      expect(['windows', 'macos', 'linux', 'browser']).toContain(info.os);
    });
  });

  describe('2. Window Bounds & Size Dimensions', () => {
    it('defines precise dimensions for Compact (280x420), Default (360x520), Large (460x640)', () => {
      expect(SIZE_DIMENSIONS.compact).toEqual({ width: 280, height: 420 });
      expect(SIZE_DIMENSIONS.default).toEqual({ width: 360, height: 520 });
      expect(SIZE_DIMENSIONS.large).toEqual({ width: 460, height: 640 });
    });

    it('gracefully executes setWindowSize without throwing in browser mode', async () => {
      await expect(setWindowSize(360, 520)).resolves.not.toThrow();
    });
  });

  describe('3. Persistence & State Recovery', () => {
    it('persists and restores window state through persistence layer', async () => {
      const initial = await getPersistedWindowState();
      expect(initial.sizePreset).toBe('compact');
      expect(initial.alwaysOnTop).toBe(true);

      await savePersistedWindowState({ sizePreset: 'large', alwaysOnTop: false, x: 250, y: 180 });
      const updated = await getPersistedWindowState();
      expect(updated.sizePreset).toBe('large');
      expect(updated.alwaysOnTop).toBe(false);
      expect(updated.x).toBe(250);
      expect(updated.y).toBe(180);
    });
  });

  describe('4. Tray Event Handling', () => {
    it('registers and unregisters tray event listeners cleanly', async () => {
      const handler = vi.fn();
      const unsub = await initTrayListener(handler);
      expect(typeof unsub).toBe('function');
      unsub();
    });
  });

  describe('5. Global Hotkey Routing', () => {
    it('handles keyboard shortcuts in browser fallback mode (Ctrl+Shift+M / Ctrl+Shift+C)', async () => {
      const hotkeyEvents: string[] = [];
      const unsub = await initHotkeyListener((shortcut) => {
        hotkeyEvents.push(shortcut);
      });

      if (typeof window !== 'undefined') {
        window.dispatchEvent(
          new KeyboardEvent('keydown', {
            key: 'M',
            ctrlKey: true,
            shiftKey: true,
          })
        );

        window.dispatchEvent(
          new KeyboardEvent('keydown', {
            key: 'C',
            ctrlKey: true,
            shiftKey: true,
          })
        );

        expect(hotkeyEvents).toContain('toggle_window');
        expect(hotkeyEvents).toContain('focus_chat');
      }

      unsub();
    });
  });
});
