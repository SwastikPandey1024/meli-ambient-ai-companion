/**
 * AssetShowcaseModal.tsx - Development & Demo QA Asset Showcase Modal
 *
 * Allows deliberate previewing of all 16 frozen runtime performance assets
 * with trigger conditions and direct live preview triggers.
 */

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, Play, RotateCcw } from 'lucide-react';
import { MeliPerformanceState, getPerformanceAssetPath } from '../enrichment/PerformanceAssetManager';

export interface AssetShowcaseItem {
  key: MeliPerformanceState;
  name: string;
  category: 'Core Performance' | 'Special Interaction';
  condition: string;
  trigger: string;
}

export const ASSET_CATALOG: AssetShowcaseItem[] = [
  // 12 Standalone Core Performance States
  {
    key: 'idle',
    name: '01. IDLE',
    category: 'Core Performance',
    condition: 'Default resting state when no active task is running.',
    trigger: 'Initial load / Interaction complete',
  },
  {
    key: 'curious',
    name: '02. CURIOUS',
    category: 'Core Performance',
    condition: 'Memory retrieved or user asks exploratory question ("what", "why", "how").',
    trigger: 'Recalled Memory / Confirmation Prompt',
  },
  {
    key: 'happy',
    name: '03. HAPPY',
    category: 'Core Performance',
    condition: 'Positive conversational synthesis or gentle user praise.',
    trigger: 'Warm response / Praise',
  },
  {
    key: 'thinking',
    name: '04. THINKING',
    category: 'Core Performance',
    condition: 'LLM reasoning active and generating answer stream.',
    trigger: 'THINKING companion event',
  },
  {
    key: 'working',
    name: '05. WORKING',
    category: 'Core Performance',
    condition: 'Active background tool execution in progress.',
    trigger: 'TOOL_STARTED companion event',
  },
  {
    key: 'focused',
    name: '06. FOCUSED',
    category: 'Core Performance',
    condition: 'Enterprise knowledge retrieval or multi-step execution.',
    trigger: 'SEARCH_KNOWLEDGE / Multi-step task',
  },
  {
    key: 'sleepy',
    name: '07. SLEEPY',
    category: 'Core Performance',
    condition: 'Extended user inactivity (> 45 seconds).',
    trigger: 'Inactivity timer decay',
  },
  {
    key: 'confused',
    name: '08. CONFUSED',
    category: 'Core Performance',
    condition: 'Ambiguous prompt or missing input parameters.',
    trigger: 'Clarification required',
  },
  {
    key: 'surprised',
    name: '09. SURPRISED',
    category: 'Core Performance',
    condition: 'Sudden new external discovery or return from absence.',
    trigger: 'Unexpected result / Return',
  },
  {
    key: 'error',
    name: '10. ERROR',
    category: 'Core Performance',
    condition: 'Recoverable tool failure or blocked shell injection.',
    trigger: 'TOOL_FAILED / Blocked attempt',
  },
  {
    key: 'complete',
    name: '11. COMPLETE',
    category: 'Core Performance',
    condition: 'Tool action or conversational response completed successfully.',
    trigger: 'TOOL_COMPLETED / Response finished',
  },
  {
    key: 'greeting',
    name: '12. GREETING',
    category: 'Core Performance',
    condition: 'First launch or returning after absence.',
    trigger: 'App launch / Wakeup',
  },

  // 4 Standalone Special Performance States
  {
    key: 'proximity',
    name: '13. PROXIMITY',
    category: 'Special Interaction',
    condition: 'Cursor enters proximity awareness radius around Meli.',
    trigger: 'Mouse within 180px radius',
  },
  {
    key: 'hover',
    name: '14. HOVER',
    category: 'Special Interaction',
    condition: 'Cursor directly over Meli interaction canvas.',
    trigger: 'Pointer enters viewport',
  },
  {
    key: 'click_pet',
    name: '15. CLICK_PET',
    category: 'Special Interaction',
    condition: 'Single click / gentle pet interaction.',
    trigger: 'Single click on character',
  },
  {
    key: 'celebration',
    name: '16. CELEBRATION',
    category: 'Special Interaction',
    condition: 'Major milestone completed or explicit celebratory event.',
    trigger: 'Milestone success / Celebration event',
  },
];

interface AssetShowcaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPreviewState?: (stateKey: MeliPerformanceState) => void;
}

export const AssetShowcaseModal: React.FC<AssetShowcaseModalProps> = ({
  isOpen,
  onClose,
  onPreviewState,
}) => {
  const [activePreview, setActivePreview] = useState<AssetShowcaseItem | null>(null);
  const [remainingTimeMs, setRemainingTimeMs] = useState<number>(3500);
  const timerRef = useRef<number | null>(null);
  const intervalRef = useRef<number | null>(null);

  const startPreviewTimer = (item: AssetShowcaseItem) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (intervalRef.current) clearInterval(intervalRef.current);

    setActivePreview(item);
    setRemainingTimeMs(3500);

    const startTime = Date.now();
    const duration = 3500;

    intervalRef.current = window.setInterval(() => {
      const elapsed = Date.now() - startTime;
      const left = Math.max(0, duration - elapsed);
      setRemainingTimeMs(left);
    }, 50);

    timerRef.current = window.setTimeout(() => {
      closePreview();
    }, duration);

    // Optional legacy notification if caller provided callback
    onPreviewState?.(item.key);
  };

  const closePreview = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (intervalRef.current) clearInterval(intervalRef.current);
    timerRef.current = null;
    intervalRef.current = null;
    setActivePreview(null);
    setRemainingTimeMs(3500);
  };

  const replayPreview = () => {
    if (activePreview) {
      startPreviewTimer(activePreview);
    }
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="showcase-backdrop"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.94, opacity: 0, y: 15 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.94, opacity: 0, y: 15 }}
          transition={{ duration: 0.2 }}
          className="showcase-modal"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Modal Header */}
          <div className="showcase-header">
            <div className="showcase-title-row">
              <Sparkles size={16} color="#FF7AA2" />
              <h2>Meli 16-Asset Performance Showcase</h2>
            </div>
            <button className="showcase-close-btn" onClick={onClose} title="Close Showcase">
              <X size={15} />
            </button>
          </div>

          <p className="showcase-subtitle">
            Deliberately preview each of Meli's 16 approved frozen runtime assets and their exact runtime conditions.
          </p>

          {/* Asset Grid */}
          <div className="showcase-grid">
            {ASSET_CATALOG.map((item) => (
              <div key={item.key} className="showcase-card">
                <div className="showcase-card-thumb">
                  <img
                    src={getPerformanceAssetPath(item.key)}
                    alt={item.name}
                    className="showcase-thumb-img"
                  />
                  <span className={`showcase-tag ${item.category === 'Special Interaction' ? 'special' : 'core'}`}>
                    {item.category === 'Special Interaction' ? 'Special' : 'Core'}
                  </span>
                </div>

                <div className="showcase-card-info">
                  <div className="showcase-card-name">{item.name}</div>
                  <div className="showcase-card-cond">{item.condition}</div>
                  <div className="showcase-card-trigger">
                    <strong>Trigger:</strong> {item.trigger}
                  </div>
                </div>

                <button
                  className="showcase-preview-btn"
                  onClick={() => startPreviewTimer(item)}
                  title={`Preview ${item.name} on Meli`}
                >
                  <Play size={10} /> Preview
                </button>
              </div>
            ))}
          </div>

          {/* Dedicated Foreground Preview Stage Overlay */}
          <AnimatePresence>
            {activePreview && (
              <motion.div
                initial={{ opacity: 0, scale: 0.92 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.92 }}
                transition={{ duration: 0.18 }}
                className="showcase-preview-overlay"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="showcase-preview-stage-card">
                  {/* Overlay Header */}
                  <div className="showcase-preview-stage-header">
                    <div className="showcase-preview-stage-title">
                      <Sparkles size={14} color="#FF7AA2" />
                      <span>{activePreview.name}</span>
                      <span className={`showcase-tag ${activePreview.category === 'Special Interaction' ? 'special' : 'core'}`}>
                        {activePreview.category}
                      </span>
                    </div>
                    <button
                      className="showcase-preview-stage-close"
                      onClick={closePreview}
                      title="Close Preview (Return to Showcase)"
                    >
                      <X size={14} />
                    </button>
                  </div>

                  {/* Character Stage Rendering Canonical PNG */}
                  <div className="showcase-preview-stage-viewport">
                    <img
                      src={getPerformanceAssetPath(activePreview.key)}
                      alt={activePreview.name}
                      className="showcase-preview-large-img"
                    />
                  </div>

                  {/* Condition Context */}
                  <div className="showcase-preview-stage-details">
                    <div className="preview-detail-row">
                      <span className="preview-label">Condition:</span>
                      <span className="preview-value">{activePreview.condition}</span>
                    </div>
                    <div className="preview-detail-row">
                      <span className="preview-label">Trigger:</span>
                      <span className="preview-value">{activePreview.trigger}</span>
                    </div>
                  </div>

                  {/* Animated 3.5s Progress Bar */}
                  <div className="showcase-progress-wrapper">
                    <div
                      className="showcase-progress-bar"
                      style={{ width: `${(remainingTimeMs / 3500) * 100}%` }}
                    />
                  </div>

                  {/* Overlay Controls */}
                  <div className="showcase-preview-stage-actions">
                    <div className="showcase-timer-badge">
                      Preview Active: {(remainingTimeMs / 1000).toFixed(1)}s
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        className="showcase-replay-btn"
                        onClick={replayPreview}
                        title="Restart 3.5s Preview"
                      >
                        <RotateCcw size={12} /> Replay
                      </button>
                      <button
                        className="showcase-done-btn"
                        onClick={closePreview}
                        title="Close and return to showcase"
                      >
                        <X size={12} /> Close
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
