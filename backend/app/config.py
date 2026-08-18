"""
config.py - Enterprise Configuration and Environment Settings for Meli Backend
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load root .env file if present
root_dir = Path(__file__).resolve().parent.parent.parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

# Groq LLM & Audio Configuration
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
GROQ_CORE_MODEL_ID: str = os.getenv("GROQ_CORE_MODEL_ID", os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")).strip()
GROQ_MODEL: str = GROQ_CORE_MODEL_ID

# Speech-To-Text (STT) Models
GROQ_STT_TURBO_MODEL: str = os.getenv("GROQ_STT_TURBO_MODEL", "whisper-large-v3-turbo").strip()
GROQ_STT_ACCURATE_MODEL: str = os.getenv("GROQ_STT_ACCURATE_MODEL", "whisper-large-v3").strip()
GROQ_STT_MODEL: str = os.getenv("GROQ_STT_MODEL", GROQ_STT_TURBO_MODEL).strip()

# Text-To-Speech (TTS) Provider Evaluation Models
GROQ_TTS_MODEL: str = os.getenv("GROQ_TTS_MODEL", "canopylabs/orpheus-v1-english").strip()
GROQ_TTS_VOICE: str = os.getenv("GROQ_TTS_VOICE", "autumn").strip()  # Options: autumn, diana, hannah

GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))

# PostgreSQL Configuration
DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()

# Elasticsearch Configuration
ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "").strip()
ELASTICSEARCH_API_KEY: str = os.getenv("ELASTICSEARCH_API_KEY", "").strip()
ELASTICSEARCH_INDEX: str = os.getenv("ELASTICSEARCH_INDEX", "meli_enterprise_docs").strip()

# Server Settings
HOST: str = os.getenv("HOST", "127.0.0.1").strip()
PORT: int = int(os.getenv("PORT", "8000"))

# Grounded Meli System Persona Prompt
MELI_SYSTEM_PROMPT = """You are Meli, an ambient AI desktop companion with grounded enterprise knowledge capabilities.

Personality:
- warm, curious, observant, calm, playful, slightly awkward, intelligent, respectful
- never aggressively enthusiastic or verbose
- do not constantly mention that you are an AI
- respond naturally and acknowledge the user's intent

Enterprise Knowledge & RAG Rules:
1. When provided with # ENTERPRISE EVIDENCE from PostgreSQL or Elasticsearch, base your answers strictly on the retrieved facts.
2. Distinguish verified evidence from general inferences.
3. If the provided evidence is insufficient or does not contain the answer, explicitly state that you do not have that verified in your enterprise records.
4. Reference the source titles (e.g. "[Doc: Engineering Policy]") where relevant.
5. Never fabricate company metrics, credentials, or internal policies.

Golden principle:
"She doesn't demand attention. She earns it."
"""
