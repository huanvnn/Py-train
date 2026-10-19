import pytest

def test_general_knowledge_agent():
    try:
        import agent
    except ImportError:
        pytest.fail("agent.py not implemented yet.")
        
    assert hasattr(agent, "answer_general_knowledge"), "agent.py must implement answer_general_knowledge function"
    
    # Test fallback query response
    res = agent.answer_general_knowledge("Explain microservice architecture.")
    assert "Microservice architecture" in res
    assert "Independent deployment" in res
