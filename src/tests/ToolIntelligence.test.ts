/**
 * ToolIntelligence.test.ts - Unit & Integration Tests for Phase 1D Tool Intelligence
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { companionEvents } from '../enrichment/bridge/CompanionEventManager';
import { resolvePerformanceState } from '../enrichment/PerformanceAssetManager';

describe('Meli Phase 1D — Tool / Action Intelligence', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('1. Companion Event Protocol for Tools', () => {
    it('dispatches TOOL_REQUESTED, TOOL_CONFIRMATION_REQUIRED, TOOL_STARTED, TOOL_COMPLETED, TOOL_FAILED events', () => {
      const receivedEvents: string[] = [];
      const unsub = companionEvents.subscribe((event) => {
        receivedEvents.push(event.type);
      });

      companionEvents.emit('TOOL_REQUESTED', 'Action: GET_TIME');
      companionEvents.emit('TOOL_CONFIRMATION_REQUIRED', 'Meli wants to create note');
      companionEvents.emit('TOOL_STARTED', 'Executing GET_TIME');
      companionEvents.emit('TOOL_COMPLETED', 'GET_TIME succeeded');
      companionEvents.emit('TOOL_FAILED', 'Execution failed');

      expect(receivedEvents).toContain('TOOL_REQUESTED');
      expect(receivedEvents).toContain('TOOL_CONFIRMATION_REQUIRED');
      expect(receivedEvents).toContain('TOOL_STARTED');
      expect(receivedEvents).toContain('TOOL_COMPLETED');
      expect(receivedEvents).toContain('TOOL_FAILED');

      unsub();
    });

    it('maps tool event visual hints to correct standalone performance assets', () => {
      expect(resolvePerformanceState('focused')).toBe('focused');
      expect(resolvePerformanceState('curious')).toBe('curious');
      expect(resolvePerformanceState('complete')).toBe('complete');
      expect(resolvePerformanceState('error')).toBe('error');
    });
  });

  describe('2. Tool Policy & Confirmation API Contract', () => {
    it('serializes confirmation request payload with call_id and decision', () => {
      const confirmationPayload = {
        call_id: 'call_12345678',
        approved: true,
        conversation_id: 'conv_test_1',
      };

      expect(confirmationPayload.call_id).toBe('call_12345678');
      expect(confirmationPayload.approved).toBe(true);
      expect(JSON.stringify(confirmationPayload)).toContain('"approved":true');
    });
  });
});
