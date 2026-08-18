/**
 * stt/web_speech_stt.ts - Browser / WebView Web Speech API STT Adapter
 */

import {
  ISTTAdapter,
  STTResultCallback,
  STTErrorCallback,
  STTEndCallback,
} from './stt_adapter';

export class WebSpeechSTT implements ISTTAdapter {
  public readonly name = 'WebSpeechSTT';
  private recognition: any = null;
  private listening: boolean = false;
  private finalTranscript: string = '';
  private onResultCb: STTResultCallback | null = null;
  private onErrorCb: STTErrorCallback | null = null;
  private onEndCb: STTEndCallback | null = null;

  public isSupported(): boolean {
    const hasWindow = typeof window !== 'undefined';
    const hasGlobal = typeof globalThis !== 'undefined';
    return !!(
      (hasWindow && ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)) ||
      (hasGlobal && ((globalThis as any).SpeechRecognition || (globalThis as any).webkitSpeechRecognition))
    );
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
      onError(new Error('Web Speech API is not supported in this environment.'));
      return;
    }

    if (this.listening) {
      this.cancel();
    }

    this.onResultCb = onResult;
    this.onErrorCb = onError;
    this.onEndCb = onEnd;
    this.finalTranscript = '';

    const SpeechRecognitionClass =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    try {
      this.recognition = new SpeechRecognitionClass();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';

      this.recognition.onstart = () => {
        this.listening = true;
      };

      this.recognition.onresult = (event: any) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const item = event.results[i];
          if (item.isFinal) {
            this.finalTranscript += item[0].transcript + ' ';
          } else {
            interim += item[0].transcript;
          }
        }

        const combined = (this.finalTranscript + interim).trim();
        if (this.onResultCb) {
          this.onResultCb({
            text: combined,
            isFinal: false,
          });
        }
      };

      this.recognition.onerror = (event: any) => {
        const errorMsg = event.error || 'Speech recognition error';
        if (errorMsg === 'no-speech') {
          // Soft timeout or no voice detected
          return;
        }
        this.listening = false;
        if (this.onErrorCb) {
          this.onErrorCb(new Error(`Speech recognition error: ${errorMsg}`));
        }
      };

      this.recognition.onend = () => {
        const wasListening = this.listening;
        this.listening = false;
        if (wasListening && this.onResultCb && this.finalTranscript.trim()) {
          this.onResultCb({
            text: this.finalTranscript.trim(),
            isFinal: true,
          });
        }
        if (this.onEndCb) {
          this.onEndCb();
        }
        this.cleanup();
      };

      this.recognition.start();
    } catch (err) {
      this.listening = false;
      this.cleanup();
      onError(err instanceof Error ? err : new Error(String(err)));
    }
  }

  public async stop(): Promise<string | void> {
    if (!this.listening || !this.recognition) return;
    try {
      this.listening = false;
      this.recognition.stop();
      return this.finalTranscript.trim();
    } catch {
      this.cleanup();
    }
  }

  public cancel(): void {
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch {}
    }
    this.listening = false;
    this.cleanup();
  }

  private cleanup(): void {
    if (this.recognition) {
      this.recognition.onstart = null;
      this.recognition.onresult = null;
      this.recognition.onerror = null;
      this.recognition.onend = null;
      this.recognition.abort();
      this.recognition = null;
    }
    this.onResultCb = null;
    this.onErrorCb = null;
    this.onEndCb = null;
  }
}
