# Day 11: Cloud Run Production Deployment

Deployed: 2026-08-07
Documented: 2026-08-09
Project: `agentic-erp-502706`
Region: `us-central1`

## Outcome

The Customer Operations Agent is deployed as a private Cloud Run service with:

- ADK supervisor and specialist agents
- A2A JSON-RPC endpoint
- BigQuery customer-data retrieval
- Agent Platform RAG policy retrieval
- MCP Toolbox sidecar
- Dedicated runtime service account
- Cloud Logging, Cloud Trace, and BigQuery Agent Analytics
- Application rate limiting
- Non-root production container

## Deployed architecture

```text
Authenticated client
        |
        v
Cloud Run: customer-ops-agent
        |
        +-- customer-ops-agent-1
        |     ADK supervisor
        |     Customer data specialist
        |     Policy specialist
        |     A2A and FastAPI endpoints
        |
        +-- customer-ops-toolbox-1
              MCP Toolbox
              BigQuery read-only tools
        |
        +-- BigQuery curated views
        |
        +-- Agent Platform RAG Engine
```

## Main resources

| Resource | Value |
|---|---|
| Cloud Run service | `customer-ops-agent` |
| Runtime service account | `customer-ops-agent-runtime@agentic-erp-502706.iam.gserviceaccount.com` |
| Artifact Registry repository | `agentic-erp-containers` |
| Agent container | `customer-ops-agent:day11-v2` |
| Toolbox container | `customer-ops-toolbox:day11-v3` |
| Agent port | `8080` |
| Toolbox sidecar port | `5000` |
| Toolbox URL | `http://127.0.0.1:5000` |
| BigQuery dataset | `curated` |
| RAG region | `us-central1` |

## Runtime IAM

The runtime service account has:

- Agent Platform User
- BigQuery Job User
- Cloud Trace Agent
- Logs Writer
- BigQuery Data Viewer on `curated`
- BigQuery Data Editor on `agent_analytics`

The runtime service account does not have direct access to `raw_cdc`.

## Important source files

```text
agents/customer-ops-agent/
├── Dockerfile
├── .dockerignore
├── .gcloudignore
├── pyproject.toml
├── uv.lock
├── app/
└── toolbox/
    ├── Dockerfile
    └── tools.yaml
```

## Validate local code

```bash
cd ~/agentic-erp-lab/agents/customer-ops-agent
uv run --extra lint ruff check app tests/unit
uv run pytest tests/unit -q
```

Expected result:

```text
All checks passed!
35 passed
```

## Build the agent container

```bash
cd ~/agentic-erp-lab/agents/customer-ops-agent

gcloud builds submit . \
  --project=agentic-erp-502706 \
  --region=us-central1 \
  --tag=us-central1-docker.pkg.dev/agentic-erp-502706/agentic-erp-containers/customer-ops-agent:day11-v2
```

This builds the ADK/FastAPI agent image and pushes it to Artifact Registry.

## Build the Toolbox sidecar

```bash
gcloud config set builds/use_kaniko true

gcloud builds submit toolbox \
  --no-cache \
  --project=agentic-erp-502706 \
  --region=us-central1 \
  --tag=us-central1-docker.pkg.dev/agentic-erp-502706/agentic-erp-containers/customer-ops-toolbox:day11-v3

gcloud config unset builds/use_kaniko
```

This builds a cache-free Toolbox image containing the current curated-view SQL.

## Deploy the private agent service

```bash
gcloud run deploy customer-ops-agent \
  --project=agentic-erp-502706 \
  --region=us-central1 \
  --image=us-central1-docker.pkg.dev/agentic-erp-502706/agentic-erp-containers/customer-ops-agent:day11-v2 \
  --service-account=customer-ops-agent-runtime@agentic-erp-502706.iam.gserviceaccount.com \
  --no-allow-unauthenticated
```

This deploys the primary private Cloud Run container.

## Update the Toolbox sidecar

```bash
gcloud run services update customer-ops-agent \
  --project=agentic-erp-502706 \
  --region=us-central1 \
  --container=customer-ops-toolbox-1 \
  --image=us-central1-docker.pkg.dev/agentic-erp-502706/agentic-erp-containers/customer-ops-toolbox:day11-v3
```

This updates the MCP Toolbox container in the same Cloud Run service.

## Configure the public A2A URL

```bash
CLOUD_RUN_URL="$(gcloud run services describe customer-ops-agent \
  --project=agentic-erp-502706 \
  --region=us-central1 \
  --format='value(status.url)')"

gcloud run services update customer-ops-agent \
  --project=agentic-erp-502706 \
  --region=us-central1 \
  --update-env-vars="APP_URL=${CLOUD_RUN_URL}"
```

This ensures the A2A agent card advertises the Cloud Run URL instead of `0.0.0.0`.

## Inspect the deployed revision

```bash
LATEST_REVISION="$(gcloud run services describe customer-ops-agent \
  --project=agentic-erp-502706 \
  --region=us-central1 \
  --format='value(status.latestReadyRevisionName)')"

gcloud run revisions describe "$LATEST_REVISION" \
  --project=agentic-erp-502706 \
  --region=us-central1 \
  --format="yaml(metadata.name,spec.containers[].name,spec.containers[].image)"
```

This displays the exact immutable image digests running in Cloud Run.

## Authenticated health check

```bash
CLOUD_RUN_URL="$(gcloud run services describe customer-ops-agent \
  --project=agentic-erp-502706 \
  --region=us-central1 \
  --format='value(status.url)')"

curl -sS \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$CLOUD_RUN_URL/health"
```

Expected response:

```json
{"status":"ok"}
```

## Authenticated A2A test

```bash
curl -sS --max-time 180 \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -X POST "$CLOUD_RUN_URL/a2a/app" \
  --data-binary @- <<'JSON'
{
  "jsonrpc": "2.0",
  "id": "day11-test",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "messageId": "day11-message",
      "parts": [
        {
          "kind": "text",
          "text": "For customer ID c0000000-0000-4000-a000-000000000001, return only the customer name, company, and status."
        }
      ]
    },
    "metadata": {}
  }
}
JSON
```

Expected business response:

```text
Name: Alice Smith
Company: Nexus Systems Ltd
Status: Active
```

## RAG deployment test

Use the same A2A request structure with this prompt:

```text
According to approved policy, how long after delivery may a customer request a return? Cite the policy filename and source URI.
```

Expected response:

```text
30 calendar days after delivery
returns-and-refunds.md
gs://agentic-erp-502706-rag-source/customer-ops/returns-and-refunds.md
```

## Authorized BigQuery dataset

The Toolbox queries curated views, but those views read underlying `raw_cdc` tables.

Console configuration:

1. Open BigQuery Studio.
2. Select `raw_cdc`.
3. Select **Sharing → Authorize datasets**.
4. Authorize:
   - Project: `agentic-erp-502706`
   - Dataset: `curated`
   - Target type: `Views`
5. Save the authorization.

This lets curated views read underlying CDC tables without granting the runtime service account direct raw-data access.

## Important troubleshooting findings

### Cloud Build source-bucket 403

The Compute Engine default service account required:

- Storage Object Viewer on the Cloud Build source bucket
- Artifact Registry Writer on `agentic-erp-containers`
- Logs Writer for Cloud Build logs

### RAG pandas error

The RAG client required this runtime dependency:

```toml
"pandas>=2.2.0,<3.0.0"
```

### Curated view returned raw_cdc permission error

The Toolbox SQL was correct. BigQuery expanded the curated view to its underlying `raw_cdc` table.

Resolution: authorize the `curated` dataset on `raw_cdc`; do not grant the runtime identity direct raw-data access.

### agents-cli authentication timeout

`agents-cli run -H ...` fetched the private agent card but did not reliably preserve the Cloud Run authorization header on the subsequent A2A request.

Resolution: use an authenticated direct JSON-RPC request with `curl`.

### Toolbox image validation

The packaged `day11-v3` Toolbox image contains only curated references:

```text
curated.customers_current
curated.orders_current
curated.support_tickets_current
```

## Current verification status

- Cloud Run readiness: passed
- Private IAM authentication: passed
- Health endpoint: passed
- BigQuery customer lookup: passed
- Agent Platform RAG lookup: passed
- A2A JSON-RPC endpoint: passed
- Local lint: passed
- Unit tests: 35 passed

## Follow-up hardening

A mixed customer-data plus policy request exposed an orchestration reliability issue:

```text
Tool 'search_customers' not found
```

Separate BigQuery and RAG requests pass. The specialist instructions should be strengthened with exact MCP tool mappings before production promotion.

## Remaining cleanup

- Commit the Day 11 source and documentation.
- Decide whether to delete the older `customer-ops-agent-dev` service.
- Keep the canonical `customer-ops-agent` service private.
- Fix and retest mixed-agent orchestration.