import os
import uvicorn
from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

def search_local_docs(query: str, mock_content: str = None) -> str:
    """Search local project documentation for matching terms and return context lines."""
    if mock_content is not None:
        content = mock_content
    else:
        # Resolve paths for both local and Docker Compose environments
        file_path = os.path.join(os.path.dirname(__file__), "data", "project_info.txt")
        if not os.path.exists(file_path):
            file_path = "/app/data/project_info.txt"
        if not os.path.exists(file_path):
            return "Error: local project_info.txt documentation not found."
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
    # Split content by markdown headings to parse sections
    sections = []
    current_section = []
    for line in content.split("\n"):
        if line.strip().startswith("#"):
            if current_section:
                sections.append("\n".join(current_section))
            current_section = [line]
        else:
            current_section.append(line)
    if current_section:
        sections.append("\n".join(current_section))

    # Search query words against each section
    matches = []
    query_words = [w.strip(".,;:?!") for w in query.lower().split()]
    query_words = [w for w in query_words if len(w) > 2]
    if not query_words:
        query_words = query.lower().split()
    
    for sec in sections:
        sec_lower = sec.lower()
        match_count = sum(1 for word in query_words if word in sec_lower)
        if match_count > 0:
            matches.append((match_count, sec))
            
    if not matches:
        import json
        return json.dumps({
            "status": "not_found"
        })
        
    # Return the section with the highest match score
    matches.sort(key=lambda x: x[0], reverse=True)
    return matches[0][1].strip()

# Instantiate the ADK Agent
agent = Agent(
    name="knowledge_agent",
    model="gemini-2.5-flash",
    instruction="""You are a Knowledge Agent.
You look up facts in local documentation using the search_local_docs tool.
If the search_local_docs tool returns '{"status": "not_found"}', you must output exactly '{"status": "not_found"}' without any other text or markdown formatting.
""",
    tools=[search_local_docs]
)

# Expose agent card and capability endpoints via A2A
host = os.environ.get("KNOWLEDGE_HOST", "agent-knowledge")
port = int(os.environ.get("KNOWLEDGE_PORT", 8002))
app = to_a2a(agent, host=host, port=port)

# Expose simple HTTP routing for direct endpoint execution using Starlette conventions
from starlette.responses import JSONResponse

async def run_direct(request):
    payload = await request.json()
    prompt = payload.get("prompt", "")
    res = search_local_docs(prompt)
    return JSONResponse({"result": res})

app.add_route("/run", run_direct, methods=["POST"])

if __name__ == "__main__":
    port = int(os.environ.get("KNOWLEDGE_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
