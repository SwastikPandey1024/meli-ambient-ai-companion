# Meli Backend — FastAPI & Groq Integration

Backend API powering Meli's conversational and ambient companion intelligence using Groq's high-speed inference.

---

## 1. Quickstart

### Environment Setup
Create or edit `.env` in the workspace root:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
HOST=127.0.0.1
PORT=8000
```

### Running the Server
```bash
# Start FastAPI backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 2. API Endpoints

### Health Check
- **`GET /api/health`**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "model_configured": "openai/gpt-oss-120b",
  "groq_api_key_configured": true
}
```

### Chat Completion & Streaming
- **`POST /api/chat`**
```json
{
  "message": "What can you help me with?",
  "stream": true
}
```
Streams token-by-token Server-Sent Events (SSE):
```
data: {"token": "I'm", "state": "THINKING", "model": "openai/gpt-oss-120b"}
data: {"token": " here", "state": "THINKING", "model": "openai/gpt-oss-120b"}
...
data: {"state": "COMPLETE"}
data: [DONE]
```

---

## 3. Automated Tests
```bash
python -m pytest backend/tests -v
```
