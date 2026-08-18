# Business Requirements Document (BRD) — Meli 💖

- **Project**: Meli — Ambient AI Desktop Companion
- **Version**: 1.0.0
- **Classification**: Strategic Engineering & Enterprise Enablement Baseline

---

## 1. Project Background & Opportunity

Modern AI assistants are predominantly confined to browser tabs or standalone chat clients, creating high context-switching overhead and disjointed user engagement.

**Meli** addresses this market gap by delivering an always-accessible, native desktop companion that blends ambient anime aesthetics with enterprise-grade knowledge grounding and secure system automation.

---

## 2. Business Objectives & Value Drivers

1. **Context-Switching Reduction**: Allow users to query knowledge and record notes directly from their current workspace without switching windows.
2. **Enterprise Data Grounding**: Enable employees to query internal documentation securely with cited BM25 Elasticsearch retrieval.
3. **Safe Desktop Automation**: Provide a trustworthy AI agent with transparent human-in-the-loop confirmation for any sensitive or state-altering actions.
4. **Enhanced User Engagement**: Drive sustained daily active engagement through multi-sensory feedback (character state transitions, vocal personality, and tactile physics).

---

## 3. Scope of the System

### In-Scope (v1.0.0)
- Desktop native transparent application running on Windows 10/11.
- Full local and remote conversation and memory persistence with PostgreSQL.
- Hybrid BM25 enterprise document search with Elasticsearch.
- Push-to-talk speech synthesis and recognition.
- Auditable tool execution with interactive user approval.
- 16 canonical visual performance states.

### Out-of-Scope (Future Releases)
- Direct screen capture / visual OCR processing (reserved for future multimodal adapter phase).
- Multi-user real-time collaborative avatars.
- Mobile (iOS/Android) companion builds.

---

## 4. Key Performance Indicators (KPIs)

| Business KPI | Target Metric |
| :--- | :--- |
| **Response Latency** | Time-to-first-token < 800ms for streaming responses. |
| **Voice Interaction Success** | STT accuracy > 95% on conversational English. |
| **Security Compliance** | 0 unconfirmed file writes or shell command executions. |
| **Crash-Free Sessions** | > 99.8% stability on desktop sessions. |
