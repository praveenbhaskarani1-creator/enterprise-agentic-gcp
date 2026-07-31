"""Unit tests for MCP Toolbox configuration."""

from unittest.mock import patch

from app.mcp_tools import (
    DEFAULT_TOOLBOX_SERVER_URL,
    DEFAULT_TOOLBOX_TOOLSET_NAME,
    create_customer_ops_toolset,
)


def test_create_customer_ops_toolset_uses_defaults(monkeypatch):
    """Use safe local defaults when environment variables are absent."""
    monkeypatch.delenv("TOOLBOX_SERVER_URL", raising=False)
    monkeypatch.delenv("TOOLBOX_TOOLSET_NAME", raising=False)

    with patch("app.mcp_tools.ToolboxToolset") as constructor:
        result = create_customer_ops_toolset()

    assert result is constructor.return_value
    constructor.assert_called_once_with(
        server_url=DEFAULT_TOOLBOX_SERVER_URL,
        toolset_name=DEFAULT_TOOLBOX_TOOLSET_NAME,
    )


def test_create_customer_ops_toolset_uses_environment(monkeypatch):
    """Allow deployment-specific server and toolset configuration."""
    monkeypatch.setenv(
        "TOOLBOX_SERVER_URL",
        "https://toolbox.internal.example",
    )
    monkeypatch.setenv(
        "TOOLBOX_TOOLSET_NAME",
        "production-readonly",
    )

    with patch("app.mcp_tools.ToolboxToolset") as constructor:
        result = create_customer_ops_toolset()

    assert result is constructor.return_value
    constructor.assert_called_once_with(
        server_url="https://toolbox.internal.example",
        toolset_name="production-readonly",
    )
