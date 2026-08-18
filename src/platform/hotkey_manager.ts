import { isTauriEnvironment } from './window_manager';

export type HotkeyListener = (hotkey: string) => void;

const listeners: Set<HotkeyListener> = new Set();
let unlistenTauriFn: (() => void) | null = null;
let isPttPressed = false;
let globalListenersAttached = false;

function dispatchHotkey(shortcut: string) {
  listeners.forEach((fn) => {
    try {
      fn(shortcut);
    } catch (err) {
      console.warn('[HotkeyManager] Listener error:', err);
    }
  });
}

function handleKeyDown(e: KeyboardEvent) {
  const isModifier = e.ctrlKey || e.metaKey;
  if (!isModifier || !e.shiftKey) return;

  const keyLower = e.key.toLowerCase();
  const code = e.code;

  if (code === 'KeyM' || keyLower === 'm') {
    e.preventDefault();
    dispatchHotkey('toggle_window');
  } else if (code === 'KeyC' || keyLower === 'c') {
    e.preventDefault();
    dispatchHotkey('focus_chat');
  } else if (code === 'KeyV' || keyLower === 'v') {
    e.preventDefault();
    // Push-to-talk keydown (suppress auto-repeat)
    if (!e.repeat && !isPttPressed) {
      isPttPressed = true;
      dispatchHotkey('voice_ptt_start');
    }
  }
}

function handleKeyUp(e: KeyboardEvent) {
  if (!isPttPressed) return;

  const keyLower = e.key.toLowerCase();
  const code = e.code;

  if (
    code === 'KeyV' ||
    keyLower === 'v' ||
    e.key === 'Control' ||
    e.key === 'Shift' ||
    e.key === 'Meta'
  ) {
    isPttPressed = false;
    dispatchHotkey('voice_ptt_stop');
  }
}

function handleWindowBlur() {
  if (isPttPressed) {
    isPttPressed = false;
    dispatchHotkey('voice_ptt_stop');
  }
}

function attachGlobalListeners() {
  if (globalListenersAttached || typeof window === 'undefined') return;
  window.addEventListener('keydown', handleKeyDown, { passive: false });
  window.addEventListener('keyup', handleKeyUp, { passive: false });
  window.addEventListener('blur', handleWindowBlur);
  globalListenersAttached = true;
}

function detachGlobalListeners() {
  if (!globalListenersAttached || typeof window === 'undefined') return;
  window.removeEventListener('keydown', handleKeyDown);
  window.removeEventListener('keyup', handleKeyUp);
  window.removeEventListener('blur', handleWindowBlur);
  globalListenersAttached = false;
}

export async function initHotkeyListener(onHotkey: HotkeyListener): Promise<() => void> {
  listeners.add(onHotkey);
  attachGlobalListeners();

  if (isTauriEnvironment() && !unlistenTauriFn) {
    try {
      const { listen } = await import('@tauri-apps/api/event');
      const unlisten = await listen<{ shortcut: string }>('hotkey_triggered', (event) => {
        dispatchHotkey(event.payload.shortcut);
      });
      unlistenTauriFn = unlisten;
    } catch (err) {
      console.debug('[HotkeyManager] Tauri event listener registration skipped:', err);
    }
  }

  return () => {
    listeners.delete(onHotkey);
    if (listeners.size === 0) {
      detachGlobalListeners();
      if (unlistenTauriFn) {
        unlistenTauriFn();
        unlistenTauriFn = null;
      }
    }
  };
}
