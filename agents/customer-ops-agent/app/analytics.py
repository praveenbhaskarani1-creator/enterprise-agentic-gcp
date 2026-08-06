"""BigQuery Agent Analytics configuration."""

import os

from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)

_TRUE_VALUES = {"1", "true", "yes", "on"}


def analytics_enabled() -> bool:
    """Return whether BigQuery Agent Analytics is enabled."""
    return (
        os.getenv("BQ_ANALYTICS_ENABLED", "false").strip().lower()
        in _TRUE_VALUES
    )


def build_agent_analytics_plugins() -> list[BigQueryAgentAnalyticsPlugin]:
    """Build the optional BigQuery Agent Analytics plugin."""
    if not analytics_enabled():
        return []

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT is required when analytics is enabled."
        )

    dataset_id = os.getenv(
        "BQ_ANALYTICS_DATASET_ID",
        "agent_analytics",
    )
    table_id = os.getenv(
        "BQ_ANALYTICS_TABLE_ID",
        "agent_events",
    )
    location = (
        os.getenv("BQ_ANALYTICS_LOCATION")
        or os.getenv("BIGQUERY_LOCATION")
        or "us-central1"
    )

    config = BigQueryLoggerConfig(
        enabled=True,
        table_id=table_id,
        max_content_length=64 * 1024,
        log_multi_modal_content=False,
        batch_size=1,
        log_session_metadata=True,
        auto_schema_upgrade=True,
        create_views=True,
        enable_otel_correlation=True,
        custom_tags={
            "application": "customer-ops-agent",
            "environment": os.getenv("APP_ENV", "dev"),
        },
    )

    return [
        BigQueryAgentAnalyticsPlugin(
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
            config=config,
            location=location,
        )
    ]
