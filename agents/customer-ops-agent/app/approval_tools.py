"""Human-review tools for sensitive Customer Operations requests."""

from typing import Any

from google.adk.tools import FunctionTool

SUPPORTED_REVIEW_ACTIONS = {
    "account_closure",
    "jira_write",
    "payment_change",
    "privileged_export",
    "refund",
}


def stage_human_review_request(
    action_type: str,
    resource_id: str,
    justification: str,
) -> dict[str, Any]:
    """Stage a sensitive request for human review without executing it.

    Args:
        action_type: Allowlisted category of sensitive action.
        resource_id: Customer, order, ticket, account, or Jira identifier.
        justification: Business reason supplied for human review.

    Returns:
        A structured staging result. This never executes the requested
        business action and never represents human approval.
    """
    normalized_action = action_type.strip().lower()
    normalized_resource = resource_id.strip()
    normalized_justification = justification.strip()

    if normalized_action not in SUPPORTED_REVIEW_ACTIONS:
        return {
            "status": "rejected",
            "action_executed": False,
            "message": "Unsupported human-review action type.",
        }

    if not normalized_resource:
        return {
            "status": "rejected",
            "action_executed": False,
            "message": "A resource identifier is required.",
        }

    if len(normalized_justification) < 10:
        return {
            "status": "rejected",
            "action_executed": False,
            "message": "A meaningful justification is required.",
        }

    return {
        "status": "staged_for_human_review",
        "action_type": normalized_action,
        "resource_id": normalized_resource,
        "justification": normalized_justification,
        "authorized_human_approval": False,
        "action_executed": False,
        "message": (
            "The request was staged for review only. No business action "
            "was approved or executed."
        ),
    }


human_review_tool = FunctionTool(
    func=stage_human_review_request,
    require_confirmation=True,
)
