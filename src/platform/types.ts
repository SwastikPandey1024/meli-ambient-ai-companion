export type SizePreset = 'compact' | 'default' | 'large';

export interface WindowBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface WindowState {
  x: number;
  y: number;
  width: number;
  height: number;
  sizePreset: SizePreset;
  alwaysOnTop: boolean;
  visible: boolean;
}

export interface PlatformInfo {
  os: 'windows' | 'macos' | 'linux' | 'browser';
  arch: string;
  version: string;
  isTauri: boolean;
}

export interface TrayEventPayload {
  action: 'show' | 'hide' | 'toggle_chat' | 'set_size' | 'toggle_always_on_top' | 'quit';
  sizePreset?: SizePreset;
}
