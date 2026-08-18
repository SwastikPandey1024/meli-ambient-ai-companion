import { useEffect, useMemo, useState, useRef } from 'react';
import { CharacterStateMachine } from './state/CharacterStateMachine';
import { EnrichedCharacterViewport, CompanionSize } from './enrichment/EnrichedCharacterViewport';
import { useCompanionEventBridge } from './enrichment/bridge/useCompanionEventBridge';
import { companionEvents } from './enrichment/bridge/CompanionEventManager';
import { ChatPanel } from './components/ChatPanel';
import { AssetShowcaseModal } from './components/AssetShowcaseModal';
import { voiceManager } from './voice';
import { Heart, Minus, X, MessageSquare, Sun, Moon, Sparkles, Eye, ArrowDownToDot } from 'lucide-react';
import { preloadAllPerformanceAssets } from './enrichment/PerformanceAssetManager';
import {
  getPersistedWindowState,
  savePersistedWindowState,
  setWindowSize,
  startWindowDrag,
  hideWindow,
  initTrayListener,
  initHotkeyListener,
  SIZE_DIMENSIONS,
} from './platform';

export function App() {
  const stateMachine = useMemo(() => new CharacterStateMachine(), []);
  const [size, setSize] = useState<CompanionSize>('default');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isShowcaseOpen, setIsShowcaseOpen] = useState(false);
  const [bgTheme, setBgTheme] = useState<'transparent' | 'dark' | 'glass'>('transparent');
  const inactivityTimerRef = useRef<any>(null);
  const dragStartPos = useRef<{ x: number; y: number } | null>(null);

  // Preload all 16 runtime assets immediately on app boot
  useEffect(() => {
    preloadAllPerformanceAssets();
  }, []);

  const {
    activePerformanceState,
    bubbles,
    dismissBubble,
    equippedAccessories,
  } = useCompanionEventBridge({ enableAutoBubbles: true, stateMachine });

  // Toggle chat with automatic native window expansion/contraction
  const toggleChat = (nextOpen?: boolean) => {
    setIsChatOpen((prev) => {
      const target = typeof nextOpen === 'boolean' ? nextOpen : !prev;
      const dims = SIZE_DIMENSIONS[size];
      if (dims) {
        const targetWidth = target ? dims.width + 340 : dims.width;
        setWindowSize(targetWidth, dims.height);
      }
      return target;
    });
  };

  // Reset inactivity timer & manage SLEEP state after 45s of idle
  const resetInactivityTimer = () => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
    }
    inactivityTimerRef.current = setTimeout(() => {
      if (!isChatOpen && voiceManager.getState() !== 'SPEAKING') {
        companionEvents.emit('SLEEP');
      }
    }, 45000);
  };

  useEffect(() => {
    const handleUserActivity = () => resetInactivityTimer();
    window.addEventListener('mousemove', handleUserActivity);
    window.addEventListener('keydown', handleUserActivity);
    window.addEventListener('click', handleUserActivity);
    resetInactivityTimer();

    return () => {
      window.removeEventListener('mousemove', handleUserActivity);
      window.removeEventListener('keydown', handleUserActivity);
      window.removeEventListener('click', handleUserActivity);
      if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
    };
  }, [isChatOpen]);

  // Shortcut for Ctrl+Shift+S (Asset Showcase)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'S' || e.code === 'KeyS')) {
        e.preventDefault();
        setIsShowcaseOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // 1. Initial State Restoration from Native Persistence
  useEffect(() => {
    getPersistedWindowState().then((persisted) => {
      if (persisted.sizePreset) {
        setSize(persisted.sizePreset as CompanionSize);
      }
    });
  }, []);

  // 2. Tray Event Listener
  useEffect(() => {
    const unlistenPromise = initTrayListener((payload) => {
      if (payload.action === 'toggle_chat') {
        toggleChat();
      } else if (payload.action === 'set_size' && payload.sizePreset) {
        handleSizeChange(payload.sizePreset as CompanionSize);
      }
    });

    return () => {
      unlistenPromise.then((unsub) => unsub());
    };
  }, [size, isChatOpen]);

  // 3. Global Hotkey Listener (Ctrl+Shift+M / Ctrl+Shift+C / Ctrl+Shift+V)
  useEffect(() => {
    const unlistenPromise = initHotkeyListener((shortcut) => {
      if (shortcut === 'focus_chat') {
        toggleChat();
      } else if (shortcut === 'voice_ptt_start') {
        toggleChat(true); // Open chat drawer to show active transcript & voice states
        voiceManager.startListening();
      } else if (shortcut === 'voice_ptt_stop') {
        voiceManager.stopListening();
      }
    });

    return () => {
      unlistenPromise.then((unsub) => unsub());
    };
  }, [size, isChatOpen]);

  const handleSizeChange = (newSize: CompanionSize) => {
    setSize(newSize);
    savePersistedWindowState({ sizePreset: newSize });
    const dims = SIZE_DIMENSIONS[newSize];
    if (dims) {
      const targetWidth = isChatOpen ? dims.width + 340 : dims.width;
      setWindowSize(targetWidth, dims.height);
    }
  };

  const cycleSize = () => {
    const nextSize: CompanionSize =
      size === 'compact' ? 'default' : size === 'default' ? 'large' : 'compact';
    handleSizeChange(nextSize);
  };

  const handleMinimize = async () => {
    await hideWindow();
  };

  const handleClose = async () => {
    await hideWindow();
  };

  const cycleTheme = () => {
    setBgTheme((prev) =>
      prev === 'transparent' ? 'dark' : prev === 'dark' ? 'glass' : 'transparent'
    );
  };

  const getBackgroundStyle = () => {
    switch (bgTheme) {
      case 'dark':
        return '#0E1017';
      case 'glass':
        return 'linear-gradient(135deg, #181A26 0%, #0D0E15 100%)';
      case 'transparent':
      default:
        return 'transparent';
    }
  };

  // Safe window drag handler that preserves clicks and double-clicks (SINK/POP)
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      const target = e.target as HTMLElement;
      if (
        !target.closest('button') &&
        !target.closest('input') &&
        !target.closest('textarea') &&
        !target.closest('.meli-chat-panel') &&
        !target.closest('.showcase-modal') &&
        !target.closest('.showcase-preview-overlay')
      ) {
        dragStartPos.current = { x: e.clientX, y: e.clientY };
      }
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (dragStartPos.current) {
      const dx = Math.abs(e.clientX - dragStartPos.current.x);
      const dy = Math.abs(e.clientY - dragStartPos.current.y);
      if (dx > 6 || dy > 6) {
        dragStartPos.current = null;
        startWindowDrag();
      }
    }
  };

  const handleMouseUp = () => {
    dragStartPos.current = null;
  };

  return (
    <main
      className="app-container"
      style={{
        position: 'relative',
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
        background: getBackgroundStyle(),
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'background 0.3s ease',
        userSelect: 'none',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Mini Companion Capsule Controls - Anchored safely at top */}
      <header className="control-capsule" data-tauri-drag-region>
        {/* Pet Meli (Single Click / Tactile Bounce) */}
        <button
          className="capsule-btn"
          title="Pet Meli (Single Click)"
          onClick={(e) => {
            e.stopPropagation();
            stateMachine.triggerClick();
          }}
        >
          <Heart size={13} fill="#FF7AA2" color="#FF7AA2" />
        </button>

        {/* Sink / Pop Portal Trigger */}
        <button
          className="capsule-btn"
          title="Sink & Pop Portal ✨ (Double Click on Meli)"
          onClick={(e) => {
            e.stopPropagation();
            stateMachine.triggerSinkPop();
          }}
        >
          <ArrowDownToDot size={13} color="#FF7AA2" />
        </button>

        {/* Celebrate Milestone */}
        <button
          className="capsule-btn"
          title="Celebrate Milestone ✨"
          onClick={(e) => {
            e.stopPropagation();
            companionEvents.emit('CELEBRATION', 'Mission accomplished! ✨🎉');
          }}
        >
          <Sparkles size={13} color="#69F0AE" />
        </button>

        {/* Toggle Chat */}
        <button
          className={`capsule-btn ${isChatOpen ? 'active' : ''}`}
          title="Toggle Chat"
          onClick={(e) => {
            e.stopPropagation();
            toggleChat();
          }}
        >
          <MessageSquare size={13} color="#FF7AA2" />
        </button>

        {/* Cycle S/M/L Size */}
        <button
          className="capsule-btn"
          title={`Cycle Size: ${size.toUpperCase()} (S=280px, M=360px, L=460px)`}
          onClick={(e) => {
            e.stopPropagation();
            cycleSize();
          }}
          style={{ fontSize: '9.5px', fontWeight: 700 }}
        >
          {size === 'compact' ? 'S' : size === 'default' ? 'M' : 'L'}
        </button>

        {/* 16-Asset State Showcase */}
        <button
          className={`capsule-btn ${isShowcaseOpen ? 'active' : ''}`}
          title="16-Asset Showcase (Ctrl+Shift+S)"
          onClick={(e) => {
            e.stopPropagation();
            setIsShowcaseOpen((prev) => !prev);
          }}
        >
          <Eye size={13} color="#B388FF" />
        </button>

        {/* Cycle Background Theme */}
        <button
          className="capsule-btn"
          title={`Theme: ${bgTheme}`}
          onClick={(e) => {
            e.stopPropagation();
            cycleTheme();
          }}
        >
          {bgTheme === 'transparent' ? <Moon size={12} /> : <Sun size={12} />}
        </button>

        {/* Window Controls */}
        <button
          className="capsule-btn"
          title="Minimize to Tray"
          onClick={(e) => {
            e.stopPropagation();
            handleMinimize();
          }}
        >
          <Minus size={12} />
        </button>

        <button
          className="capsule-btn"
          title="Hide to Tray"
          onClick={(e) => {
            e.stopPropagation();
            handleClose();
          }}
        >
          <X size={12} />
        </button>
      </header>

      {/* Main Character Stage + Side-by-Side Chat */}
      <div
        className="app-stage-wrapper"
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          flex: 1,
          padding: '38px 10px 10px 10px',
        }}
      >
        <EnrichedCharacterViewport
          stateMachine={stateMachine}
          size={size}
          activePerformanceState={activePerformanceState}
          equippedAccessories={equippedAccessories}
          bubbles={bubbles}
          onDismissBubble={dismissBubble}
        />

        {/* Floating Side-by-Side Chat Panel */}
        {isChatOpen && (
          <ChatPanel
            isOpen={isChatOpen}
            onClose={() => toggleChat(false)}
            stateMachine={stateMachine}
          />
        )}

        {/* Asset Performance Showcase Modal */}
        <AssetShowcaseModal
          isOpen={isShowcaseOpen}
          onClose={() => setIsShowcaseOpen(false)}
          onPreviewState={(key) => {
            companionEvents.emit('SHOWCASE_PREVIEW', { visual_hint: key } as any);
          }}
        />
      </div>
    </main>
  );
}

export default App;
