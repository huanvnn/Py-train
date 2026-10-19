import os
import uvicorn

from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

agent = Agent(
    name="general_knowledge_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are a General Knowledge Agent.

    Answer questions using your built-in knowledge.

    Do not use project documentation.
    Keep answers concise and accurate.
    """
)

# Expose agent card and capability endpoints via A2A
host = os.environ.get("GENERAL_KNOWLEDGE_HOST", "agent-general-knowledge")
port = int(os.environ.get("GENERAL_KNOWLEDGE_PORT", 8004))
app = to_a2a(agent, host=host, port=port)

if __name__ == "__main__":
    port = int(os.environ.get("GENERAL_KNOWLEDGE_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)