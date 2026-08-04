# Day 8 Cheat Sheet — Multi-Agent Orchestration and A2A

## Outcome

Created a Customer Operations Supervisor that can call two specialist agents:

- Customer Data Agent: read-only BigQuery customer, order, and ticket retrieval.
- Policy Agent: read-only Agent Platform RAG policy retrieval with citations.

## Architecture

User or A2A Client
→ Supervisor Agent
→ A2A Customer Data Agent
→ curated BigQuery

User or A2A Client
→ Supervisor Agent
→ A2A Policy Agent
→ Agent Platform RAG Engine

## Protocol Responsibilities

- A2A connects agents to other agents.
- MCP connects agents to tools and data systems.
- ADK supplies agent definitions and orchestration.
- Agents CLI supplies local execution, evaluation, deployment, and A2A routes.

## Runtime Modes

`AGENT_ROLE=combined`
Runs the Supervisor with in-process specialists for development and unit tests.

`AGENT_ROLE=customer_data`
Runs the standalone Customer Data Agent.

`AGENT_ROLE=policy`
Runs the standalone Policy Agent.

`AGENT_ROLE=supervisor`
Runs the Supervisor with remote A2A specialists.

## Local Ports

- `18080`: combined application
- `18081`: standalone Customer Data Agent
- `18082`: standalone Policy Agent
- `18083`: distributed Supervisor

## A2A Endpoints

Agent card:

`/a2a/app/.well-known/agent-card.json`

JSON-RPC endpoint:

`/a2a/app`

The tested protocol version was A2A `0.3.0` over JSON-RPC with streaming enabled.

## Important Files

- `app/agent.py`: selects runtime role and creates the Supervisor.
- `app/specialist_agents.py`: defines local Data and Policy Agents.
- `app/remote_agents.py`: creates remote specialists from A2A agent cards.
- `app/tools.py`: read-only BigQuery tools.
- `app/rag_tools.py`: read-only RAG Engine policy search.
- `tests/unit/test_tools.py`: tool and orchestration tests.
- `tests/unit/test_remote_agents.py`: remote A2A configuration tests.

## Orchestration Decision

ADK `sub_agents` performs a control handoff. It handled single-specialist
requests but failed to return control for a mixed request.

The Supervisor therefore uses `AgentTool` wrappers. Each specialist returns its
result to the Supervisor, allowing it to call both specialists and synthesize
one final response.

## Verified Scenarios

- Supervisor routed a policy request to the Policy Agent.
- Supervisor routed a customer request to the Data Agent.
- Agents CLI invoked the application through A2A.
- Remote Supervisor called the standalone Policy Agent through A2A.
- Remote Supervisor called the standalone Data Agent through A2A.
- Mixed customer-and-policy request called both specialists successfully.
- Unit tests passed.

## Current Local Security

All servers bind to `127.0.0.1`, so they are not public internet endpoints.

## Production Security Plan

- Deploy three authenticated Cloud Run services.
- Use a separate service account for each runtime.
- Do not allow unauthenticated specialist access.
- Grant the Supervisor `roles/run.invoker` only on specialist services.
- Give the Data Agent read-only access only to the curated BigQuery dataset.
- Give the Policy Agent access only to the approved RAG corpus.
- Use short-lived Google identity tokens instead of service-account keys.
- Register endpoints in Agent Registry and govern traffic with Agent Gateway.

## Known Dependency Status

ADK `RemoteA2aAgent`, `A2aAgentExecutor`, and related converters currently emit
experimental implementation warnings. The A2A protocol and A2A SDK themselves
are not experimental.## Completion Record

- Completion date: 2026-07-31
- Status: Complete and merged into `Main`
- Unit tests: 15 passed
- A2A protocol test: Passed
- Distributed Data Agent test: Passed
- Distributed Policy Agent test: Passed
- Mixed-specialist orchestration test: Passed
- Local test servers: Stopped after validation
- Feature commit: `b4cfe7e`
- Documentation commit: `00e91e9`