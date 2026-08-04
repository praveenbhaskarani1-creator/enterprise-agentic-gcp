"""Disabled-by-default Atlassian Jira MCP integration."""

import os

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

DEFAULT_ATLASSIAN_MCP_URL = (
    "https://mcp.atlassian.com/v1/mcp/authv2"
)

JIRA_READ_TOOLS = [
    "atlassianUserInfo",
    "getAccessibleAtlassianResources",
    "getJiraIssue",
    "getVisibleJiraProjects",
    "getTransitionsForJiraIssue",
    "searchJiraIssuesUsingJql",
]

JIRA_WRITE_TOOLS = [
    "addCommentToJiraIssue",
    "createJiraIssue",
    "editJiraIssue",
    "transitionJiraIssue",
]


def _environment_flag(name: str) -> bool:
    """Return whether an environment feature flag is enabled."""
    return os.getenv(name, "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _authorization_headers(
    _context: ReadonlyContext,
) -> dict[str, str]:
    """Return the short-lived Atlassian bearer token without logging it."""
    access_token = os.getenv("ATLASSIAN_MCP_ACCESS_TOKEN")

    if not access_token:
        raise RuntimeError(
            "ATLASSIAN_MCP_ACCESS_TOKEN is required when Jira MCP is enabled."
        )

    return {"Authorization": f"Bearer {access_token}"}


def _connection_params() -> StreamableHTTPConnectionParams:
    """Create the Atlassian Streamable HTTP connection."""
    return StreamableHTTPConnectionParams(
        url=os.getenv(
            "ATLASSIAN_MCP_URL",
            DEFAULT_ATLASSIAN_MCP_URL,
        ),
        timeout=30.0,
        sse_read_timeout=300.0,
    )


def create_jira_read_toolset() -> McpToolset | None:
    """Create the allowlisted Jira read toolset when enabled."""
    if not _environment_flag("ATLASSIAN_MCP_ENABLED"):
        return None

    return McpToolset(
        connection_params=_connection_params(),
        tool_filter=JIRA_READ_TOOLS,
        tool_name_prefix="jira_",
        header_provider=_authorization_headers,
    )


def create_jira_write_toolset() -> McpToolset | None:
    """Create human-confirmed Jira write tools when explicitly enabled."""
    if not _environment_flag("ATLASSIAN_MCP_ENABLED"):
        return None

    if not _environment_flag("ATLASSIAN_MCP_WRITE_ENABLED"):
        return None

    return McpToolset(
        connection_params=_connection_params(),
        tool_filter=JIRA_WRITE_TOOLS,
        tool_name_prefix="jira_",
        header_provider=_authorization_headers,
        require_confirmation=True,
    )
