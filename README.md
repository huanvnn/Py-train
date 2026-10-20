# Google ADK A2A Multi-Agent Chat Application

This project is a containerized local demo illustrating **Multi-Agent Collaboration** using the **Google ADK (Agent Development Kit)** and the open **A2A (Agent-to-Agent) protocol**.

## Architecture Overview

The system is split into five decoupled services:
1. **Frontend (React + Vite)**: A responsive chat interface providing live word-by-word streaming responses and typing indicator states. Communicates exclusively with the Gateway API.
2. **Gateway API (FastAPI)**: The central ingress web service. Exposes Server-Sent Events (SSE) streaming connections to clients and manages conversation thread memory.
3. **Coordinator Agent (Google ADK)**: The orchestrator specialist. Connects to sub-agents via the A2A protocol and manages query routing.
4. **Knowledge Agent (Google ADK)**: Performs lookup and scanning over local documentation resources mapped into the container volume.
5. **Summary Agent (Google ADK)**: Summarizes discussion threads and details.

All agents communicate natively over A2A endpoints wrapped via ADK, utilizing HTTP POST fallbacks for extreme reliability. Model Context Protocol (MCP) is prohibited.

---

## Quickstart Setup

### Prerequisites
- Docker and Docker Compose installed.
- A Google Gemini API Key.

### 1. Configure the Environment
Create a `.env` file in the project root:
```bash
# Add your Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here
CHAT_API_TOKEN=<generate-a-random-token-of-at-least-32-characters>
```

### 2. Start the Application Stack
Build the images and spin up all containers in a bridge network:
```bash
docker compose up --build
```

Once up, the services will run at:
- **React Frontend**: http://localhost:3000
- **FastAPI Gateway**: http://localhost:8000
- **Coordinator Agent**: http://localhost:8001
- **Knowledge Agent**: http://localhost:8002
- **Summary Agent**: http://localhost:8003

---

## Verification Scenarios

Refer to [quickstart.md](specs/001-a2a-ai-chat/quickstart.md) for direct curl scenarios, testing scripts, and output assertions.

### A2A Discovery Check
Verify the Knowledge agent card is exposed:
```bash
curl -f http://localhost:8002/.well-known/agent.json
```

### E2E Chat SSE Check
Stream chat completions from the FastAPI Gateway:
```bash
curl -N -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the project purpose?"}' \
  http://localhost:8000/api/chat/stream
```

---

## Troubleshooting

- **Agent Endpoint Offline Fallbacks**: If the Coordinator cannot reach the Knowledge or Summary agents, it yields a graceful fallback message: `Fallback answer (Knowledge Specialist endpoint down...)`.
- **Docker Mount Errors**: Verify that local paths are preserved. If the Knowledge Agent starts but cannot query documentation, ensure `agents/knowledge/data/project_info.txt` is mounted properly into the container's `/app/data/` workspace.

## Secure local access
Generate CHAT_API_TOKEN locally with Python: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Save it in the root .env, then paste it into the frontend Access token field. It is not the Gemini API key. Do not commit either secret. The gateway fails closed when the token is missing or shorter than 32 characters.

Only frontend and gateway ports are published, bound to localhost. Specialist URLs listed above are internal container endpoints; use `docker compose exec` for diagnostics. Direct API calls require `Authorization: Bearer <CHAT_API_TOKEN>`. Conversation reads, continuations and deletion additionally require `X-Session-Token`, issued by the stream's session event as JSON `{ "id": "...", "token": "..." }`.

The gateway accepts at most 20 chat requests/minute, 8 concurrent replies, 8,000 characters per prompt, and 32 KiB per request body. Run one gateway worker. See [Safety and privacy](SECURITY.md) for retention, acceptable use and reporting.

Run gateway regression tests from gateway: `python -m pytest -q` after installing requirements.txt.

## Knowledge RAG
The Knowledge Agent now chunks UTF-8 text/Markdown documents, caches Gemini embeddings in SQLite, retrieves semantic top-k evidence and generates answers with file/line citations. See [Knowledge Agent RAG](agents/knowledge/README.md) for indexing, settings and tests.
