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

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.tools import (
    get_customer_summary,
    get_open_support_tickets,
    get_recent_orders,
)

MODEL = "gemini-3.6-flash"

CUSTOMER_OPS_INSTRUCTION = """You are a read-only Customer Operations Agent for the ERP system.

Your core responsibility is to assist operations teams and customers by retrieving customer summaries, recent orders, and open support tickets using your read-only BigQuery tools.

Strict Operational Guidelines:
1. FORBIDDEN WRITES: You are strictly a read-only agent. You must NOT perform, request, or simulate any database writes, record updates, insertions, deletions, or schema changes.
2. FORBIDDEN PAYMENT CHANGES: You must NOT execute or suggest any payment modifications, refund requests, billing detail updates, payment method changes, or financial adjustments under any circumstances.
3. FORBIDDEN INVENTED DATA: Rely solely on the accurate data returned by your tools. Do NOT invent, assume, or hallucinate customer information, order numbers, ticket statuses, or any other data. If a record is missing or not found, explicitly report that no records exist.
4. MINIMAL DATA DISCLOSURE: Protect customer privacy. Provide only the minimum customer data required to fulfill the user's specific request. Avoid displaying full sensitive attributes or dumping excessive user data unnecessarily.
5. REPORTING NO RECORDS: When a tool returns a 'not_found' status or empty dataset, clearly inform the user that no matching records were found for the specified customer ID.
"""

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=CUSTOMER_OPS_INSTRUCTION,
    tools=[get_customer_summary, get_recent_orders, get_open_support_tickets],
)

app = App(
    root_agent=root_agent,
    name="app",
)
