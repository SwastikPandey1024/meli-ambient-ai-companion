/**
 * bridge/types.ts - Typed contracts for Structured Companion Events
 */

export type CompanionEventType =
  | 'IDLE'
  | 'THINKING'
  | 'MEMORY_RETRIEVED'
  | 'TOOL_REQUESTED'
  | 'TOOL_CONFIRMATION_REQUIRED'
  | 'TOOL_STARTED'
  | 'TOOL_COMPLETED'
  | 'TOOL_FAILED'
  | 'RESPONSE_STREAM'
  | 'RESPONSE_COMPLETED'
  | 'ERROR'
  | 'APP_LAUNCH'
  | 'WORKING'
  | 'SLEEP'
  | 'CONFUSED'
  | 'SURPRISED'
  | 'HAPPY'
  | 'PROXIMITY'
  | 'HOVER'
  | 'CLICK_PET'
  | 'CELEBRATION'
  | 'LISTENING'
  | 'TRANSCRIBING'
  | 'SPEAKING'
  | 'SHOWCASE_PREVIEW';

export interface CompanionEventPayload {
  type: CompanionEventType;
  event_id?: string;
  timestamp: string | number;
  token?: string;
  message?: string;
  metadata?: Record<string, any>;
  visual_hint?: string;
  source?: string;
}

export type CompanionEventListener = (event: CompanionEventPayload) => void;
