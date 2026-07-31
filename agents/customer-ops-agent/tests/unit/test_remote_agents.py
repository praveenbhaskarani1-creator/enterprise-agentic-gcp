"""Unit tests for remote A2A specialist configuration."""

import pytest
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from app.remote_agents import build_remote_specialists


def test_remote_specialists_require_agent_card_urls(monkeypatch):
    """Missing remote agent-card URLs must fail during startup."""
    monkeypatch.delenv("CUSTOMER_DATA_AGENT_CARD_URL", raising=False)
    monkeypatch.delenv("POLICY_AGENT_CARD_URL", raising=False)

    with pytest.raises(
        ValueError,
        match="CUSTOMER_DATA_AGENT_CARD_URL",
    ):
        build_remote_specialists()


def test_remote_specialists_are_created_from_environment(monkeypatch):
    """Both configured A2A specialists should be created."""
    monkeypatch.setenv(
        "CUSTOMER_DATA_AGENT_CARD_URL",
        "http://customer-data/a2a/app/.well-known/agent-card.json",
    )
    monkeypatch.setenv(
        "POLICY_AGENT_CARD_URL",
        "http://policy/a2a/app/.well-known/agent-card.json",
    )

    agents = build_remote_specialists()

    assert [agent.name for agent in agents] == [
        "customer_data_agent",
        "policy_agent",
    ]
    assert all(isinstance(agent, RemoteA2aAgent) for agent in agents)
