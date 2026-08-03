# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Customer Operations Agent module."""

import os

from google.adk.agents import Agent
from google.adk.agents.base_agent import BaseAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types

from app.jira_agent import build_jira_agent
from app.remote_agents import build_remote_specialists
from app.specialist_agents import customer_data_agent, policy_agent

MODEL = "gemini-3.6-flash"


def _with_optional_jira(
    specialist_agents: list[BaseAgent],
) -> list[BaseAgent]:
    """Add the Jira specialist only when Jira MCP is enabled."""
    jira_agent = build_jira_agent()

    if jira_agent is not None:
        specialist_agents.append(jira_agent)

    return specialist_agents


def _build_supervisor(specialist_agents: list[BaseAgent]) -> Agent:
    """Build a supervisor with local or remote specialist agents."""
    return Agent(
        name="root_agent",
        description=(
            "Supervises customer operations requests and delegates them "
            "to scoped specialist agents."
        ),
        model=Gemini(
            model=MODEL,
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction="""
I am the Customer Operations Supervisor Agent.

Route requests as follows:
- Call the customer_data_agent tool for customer, order, and support-ticket
  lookups.
- Call the policy_agent tool for policy, privacy, returns, refunds, and
  escalation questions.
- When the jira_agent tool is available, call it for Jira issue, project,
  search, or explicitly requested Jira workflow operations.
- For mixed requests, call every required specialist tool before composing
  the final response.

Customer database access and policy retrieval are read-only. Do not perform
database operations or policy searches yourself. Do not invent customer data,
policy information, Jira records, or tool results.

Database writes, order changes, payment modifications, refund approvals,
account closures, privileged exports, and access-control bypasses are
forbidden.

A Jira write may occur only through the Jira specialist when write access is
explicitly enabled, the user requested that exact action, and an authorized
human confirms the proposed tool call. Never bypass or simulate confirmation.

Return concise answers and preserve source citations supplied by specialists.
""",
        tools=[
            AgentTool(agent=agent)
            for agent in specialist_agents
        ],
    )


AGENT_ROLE = os.getenv("AGENT_ROLE", "combined").strip().lower()

if AGENT_ROLE == "combined":
    root_agent = _build_supervisor(
        _with_optional_jira(
            [customer_data_agent, policy_agent],
        )
    )
elif AGENT_ROLE == "customer_data":
    root_agent = customer_data_agent
elif AGENT_ROLE == "policy":
    root_agent = policy_agent
elif AGENT_ROLE == "jira":
    jira_agent = build_jira_agent()

    if jira_agent is None:
        raise ValueError(
            "AGENT_ROLE=jira requires ATLASSIAN_MCP_ENABLED=true."
        )

    root_agent = jira_agent
elif AGENT_ROLE == "supervisor":
    root_agent = _build_supervisor(
        _with_optional_jira(build_remote_specialists())
    )
else:
    raise ValueError(
        f"Unsupported AGENT_ROLE '{AGENT_ROLE}'. Use combined, "
        "customer_data, policy, jira, or supervisor."
    )


app = App(
    root_agent=root_agent,
    name="app",
)
