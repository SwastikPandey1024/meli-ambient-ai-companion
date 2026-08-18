/**
 * CompanionEventManager.ts - Decoupled Event Bus for Companion State & Visual Enrichment
 */

import { CompanionEventType, CompanionEventPayload, CompanionEventListener } from './types';

export class CompanionEventManager {
  private listeners: Set<CompanionEventListener> = new Set();
  private static instance: CompanionEventManager;

  public static getInstance(): CompanionEventManager {
    if (!CompanionEventManager.instance) {
      CompanionEventManager.instance = new CompanionEventManager();
    }
    return CompanionEventManager.instance;
  }

  public subscribe(listener: CompanionEventListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  public emit(
    type: CompanionEventType,
    message?: string,
    metadata?: Record<string, any>,
    extra?: Partial<CompanionEventPayload>
  ): CompanionEventPayload {
    const payload: CompanionEventPayload = {
      type,
      message,
      metadata,
      timestamp: Date.now(),
      ...extra,
    };

    this.emitEvent(payload);
    return payload;
  }

  public emitEvent(payload: CompanionEventPayload) {
    this.listeners.forEach((cb) => {
      try {
        cb(payload);
      } catch (err) {
        console.warn('[CompanionEventManager] Listener exception:', err);
      }
    });
  }

  public clearAll() {
    this.listeners.clear();
  }
}

export const companionEvents = CompanionEventManager.getInstance();
