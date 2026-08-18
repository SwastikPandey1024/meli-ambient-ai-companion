"""
groq_client.py - Groq API Client Integration & Streaming Service
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from groq import Groq, AsyncGroq
from backend.app.config import GROQ_API_KEY, GROQ_MODEL, MELI_SYSTEM_PROMPT

logger = logging.getLogger("meli.groq")


def get_async_groq_client(api_key: Optional[str] = None) -> Optional[AsyncGroq]:
    """Factory to instantiate AsyncGroq client safely."""
    key = api_key if api_key is not None else GROQ_API_KEY
    if not key:
        return None
    try:
        return AsyncGroq(api_key=key)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None


get_groq_client = get_async_groq_client


def format_messages(user_message: str, history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    """Format full prompt with Meli persona and conversation context."""
    messages = [{"role": "system", "content": MELI_SYSTEM_PROMPT}]
    if history:
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    return messages


async def stream_groq_chat(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    client: Optional[AsyncGroq] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream token-by-token response from Groq as Server-Sent Events (SSE).
    """
    groq_model = model or GROQ_MODEL
    groq_client = client or get_async_groq_client()

    if not groq_client:
        fallback_msg = "I'm having a little trouble reaching my thinking space right now. Give me a moment and try again."
        yield f"data: {json.dumps({'token': fallback_msg, 'state': 'ERROR'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    messages = format_messages(user_message, history)

    try:
        stream = await groq_client.chat.completions.create(
            model=groq_model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                token = delta.content or ""
                if token:
                    payload = {
                        "token": token,
                        "state": "THINKING",
                        "model": groq_model,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

        yield f"data: {json.dumps({'state': 'COMPLETE'})}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Groq API streaming exception: {type(e).__name__}")
        fallback_msg = "I'm having a little trouble reaching my thinking space right now. Give me a moment and try again."
        yield f"data: {json.dumps({'token': fallback_msg, 'state': 'ERROR'})}\n\n"
        yield "data: [DONE]\n\n"


async def generate_groq_chat(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    client: Optional[AsyncGroq] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Non-streaming single-shot chat completion.
    """
    groq_model = model or GROQ_MODEL
    groq_client = client or get_async_groq_client()

    if not groq_client:
        return {
            "reply": "I'm having a little trouble reaching my thinking space right now. Give me a moment and try again.",
            "state": "ERROR",
            "model": groq_model,
            "usage": None,
        }

    messages = format_messages(user_message, history)

    try:
        completion = await groq_client.chat.completions.create(
            model=groq_model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=False,
        )

        reply_text = completion.choices[0].message.content or ""
        usage_info = {
            "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
            "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
            "total_tokens": completion.usage.total_tokens if completion.usage else 0,
        } if completion.usage else None

        return {
            "reply": reply_text,
            "state": "COMPLETE",
            "model": groq_model,
            "usage": usage_info,
        }

    except Exception as e:
        logger.error(f"Groq API request exception: {type(e).__name__}")
        return {
            "reply": "I'm having a little trouble reaching my thinking space right now. Give me a moment and try again.",
            "state": "ERROR",
            "model": groq_model,
            "usage": None,
        }
