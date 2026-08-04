# Agentic ERP on Google Cloud - Day 9 Cheat Sheet

## Outcome

- Installed MCP Toolbox for Databases `1.8.0`.
- Exposed three parameterized, read-only BigQuery tools through MCP.
- Connected the Customer Data Agent to MCP Toolbox using the official ADK adapter.
- Removed direct BigQuery functions from the Customer Data Agent runtime.
- Added a disabled-by-default Atlassian Jira MCP integration.
- Separated Jira read and write tools.
- Required human confirmation for every enabled Jira write.
- Added a safe human-review staging tool requiring ADK confirmation.
- Passed 30 deterministic unit tests.
- Upgraded Agents CLI to `1.3.1`.

## Architecture

```text
User
 |
 v
Customer Operations Supervisor
 |
 +-- A2A/AgentTool --> Customer Data Agent
 |                         |
 |                         v
 |                    MCP Toolbox :5000
 |                         |
 |                         v
 |                  BigQuery curated views
 |
 +-- A2A/AgentTool --> Policy Agent
 |                         |
 |                         v
 |                  Agent Platform RAG
 |
 +-- Optional AgentTool --> Jira Agent
 |                              |
 |                              v
 |                    Atlassian Rovo MCP
 |
 +-- FunctionTool --> Human-review staging
                       confirmation required
```

## MCP Toolbox installation

```text
Version: 1.8.0
Platform: Linux x86_64
Binary: ~/.local/bin/toolbox
SHA256:
8c0ac3b9785d1424ad3d66799c26c5da695d73c74c45225a301689bf7d39d714
```

Toolbox is a local MCP server, not a Python package or database.

## Toolbox configuration

```text
agents/customer-ops-agent/toolbox/tools.yaml
```

The configuration exposes only:

```text
get_customer_summary
get_recent_orders
get_open_support_tickets
```

Security controls:

```text
BigQuery dataset allowlist: curated
Write mode: blocked
Maximum result rows: 10
Maximum bytes billed: 100 MiB
Parameterized customer_id input
No unrestricted execute-SQL tool
```

The SQL targets:

```text
curated.customers_current
curated.orders_current
curated.support_tickets_current
```

## Starting Toolbox locally

```bash
~/.local/bin/toolbox \
  --config "$HOME/agentic-erp-lab/agents/customer-ops-agent/toolbox/tools.yaml" \
  --address 127.0.0.1 \
  --port 5000 \
  --allowed-hosts="localhost,127.0.0.1" \
  --allowed-origins="http://localhost:5000,http://127.0.0.1:5000" \
  > /tmp/customer-ops-toolbox.log 2>&1 &
```

Verify:

```bash
tail -n 15 /tmp/customer-ops-toolbox.log
```

Expected:

```text
Initialized 1 sources
Initialized 3 tools
Initialized 2 groups
Server ready to serve!
```

Cloud Shell background processes disappear when the Cloud Shell VM restarts.
Restart Toolbox at the beginning of a new session.

## ADK Toolbox integration

Files:

```text
app/mcp_tools.py
app/specialist_agents.py
```

Environment:

```dotenv
TOOLBOX_SERVER_URL=http://127.0.0.1:5000
TOOLBOX_TOOLSET_NAME=customer-ops-readonly
```

Runtime path:

```text
Supervisor
  -> Customer Data Agent
  -> ToolboxToolset
  -> MCP Toolbox
  -> BigQuery
```

The top-level Agents CLI trace shows the supervisor calling
`customer_data_agent`. Nested MCP calls may appear only in Toolbox logs because
AgentTool encapsulates specialist events.

## Python import collision discovered

The Toolbox configuration was initially stored in:

```text
mcp/tools.yaml
```

That folder shadowed the installed Python package named `mcp`, causing:

```text
ImportError: cannot import name SamplingCapability from mcp
ModuleNotFoundError: No module named mcp
```

The folder was renamed to:

```text
toolbox/tools.yaml
```

Rule: do not create a top-level Python project folder named `mcp` when the MCP
SDK is installed.

Required ADK extras:

```bash
uv add "google-adk[mcp,toolbox]>=2.5.0,<3.0.0"
```

Installed MCP SDK:

```text
mcp 1.29.0
```

## Jira MCP scaffold

Current Atlassian endpoint:

```text
https://mcp.atlassian.com/v1/mcp/authv2
```

Files:

```text
app/jira_mcp.py
app/jira_agent.py
tests/unit/test_jira_mcp.py
tests/unit/test_jira_agent.py
```

Environment template:

```dotenv
ATLASSIAN_MCP_ENABLED=false
ATLASSIAN_MCP_WRITE_ENABLED=false
ATLASSIAN_MCP_URL=https://mcp.atlassian.com/v1/mcp/authv2
ATLASSIAN_MCP_ACCESS_TOKEN=
```

No real Atlassian token is committed.

Read tools are separately allowlisted from write tools. Jira remains absent
from the supervisor while `ATLASSIAN_MCP_ENABLED=false`.

When write access is eventually enabled, every Jira write tool uses:

```python
require_confirmation=True
```

Live Jira testing is deferred until Jira Cloud access and authorization are
available.

## Human-in-the-loop demonstration

Files:

```text
app/approval_tools.py
tests/unit/test_approval_tools.py
```

The supervisor exposes:

```text
stage_human_review_request
```

Supported review categories:

```text
refund
payment_change
account_closure
privileged_export
jira_write
```

The tool only stages a review demonstration. It never approves or executes the
underlying action.

All successful results retain:

```text
authorized_human_approval: false
action_executed: false
```

The tool itself is configured with:

```python
FunctionTool(
    func=stage_human_review_request,
    require_confirmation=True,
)
```

## Live HITL verification

An immediate-refund request was refused without automatically staging review.

An explicit review request produced:

```text
adk_request_confirmation
confirmed: false
```

The tool was blocked with:

```text
This tool call requires confirmation, please approve or reject.
```

This proves the tool cannot execute before confirmation.

`agents-cli run` is a non-interactive, one-prompt command. It displays the
pending confirmation but cannot complete the approve/reject exchange. Full
interactive approval will be tested later in ADK Playground or the deployed
Agent Platform UI.

## Tests

```bash
cd ~/agentic-erp-lab/agents/customer-ops-agent
uv run --extra lint ruff check app tests/unit
uv run pytest tests/unit -q
```

Result:

```text
30 passed
```

The tests cover:

- MCP Toolbox environment configuration.
- Jira disabled-by-default behavior.
- Jira read-tool allowlisting.
- Separate Jira write enablement.
- Required confirmation for Jira writes.
- Missing-token fail-closed behavior.
- Optional Jira specialist construction.
- Human-review input validation.
- Confirmation-protected review staging.
- No approval or business-action execution.

## Security boundaries

- No unrestricted SQL MCP tool.
- Agents query only curated BigQuery views.
- No database writes.
- No real Jira token committed.
- Jira is disabled until authorized.
- Jira write tools require two feature flags and human confirmation.
- Review staging is not approval.
- Retrieved Jira and RAG content is treated as untrusted data.
- No service-account keys are downloaded.
- Production secrets will use Secret Manager.
- Production Toolbox and agents will use private Cloud Run services and IAM.

## Current limitations

- Jira access is not available yet.
- HITL approval has not been exercised in a browser UI.
- MCP Toolbox is local and must be restarted after Cloud Shell restarts.
- No Day 9 service is deployed to Cloud Run, Agent Runtime, or GKE yet.

## Next

- Complete the Day 9 Git commit.
- Test interactive approval later through ADK Playground.
- Configure live Jira OAuth when access is granted.
- Begin observability, token usage, quotas, and rate-limit work.
