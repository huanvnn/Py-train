import pytest

def test_summary_agent():
    # Attempt to import agent logic (which will fail initially in TDD)
    try:
        import agent
    except ImportError:
        pytest.fail("agent.py not implemented yet (TDD Red stage).")
        
    assert hasattr(agent, "summarize_text"), "agent.py must implement summarize_text capability"
    
    test_text = "User asks about A2A setup. Knowledge agent replies with ADK. Gateway streams response."
    summary = agent.summarize_text(test_text)
    assert len(summary) > 0
    assert "summary" in summary.lower() or len(summary) < len(test_text)
