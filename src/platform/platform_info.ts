import { PlatformInfo } from './types';
import { isTauriEnvironment } from './window_manager';

export async function getPlatformInfo(): Promise<PlatformInfo> {
  if (isTauriEnvironment()) {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const info = await invoke<PlatformInfo>('get_platform_info');
      if (info) return info;
    } catch (err) {
      console.debug('[PlatformInfo] Tauri get_platform_info error:', err);
    }
  }

  // Browser fallback inspection
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : '';
  let os: 'windows' | 'macos' | 'linux' | 'browser' = 'browser';
  if (ua.includes('Win')) os = 'windows';
  else if (ua.includes('Mac')) os = 'macos';
  else if (ua.includes('Linux')) os = 'linux';

  return {
    os,
    arch: 'x64',
    version: '1.0.0',
    isTauri: isTauriEnvironment(),
  };
}
