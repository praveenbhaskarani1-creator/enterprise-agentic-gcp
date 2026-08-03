"""Unit tests for the optional Jira specialist."""

from unittest.mock import patch

from app.jira_agent import build_jira_agent


def test_jira_agent_is_absent_when_mcp_is_disabled():
    """Do not create a Jira specialist without a read toolset."""
    with (
        patch(
            "app.jira_agent.create_jira_read_toolset",
            return_value=None,
        ),
        patch("app.jira_agent.Agent") as agent_constructor,
    ):
        result = build_jira_agent()

    assert result is None
    agent_constructor.assert_not_called()


def test_jira_agent_uses_only_read_tools_by_default():
    """Build a read-only Jira specialist when writes are disabled."""
    read_toolset = object()

    with (
        patch(
            "app.jira_agent.create_jira_read_toolset",
            return_value=read_toolset,
        ),
        patch(
            "app.jira_agent.create_jira_write_toolset",
            return_value=None,
        ),
        patch("app.jira_agent.Agent") as agent_constructor,
    ):
        result = build_jira_agent()

    assert result is agent_constructor.return_value
    assert agent_constructor.call_args.kwargs["tools"] == [
        read_toolset
    ]


def test_jira_agent_adds_confirmed_write_toolset():
    """Add the separately gated write toolset when enabled."""
    read_toolset = object()
    write_toolset = object()

    with (
        patch(
            "app.jira_agent.create_jira_read_toolset",
            return_value=read_toolset,
        ),
        patch(
            "app.jira_agent.create_jira_write_toolset",
            return_value=write_toolset,
        ),
        patch("app.jira_agent.Agent") as agent_constructor,
    ):
        result = build_jira_agent()

    assert result is agent_constructor.return_value
    assert agent_constructor.call_args.kwargs["tools"] == [
        read_toolset,
        write_toolset,
    ]

    instruction = agent_constructor.call_args.kwargs[
        "instruction"
    ].lower()
    assert "human confirmation" in instruction
    assert "never bypass confirmation" in instruction
