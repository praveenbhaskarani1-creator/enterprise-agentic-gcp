"""MCP Toolbox configuration for read-only customer data access."""

import os

from toolbox_adk import ToolboxToolset

DEFAULT_TOOLBOX_SERVER_URL = "http://127.0.0.1:5000"
DEFAULT_TOOLBOX_TOOLSET_NAME = "customer-ops-readonly"


def create_customer_ops_toolset() -> ToolboxToolset:
    """Create the scoped read-only Toolbox toolset for the data agent."""
    return ToolboxToolset(
        server_url=os.getenv(
            "TOOLBOX_SERVER_URL",
            DEFAULT_TOOLBOX_SERVER_URL,
        ),
        toolset_name=os.getenv(
            "TOOLBOX_TOOLSET_NAME",
            DEFAULT_TOOLBOX_TOOLSET_NAME,
        ),
    )


customer_ops_mcp_toolset = create_customer_ops_toolset()
