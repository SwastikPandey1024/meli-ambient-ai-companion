import { SizePreset } from './types';

export function isTauriEnvironment(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

export async function startWindowDrag(): Promise<void> {
  if (!isTauriEnvironment()) return;
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('start_drag');
  } catch (err) {
    console.debug('[WindowManager] Drag error or browser fallback:', err);
  }
}

export async function setWindowSize(width: number, height: number): Promise<void> {
  if (!isTauriEnvironment()) return;
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('set_window_size', { width, height });
  } catch (err) {
    console.debug('[WindowManager] setWindowSize error:', err);
  }
}

export async function setWindowPosition(x: number, y: number): Promise<void> {
  if (!isTauriEnvironment()) return;
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('set_window_position', { x, y });
  } catch (err) {
    console.debug('[WindowManager] setWindowPosition error:', err);
  }
}

export async function setAlwaysOnTop(enabled: boolean): Promise<void> {
  if (!isTauriEnvironment()) return;
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('set_always_on_top', { enabled });
  } catch (err) {
    console.debug('[WindowManager] setAlwaysOnTop error:', err);
  }
}

export async function toggleWindowVisibility(): Promise<void> {
  if (!isTauriEnvironment()) return;
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('toggle_window_visibility');
  } catch (err) {
    console.debug('[WindowManager] toggleWindowVisibility error:', err);
  }
}

export async function showWindow(): Promise<void> {
  if (!isTauriEnvironment()) return;
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('show_window');
  } catch (err) {
    console.debug('[WindowManager] showWindow error:', err);
  }
}

export async function hideWindow(): Promise<void> {
  if (!isTauriEnvironment()) return;
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('hide_window');
  } catch (err) {
    console.debug('[WindowManager] hideWindow error:', err);
  }
}

export const SIZE_DIMENSIONS: Record<SizePreset, { width: number; height: number }> = {
  compact: { width: 280, height: 420 },
  default: { width: 360, height: 520 },
  large: { width: 460, height: 640 },
};
