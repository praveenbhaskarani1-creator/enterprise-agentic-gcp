"""Unit tests for the read-only RAG policy tool."""

from types import SimpleNamespace
from unittest.mock import Mock

import app.rag_tools as rag_tools


def test_empty_query_is_rejected():
    result = rag_tools.search_customer_ops_policies("   ")

    assert result["status"] == "invalid_argument"


def test_missing_corpus_configuration(monkeypatch):
    monkeypatch.delenv("RAG_CORPUS_RESOURCE", raising=False)

    result = rag_tools.search_customer_ops_policies("What is the return policy?")

    assert result["status"] == "configuration_error"


def test_top_k_is_bounded(monkeypatch):
    monkeypatch.setenv("RAG_CORPUS_RESOURCE", "projects/test/corpus")
    monkeypatch.setenv("RAG_TOP_K", "999")

    *_, top_k = rag_tools.get_rag_config()

    assert top_k == rag_tools.MAX_TOP_K


def test_successful_policy_retrieval(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("RAG_CORPUS_RESOURCE", "projects/test/corpus")
    monkeypatch.setenv("RAG_LOCATION", "us-central1")

    context = SimpleNamespace(
        source_uri="gs://test/returns.md",
        source_display_name="returns.md",
        text="Returns are allowed within 30 calendar days.",
        score=0.2,
    )
    response = SimpleNamespace(
        contexts=SimpleNamespace(contexts=[context]),
    )

    retrieve_contexts = Mock(return_value=response)
    fake_client = SimpleNamespace(
        rag=SimpleNamespace(retrieve_contexts=retrieve_contexts),
    )
    client_factory = Mock(return_value=fake_client)
    monkeypatch.setattr(rag_tools.agentplatform, "Client", client_factory)

    result = rag_tools.search_customer_ops_policies(
        "When can I return an item?"
    )

    assert result["status"] == "success"
    assert result["result_count"] == 1
    assert result["results"][0]["source_display_name"] == "returns.md"
    assert result["results"][0]["score"] == 0.2
    client_factory.assert_called_once_with(
        project="test-project",
        location="us-central1",
    )
    retrieve_contexts.assert_called_once()


def test_retrieval_failure_is_sanitized(monkeypatch):
    monkeypatch.setenv("RAG_CORPUS_RESOURCE", "projects/test/corpus")

    client_factory = Mock(side_effect=RuntimeError("internal details"))
    monkeypatch.setattr(rag_tools.agentplatform, "Client", client_factory)

    result = rag_tools.search_customer_ops_policies(
        "What is the privacy policy?"
    )

    assert result == {
        "status": "error",
        "message": "Approved policy retrieval is temporarily unavailable.",
    }
