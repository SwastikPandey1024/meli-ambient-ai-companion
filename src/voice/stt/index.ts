/**
 * stt/index.ts - STT Adapter Factory & Exports
 */

import { ISTTAdapter } from './stt_adapter';
import { MediaRecorderSTT } from './audio_recorder_stt';
import { WebSpeechSTT } from './web_speech_stt';

export * from './stt_adapter';
export * from './audio_recorder_stt';
export * from './web_speech_stt';

export function createSTTAdapter(): ISTTAdapter {
  const mediaRecorderSTT = new MediaRecorderSTT();
  if (mediaRecorderSTT.isSupported()) {
    return mediaRecorderSTT;
  }

  const webSpeechSTT = new WebSpeechSTT();
  if (webSpeechSTT.isSupported()) {
    return webSpeechSTT;
  }

  // Fallback to MediaRecorderSTT instance even if currently uninitialized
  return mediaRecorderSTT;
}
