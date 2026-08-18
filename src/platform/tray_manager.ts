import { SizePreset } from './types';
import { isTauriEnvironment } from './window_manager';

export type TrayListener = (payload: { action: string; sizePreset?: SizePreset }) => void;

const listeners: Set<TrayListener> = new Set();
let unlistenFn: (() => void) | null = null;

export async function initTrayListener(onTrayEvent: TrayListener): Promise<() => void> {
  listeners.add(onTrayEvent);

  if (isTauriEnvironment() && !unlistenFn) {
    try {
      const { listen } = await import('@tauri-apps/api/event');
      const unlisten = await listen<{ action: string; sizePreset?: SizePreset }>(
        'tray_event',
        (event) => {
          listeners.forEach((fn) => fn(event.payload));
        }
      );
      unlistenFn = unlisten;
    } catch (err) {
      console.debug('[TrayManager] Event listener registration skipped or failed:', err);
    }
  }

  return () => {
    listeners.delete(onTrayEvent);
  };
}
