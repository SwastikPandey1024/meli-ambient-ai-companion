/**
 * stt/audio_recorder_stt.ts - MediaRecorder + Groq Whisper Backend STT Adapter
 *
 * Preferred desktop / native Tauri STT adapter for accurate, sub-second transcription.
 * Captures microphone stream, encodes audio, and forwards to /api/companion/transcribe.
 * Guarantees all MediaStream tracks are explicitly released immediately on stop/cancel.
 */

import {
  ISTTAdapter,
  STTResultCallback,
  STTErrorCallback,
  STTEndCallback,
} from './stt_adapter';

export class MediaRecorderSTT implements ISTTAdapter {
  public readonly name = 'MediaRecorderSTT';
  private mediaStream: MediaStream | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private listening: boolean = false;
  private isCancelled: boolean = false;
  private mimeType: string = 'audio/webm';
  private endpointUrl: string = 'http://127.0.0.1:8000/api/companion/transcribe';

  private onResultCb: STTResultCallback | null = null;
  private onErrorCb: STTErrorCallback | null = null;
  private onEndCb: STTEndCallback | null = null;

  constructor(endpointUrl?: string) {
    if (endpointUrl) {
      this.endpointUrl = endpointUrl;
    }
  }

  public isSupported(): boolean {
    const nav = typeof navigator !== 'undefined' ? navigator : (typeof globalThis !== 'undefined' ? (globalThis as any).navigator : null);
    const hasRecorder = typeof MediaRecorder !== 'undefined' || (typeof globalThis !== 'undefined' && typeof (globalThis as any).MediaRecorder !== 'undefined');
    return !!(nav && nav.mediaDevices && typeof nav.mediaDevices.getUserMedia === 'function' && hasRecorder);
  }

  public isListening(): boolean {
    return this.listening;
  }

  public async start(
    onResult: STTResultCallback,
    onError: STTErrorCallback,
    onEnd: STTEndCallback
  ): Promise<void> {
    if (!this.isSupported()) {
      onError(new Error('MediaRecorder or getUserMedia is not supported in this environment.'));
      return;
    }

    if (this.listening) {
      this.cancel();
    }

    this.onResultCb = onResult;
    this.onErrorCb = onError;
    this.onEndCb = onEnd;
    this.audioChunks = [];
    this.isCancelled = false;

    try {
      // 1. Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      this.mediaStream = stream;

      // 2. Determine best supported MIME type
      const possibleTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
        'audio/aac',
      ];
      this.mimeType = possibleTypes.find((t) => MediaRecorder.isTypeSupported(t)) || '';

      const recorderOptions: MediaRecorderOptions = this.mimeType ? { mimeType: this.mimeType } : {};
      this.mediaRecorder = new MediaRecorder(stream, recorderOptions);

      this.mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstart = () => {
        this.listening = true;
      };

      this.mediaRecorder.onerror = (event: any) => {
        this.listening = false;
        this.releaseMicrophone();
        if (this.onErrorCb && !this.isCancelled) {
          this.onErrorCb(new Error(event.error?.message || 'MediaRecorder recording error'));
        }
      };

      this.mediaRecorder.onstop = async () => {
        this.listening = false;
        this.releaseMicrophone();

        if (this.isCancelled) {
          this.cleanup();
          return;
        }

        const audioBlob = new Blob(this.audioChunks, { type: this.mimeType || 'audio/webm' });
        this.audioChunks = [];

        if (audioBlob.size < 100) {
          // Empty or near-empty recording
          if (this.onEndCb) this.onEndCb();
          this.cleanup();
          return;
        }

        // 3. Post to backend transcription endpoint
        try {
          const extension = this.mimeType.includes('ogg') ? 'ogg' : this.mimeType.includes('mp4') ? 'mp4' : 'webm';
          const filename = `recording.${extension}`;

          const response = await fetch(this.endpointUrl, {
            method: 'POST',
            headers: {
              'Content-Type': this.mimeType || 'audio/webm',
              'X-Audio-Filename': filename,
            },
            body: audioBlob,
          });

          if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Transcription failed with HTTP ${response.status}`);
          }

          const result = await response.json();
          const transcript = (result.transcript || '').trim();

          if (this.onResultCb) {
            this.onResultCb({
              text: transcript,
              isFinal: true,
            });
          }

          if (this.onEndCb) {
            this.onEndCb();
          }
        } catch (err) {
          if (this.onErrorCb && !this.isCancelled) {
            this.onErrorCb(err instanceof Error ? err : new Error(String(err)));
          }
        } finally {
          this.cleanup();
        }
      };

      // Start recording with timeslice (e.g. 250ms chunks)
      this.listening = true;
      this.mediaRecorder.start(250);
    } catch (err) {
      this.listening = false;
      this.releaseMicrophone();
      this.cleanup();
      onError(err instanceof Error ? err : new Error(String(err)));
    }
  }

  public async stop(): Promise<string | void> {
    if (!this.listening || !this.mediaRecorder) return;
    if (this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch {
        this.releaseMicrophone();
        this.cleanup();
      }
    }
  }

  public cancel(): void {
    this.isCancelled = true;
    this.listening = false;
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch {}
    }
    this.releaseMicrophone();
    this.cleanup();
  }

  private releaseMicrophone(): void {
    if (this.mediaStream) {
      try {
        this.mediaStream.getTracks().forEach((track) => {
          track.stop();
        });
      } catch {}
      this.mediaStream = null;
    }
  }

  private cleanup(): void {
    this.releaseMicrophone();
    if (this.mediaRecorder) {
      this.mediaRecorder.ondataavailable = null;
      this.mediaRecorder.onstart = null;
      this.mediaRecorder.onerror = null;
      this.mediaRecorder.onstop = null;
      this.mediaRecorder = null;
    }
    this.audioChunks = [];
    this.onResultCb = null;
    this.onErrorCb = null;
    this.onEndCb = null;
  }
}
