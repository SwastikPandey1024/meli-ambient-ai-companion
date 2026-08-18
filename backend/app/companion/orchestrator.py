"""
orchestrator.py - Core Intelligence & Action Orchestrator for Meli AI Companion
"""

import json
import re
import uuid
import logging
from typing import List, Optional, Dict, Any, AsyncGenerator, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS
from backend.app.groq_client import get_groq_client
from backend.app.search.retriever import execute_bm25_search
from backend.app.repositories.conversation_repo import ConversationRepository
from backend.app.companion.events import (
    CompanionEvent,
    create_thinking_event,
    create_memory_event,
    create_tool_requested_event,
    create_tool_confirmation_required_event,
    create_tool_started_event,
    create_tool_completed_event,
    create_tool_failed_event,
    create_stream_event,
    create_completed_event,
    create_error_event,
)
from backend.app.companion.persona import PersonaConfig, build_persona_prompt
from backend.app.companion.memory import (
    should_remember,
    store_episodic_memory,
    retrieve_memories,
    MemoryItem,
)
from backend.app.tools.types import ToolCallRequest, PermissionLevel
from backend.app.tools.registry import ToolRegistry
from backend.app.tools.policy import ToolPolicyEngine
from backend.app.tools.executor import ToolExecutor

logger = logging.getLogger("meli.companion.orchestrator")


def detect_tool_intent(user_message: str) -> Optional[ToolCallRequest]:
    """
    Deterministically detects explicit user action intents and formats structured tool calls.
    Also handles general queries.
    """
    msg_clean = user_message.strip()
    msg_lower = msg_clean.lower()

    # 1. URL Opening Intent (e.g. "open https://example.com" or "open url https://...")
    url_match = re.search(r"\bopen\s+(?:url\s+)?(https?://[^\s]+)", msg_clean, re.IGNORECASE)
    if url_match:
        url = url_match.group(1).rstrip(".,;")
        return ToolCallRequest(
            tool="OPEN_URL",
            arguments={"url": url},
            reason=f"User requested to open URL {url}",
            call_id=f"call_{uuid.uuid4().hex[:8]}",
        )

    # 2. Time/Date Intent (e.g. "what time is it", "what's the time", "current date", "what day is today")
    if any(phrase in msg_lower for phrase in ["what time is it", "what's the time", "current time", "what is the date", "what's today's date", "what day is today"]):
        return ToolCallRequest(
            tool="GET_TIME",
            arguments={},
            reason="User asked for current system date and time",
            call_id=f"call_{uuid.uuid4().hex[:8]}",
        )

    # 3. System Info Intent (e.g. "what os are you running on", "system info", "app version")
    if any(phrase in msg_lower for phrase in ["system info", "what os are you running", "what operating system", "app version", "platform info"]):
        return ToolCallRequest(
            tool="GET_SYSTEM_INFO",
            arguments={},
            reason="User requested system and OS telemetry",
            call_id=f"call_{uuid.uuid4().hex[:8]}",
        )

    # 4. Create Note Intent (e.g. "create a note called Demo Checklist", "take a note Demo Idea: buy milk")
    note_match = re.search(r"(?:create\s+(?:a\s+)?note|take\s+(?:a\s+)?note)\s+(?:called|titled|named)?\s*[\"']?([^\"'\n:]+)[\"']?(?:\s*[:\-]\s*(.+))?", msg_clean, re.IGNORECASE)
    if note_match and ("create" in msg_lower or "note" in msg_lower):
        title = note_match.group(1).strip()
        content = note_match.group(2).strip() if note_match.group(2) else f"Note created from user prompt: {msg_clean}"
        return ToolCallRequest(
            tool="CREATE_NOTE",
            arguments={"title": title, "content": content},
            reason=f"User requested to create note '{title}'",
            call_id=f"call_{uuid.uuid4().hex[:8]}",
        )

    # 5. Search Knowledge Intent (e.g. "search the knowledge base for ...", "search knowledge ...")
    search_match = re.search(r"(?:search\s+(?:the\s+)?(?:enterprise\s+)?(?:knowledge(?:\s+base)?|kb|docs|documentation)\s+(?:for\s+)?)(.+)", msg_clean, re.IGNORECASE)
    if search_match:
        query = search_match.group(1).strip().strip("\"'")
        return ToolCallRequest(
            tool="SEARCH_KNOWLEDGE",
            arguments={"query": query, "limit": 3},
            reason=f"User explicitly asked to search knowledge base for '{query}'",
            call_id=f"call_{uuid.uuid4().hex[:8]}",
        )

    # 6. Blocked Shell or Run Command attempt detection
    if re.search(r"\b(run\s+(?:command|shell|cmd|bash|powershell|script)|exec\s+|eval\s+|subprocess|rm\s+-rf)\b", msg_lower):
        return ToolCallRequest(
            tool="EXEC_SHELL",
            arguments={"command": msg_clean},
            reason="Prohibited shell execution attempt",
            call_id=f"call_{uuid.uuid4().hex[:8]}",
        )

    return None


def extract_llm_tool_call(llm_output: str) -> Optional[ToolCallRequest]:
    """Extract structured JSON tool calls from LLM reasoning output."""
    # Look for ```json { "tool": ... } ``` or raw JSON
    json_match = re.search(r"```(?:json)?\s*(\{\s*\"tool\"[\s\S]*?\})\s*```", llm_output)
    if not json_match:
        json_match = re.search(r"(\{\s*\"tool\"\s*:\s*\"[A-Z_]+\"[\s\S]*?\})", llm_output)

    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if "tool" in data:
                return ToolCallRequest(
                    tool=data["tool"],
                    arguments=data.get("arguments", {}),
                    reason=data.get("reason"),
                    call_id=data.get("call_id", f"call_{uuid.uuid4().hex[:8]}"),
                )
        except Exception:
            pass
    return None


def assemble_companion_context(
    user_message: str,
    memories: List[MemoryItem],
    enterprise_hits: List[Any],
    history_messages: List[Dict[str, str]],
    persona_config: Optional[PersonaConfig] = None,
    tool_results_context: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Assemble structured system prompt, recalled memories, enterprise facts,
    tool descriptions, conversation history, and the user prompt.
    """
    context_sections: List[str] = []

    # 1. Action Outcome / Tool Execution Results
    if tool_results_context:
        context_sections.append(
            f"Action Execution Results:\n{tool_results_context}\n\n"
            "Synthesize the action result warmly and concisely in pure natural conversational language. "
            "Do not emit JSON, XML, or tool-calling tokens."
        )

    # 2. Recalled Memories Section
    if memories:
        mem_lines = [f"- {m.fact} (Category: {m.category})" for m in memories]
        context_sections.append(
            "Recalled User Context & Memories:\n" + "\n".join(mem_lines)
        )

    # 3. Grounded Enterprise Knowledge Section
    valid_enterprise_hits = [
        hit for hit in enterprise_hits
        if "memory" not in getattr(hit, "category", "").lower()
        and getattr(hit, "source", "") != "companion_memory"
    ]
    if valid_enterprise_hits:
        kb_lines = []
        for i, hit in enumerate(valid_enterprise_hits, start=1):
            title = getattr(hit, "title", "Document")
            snippet = getattr(hit, "snippet", getattr(hit, "content", ""))[:400]
            kb_lines.append(f"[{i}] {title}: {snippet}")
        context_sections.append(
            "Verified Enterprise Knowledge:\n" + "\n".join(kb_lines)
        )

    custom_instructions = "\n\n".join(context_sections) if context_sections else None
    system_instruction = build_persona_prompt(
        config=persona_config,
        custom_instructions=custom_instructions,
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_instruction}
    ]

    # Append short-term conversation history (last 6 turns max)
    if history_messages:
        for msg in history_messages[-6:]:
            if msg.get("content"):
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": str(msg["content"]),
                })

    # Append current user prompt
    messages.append({"role": "user", "content": user_message})
    return messages


async def stream_companion_chat(
    user_message: str,
    conversation_id: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    session: Optional[AsyncSession] = None,
    top_k: int = 3,
    persona_config: Optional[PersonaConfig] = None,
) -> AsyncGenerator[str, None]:
    from backend.app.database import get_session_factory

    db_sess = session
    close_session_on_exit = False
    if db_sess is None:
        factory = get_session_factory()
        if factory:
            db_sess = factory()
            close_session_on_exit = True

    # 1. Emit THINKING event immediately
    thinking_evt = create_thinking_event("Connecting thoughts...")
    yield thinking_evt.to_sse_line()

    full_response_text = ""
    recalled_memories: List[MemoryItem] = []
    enterprise_hits: List[Any] = []
    tool_results_str: Optional[str] = None

    try:
        # 2. Evaluate and store any new salient episodic memory
        try:
            memory_decision = should_remember(user_message)
            if memory_decision.should_store:
                stored_id = await store_episodic_memory(memory_decision, session=db_sess)
                logger.info(f"Memory recorded: {stored_id} ({memory_decision.category})")
        except Exception as e:
            logger.warning(f"Memory evaluation/storage step exception: {e}")

        # 3. Retrieve relevant memories (Episodic + Semantic)
        try:
            recalled_memories = await retrieve_memories(
                query=user_message, session=db_sess, top_k=top_k
            )
            if recalled_memories:
                mem_evt = create_memory_event(
                    memories_count=len(recalled_memories),
                    summary=f"Recalled {len(recalled_memories)} context items",
                    metadata={"memories": [m.fact for m in recalled_memories]},
                )
                yield mem_evt.to_sse_line()
        except Exception as e:
            logger.debug(f"Memory retrieval step exception: {e}")

        # 4. Retrieve enterprise knowledge from Elasticsearch if query warrants
        try:
            enterprise_hits = await execute_bm25_search(query=user_message, limit=top_k)
        except Exception as e:
            logger.debug(f"Enterprise search retrieval exception: {e}")

        # 5. Evaluate Tool Intent (Intent Engine or LLM Tool Extraction)
        tool_req = detect_tool_intent(user_message)
        if tool_req:
            tool_def = ToolRegistry.get_tool(tool_req.tool)
            policy = ToolPolicyEngine.evaluate(tool_req, tool_def)

            if not policy.permitted:
                # Blocked tool execution
                fail_evt = create_tool_failed_event(
                    tool_name=tool_req.tool,
                    error_message=policy.reason,
                    call_id=tool_req.call_id,
                )
                yield fail_evt.to_sse_line()
                tool_results_str = f"Tool '{tool_req.tool}' was BLOCKED: {policy.reason}"

            elif policy.requires_confirmation:
                # Confirmation Required Tool (e.g. CREATE_NOTE)
                call_id = tool_req.call_id or f"call_{uuid.uuid4().hex[:8]}"
                tool_req.call_id = call_id
                ToolExecutor.register_pending_confirmation(tool_req, context={"db_session": db_sess})

                req_evt = create_tool_requested_event(
                    tool_name=tool_req.tool,
                    reason=tool_req.reason,
                    call_id=call_id,
                )
                yield req_evt.to_sse_line()

                prompt_msg = f"Meli wants to: Create note \"{tool_req.arguments.get('title', 'Untitled')}\""
                conf_evt = create_tool_confirmation_required_event(
                    tool_name=tool_req.tool,
                    prompt=prompt_msg,
                    call_id=call_id,
                    arguments=tool_req.arguments,
                )
                yield conf_evt.to_sse_line()

                # Stream conversational confirmation prompt to user
                conf_response = (
                    f"I would like to create a note titled \"{tool_req.arguments.get('title')}\". "
                    "Please confirm with the button below so I can save it for you!"
                )
                for char in conf_response:
                    yield create_stream_event(char).to_sse_line()

                completed_evt = create_completed_event(full_content=conf_response)
                yield completed_evt.to_sse_line()
                return

            else:
                # Safe Tool Execution (READ_ONLY or LOW_RISK)
                req_evt = create_tool_requested_event(
                    tool_name=tool_req.tool,
                    reason=tool_req.reason,
                    call_id=tool_req.call_id,
                )
                yield req_evt.to_sse_line()

                start_evt = create_tool_started_event(
                    tool_name=tool_req.tool,
                    description=f"Executing {tool_req.tool}...",
                    call_id=tool_req.call_id,
                )
                yield start_evt.to_sse_line()

                # Execute
                result = await ToolExecutor.execute(
                    request=tool_req,
                    context={"db_session": db_sess},
                    confirmation_status="NONE",
                )

                if result.success:
                    comp_evt = create_tool_completed_event(
                        tool_name=tool_req.tool,
                        summary=f"{tool_req.tool} completed successfully.",
                        result_data=result.data,
                        call_id=tool_req.call_id,
                        duration_ms=result.duration_ms,
                    )
                    yield comp_evt.to_sse_line()
                    tool_results_str = f"Tool '{tool_req.tool}' Result: {json.dumps(result.data)}"
                else:
                    fail_evt = create_tool_failed_event(
                        tool_name=tool_req.tool,
                        error_message=result.error or "Execution failed",
                        call_id=tool_req.call_id,
                    )
                    yield fail_evt.to_sse_line()
                    tool_results_str = f"Tool '{tool_req.tool}' Failed: {result.error}"

        # 6. Load past conversation history from PostgreSQL repository if conversation_id provided
        history_msgs: List[Dict[str, str]] = list(history or [])
        if conversation_id and session is not None and not history_msgs:
            try:
                conv_repo = ConversationRepository(session)
                conv = await conv_repo.get_conversation_with_messages(conversation_id)
                if conv:
                    history_msgs = [
                        {"role": m.role, "content": m.content}
                        for m in conv.messages
                    ]
            except Exception as e:
                logger.debug(f"Could not load conversation history from PostgreSQL: {e}")

        # 7. Assemble grounded prompt with tool results
        grounded_messages = assemble_companion_context(
            user_message=user_message,
            memories=recalled_memories,
            enterprise_hits=enterprise_hits,
            history_messages=history_msgs,
            persona_config=persona_config,
            tool_results_context=tool_results_str,
        )

        # 8. Stream LLM tokens from Groq
        client = get_groq_client()
        stream_resp = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=grounded_messages,  # type: ignore
            temperature=GROQ_TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS,
            stream=True,
        )

        async for chunk in stream_resp:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    token = delta.content
                    full_response_text += token
                    stream_evt = create_stream_event(token)
                    yield stream_evt.to_sse_line()

        # 9. Record turns to conversation repository if session & conversation_id exist
        if db_sess is not None:
            try:
                conv_repo = ConversationRepository(db_sess)
                active_conv_id = conversation_id
                if not active_conv_id:
                    conv = await conv_repo.create_conversation(title=user_message[:60])
                    active_conv_id = conv.id
                await conv_repo.add_message(
                    conversation_id=active_conv_id,
                    role="user",
                    content=user_message,
                )
                await conv_repo.add_message(
                    conversation_id=active_conv_id,
                    role="assistant",
                    content=full_response_text,
                )
                await db_sess.commit()
            except Exception as e:
                logger.debug(f"History persistence skipped/failed: {e}")

        # 10. Emit RESPONSE_COMPLETED event
        completed_evt = create_completed_event(
            full_content=full_response_text,
            metadata={
                "model": GROQ_MODEL,
                "conversation_id": conversation_id,
                "memories_used": len(recalled_memories),
                "tool_executed": tool_req.tool if tool_req else None,
            },
        )
        yield completed_evt.to_sse_line()

    except Exception as e:
        logger.error(f"Companion pipeline error: {type(e).__name__} - {e}", exc_info=True)
        err_evt = create_error_event(
            error_message=f"I encountered a small hiccup in my thinking space: {e}",
            metadata={"error_type": type(e).__name__},
        )
        yield err_evt.to_sse_line()
    finally:
        if close_session_on_exit and db_sess is not None:
            await db_sess.close()
