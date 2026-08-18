import { WindowState } from './types';
import { isTauriEnvironment } from './window_manager';

const LOCAL_STORAGE_KEY = 'meli_window_state_v1';

const DEFAULT_STATE: WindowState = {
  x: 100,
  y: 100,
  width: 280,
  height: 420,
  sizePreset: 'compact',
  alwaysOnTop: true,
  visible: true,
};

export async function getPersistedWindowState(): Promise<WindowState> {
  if (isTauriEnvironment()) {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const state = await invoke<WindowState>('get_window_state');
      if (state) return state;
    } catch (err) {
      console.debug('[Persistence] Tauri get_window_state failed, using browser storage:', err);
    }
  }

  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (raw) {
      return { ...DEFAULT_STATE, ...JSON.parse(raw) };
    }
  } catch (err) {
    console.debug('[Persistence] localStorage read error:', err);
  }

  return DEFAULT_STATE;
}

export async function savePersistedWindowState(state: Partial<WindowState>): Promise<void> {
  if (isTauriEnvironment()) {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('save_window_state', { state });
    } catch (err) {
      console.debug('[Persistence] Tauri save_window_state error:', err);
    }
  }

  try {
    const current = await getPersistedWindowState();
    const updated = { ...current, ...state };
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updated));
  } catch (err) {
    console.debug('[Persistence] localStorage save error:', err);
  }
}
