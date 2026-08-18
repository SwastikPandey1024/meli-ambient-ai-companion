import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, X, Mic, MicOff, Volume2, VolumeX, AlertCircle, Loader2, ShieldAlert, Check, Wrench } from 'lucide-react';
import { CharacterStateMachine } from '../state/CharacterStateMachine';
import { companionEvents } from '../enrichment/bridge/CompanionEventManager';
import { voiceManager, VoiceState } from '../voice';

import { parseVoiceCommand } from '../voice/voice_command_parser';
import { OrpheusFemaleVoice } from '../voice/tts';

export interface ChatMsg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface PendingConfirmationState {
  call_id: string;
  tool: string;
  prompt: string;
  arguments?: Record<string, any>;
}

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  stateMachine?: CharacterStateMachine;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      id: 'welcome-1',
      role: 'assistant',
      content: "Hi. I'm Meli. I'm right here if you need a quiet companion, want to talk, or need me to take action for you.",
    },
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeToolAction, setActiveToolAction] = useState<string | null>(null);
  const [pendingConfirmation, setPendingConfirmation] = useState<PendingConfirmationState | null>(null);
  const [isConfirming, setIsConfirming] = useState<boolean>(false);
  const [voiceState, setVoiceState] = useState<VoiceState>(voiceManager.getState());
  const [currentVoice, setCurrentVoice] = useState<OrpheusFemaleVoice>(voiceManager.getVoice());
  const [isMuted, setIsMuted] = useState<boolean>(voiceManager.getConfig().muted);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 1. Subscribe to Voice Manager state, voice, & config changes
  useEffect(() => {
    const unsubState = voiceManager.subscribe((state) => {
      setVoiceState(state);
    });
    const unsubVoice = voiceManager.subscribeVoice((v) => {
      setCurrentVoice(v);
    });
    return () => {
      unsubState();
      unsubVoice();
    };
  }, []);

  // 2. Register Transcript Handler from Voice Pipeline
  useEffect(() => {
    const unsub = voiceManager.registerTranscriptHandler((transcript) => {
      handleSend(transcript);
    });
    return () => unsub();
  }, [messages, isStreaming, currentVoice]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSend = async (customText?: string) => {
    const rawText = (customText || input).trim();
    if (!rawText || isStreaming) return;

    setInput('');

    // Check for explicit voice command
    const voiceCmd = parseVoiceCommand(rawText);
    if (voiceCmd.isVoiceCommand && voiceCmd.voice) {
      voiceManager.setVoice(voiceCmd.voice);
      setCurrentVoice(voiceCmd.voice);

      // If user ONLY asked to switch voice (e.g. "Switch to Diana" or "Use Hannah voice")
      if (!voiceCmd.remainingText) {
        const confirmText = `Switched voice to ${voiceCmd.voice.charAt(0).toUpperCase() + voiceCmd.voice.slice(1)}. ✨`;
        const userMsg: ChatMsg = {
          id: `user-${Date.now()}`,
          role: 'user',
          content: rawText,
        };
        const asstMsg: ChatMsg = {
          id: `asst-${Date.now()}`,
          role: 'assistant',
          content: confirmText,
        };
        setMessages((prev) => [...prev, userMsg, asstMsg]);
        voiceManager.speak(`I'm now speaking with ${voiceCmd.voice} voice.`);
        return;
      }
    }

    const text = voiceCmd.isVoiceCommand && voiceCmd.remainingText ? voiceCmd.remainingText : rawText;

    const userMsg: ChatMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: rawText,
    };

    const assistantMsgId = `asst-${Date.now()}`;
    const initialAssistantMsg: ChatMsg = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setIsStreaming(true);
    companionEvents.emit('THINKING');

    const historyPayload = messages
      .filter((m) => m.content.trim().length > 0)
      .slice(-6)
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      const response = await fetch('http://127.0.0.1:8000/api/companion/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: historyPayload,
          top_k: 3,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const dataStr = trimmed.slice(5).trim();

          if (dataStr === '[DONE]') {
            break;
          }

          try {
            const data = JSON.parse(dataStr);

            // Forward structured companion event to event bridge
            if (data.type) {
              companionEvents.emitEvent(data);
            }

            // Process Tool Intelligence Events
            if (data.type === 'TOOL_CONFIRMATION_REQUIRED') {
              setPendingConfirmation({
                call_id: data.metadata?.call_id || '',
                tool: data.metadata?.tool || '',
                prompt: data.message || 'Confirmation Required',
                arguments: data.metadata?.arguments,
              });
            } else if (data.type === 'TOOL_COMPLETED') {
              setActiveToolAction(null);
              // Handle URL opening in browser on client side
              if (data.metadata?.tool === 'OPEN_URL' || data.metadata?.result_data?.url) {
                const targetUrl = data.metadata?.result_data?.url || data.metadata?.arguments?.url;
                if (targetUrl && (targetUrl.startsWith('http://') || targetUrl.startsWith('https://'))) {
                  try {
                    window.open(targetUrl, '_blank', 'noopener,noreferrer');
                  } catch (e) {
                    console.warn('Could not open browser window:', e);
                  }
                }
              }
            } else if (data.type === 'TOOL_FAILED') {
              setActiveToolAction(null);
            }

            // Handle error event payload
            if (data.type === 'ERROR') {
              const errMsg = data.message || "I encountered a small hiccup in my thinking space.";
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantMsgId ? { ...m, content: errMsg } : m))
              );
            }

            // Accumulate response tokens
            if (data.token) {
              fullContent += data.token;
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantMsgId ? { ...m, content: fullContent } : m))
              );
            }
          } catch {
            // Non-JSON line
          }
        }
      }

      setIsStreaming(false);

      // Vocalize response through Text-To-Speech if configured and non-empty
      if (fullContent.trim()) {
        voiceManager.speakText(fullContent.trim());
      }
    } catch (err) {
      console.warn('Companion chat request failed:', err);
      const fallbackText =
        "I'm having a little trouble reaching my thinking space right now. Give me a moment and try again.";
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantMsgId ? { ...m, content: fallbackText } : m))
      );
      setIsStreaming(false);
      companionEvents.emit('ERROR', fallbackText);
    }
  };

  // Global key listener for confirmation card (Enter = Approve, Escape = Cancel)
  useEffect(() => {
    if (!pendingConfirmation) return;
    const handleConfKey = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        e.stopPropagation();
        handleConfirmTool(true);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        handleConfirmTool(false);
      }
    };
    window.addEventListener('keydown', handleConfKey);
    return () => window.removeEventListener('keydown', handleConfKey);
  }, [pendingConfirmation, isConfirming]);

  const handleConfirmTool = async (approved: boolean) => {
    if (!pendingConfirmation || isConfirming) return;
    const { call_id, tool } = pendingConfirmation;
    setIsConfirming(true);

    try {
      const resp = await fetch('http://127.0.0.1:8000/api/companion/confirm_tool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ call_id, approved }),
      });
      await resp.json();

      setPendingConfirmation(null);
      setIsConfirming(false);

      if (approved) {
        setMessages((prev) => [
          ...prev,
          {
            id: `user-conf-${Date.now()}`,
            role: 'user',
            content: `Approved: ${tool}`,
          },
          {
            id: `asst-conf-${Date.now()}`,
            role: 'assistant',
            content: `I've approved and executed the action for you! Your note has been created and saved.`,
          },
        ]);
        companionEvents.emit('TOOL_COMPLETED', `Action approved: ${tool}`);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `user-conf-${Date.now()}`,
            role: 'user',
            content: `Cancelled: ${tool}`,
          },
          {
            id: `asst-conf-${Date.now()}`,
            role: 'assistant',
            content: `Action cancelled. Nothing was modified.`,
          },
        ]);
      }
    } catch (err) {
      console.warn('Tool confirmation request failed:', err);
      setIsConfirming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleVoiceMute = (e: React.MouseEvent) => {
    e.stopPropagation();
    const nextMuted = voiceManager.toggleMute();
    setIsMuted(nextMuted);
  };

  const handleMicClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (voiceState === 'LISTENING') {
      await voiceManager.stopListening();
    } else if (voiceState === 'SPEAKING') {
      voiceManager.cancel();
    } else if (voiceState === 'IDLE' || voiceState === 'ERROR') {
      await voiceManager.startListening();
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 15, scale: 0.95 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className="meli-chat-panel"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="chat-header">
        <div className="chat-title">
          <div className={`chat-status-dot ${isStreaming ? 'thinking' : 'ready'}`} />
          <span className="meli-name">Meli</span>
          <span className="meli-tag">Companion</span>
          <span className="meli-voice-badge" title={`Current Voice: ${currentVoice}`}>
            {currentVoice.toUpperCase()}
          </span>

          {/* Active Tool Status Tag */}
          {activeToolAction && (
            <span className="tool-status-pill">
              <Wrench size={10} className="spin" /> {activeToolAction}
            </span>
          )}

          {/* Voice State Indicator Tag */}
          {voiceState === 'LISTENING' && (
            <span className="voice-status-pill listening">Listening</span>
          )}
          {voiceState === 'TRANSCRIBING' && (
            <span className="voice-status-pill transcribing">Processing</span>
          )}
          {voiceState === 'SPEAKING' && (
            <span className="voice-status-pill speaking">Speaking</span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {/* Quick Voice Selector Pills */}
          <div className="voice-selector-bar" title="Select Voice Preset">
            {(['autumn', 'diana', 'hannah'] as const).map((v) => (
              <button
                key={v}
                className={`voice-pill ${currentVoice === v ? 'active' : ''}`}
                onClick={() => {
                  voiceManager.setVoice(v);
                  setCurrentVoice(v);
                }}
                title={`Switch to ${v.charAt(0).toUpperCase() + v.slice(1)} voice`}
              >
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </button>
            ))}
          </div>

          {/* Mute Voice Toggle */}
          <button
            className="chat-audio-btn"
            onClick={toggleVoiceMute}
            title={isMuted ? 'Voice Muted (Click to Unmute)' : 'Voice Active (Click to Mute)'}
          >
            {isMuted ? <VolumeX size={12} color="#FF7AA2" /> : <Volume2 size={12} />}
          </button>

          <button className="chat-close-btn" onClick={onClose} title="Close Chat">
            <X size={13} />
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="chat-messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-bubble ${msg.role === 'user' ? 'user-bubble' : 'assistant-bubble'}`}
          >
            {msg.content || (isStreaming && msg.role === 'assistant' ? (
              <span className="streaming-dots">
                <span>.</span><span>.</span><span>.</span>
              </span>
            ) : null)}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Interactive Tool Confirmation Card */}
      {pendingConfirmation && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="tool-confirmation-card"
        >
          <div className="tool-confirmation-header">
            <ShieldAlert size={14} color="#FFAA00" />
            <span className="tool-confirmation-prompt">{pendingConfirmation.prompt}</span>
          </div>
          <div className="tool-confirmation-actions">
            <button
              className="confirm-btn approve"
              onClick={() => handleConfirmTool(true)}
              title="Approve and execute this action"
            >
              <Check size={11} /> Approve
            </button>
            <button
              className="confirm-btn cancel"
              onClick={() => handleConfirmTool(false)}
              title="Cancel this action"
            >
              <X size={11} /> Cancel
            </button>
          </div>
        </motion.div>
      )}

      {/* Suggested Quick Prompts */}
      {messages.length <= 2 && !isStreaming && voiceState === 'IDLE' && (
        <div className="quick-suggestions">
          <button
            className="suggestion-chip"
            onClick={() => handleSend('What can you help me with?')}
          >
            "What can you help me with?"
          </button>
          <button
            className="suggestion-chip"
            onClick={() => handleSend('Tell me about your memory.')}
          >
            "Tell me about your memory"
          </button>
        </div>
      )}

      {/* Input Area */}
      <div className="chat-input-row">
        {/* Push-to-Talk / Click-to-Talk Microphone Button */}
        <button
          className={`chat-mic-btn ${
            voiceState === 'LISTENING'
              ? 'listening'
              : voiceState === 'TRANSCRIBING'
              ? 'transcribing'
              : voiceState === 'SPEAKING'
              ? 'speaking'
              : voiceState === 'ERROR'
              ? 'error'
              : ''
          }`}
          onClick={handleMicClick}
          onMouseDown={() => {
            if (voiceState === 'IDLE') voiceManager.startListening();
          }}
          onMouseUp={() => {
            if (voiceState === 'LISTENING') voiceManager.stopListening();
          }}
          disabled={isStreaming || voiceState === 'TRANSCRIBING'}
          title={
            voiceState === 'LISTENING'
              ? 'Recording... (Click or Release to finish)'
              : voiceState === 'TRANSCRIBING'
              ? 'Transcribing speech...'
              : voiceState === 'SPEAKING'
              ? 'Meli is speaking (Click to interrupt)'
              : 'Voice Input: Push-to-Talk (Ctrl+Shift+V or Hold/Click)\nPrivacy: Microphone activates only when you explicitly start voice input.'
          }
        >
          {voiceState === 'LISTENING' ? (
            <Mic size={13} color="#FF4B6E" />
          ) : voiceState === 'TRANSCRIBING' ? (
            <Loader2 size={13} className="spin" color="#FFAA00" />
          ) : voiceState === 'SPEAKING' ? (
            <Volume2 size={13} color="#69F0AE" />
          ) : voiceState === 'ERROR' ? (
            <AlertCircle size={13} color="#FF5252" />
          ) : isMuted ? (
            <MicOff size={12} />
          ) : (
            <Mic size={12} />
          )}
        </button>

        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder={
            voiceState === 'LISTENING'
              ? 'Listening to you speak...'
              : voiceState === 'TRANSCRIBING'
              ? 'Transcribing audio...'
              : isStreaming
              ? 'Meli is thinking...'
              : 'Message Meli or press Ctrl+Shift+V...'
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming || voiceState === 'LISTENING' || voiceState === 'TRANSCRIBING'}
        />

        <button
          className={`chat-send-btn ${input.trim() ? 'active' : ''}`}
          onClick={() => handleSend()}
          disabled={!input.trim() || isStreaming || voiceState === 'LISTENING'}
          title="Send message"
        >
          <Send size={12} />
        </button>
      </div>
    </motion.div>
  );
};
