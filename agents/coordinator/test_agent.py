import pytest
import json
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_coordinator_agent_normal_flow():
    try:
        import agent
    except ImportError:
        pytest.fail("agent.py not implemented yet.")
        
    assert hasattr(agent, "run_coordinator"), "agent.py must implement run_coordinator function"
    
    # Mock specialists answers
    mock_knowledge = AsyncMock(return_value="React + Vite frontend.")
    mock_summary = AsyncMock(return_value="React + Vite frontend.")  # format_text returns it
    mock_gk = AsyncMock(return_value="General Answer")
    
    res = await agent.run_coordinator("What is the frontend?", mock_knowledge, mock_summary, mock_gk)
    assert isinstance(res, dict)
    assert "React" in res["result"]
    assert "coordinator_agent" in res["agents"]
    assert "knowledge_agent" in res["agents"]
    assert "summary_agent" in res["agents"]
    assert "general_knowledge_agent" not in res["agents"]

@pytest.mark.asyncio
async def test_coordinator_agent_fallback_flow():
    try:
        import agent
    except ImportError:
        pytest.fail("agent.py not implemented yet.")
        
    # Mock knowledge returns structured not_found JSON
    not_found_response = json.dumps({"status": "not_found"})
    mock_knowledge = AsyncMock(return_value=not_found_response)
    mock_summary = AsyncMock(return_value="Factual answer about HTTPS.")
    mock_gk = AsyncMock(return_value="HTTPS is secure HTTP.")
    
    res = await agent.run_coordinator("Explain HTTPS.", mock_knowledge, mock_summary, mock_gk)
    assert isinstance(res, dict)
    assert "HTTPS" in res["result"]
    assert "coordinator_agent" in res["agents"]
    assert "knowledge_agent" in res["agents"]
    assert "general_knowledge_agent" in res["agents"]
    assert "summary_agent" in res["agents"]

@pytest.mark.asyncio
async def test_coordinator_agent_summary_flow():
    try:
        import agent
    except ImportError:
        pytest.fail("agent.py not implemented yet.")
        
    mock_knowledge = AsyncMock(return_value="React + Vite frontend.")
    mock_summary = AsyncMock(return_value="Summary of discussion.")
    mock_gk = AsyncMock(return_value="General Answer")
    
    res = await agent.run_coordinator("Please summarize the project purpose.", mock_knowledge, mock_summary, mock_gk)
    assert isinstance(res, dict)
    assert "Summary" in res["result"]
    assert "coordinator_agent" in res["agents"]
    assert "summary_agent" in res["agents"]
    assert "knowledge_agent" not in res["agents"]
    assert "general_knowledge_agent" not in res["agents"]

