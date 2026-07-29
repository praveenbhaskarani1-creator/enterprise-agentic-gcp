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

"""Read-only BigQuery tools for Customer Operations Agent."""

import datetime
import decimal
import os
import uuid
from typing import Any

from google.cloud import bigquery

# Default constants
DEFAULT_PROJECT_ID = "agentic-erp-502706"
DEFAULT_DATASET = "curated"
DEFAULT_MAX_BYTES_BILLED = 100 * 1024 * 1024  # 100 MB limit
MAX_RESULT_LIMIT = 20


def get_bigquery_config() -> tuple[str, str | None]:
    """Get BigQuery project ID and location from environment configuration."""
    project_id = (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("BIGQUERY_PROJECT_ID")
        or os.getenv("PROJECT_ID")
        or DEFAULT_PROJECT_ID
    )
    location = (
        os.getenv("GOOGLE_CLOUD_LOCATION")
        or os.getenv("BIGQUERY_LOCATION")
        or os.getenv("LOCATION")
        or os.getenv("GOOGLE_CLOUD_REGION")
    )
    return project_id, location


def get_bigquery_client() -> bigquery.Client:
    """Instantiate a BigQuery client using configuration from environment."""
    project_id, location = get_bigquery_config()
    if location:
        return bigquery.Client(project=project_id, location=location)
    return bigquery.Client(project=project_id)


def _format_value(val: Any) -> Any:
    """Format row field values into JSON-serializable types."""
    if val is None:
        return None
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, uuid.UUID):
        return str(val)
    return val


def _format_row(row_dict: dict[str, Any]) -> dict[str, Any]:
    """Format row dictionary into JSON-serializable types."""
    return {k: _format_value(v) for k, v in row_dict.items()}


def get_customer_summary(customer_id: str) -> dict[str, Any]:
    """Retrieve customer summary by customer ID from curated BigQuery dataset.

    Args:
        customer_id: The UUID or unique identifier of the customer.

    Returns:
        Structured result containing customer details or notification if no record exists.
    """
    client = get_bigquery_client()
    project_id, _ = get_bigquery_config()
    table_name = f"`{project_id}.{DEFAULT_DATASET}.customers`"

    query = f"""
        SELECT
            customer_id,
            tenant_id,
            external_customer_ref,
            first_name,
            last_name,
            email,
            phone_number,
            company_name,
            status,
            created_at,
            updated_at
        FROM {table_name}
        WHERE customer_id = @customer_id
        LIMIT @limit
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
            bigquery.ScalarQueryParameter("limit", "INT64", MAX_RESULT_LIMIT),
        ],
        maximum_bytes_billed=DEFAULT_MAX_BYTES_BILLED,
    )

    query_job = client.query(query, job_config=job_config)
    results = [_format_row(dict(row)) for row in query_job]

    if not results:
        return {
            "status": "not_found",
            "message": f"No customer found with customer_id '{customer_id}'.",
            "data": [],
        }

    return {
        "status": "success",
        "count": len(results),
        "data": results,
    }


def get_recent_orders(customer_id: str) -> dict[str, Any]:
    """Retrieve recent orders by customer ID from curated BigQuery dataset.

    Args:
        customer_id: The UUID or unique identifier of the customer.

    Returns:
        Structured result containing order list or notification if no record exists.
    """
    client = get_bigquery_client()
    project_id, _ = get_bigquery_config()
    table_name = f"`{project_id}.{DEFAULT_DATASET}.orders`"

    query = f"""
        SELECT
            order_id,
            tenant_id,
            customer_id,
            order_number,
            order_status,
            total_amount,
            currency,
            shipping_address_masked,
            ordered_at,
            promised_delivery_at,
            created_at,
            updated_at
        FROM {table_name}
        WHERE customer_id = @customer_id
        ORDER BY ordered_at DESC
        LIMIT @limit
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
            bigquery.ScalarQueryParameter("limit", "INT64", MAX_RESULT_LIMIT),
        ],
        maximum_bytes_billed=DEFAULT_MAX_BYTES_BILLED,
    )

    query_job = client.query(query, job_config=job_config)
    results = [_format_row(dict(row)) for row in query_job]

    if not results:
        return {
            "status": "not_found",
            "message": f"No recent orders found for customer_id '{customer_id}'.",
            "data": [],
        }

    return {
        "status": "success",
        "count": len(results),
        "data": results,
    }


def get_open_support_tickets(customer_id: str) -> dict[str, Any]:
    """Retrieve open support tickets by customer ID from curated BigQuery dataset.

    Args:
        customer_id: The UUID or unique identifier of the customer.

    Returns:
        Structured result containing open support tickets or notification if no record exists.
    """
    client = get_bigquery_client()
    project_id, _ = get_bigquery_config()
    table_name = f"`{project_id}.{DEFAULT_DATASET}.support_tickets`"

    query = f"""
        SELECT
            support_ticket_id,
            tenant_id,
            customer_id,
            order_id,
            ticket_number,
            subject,
            priority,
            status,
            category,
            created_at,
            updated_at
        FROM {table_name}
        WHERE customer_id = @customer_id
          AND status IN ('open', 'pending')
        ORDER BY created_at DESC
        LIMIT @limit
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
            bigquery.ScalarQueryParameter("limit", "INT64", MAX_RESULT_LIMIT),
        ],
        maximum_bytes_billed=DEFAULT_MAX_BYTES_BILLED,
    )

    query_job = client.query(query, job_config=job_config)
    results = [_format_row(dict(row)) for row in query_job]

    if not results:
        return {
            "status": "not_found",
            "message": f"No open support tickets found for customer_id '{customer_id}'.",
            "data": [],
        }

    return {
        "status": "success",
        "count": len(results),
        "data": results,
    }
