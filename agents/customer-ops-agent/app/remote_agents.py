"""Remote A2A specialist-agent definitions."""

import os

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent


def _required_environment_value(name: str) -> str:
    """Return a required nonempty environment value."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Required environment variable is missing: {name}")
    return value


def build_remote_specialists() -> list[RemoteA2aAgent]:
    """Create specialist clients from their A2A agent-card URLs."""
    customer_data_agent = RemoteA2aAgent(
        name="customer_data_agent",
        description=(
            "Remote read-only specialist for customer summaries, "
            "orders, and support tickets."
        ),
        agent_card=_required_environment_value(
            "CUSTOMER_DATA_AGENT_CARD_URL"
        ),
        timeout=60.0,
    )

    policy_agent = RemoteA2aAgent(
        name="policy_agent",
        description=(
            "Remote read-only specialist for approved policy retrieval "
            "with source citations."
        ),
        agent_card=_required_environment_value(
            "POLICY_AGENT_CARD_URL"
        ),
        timeout=60.0,
    )

    return [customer_data_agent, policy_agent]
