# Architecture

This document describes how the Customer Operations agent system is structured, how a request flows through it, and how it is deployed and observed. All diagrams are Mermaid and render on GitHub.

Contents: [1. System context](#1-system-context) · [2. Agent topology](#2-agent-topology) · [3. Request flow](#3-request-flow) · [4. Human-in-the-loop flow](#4-human-in-the-loop-flow) · [5. Runtime modes](#5-runtime-modes) · [6. Data architecture](#6-data-architecture) · [7. Deployment](#7-deployment) · [8. Observability](#8-observability) · [9. Security layers](#9-security-layers) · [10. Component reference](#10-component-reference)

---

## 1. System context

![Customer Operations agent architecture](images/architecture-overview.svg)

Overview as an editable Mermaid diagram, with the surrounding GCP services:

```mermaid
flowchart TB
    subgraph Clients
        WEB["ADK web playground"]
        A2AC["A2A clients<br/>Gemini Enterprise"]
        GECX["GECX conversational app<br/>prompt and safety guardrails"]
    end

    subgraph GCP["Google Cloud project, us-central1"]
        SVC["customer-ops-agent service<br/>FastAPI + ADK + A2A"]
        TB["MCP Toolbox sidecar"]
        BQ[("BigQuery<br/>curated views")]
        RAG[("RAG Engine<br/>policy corpus")]
        GEM["Gemini on Vertex AI"]
        OBS["Trace · Logging · Monitoring<br/>BigQuery agent_analytics"]
    end

    ATL["Atlassian Rovo MCP<br/>external, optional"]
    HUM(["Authorized human reviewer"])

    WEB --> SVC
    A2AC --> SVC
    GECX -.-> SVC
    SVC --> GEM
    SVC --> TB --> BQ
    SVC --> RAG
    SVC -.-> ATL
    SVC -. "staged review requests" .-> HUM
    SVC --> OBS
```

## 2. Agent topology

The supervisor exposes specialists to the model as **tools** (`AgentTool`), so the supervisor stays in control of the conversation and composes the final answer. Specialists are scoped by instruction and by tool set.

```mermaid
flowchart TB
    SUP{{"root_agent (Supervisor)<br/>routes, composes, never touches data"}}

    subgraph Specialists["Read-only specialists"]
        CDA["customer_data_agent<br/>get_customer_summary<br/>get_recent_orders<br/>get_open_support_tickets"]
        PA["policy_agent<br/>search_customer_ops_policies"]
        JA["jira_agent (optional)<br/>read toolset<br/>write toolset only if enabled"]
    end

    HR["stage_human_review_request<br/>FunctionTool, require_confirmation=True"]

    SUP --> CDA
    SUP --> PA
    SUP -.-> JA
    SUP --> HR

    CDA --> MCP1["MCP Toolbox toolset<br/>customer-ops-readonly"]
    PA --> RAGT["RAG retrieve_contexts<br/>top_k 1 to 5"]
    JA --> MCP2["Atlassian MCP<br/>allowlisted tools"]
```

Routing rules enforced in the supervisor instruction:

| Request type | Routed to |
| :--- | :--- |
| Customer, order, or support-ticket lookup | `customer_data_agent` |
| Policy, privacy, returns, refunds, escalation | `policy_agent` |
| Jira issue, project, or search | `jira_agent` (when enabled) |
| Mixed request | Every required specialist, then one composed answer |
| Sensitive action the user wants reviewed | `stage_human_review_request` (after explaining it only stages) |
| Writes, refunds, account closure, exports, bypasses | Refused |

## 3. Request flow

A mixed request: *"What is customer X's latest order status, and can they still return it?"*

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant API as FastAPI + rate limiter
    participant S as Supervisor
    participant D as Customer Data Agent
    participant TB as MCP Toolbox
    participant BQ as BigQuery curated
    participant P as Policy Agent
    participant R as RAG Engine

    U->>API: POST (message)
    API->>API: sliding-window check (429 if exceeded)
    API->>S: run via ADK Runner
    S->>D: AgentTool call (customer_id)
    D->>TB: get_recent_orders(customer_id)
    TB->>BQ: parameterized SQL, row and byte caps
    BQ-->>TB: rows
    TB-->>D: orders
    D-->>S: order summary
    S->>P: AgentTool call (return window question)
    P->>R: retrieve_contexts(query, top_k)
    R-->>P: passages + source URIs
    P-->>S: answer with citations
    S-->>U: composed answer, citations preserved
    Note over API,S: Every step emits OpenTelemetry spans,<br/>structured logs, and BigQuery agent events
```

## 4. Human-in-the-loop flow

Sensitive actions are never executed by an agent. The agent can only **stage** a review request, and even staging pauses for explicit user confirmation.

```mermaid
flowchart TD
    A["User asks for a sensitive action<br/>refund, payment change, account closure,<br/>privileged export, Jira write"] --> B{"Did the user explicitly ask<br/>to submit it for review?"}
    B -- No --> C["Refuse, explain policy.<br/>Do NOT call the review tool"]
    B -- Yes --> D["Supervisor explains: confirmation<br/>stages a request only"]
    D --> E["ADK confirmation gate<br/>require_confirmation=True"]
    E -- Declined --> F["Nothing happens"]
    E -- Confirmed --> G["stage_human_review_request<br/>validates action type, resource id,<br/>justification length"]
    G --> H["Result:<br/>status = staged_for_human_review<br/>authorized_human_approval = false<br/>action_executed = false"]
    H --> I(["Authorized human reviews<br/>and acts outside the agent"])
```

Jira writes follow the same principle: write tools exist only when `ATLASSIAN_MCP_WRITE_ENABLED` is set, the user must request the exact action, and ADK requires human confirmation of the tool call.

## 5. Runtime modes

One image, five shapes. `AGENT_ROLE` selects what `root_agent` is.

```mermaid
flowchart LR
    subgraph Single["combined (default): one process"]
        direction TB
        S1{{Supervisor}} --> D1[Data agent]
        S1 --> P1[Policy agent]
    end

    subgraph Distributed["supervisor + remote specialists over A2A"]
        direction TB
        S2{{"Supervisor<br/>AGENT_ROLE=supervisor"}}
        S2 -- "A2A JSON-RPC" --> D2["Data agent service<br/>AGENT_ROLE=customer_data"]
        S2 -- "A2A JSON-RPC" --> P2["Policy agent service<br/>AGENT_ROLE=policy"]
    end
```

In distributed mode the supervisor discovers specialists from their **A2A agent cards** (`CUSTOMER_DATA_AGENT_CARD_URL`, `POLICY_AGENT_CARD_URL`). Each agent serves `/.well-known/agent-card.json` under `/a2a/<app>`, so specialists are independently deployable, scalable, and replaceable.

## 6. Data architecture

```mermaid
flowchart LR
    PG[("PostgreSQL OLTP<br/>multi-tenant schema<br/>synthetic data")] -->|"CDC replication"| RAW[("BigQuery raw_cdc<br/>not exposed to the agent")]
    RAW -->|"curated views"| CUR[("BigQuery curated<br/>customers_current<br/>orders_current<br/>support_tickets_current")]
    CUR -->|"parameterized read-only SQL"| TB["MCP Toolbox"]
    TB --> AG["Customer Data Agent"]

    KB["knowledge-base/*.md<br/>versioned policy documents"] -->|"ingest"| RC[("RAG corpus")]
    RC --> PAG["Policy Agent"]

    AG -. events .-> AN[("BigQuery agent_analytics<br/>agent_events + views")]
    PAG -. events .-> AN
```

Boundaries that matter:

- The runtime identity can read **`curated`** only. It has no access to `raw_cdc`.
- The curated views mask sensitive fields (for example `shipping_address_masked`).
- Policy documents carry front matter (`document_id`, `version`, `effective_date`, `owner`) so citations are traceable.

### Transactional model

Ten tables, each with a UUID primary key and a `tenant_id` for tenant isolation. The `approval_requests` and `agent_action_audit` tables model the human-approval and audit trail the agent is designed to feed.

```mermaid
erDiagram
    tenants ||--o{ customers : owns
    customers ||--o{ orders : places
    customers ||--o{ support_tickets : submits
    orders ||--o{ order_items : includes
    orders ||--o{ payments : funded_by
    orders ||--o{ approval_requests : triggers
    products ||--o{ order_items : referenced_by
    support_tickets ||--o{ ticket_events : logs
    support_tickets ||--o{ approval_requests : requires
    tenants ||--o{ agent_action_audit : audits
```

Column-level detail is in [specs/data-model.md](../specs/data-model.md).

## 7. Deployment

### Cloud Run (private service, two containers)

```mermaid
flowchart TB
    C(["Authenticated client<br/>IAM identity token"]) --> CR

    subgraph CR["Cloud Run service: customer-ops-agent"]
        direction LR
        AG["agent container :8080<br/>non-root uid 10001"] -- "127.0.0.1:5000" --> TBX["toolbox sidecar :5000"]
    end

    CR -- "runtime service account<br/>customer-ops-agent-runtime" --> BQ[("BigQuery curated<br/>Data Viewer")]
    CR --> RAG[("RAG Engine<br/>Agent Platform User")]
    CR --> OBS["Trace Agent · Logs Writer<br/>agent_analytics Data Editor"]
    AR[("Artifact Registry<br/>agentic-erp-containers")] -. images .-> CR
    CB["Cloud Build"] --> AR
```

### GKE

```mermaid
flowchart TB
    subgraph NS["namespace: agentic-erp"]
        KSA["ServiceAccount customer-ops-agent<br/>annotated for Workload Identity"]
        subgraph POD["Pod: customer-ops-agent"]
            AG["agent :8080<br/>startup, readiness, liveness on /health"]
            TBX["toolbox :5000"]
        end
        KSA --> POD
    end
    KSA -. "Workload Identity" .-> GSA["GCP service account<br/>customer-ops-agent-runtime"]
    GSA --> BQ[("BigQuery curated")]
    GSA --> RAG[("RAG Engine")]
```

Hardening applied to both targets: non-root user, no privilege escalation, all Linux capabilities dropped, resource requests and limits, health probes, images pinned by digest, no keys in images (Application Default Credentials).

## 8. Observability

```mermaid
flowchart LR
    REQ["Request"] --> APP["FastAPI + ADK"]

    APP -->|"BigQueryAgentAnalyticsPlugin"| EV[("agent_analytics.agent_events")]
    EV --> VW["Views: v_llm_request, v_llm_response,<br/>v_tool_starting, v_tool_completed,<br/>v_agent_transfer, v_hitl_confirmation_request,<br/>v_invocation_completed"]
    VW --> TOK["dashboard_token_usage_daily"] --> LS["Looker Studio"]

    APP -->|"OpenTelemetry"| TR["Cloud Trace"]
    APP -->|"structured logs"| LG["Cloud Logging"]
    LG -->|"RATE_LIMIT_REJECTED"| LM["Log-based metric<br/>agent_rate_limit_rejections"]
    LM --> DB["Monitoring dashboard<br/>Agentic ERP Operations"]
    LM --> AL["Alert policy: rejection spike<br/>email notification"]
```

What is captured: token usage, latency, tool calls, HITL confirmation requests, errors, and rate-limit rejections. What is deliberately **not** captured: raw client addresses (logged as a 12-character SHA-256 prefix), multimodal content, and unbounded payloads (content is truncated at 64 KiB).

## 9. Security layers

Defense in depth: a failure in one layer is contained by the next.

```mermaid
flowchart TB
    L1["1. Edge: private service, IAM-authenticated callers, rate limiting (HTTP 429)"]
    L2["2. Agent: scoped instructions, one tool set per specialist, no cross-agent tools"]
    L3["3. Tool: parameterized SQL only, no execute-SQL tool, allowlisted MCP tools, input validation"]
    L4["4. Data: curated views only, masked fields, writeMode blocked, row and byte caps"]
    L5["5. Action: confirmation gate, staging only, action_executed=false"]
    L6["6. Platform: least-privilege service account, ADC, non-root container, no keys"]
    L7["7. Audit: traces, logs, and agent events for every step"]
    L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7
```

See [security-and-governance.md](security-and-governance.md) for the threat model and control matrix.

## 10. Component reference

| Component | File | Responsibility |
| :--- | :--- | :--- |
| Supervisor and modes | `app/agent.py` | Builds the supervisor, selects `AGENT_ROLE`, attaches analytics |
| Specialists | `app/specialist_agents.py` | Customer Data and Policy agents and their instructions |
| Jira specialist | `app/jira_agent.py`, `app/jira_mcp.py` | Optional Atlassian MCP agent; separate read and write toolsets |
| Remote agents | `app/remote_agents.py` | `RemoteA2aAgent` clients from agent-card URLs |
| MCP data access | `app/mcp_tools.py`, `toolbox/tools.yaml` | Toolbox client and the three read-only BigQuery tools |
| Direct BigQuery tools | `app/tools.py` | Original parameterized read-only functions, superseded by the Toolbox path |
| RAG retrieval | `app/rag_tools.py` | Validated query, bounded `top_k`, structured not-found and error results |
| Human review | `app/approval_tools.py` | Allowlisted action types, input validation, staging only |
| Telemetry | `app/analytics.py` | BigQuery Agent Analytics plugin configuration |
| Rate limiting | `app/rate_limit.py` | Sliding-window middleware with privacy-safe rejection logging |
| Server | `app/fast_api_app.py` | ADK FastAPI app, A2A routes, Cloud Logging, `/feedback` |
| A2A | `app/app_utils/a2a.py` | Dynamic agent card and JSON-RPC routes |
| Sessions and artifacts | `app/app_utils/services.py` | Shared session and artifact services across all serving surfaces |

### Configuration surface

| Variable | Purpose | Default |
| :--- | :--- | :--- |
| `AGENT_ROLE` | Runtime mode | `combined` |
| `RAG_CORPUS_RESOURCE`, `RAG_LOCATION`, `RAG_TOP_K` | RAG corpus, region, results (clamped 1 to 5) | `us-central1`, `3` |
| `TOOLBOX_SERVER_URL`, `TOOLBOX_TOOLSET_NAME` | MCP Toolbox endpoint and toolset | `127.0.0.1:5000`, `customer-ops-readonly` |
| `ATLASSIAN_MCP_ENABLED`, `ATLASSIAN_MCP_WRITE_ENABLED` | Jira read and write gates | `false`, `false` |
| `BQ_ANALYTICS_ENABLED` and related | Agent analytics sink | `false` locally, `true` deployed |
| `RATE_LIMIT_ENABLED`, `RATE_LIMIT_REQUESTS_PER_WINDOW`, `RATE_LIMIT_WINDOW_SECONDS` | Rate limiter | `true`, `60`, `60` |
| `SESSION_SERVICE_URI`, `LOGS_BUCKET_NAME` | Durable sessions and artifacts | In-memory when unset |
