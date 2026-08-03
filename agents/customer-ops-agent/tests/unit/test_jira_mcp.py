"""Unit tests for the disabled-by-default Jira MCP integration."""

from unittest.mock import patch

import pytest

from app.jira_mcp import (
    DEFAULT_ATLASSIAN_MCP_URL,
    JIRA_READ_TOOLS,
    JIRA_WRITE_TOOLS,
    _authorization_headers,
    create_jira_read_toolset,
    create_jira_write_toolset,
)


def test_jira_toolsets_are_disabled_by_default(monkeypatch):
    """Do not expose Jira tools without explicit feature flags."""
    monkeypatch.delenv("ATLASSIAN_MCP_ENABLED", raising=False)
    monkeypatch.delenv("ATLASSIAN_MCP_WRITE_ENABLED", raising=False)

    assert create_jira_read_toolset() is None
    assert create_jira_write_toolset() is None


def test_jira_read_toolset_uses_allowlist(monkeypatch):
    """Expose only approved read tools when Jira MCP is enabled."""
    monkeypatch.setenv("ATLASSIAN_MCP_ENABLED", "true")

    with (
        patch(
            "app.jira_mcp.StreamableHTTPConnectionParams"
        ) as connection_constructor,
        patch("app.jira_mcp.McpToolset") as toolset_constructor,
    ):
        result = create_jira_read_toolset()

    connection_constructor.assert_called_once_with(
        url=DEFAULT_ATLASSIAN_MCP_URL,
        timeout=30.0,
        sse_read_timeout=300.0,
    )
    toolset_constructor.assert_called_once_with(
        connection_params=connection_constructor.return_value,
        tool_filter=JIRA_READ_TOOLS,
        tool_name_prefix="jira_",
        header_provider=_authorization_headers,
    )
    assert result is toolset_constructor.return_value


def test_jira_writes_require_second_feature_flag(monkeypatch):
    """Keep write tools absent when only read access is enabled."""
    monkeypatch.setenv("ATLASSIAN_MCP_ENABLED", "true")
    monkeypatch.setenv("ATLASSIAN_MCP_WRITE_ENABLED", "false")

    assert create_jira_write_toolset() is None


def test_jira_writes_always_require_human_confirmation(monkeypatch):
    """Require ADK confirmation for every enabled Jira write tool."""
    monkeypatch.setenv("ATLASSIAN_MCP_ENABLED", "true")
    monkeypatch.setenv("ATLASSIAN_MCP_WRITE_ENABLED", "true")

    with (
        patch(
            "app.jira_mcp.StreamableHTTPConnectionParams"
        ) as connection_constructor,
        patch("app.jira_mcp.McpToolset") as toolset_constructor,
    ):
        result = create_jira_write_toolset()

    toolset_constructor.assert_called_once_with(
        connection_params=connection_constructor.return_value,
        tool_filter=JIRA_WRITE_TOOLS,
        tool_name_prefix="jira_",
        header_provider=_authorization_headers,
        require_confirmation=True,
    )
    assert result is toolset_constructor.return_value


def test_missing_access_token_fails_closed(monkeypatch):
    """Reject enabled calls when no Atlassian token is available."""
    monkeypatch.delenv("ATLASSIAN_MCP_ACCESS_TOKEN", raising=False)

    with pytest.raises(
        RuntimeError,
        match="ATLASSIAN_MCP_ACCESS_TOKEN is required",
    ):
        _authorization_headers(None)
