"""Unit tests for human-review staging guardrails."""

from app.approval_tools import (
    human_review_tool,
    stage_human_review_request,
)


def test_human_review_tool_requires_confirmation():
    """Require confirmation before the staging function executes."""
    assert human_review_tool._require_confirmation is True


def test_valid_request_is_staged_but_not_executed():
    """Stage an allowlisted request without approving its action."""
    result = stage_human_review_request(
        action_type="refund",
        resource_id="ORDER-123",
        justification="Customer reports a defective product.",
    )

    assert result["status"] == "staged_for_human_review"
    assert result["authorized_human_approval"] is False
    assert result["action_executed"] is False
    assert "No business action" in result["message"]


def test_unsupported_action_is_rejected():
    """Reject requests outside the approved review categories."""
    result = stage_human_review_request(
        action_type="delete_database",
        resource_id="customer_ops",
        justification="Attempt to bypass the approved action list.",
    )

    assert result["status"] == "rejected"
    assert result["action_executed"] is False


def test_missing_resource_id_is_rejected():
    """Require the target resource before staging review."""
    result = stage_human_review_request(
        action_type="jira_write",
        resource_id=" ",
        justification="Update the referenced Jira issue after review.",
    )

    assert result["status"] == "rejected"
    assert result["action_executed"] is False


def test_short_justification_is_rejected():
    """Require a meaningful business justification."""
    result = stage_human_review_request(
        action_type="account_closure",
        resource_id="ACCOUNT-123",
        justification="Close it",
    )

    assert result["status"] == "rejected"
    assert result["action_executed"] is False
