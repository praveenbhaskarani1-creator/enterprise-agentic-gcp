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

"""Unit tests for Customer Operations BigQuery tools using a mocked client."""

import datetime
from unittest.mock import MagicMock, patch

from google.adk.tools import AgentTool

from app.agent import root_agent
from app.tools import (
    DEFAULT_MAX_BYTES_BILLED,
    MAX_RESULT_LIMIT,
    get_customer_summary,
    get_open_support_tickets,
    get_recent_orders,
)


def _mock_query_job(rows: list[dict]):
    """Create a mock BigQuery QueryJob returning the given row dicts."""
    mock_job = MagicMock()

    class RowMock:
        def __init__(self, data: dict):
            self._data = data

        def keys(self):
            return self._data.keys()

        def items(self):
            return self._data.items()

        def __getitem__(self, item):
            return self._data[item]

        def __iter__(self):
            return iter(self._data)

    mock_rows = [RowMock(row) for row in rows]
    mock_job.__iter__.return_value = iter(mock_rows)
    return mock_job


@patch("app.tools.get_bigquery_client")
def test_get_customer_summary_success(mock_get_client):
    """Test get_customer_summary returns data when a customer is found."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    sample_customer = {
        "customer_id": "c1234567-89ab-cdef-0123-456789abcdef",
        "tenant_id": "t1234567-89ab-cdef-0123-456789abcdef",
        "external_customer_ref": "EXT-001",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "phone_number": "+15551234567",
        "company_name": "Acme Corp",
        "status": "active",
        "created_at": datetime.datetime(2026, 1, 1, 12, 0, 0),
        "updated_at": datetime.datetime(2026, 1, 2, 12, 0, 0),
    }

    mock_client.query.return_value = _mock_query_job([sample_customer])

    result = get_customer_summary(
        "c1234567-89ab-cdef-0123-456789abcdef"
    )

    assert result["status"] == "success"
    assert result["count"] == 1
    assert (
        result["data"][0]["customer_id"]
        == "c1234567-89ab-cdef-0123-456789abcdef"
    )
    assert result["data"][0]["first_name"] == "Jane"
    assert result["data"][0]["created_at"] == "2026-01-01T12:00:00"

    mock_client.query.assert_called_once()
    called_query, called_kwargs = mock_client.query.call_args
    assert "curated.customers" in called_query[0]
    job_config = called_kwargs["job_config"]
    assert job_config.maximum_bytes_billed == DEFAULT_MAX_BYTES_BILLED
    params = {p.name: p.value for p in job_config.query_parameters}
    assert params["customer_id"] == "c1234567-89ab-cdef-0123-456789abcdef"
    assert params["limit"] == MAX_RESULT_LIMIT


@patch("app.tools.get_bigquery_client")
def test_get_customer_summary_not_found(mock_get_client):
    """Test get_customer_summary reports when no records exist."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.query.return_value = _mock_query_job([])

    result = get_customer_summary("nonexistent-id")

    assert result["status"] == "not_found"
    assert "No customer found with customer_id 'nonexistent-id'" in result["message"]
    assert result["data"] == []


@patch("app.tools.get_bigquery_client")
def test_get_recent_orders_success(mock_get_client):
    """Test get_recent_orders returns recent orders for a customer."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    sample_order = {
        "order_id": "o1234567-89ab-cdef-0123-456789abcdef",
        "tenant_id": "t1234567-89ab-cdef-0123-456789abcdef",
        "customer_id": "c1234567-89ab-cdef-0123-456789abcdef",
        "order_number": "ORD-1001",
        "order_status": "delivered",
        "total_amount": 159.99,
        "currency": "USD",
        "shipping_address_masked": "123 Main St, ***",
        "ordered_at": datetime.datetime(2026, 2, 1, 10, 30, 0),
        "promised_delivery_at": datetime.datetime(2026, 2, 5, 18, 0, 0),
        "created_at": datetime.datetime(2026, 2, 1, 10, 30, 0),
        "updated_at": datetime.datetime(2026, 2, 5, 14, 0, 0),
    }

    mock_client.query.return_value = _mock_query_job([sample_order])

    result = get_recent_orders(
        "c1234567-89ab-cdef-0123-456789abcdef"
    )

    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["data"][0]["order_number"] == "ORD-1001"
    assert result["data"][0]["order_status"] == "delivered"

    called_query, called_kwargs = mock_client.query.call_args
    assert "curated.orders" in called_query[0]
    job_config = called_kwargs["job_config"]
    assert job_config.maximum_bytes_billed == DEFAULT_MAX_BYTES_BILLED
    params = {p.name: p.value for p in job_config.query_parameters}
    assert params["customer_id"] == "c1234567-89ab-cdef-0123-456789abcdef"
    assert params["limit"] == MAX_RESULT_LIMIT


@patch("app.tools.get_bigquery_client")
def test_get_recent_orders_not_found(mock_get_client):
    """Test get_recent_orders reports when no records exist."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.query.return_value = _mock_query_job([])

    result = get_recent_orders("no-order-customer")

    assert result["status"] == "not_found"
    assert (
        "No recent orders found for customer_id 'no-order-customer'"
        in result["message"]
    )
    assert result["data"] == []


@patch("app.tools.get_bigquery_client")
def test_get_open_support_tickets_success(mock_get_client):
    """Test get_open_support_tickets returns open tickets for a customer."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    sample_ticket = {
        "support_ticket_id": "st123456-89ab-cdef-0123-456789abcdef",
        "tenant_id": "t1234567-89ab-cdef-0123-456789abcdef",
        "customer_id": "c1234567-89ab-cdef-0123-456789abcdef",
        "order_id": "o1234567-89ab-cdef-0123-456789abcdef",
        "ticket_number": "TKT-5001",
        "subject": "Delayed Delivery Inquiry",
        "priority": "high",
        "status": "open",
        "category": "order_status",
        "created_at": datetime.datetime(2026, 2, 2, 8, 0, 0),
        "updated_at": datetime.datetime(2026, 2, 2, 9, 15, 0),
    }

    mock_client.query.return_value = _mock_query_job([sample_ticket])

    result = get_open_support_tickets(
        "c1234567-89ab-cdef-0123-456789abcdef"
    )

    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["data"][0]["ticket_number"] == "TKT-5001"
    assert result["data"][0]["status"] == "open"

    called_query, called_kwargs = mock_client.query.call_args
    assert "curated.support_tickets" in called_query[0]
    assert "status IN ('open', 'pending')" in called_query[0]
    job_config = called_kwargs["job_config"]
    assert job_config.maximum_bytes_billed == DEFAULT_MAX_BYTES_BILLED


@patch("app.tools.get_bigquery_client")
def test_get_open_support_tickets_not_found(mock_get_client):
    """Test get_open_support_tickets reports when no records exist."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.query.return_value = _mock_query_job([])

    result = get_open_support_tickets("no-ticket-customer")

    assert result["status"] == "not_found"
    assert (
        "No open support tickets found for customer_id 'no-ticket-customer'"
        in result["message"]
    )
    assert result["data"] == []


def test_agent_structure_and_instructions():
    """Test explicit specialist orchestration and safeguards."""
    assert root_agent.name == "root_agent"
    assert len(root_agent.sub_agents) == 0
    assert len(root_agent.tools) == 2
    assert all(isinstance(tool, AgentTool) for tool in root_agent.tools)

    specialist_agents = {
        tool.agent.name: tool.agent for tool in root_agent.tools
    }
    assert set(specialist_agents) == {
        "customer_data_agent",
        "policy_agent",
    }

    customer_data_agent = specialist_agents["customer_data_agent"]
    data_tool_names = [
        tool.__name__ for tool in customer_data_agent.tools
    ]
    assert data_tool_names == [
        "get_customer_summary",
        "get_recent_orders",
        "get_open_support_tickets",
    ]

    policy_agent = specialist_agents["policy_agent"]
    policy_tool_names = [
        tool.__name__ for tool in policy_agent.tools
    ]
    assert policy_tool_names == ["search_customer_ops_policies"]

    supervisor_instruction = root_agent.instruction.lower()
    assert "supervisor" in supervisor_instruction
    assert "call" in supervisor_instruction
    assert "read-only" in supervisor_instruction
    assert "forbidden" in supervisor_instruction
    assert "payment" in supervisor_instruction
    assert "invent" in supervisor_instruction

    data_instruction = customer_data_agent.instruction.lower()
    assert "read-only" in data_instruction
    assert "never write" in data_instruction

    policy_instruction = policy_agent.instruction.lower()
    assert "read-only" in policy_instruction
    assert "source uri" in policy_instruction
    assert "human" in policy_instruction
