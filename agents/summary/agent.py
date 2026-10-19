import os
import uvicorn
from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

def summarize_text(text: str) -> str:
    """Generate a brief summary of the conversation text."""
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    if not sentences:
        return "Empty thread."
    # Direct algorithmic summary representation for demo local verification
    return f"Summary: User discussed: '{sentences[0]}'."

def format_text(text: str) -> str:
    """Format and style a response for display, ensuring readability and list markdown alignment."""
    # Trims whitespaces and returns clean formatted text
    return text.strip()

# Instantiate the ADK Agent
agent = Agent(
    name="summary_agent",
    model="gemini-2.5-flash",
    instruction="You are a Summary Agent. You summarize text using the summarize_text tool and format answers using the format_text tool.",
    tools=[summarize_text, format_text]
)

# Expose agent via A2A
host = os.environ.get("SUMMARY_HOST", "agent-summary")
port = int(os.environ.get("SUMMARY_PORT", 8003))
app = to_a2a(agent, host=host, port=port)

# Expose simple HTTP routing for direct endpoint execution using Starlette conventions
from starlette.responses import JSONResponse

async def run_direct(request):
    payload = await request.json()
    prompt = payload.get("prompt", "")
    res = summarize_text(prompt)
    return JSONResponse({"result": res})

async def format_direct(request):
    payload = await request.json()
    prompt = payload.get("prompt", "")
    res = format_text(prompt)
    return JSONResponse({"result": res})

app.add_route("/run", run_direct, methods=["POST"])
app.add_route("/format", format_direct, methods=["POST"])

if __name__ == "__main__":
    port = int(os.environ.get("SUMMARY_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
