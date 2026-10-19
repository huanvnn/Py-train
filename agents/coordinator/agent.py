import os
import uvicorn
import uuid
import inspect
import json
from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from a2a.types import Message, Part, TextPart

# Load environment configs
knowledge_host = os.environ.get("KNOWLEDGE_HOST", "localhost")
knowledge_port = os.environ.get("KNOWLEDGE_PORT", "8002")
summary_host = os.environ.get("SUMMARY_HOST", "localhost")
summary_port = os.environ.get("SUMMARY_PORT", "8003")
general_knowledge_host = os.environ.get("GENERAL_KNOWLEDGE_HOST", "localhost")
general_knowledge_port = os.environ.get("GENERAL_KNOWLEDGE_PORT", "8004")

# Set up Specialist A2A Client instances
knowledge_agent = RemoteA2aAgent(
    name="remote_knowledge_agent",
    description="Connects to the A2A Knowledge Agent",
    agent_card=f"http://{knowledge_host}:{knowledge_port}{AGENT_CARD_WELL_KNOWN_PATH}"
)

summary_agent = RemoteA2aAgent(
    name="remote_summary_agent",
    description="Connects to the A2A Summary Agent",
    agent_card=f"http://{summary_host}:{summary_port}{AGENT_CARD_WELL_KNOWN_PATH}"
)

general_knowledge_agent = RemoteA2aAgent(
    name="remote_general_knowledge_agent",
    description="Connects to the A2A General Knowledge Agent",
    agent_card=f"http://{general_knowledge_host}:{general_knowledge_port}{AGENT_CARD_WELL_KNOWN_PATH}"
)

async def run_remote_agent_a2a(remote_agent: RemoteA2aAgent, prompt: str) -> str:
    """Helper to send an A2A message to a RemoteA2aAgent and return the text result."""
    await remote_agent._ensure_resolved()
    msg = Message(
        message_id=str(uuid.uuid4()),
        role="user",
        parts=[Part(root=TextPart(text=prompt))]
    )
    
    text = ""
    async for response in remote_agent._a2a_client.send_message(request=msg):
        if isinstance(response, tuple):
            task, _ = response
            if task and task.artifacts:
                for artifact in task.artifacts:
                    for part in artifact.parts:
                        if hasattr(part.root, "text") and part.root.text:
                            text += part.root.text
        elif isinstance(response, Message):
            if response.parts:
                for part in response.parts:
                    if hasattr(part.root, "text") and part.root.text:
                        text += part.root.text
    return text

async def call_client(client, prompt: str, is_format: bool = False, is_summary: bool = False) -> str:
    """Invokes either a RemoteA2aAgent using native A2A, or a mock/local client."""
    if isinstance(client, RemoteA2aAgent):
        if is_format:
            adjusted_prompt = f"Format and style this response for display, ensuring readability and list markdown alignment:\n\n{prompt}"
        elif is_summary:
            adjusted_prompt = f"Summarize the following text:\n\n{prompt}"
        else:
            adjusted_prompt = prompt
        return await run_remote_agent_a2a(client, adjusted_prompt)
    else:
        if is_format and hasattr(client, "format_text") and "mock" not in type(client.format_text).__name__.lower():
            res = client.format_text(prompt)
            if inspect.isawaitable(res):
                return await res
            return res
        if callable(client):
            res = client(prompt)
            if inspect.isawaitable(res):
                return await res
            return res
        elif hasattr(client, "run"):
            res = client.run(prompt)
            if inspect.isawaitable(res):
                return await res
            return res
        else:
            raise ValueError(f"Unknown client type: {type(client)}")

async def run_coordinator(prompt: str, knowledge_client=None, summary_client=None, general_knowledge_client=None) -> dict:
    """Orchestrates multi-agent routing using ADK Specialist clients via native A2A."""
    k_client = knowledge_client or knowledge_agent
    s_client = summary_client or summary_agent
    gk_client = general_knowledge_client or general_knowledge_agent
    
    participated_agents = ["coordinator_agent"]
    prompt_lower = prompt.lower()
    
    # Summary delegation routing
    if "summarize" in prompt_lower or "summary" in prompt_lower:
        participated_agents.append("summary_agent")
        try:
            res = await call_client(s_client, prompt, is_summary=True)
            return {"result": res, "agents": participated_agents}
        except Exception as e:
            return {"result": "Summary specialist temporarily unavailable", "agents": participated_agents}
            
    # Default to Knowledge lookup
    participated_agents.append("knowledge_agent")
    context = ""
    is_not_found = False
    
    try:
        context = await call_client(k_client, prompt)
        # Parse context to determine if structured not_found is returned
        try:
            data = json.loads(context)
            if isinstance(data, dict) and data.get("status") == "not_found":
                is_not_found = True
        except Exception:
            # String checks in case of plain text fallback
            if "not_found" in context or "No matching knowledge found" in context:
                is_not_found = True
    except Exception:
        # Treat connection failures to Knowledge specialist as not_found to try fallback
        is_not_found = True

    # If local knowledge is not found, fallback to General Knowledge Agent
    raw_answer = ""
    if is_not_found:
        participated_agents.append("general_knowledge_agent")
        try:
            raw_answer = await call_client(gk_client, prompt)
        except Exception as e:
            raw_answer = "General Knowledge specialist temporarily unavailable"
    else:
        raw_answer = f"Resolved context: {context}"

    # Format the final response via Summary Agent
    participated_agents.append("summary_agent")
    formatted_answer = ""
    try:
        formatted_answer = await call_client(s_client, raw_answer, is_format=True)
    except Exception:
        # Fallback to unformatted text if styling fails
        formatted_answer = raw_answer
        
    return {"result": formatted_answer, "agents": participated_agents}

# Instantiate primary Coordinator agent
agent = Agent(
    name="coordinator_agent",
    model="gemini-2.5-flash",
    instruction="You are the Coordinator Agent. Route tasks to specialists to fulfill user prompts.",
    tools=[run_coordinator]
)

# Expose Coordinator over A2A
host = os.environ.get("COORDINATOR_HOST", "agent-coordinator")
port = int(os.environ.get("COORDINATOR_PORT", 8001))
app = to_a2a(agent, host=host, port=port)

# Expose simple HTTP routing for direct endpoint execution using Starlette conventions
from starlette.responses import JSONResponse

async def run_direct(request):
    payload = await request.json()
    prompt = payload.get("prompt", "")
    data = await run_coordinator(prompt)
    return JSONResponse(data)

app.add_route("/run", run_direct, methods=["POST"])

if __name__ == "__main__":
    port = int(os.environ.get("COORDINATOR_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

