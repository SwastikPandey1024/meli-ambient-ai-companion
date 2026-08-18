# Meli Security & Safety Model

This document outlines the security architecture, tool execution policies, credential sanitization, and local-first boundaries of Meli.

---

## 1. Tool Permission Levels & Policy Engine

Meli enforces a three-tier permission model managed by `ToolPolicyEngine`:

```
┌─────────────────────────────────────────────────────────────┐
│                    Tool Execution Policy                    │
├──────────────────────┬──────────────────────────────────────┤
│ Permission Level     │ Behavior & Security Boundary         │
├──────────────────────┼──────────────────────────────────────┤
│ AUTO_APPROVED        │ Safe read-only operations executed   │
│                      │ automatically and logged to audit.   │
├──────────────────────┼──────────────────────────────────────┤
│ CONFIRMATION_REQUIRED│ Operations with external side-effects│
│                      │ require interactive user approval.   │
├──────────────────────┼──────────────────────────────────────┤
│ BLOCKED              │ Unsafe commands (arbitrary shell,    │
│                      │ system eval) immediately rejected.   │
└──────────────────────┴──────────────────────────────────────┘
```

### Supported Tool Classifications

- **`AUTO_APPROVED`**:
  - `get_time`: Queries system local time safely.
  - `search_knowledge`: Read-only Elasticsearch BM25 document search.
  - `open_url`: Validates scheme (`http`/`https` only) before launching system default browser.
- **`CONFIRMATION_REQUIRED`**:
  - `create_note`: Creates persistent local notes in PostgreSQL repository.
  - `save_memory`: Persists personal facts into long-term memory.
- **`BLOCKED`**:
  - `execute_shell`, `eval`, `system`, `subprocess`, direct disk deletion.

---

## 2. Audit Trail & Credential Sanitization

All tool requests, execution timestamps, parameters, and results are recorded in the PostgreSQL `audit_events` repository.

Before persistence and display:
- **API Keys & Tokens**: Redacted using regex pattern matching (`Bearer ***`, `gsk_***`).
- **Personal Credentials**: Stripped from client-side error streams.
- **Strict URL Scheme Validation**: Schemes like `file://`, `javascript:`, `data:`, or `ftp://` are rejected by `open_url`.

---

## 3. Local-First & Network Boundaries

- **Database**: Runs locally or within user-managed virtual private clouds (PostgreSQL + Elasticsearch).
- **Audio Captures**: Microphone audio recorded via Push-to-Talk is stored in temporary in-memory buffers and cleared immediately post-transcription.
- **Tauri IPC**: All desktop commands (`set_window_size`, `start_drag`, `save_window_state`) are strictly typed and constrained to the local application scope.
