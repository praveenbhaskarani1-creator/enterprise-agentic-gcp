"""Read-only Agent Platform RAG tools for Customer Operations."""

import logging
import os
from typing import Any

import agentplatform
from agentplatform import types as agentplatform_types
from google.genai import types as genai_types

LOGGER = logging.getLogger(__name__)

DEFAULT_PROJECT_ID = "agentic-erp-502706"
DEFAULT_RAG_LOCATION = "us-central1"
DEFAULT_TOP_K = 3
MAX_TOP_K = 5


def get_rag_config() -> tuple[str, str, str, int]:
    """Read RAG Engine settings without reusing the Gemini model location."""
    project_id = (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("PROJECT_ID")
        or DEFAULT_PROJECT_ID
    )
    location = os.getenv("RAG_LOCATION") or DEFAULT_RAG_LOCATION
    corpus_resource = os.getenv("RAG_CORPUS_RESOURCE", "").strip()

    try:
        top_k = int(os.getenv("RAG_TOP_K", str(DEFAULT_TOP_K)))
    except ValueError:
        top_k = DEFAULT_TOP_K

    top_k = max(1, min(top_k, MAX_TOP_K))
    return project_id, location, corpus_resource, top_k


def search_customer_ops_policies(query: str) -> dict[str, Any]:
    """Search approved policies and support runbooks.

    Use this read-only tool for questions about returns, refunds, privacy,
    escalation priorities, support procedures, and human-approval requirements.
    """
    normalized_query = query.strip()
    if not normalized_query:
        return {
            "status": "invalid_argument",
            "message": "A non-empty policy question is required.",
        }

    project_id, location, corpus_resource, top_k = get_rag_config()
    if not corpus_resource:
        return {
            "status": "configuration_error",
            "message": "The approved policy corpus is not configured.",
        }

    try:
        client = agentplatform.Client(project=project_id, location=location)
        response = client.rag.retrieve_contexts(
            vertex_rag_store=genai_types.VertexRagStore(
                rag_resources=[
                    genai_types.VertexRagStoreRagResource(
                        rag_corpus=corpus_resource,
                    )
                ],
            ),
            query=agentplatform_types.RagQuery(
                text=normalized_query,
                rag_retrieval_config=genai_types.RagRetrievalConfig(
                    top_k=top_k,
                ),
            ),
        )
    except Exception:
        LOGGER.exception("RAG Engine retrieval failed")
        return {
            "status": "error",
            "message": "Approved policy retrieval is temporarily unavailable.",
        }

    rag_contexts = getattr(response, "contexts", None)
    contexts = getattr(rag_contexts, "contexts", None) or []

    results = [
        {
            "source_uri": getattr(context, "source_uri", ""),
            "source_display_name": getattr(
                context,
                "source_display_name",
                "",
            ),
            "text": getattr(context, "text", ""),
            "score": getattr(context, "score", None),
        }
        for context in contexts
    ]

    if not results:
        return {
            "status": "not_found",
            "query": normalized_query,
            "message": "No relevant approved policy passages were found.",
            "results": [],
        }

    return {
        "status": "success",
        "query": normalized_query,
        "result_count": len(results),
        "results": results,
    }
