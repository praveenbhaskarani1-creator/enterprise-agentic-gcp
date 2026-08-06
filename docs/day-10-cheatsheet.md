# Day 10 — Observability, Analytics, Rate Limits and Alerts

Completed: 2026-08-06
Project: `agentic-erp-502706`
Region: `us-central1`

## What we built

- ADK agent-event analytics stored in BigQuery.
- Token-usage reporting through BigQuery and Looker Studio.
- OpenTelemetry traces in Cloud Trace.
- Structured application and rate-limit logs in Cloud Logging.
- A local FastAPI rate-limiting middleware.
- A log-based metric for HTTP 429 rejections.
- A Cloud Monitoring operations dashboard.
- A metric-threshold alert with email notification.
- Unit tests for rate-limit behavior.

## Observability flow

```text
User request
  -> FastAPI / ADK agent
  -> Agent and tool events
  -> BigQuery agent_analytics
  -> OpenTelemetry spans
  -> Cloud Trace
  -> Structured logs
  -> Cloud Logging
  -> Log-based metric
  -> Cloud Monitoring dashboard
  -> Alert incident
  -> Email notification
  Important files
app/analytics.py — configures the ADK BigQuery analytics plugin.
app/rate_limit.py — implements local sliding-window rate limiting.
app/fast_api_app.py — attaches telemetry and rate-limit middleware.
app/agent.py — attaches analytics plugins to the ADK application.
tests/unit/test_rate_limit.py — validates rate-limit behavior.
.env.example — documents analytics and rate-limit configuration.
APP_ENV=dev

BQ_ANALYTICS_ENABLED=false
BQ_ANALYTICS_DATASET_ID=agent_analytics
BQ_ANALYTICS_TABLE_ID=agent_events
BQ_ANALYTICS_LOCATION=us-central1

RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_WINDOW=60
RATE_LIMIT_WINDOW_SECONDS=60
BQ_ANALYTICS_ENABLED=true
agentic-erp-502706.agent_analytics
agent_events
Useful generated views include:
v_llm_request
v_llm_response
v_tool_starting
v_tool_completed
v_agent_transfer
v_hitl_confirmation_request
v_invocation_completed
dashboard_token_usage_daily

SELECT *
FROM `agentic-erp-502706.agent_analytics.dashboard_token_usage_daily`
ORDER BY usage_date DESC, agent;
GCP Console locations
Agent events: BigQuery → agent_analytics
Traces: Trace Explorer
Structured logs: Logging → Logs Explorer
Dashboard: Monitoring → Dashboards → Agentic ERP Operations
Incidents: Monitoring → Alerting
Token report: Looker Studio / Data Studio
SELECT *
FROM `agentic-erp-502706.agent_analytics.dashboard_token_usage_daily`
ORDER BY usage_date DESC, agent;
GCP Console locations
Agent events: BigQuery → agent_analytics
Traces: Trace Explorer
Structured logs: Logging → Logs Explorer
Dashboard: Monitoring → Dashboards → Agentic ERP Operations
Incidents: Monitoring → Alerting
Token report: Looker Studio / Data Studio
Rate-limit metric
Metric type:
logging.googleapis.com/user/agent_rate_limit_rejections
Dashboard widget:
Rate-limit Rejections/sec
Production starter alert:
Name: Agent Rate-limit Rejection Spike
Rolling window: 5 minutes
Function: Rate
Threshold: 0.1/s
Retest window: 5 minutes
Notification: Agentic ERP Operations email
Tune this threshold after measuring real production traffic.
Local commands
Start the API server:
uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 18084
Start a low-limit test server:
RATE_LIMIT_REQUESTS_PER_WINDOW=2 RATE_LIMIT_WINDOW_SECONDS=60 uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 18085
Check server health:
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18085/health
Trigger the test limiter:
for i in 1 2 3 4 5 6; do printf "Request $i: "; curl -s -X POST -H "Content-Type: application/json" -d '{}' -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18085/rate-limit-test; done
Expected result: initial 404 responses followed by 429 rejections. The missing route is harmless; the POST requests still exercise the middleware.
Verification commands
uv run --extra lint ruff check app tests/unit
uv run pytest tests/unit -q
Day 10 result:
35 passed
Troubleshooting
000 — no server is listening, or startup has not completed.
404 — the server responded, but the requested route does not exist.
429 — the rate limiter rejected the request.
All GET requests return 200 — GET, HEAD and OPTIONS are deliberately exempt.
Alert status Closed — the alert fired successfully and later recovered.
No BigQuery rows — confirm BQ_ANALYTICS_ENABLED=true and the dataset location.
No traces — verify otel_to_cloud=True and allow several minutes for ingestion.
Production notes
The current limiter is in-memory and protects only one Python process. It is useful as a local safety layer, but it does not coordinate limits across multiple Cloud Run or GKE instances.
For distributed production rate limiting, use one of:
Cloud Armor
API Gateway or Apigee
Memorystore for Redis
A centralized quota service