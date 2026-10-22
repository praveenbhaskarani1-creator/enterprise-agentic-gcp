# Design Decisions

Short architecture decision records. Each one states the context, the decision, and the trade-off accepted.

## ADR-1: Supervisor with specialists exposed as tools

- **Context:** One agent holding every tool would have broad access and a long, ambiguous prompt.
- **Decision:** A supervisor delegates to specialists through `AgentTool`. Each specialist has one narrow job and one tool set.
- **Why not sub-agent transfer?** With `AgentTool`, control returns to the supervisor, which composes a single answer and keeps citations. Transfer hands the conversation off and the supervisor loses it.
- **Trade-off:** An extra model call per delegation, in exchange for clearer boundaries, easier testing, and least privilege.

## ADR-2: MCP Toolbox instead of in-process BigQuery functions

- **Context:** The first version called BigQuery directly from Python functions (`app/tools.py`).
- **Decision:** Move data access behind **MCP Toolbox**, with the tools declared in `toolbox/tools.yaml`: parameterized SQL, `writeMode: blocked`, dataset allowlist, row cap, bytes-billed cap.
- **Why:** Data access becomes declarative, reviewable, and independent of agent code. A prompt-level mistake cannot add a new query. Standard MCP also makes the tools reusable by other agents.
- **Trade-off:** One more process to run (a sidecar), and its health is now part of the service.

## ADR-3: Curated views only, never raw CDC tables

- **Context:** Replicated source data lands in `raw_cdc`, which can hold fields the agent should not see.
- **Decision:** The agent queries `curated.*_current` views with masked fields. The runtime identity has no access to `raw_cdc`.
- **Why:** IAM enforces the boundary, so a mistake in the SQL or prompt cannot cross it. This was validated during Cloud Run rollout, when a view that still referenced `raw_cdc` failed with a permission error rather than leaking data.

## ADR-4: RAG for policy, SQL for facts

- **Context:** Two kinds of questions: *what is true about this customer* and *what does policy say*.
- **Decision:** Customer facts come from structured queries. Policy comes from RAG with mandatory citations (`source_uri`, `source_display_name`).
- **Why:** Structured facts should never be approximated by semantic search, and policy needs provenance. `top_k` is clamped to 1 to 5 to bound context and cost.

## ADR-5: Staging-only human review with an explicit confirmation gate

- **Context:** Refunds and similar actions have financial and compliance impact.
- **Decision:** No tool executes them. The only action tool *stages* a request, is wrapped with `require_confirmation=True`, validates an allowlist of action types, and returns `action_executed: false`.
- **Why:** Safety does not rely on the model declining. Even a fully manipulated model has no capability to perform the action.
- **Trade-off:** The approval workflow itself lives outside the agent (modeled by the `approval_requests` table).

## ADR-6: Jira integration is off by default and split into read and write

- **Decision:** `ATLASSIAN_MCP_ENABLED=false` by default. Read and write toolsets are built separately, and the write toolset exists only when `ATLASSIAN_MCP_WRITE_ENABLED` is set. Every write still needs exact-action intent and ADK confirmation.
- **Why:** Third-party content is a prompt-injection vector, and write access should be opt-in per environment.

## ADR-7: A2A for distributed specialists, same code path

- **Decision:** `AGENT_ROLE` lets one image run as combined, a single specialist, or a supervisor calling remote specialists over A2A using agent cards.
- **Why:** Start simple (one process) and scale out without rewriting. Agent cards give discoverability and a contract. The same endpoint can be registered with A2A-aware platforms.
- **Trade-off:** Remote mode adds network latency and needs inter-agent authentication, which is on the roadmap.

## ADR-8: Sidecar topology on Cloud Run and GKE

- **Decision:** The Toolbox runs next to the agent, reachable only on `127.0.0.1:5000`.
- **Why:** It is never exposed on a network, needs no separate authentication layer, and shares the pod's lifecycle and service account. The same shape works on both platforms.

## ADR-9: Privacy-safe, layered observability

- **Decision:** Combine BigQuery Agent Analytics (queryable events and token usage), OpenTelemetry to Cloud Trace (latency and call graphs), and structured Cloud Logging with a log-based metric and alert for rate-limit spikes.
- **Why:** Each tool answers a different question: cost, latency, and abuse. Client addresses are logged only as a truncated SHA-256, payloads are capped, and multimodal content is not logged.

## ADR-10: Application-level rate limiting as a safety floor

- **Decision:** A sliding-window middleware limits POST requests per client (default 60 per 60 seconds), exempts health checks and read-only methods, and returns `429` with `Retry-After` and `X-RateLimit-*` headers.
- **Why:** Cheap protection against runaway cost while developing, with no extra infrastructure.
- **Known limit:** In-memory and per instance. A production deployment should enforce limits at a gateway or shared store.

## ADR-11: One configuration model, environment-driven

- **Decision:** Behavior toggles (roles, Jira, analytics, rate limits, RAG corpus) are environment variables with safe defaults. Defaults lean closed: Jira off, writes off.
- **Why:** The same image runs locally, on Cloud Run, and on GKE, and a misconfiguration fails closed rather than open (for example RAG returns `configuration_error` if no corpus is set).
