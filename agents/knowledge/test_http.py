"""HTTP/A2A application smoke tests with no real model calls."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.testclient import TestClient
import agent
from rag import GeminiBackend


@pytest.fixture
def client():
    with TestClient(agent.app) as client:
        yield client


def test_direct_endpoint_uses_grounded_answer(client, monkeypatch):
    answer = AsyncMock(return_value="React. [1]\n\nSources:\n[1] ui.md, lines 1-2")
    monkeypatch.setattr(agent, "answer_from_documents", answer)
    result = client.post("/run", json={"prompt": "Which interface?"})
    assert result.status_code == 200
    assert "Sources:" in result.json()["result"]
    answer.assert_awaited_once_with("Which interface?")


def test_direct_endpoint_validates_input(client):
    for payload in ({}, {"prompt": " "}, {"prompt": "x" * 8001}, ["not-a-dict"]):
        assert client.post("/run", json=payload).status_code == 400
    assert client.post("/run", content=b"{broken").status_code == 400
    assert client.post("/run", content=b"x" * 32769).status_code == 413


def test_direct_endpoint_redacts_backend_errors(client, monkeypatch):
    monkeypatch.setattr(agent, "answer_from_documents", AsyncMock(side_effect=RuntimeError("private-key")))
    result = client.post("/run", json={"prompt": "interface"})
    assert result.status_code == 503
    assert "private-key" not in result.text


def test_embedding_and_generation_sdk_configuration(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-not-a-real-key")
    fake = MagicMock()
    fake.models.embed_content.return_value.embeddings = [MagicMock(values=[1, 0, 0])]
    fake.models.generate_content.return_value.text = "React [1]"
    with patch("google.genai.Client", return_value=fake):
        backend = GeminiBackend()
        assert backend.embed(["React"], "RETRIEVAL_DOCUMENT") == [[1, 0, 0]]
        call = fake.models.embed_content.call_args.kwargs
        assert call["config"].task_type == "RETRIEVAL_DOCUMENT"
        assert call["config"].output_dimensionality == 768
        assert backend.generate("question", [{"citation": 1, "text": "React"}]) == "React [1]"
        assert fake.models.generate_content.call_args.kwargs["config"].temperature == 0