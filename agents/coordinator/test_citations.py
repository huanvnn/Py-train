"""Grounded RAG answers must reach the frontend without losing source citations."""
import asyncio
import json
from unittest.mock import AsyncMock
import agent


def test_grounded_answer_preserves_citations():
    answer = "React [1]\n\nSources:\n[1] ui.md, lines 1-2"
    summary, fallback = AsyncMock(), AsyncMock()
    result = asyncio.run(agent.run_coordinator(
        "Which interface?", AsyncMock(return_value=answer), summary, fallback,
    ))
    assert result["result"] == answer
    summary.assert_not_called()
    fallback.assert_not_called()


def test_no_evidence_retains_general_knowledge_fallback():
    fallback = AsyncMock(return_value="General answer")
    result = asyncio.run(agent.run_coordinator(
        "Unrelated question", AsyncMock(return_value=json.dumps({"status": "not_found"})),
        AsyncMock(return_value="General answer"), fallback,
    ))
    assert "general_knowledge_agent" in result["agents"]
    fallback.assert_awaited_once()