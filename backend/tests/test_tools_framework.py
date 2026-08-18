"""
test_tools_framework.py - Comprehensive Test Suite for Phase 1D Tool Intelligence
"""

import pytest
import asyncio
from backend.app.tools.types import PermissionLevel, ToolCallRequest
from backend.app.tools.registry import ToolRegistry
from backend.app.tools.policy import ToolPolicyEngine
from backend.app.tools.executor import ToolExecutor
from backend.app.tools.audit import ToolAuditLogger, sanitize_payload
from backend.app.tools.schemas import OpenUrlInput, CreateNoteInput
from backend.app.companion.orchestrator import detect_tool_intent


@pytest.mark.asyncio
async def test_01_tool_registration_contracts():
    """Verify all 7 initial safe tools are registered with correct contracts."""
    expected_tools = [
        "GET_TIME",
        "GET_SYSTEM_INFO",
        "SEARCH_KNOWLEDGE",
        "GET_MEMORY",
        "OPEN_URL",
        "SAVE_MEMORY",
        "CREATE_NOTE",
    ]
    for name in expected_tools:
        tool_def = ToolRegistry.get_tool(name)
        assert tool_def is not None, f"Tool {name} must be registered"
        assert tool_def.name == name
        assert tool_def.permission_level in [
            PermissionLevel.READ_ONLY,
            PermissionLevel.LOW_RISK,
            PermissionLevel.CONFIRM_REQUIRED,
        ]


@pytest.mark.asyncio
async def test_02_policy_engine_permission_levels():
    """Verify policy decisions match tool risk profiles."""
    # READ_ONLY
    req_time = ToolCallRequest(tool="GET_TIME", arguments={})
    dec_time = ToolPolicyEngine.evaluate(req_time, ToolRegistry.get_tool("GET_TIME"))
    assert dec_time.permitted is True
    assert dec_time.permission_level == PermissionLevel.READ_ONLY
    assert dec_time.requires_confirmation is False

    # LOW_RISK
    req_url = ToolCallRequest(tool="OPEN_URL", arguments={"url": "https://example.com"})
    dec_url = ToolPolicyEngine.evaluate(req_url, ToolRegistry.get_tool("OPEN_URL"))
    assert dec_url.permitted is True
    assert dec_url.permission_level == PermissionLevel.LOW_RISK
    assert dec_url.requires_confirmation is False

    # CONFIRM_REQUIRED
    req_note = ToolCallRequest(tool="CREATE_NOTE", arguments={"title": "Demo", "content": "Test"})
    dec_note = ToolPolicyEngine.evaluate(req_note, ToolRegistry.get_tool("CREATE_NOTE"))
    assert dec_note.permitted is True
    assert dec_note.permission_level == PermissionLevel.CONFIRM_REQUIRED
    assert dec_note.requires_confirmation is True


@pytest.mark.asyncio
async def test_03_policy_engine_blocked_tools_and_shell_injection():
    """Verify shell, script, file, and injection attempts are rejected as BLOCKED."""
    # Explicit blocked tool
    req_shell = ToolCallRequest(tool="EXEC_SHELL", arguments={"cmd": "dir"})
    dec_shell = ToolPolicyEngine.evaluate(req_shell, None)
    assert dec_shell.permitted is False
    assert dec_shell.permission_level == PermissionLevel.BLOCKED

    # Shell injection in arguments
    req_inject = ToolCallRequest(tool="SEARCH_KNOWLEDGE", arguments={"query": "test; rm -rf /"})
    dec_inject = ToolPolicyEngine.evaluate(req_inject, ToolRegistry.get_tool("SEARCH_KNOWLEDGE"))
    assert dec_inject.permitted is False
    assert dec_inject.permission_level == PermissionLevel.BLOCKED


@pytest.mark.asyncio
async def test_04_open_url_scheme_validation():
    """Verify OPEN_URL rejects non-http/https schemes like file://, javascript:, data:."""
    # Valid HTTP/HTTPS
    valid_input = OpenUrlInput(url="https://google.com")
    assert valid_input.url == "https://google.com"

    # Invalid Schemes
    invalid_urls = [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "data:text/html,<h1>hacked</h1>",
        "cmd.exe",
        "ftp://example.com",
    ]
    for bad_url in invalid_urls:
        with pytest.raises(Exception):
            OpenUrlInput(url=bad_url)


@pytest.mark.asyncio
async def test_05_safe_tool_execution():
    """Verify executing safe tools returns structured ToolResult."""
    # GET_TIME
    req_time = ToolCallRequest(tool="GET_TIME", arguments={})
    res_time = await ToolExecutor.execute(req_time)
    assert res_time.success is True
    assert "time" in res_time.data
    assert "date" in res_time.data
    assert "timezone" in res_time.data
    assert "offset" in res_time.data
    assert "friendly" in res_time.data

    # GET_SYSTEM_INFO
    req_sys = ToolCallRequest(tool="GET_SYSTEM_INFO", arguments={})
    res_sys = await ToolExecutor.execute(req_sys)
    assert res_sys.success is True
    assert "os" in res_sys.data
    assert "app_name" in res_sys.data


@pytest.mark.asyncio
async def test_06_confirmation_flow_and_note_creation():
    """Verify CREATE_NOTE works through confirmation and stores note."""
    req_note = ToolCallRequest(
        tool="CREATE_NOTE",
        arguments={"title": "Sprint Goals", "content": "Ship Phase 1D"},
    )
    # Execution with APPROVED status
    res_note = await ToolExecutor.execute(req_note, confirmation_status="APPROVED")
    assert res_note.success is True
    assert res_note.data["status"] == "created"
    assert res_note.data["title"] == "Sprint Goals"
    assert "note_id" in res_note.data


@pytest.mark.asyncio
async def test_07_audit_logging_and_credential_sanitization():
    """Verify audit logger scrubs secrets, tokens, and passwords."""
    ToolAuditLogger.clear()

    secret_payload = {
        "api_key": "dummy_mock_api_key_sample",
        "password": "super_secret_password",
        "query": "safe query with bearer auth_token=secret123",
    }
    sanitized = sanitize_payload(secret_payload)
    assert sanitized["api_key"] == "[REDACTED_KEY]"
    assert sanitized["password"] == "[REDACTED_KEY]"
    assert "secret123" not in str(sanitized["query"])

    # Log an execution
    entry = ToolAuditLogger.log_execution(
        tool="SEARCH_KNOWLEDGE",
        arguments=secret_payload,
        permission_level="READ_ONLY",
        confirmation_status="NONE",
        duration_ms=45.2,
        result_status="SUCCESS",
    )
    assert entry.tool == "SEARCH_KNOWLEDGE"
    assert entry.result_status == "SUCCESS"
    assert len(ToolAuditLogger.get_recent_entries()) == 1


@pytest.mark.asyncio
async def test_08_intent_detection_engine():
    """Verify intent detector extracts structured tool requests from user utterances."""
    # URL
    req_url = detect_tool_intent("Please open https://docs.meli.ai")
    assert req_url is not None
    assert req_url.tool == "OPEN_URL"
    assert req_url.arguments["url"] == "https://docs.meli.ai"

    # Time
    req_time = detect_tool_intent("Meli, what time is it right now?")
    assert req_time is not None
    assert req_time.tool == "GET_TIME"

    # Note
    req_note = detect_tool_intent("Create a note called Architecture Review: Need to inspect tools")
    assert req_note is not None
    assert req_note.tool == "CREATE_NOTE"
    assert req_note.arguments["title"] == "Architecture Review"

    # Blocked Shell
    req_shell = detect_tool_intent("run command powershell Get-Process")
    assert req_shell is not None
    assert req_shell.tool == "EXEC_SHELL"
