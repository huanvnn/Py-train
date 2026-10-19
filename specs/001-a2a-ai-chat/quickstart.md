# Quickstart Validation Guide: Google ADK A2A Chat

This guide outlines the commands to spin up the application stack and validate its functionalities end-to-end.

## Prerequisites
- Docker & Docker Compose installed locally.
- Google Gemini API Key (set as `GEMINI_API_KEY` in root `.env` file).

## Startup Procedure

1. **Configure Environment**:
   Create a `.env` file in the project root:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

2. **Start Application Stack**:
   Run Docker Compose to build and start the Gateway, Agents, and React Frontend:
   ```bash
   docker compose up --build
   ```

3. **Verify running containers**:
   Ensure all 5 services are healthy and running:
   - `frontend` at port `3000` (http://localhost:3000)
   - `gateway` at port `8000` (http://localhost:8000)
   - `agent-coordinator` at port `8001` (A2A endpoint)
   - `agent-knowledge` at port `8002` (A2A endpoint)
   - `agent-summary` at port `8003` (A2A endpoint)

---

## Validation Scenarios

### Scenario 1: Validate A2A Agent Card Discovery
To verify that agents expose their well-known A2A discovery JSON properly:
```bash
curl -f http://localhost:8002/.well-known/agent.json
```
**Expected Outcome**:
A JSON payload containing the Knowledge Agent's capabilities (e.g. `search`), endpoints, and name.

### Scenario 2: Validate End-to-End Chat SSE Streaming via Gateway
Submit a chat message to the gateway and stream the Server-Sent Events output:
```bash
curl -N -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the project purpose?"}' \
  http://localhost:8000/api/chat/stream
```
**Expected Outcome**:
A series of SSE data chunks containing the streaming text response, integrating retrieved details from the Knowledge Agent:
```text
data: {"content": "This "}
data: {"content": "project "}
data: {"content": "demonstrates "}
...
```

### Scenario 3: Verify Discussion Summary Route
Ask for a summary of the chat to trigger A2A routing to the Summary Agent:
```bash
curl -N -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "Please summarize our chat so far."}' \
  http://localhost:8000/api/chat/stream
```
**Expected Outcome**:
The Coordinator delegates to the Summary Agent over A2A, generating and streaming back a brief summary block.

---

## Running Automated Tests

To validate individual services locally, run python tests inside the gateway or agent directories:
```bash
# Verify gateway routing and mocking
cd gateway
pytest

# Verify agent A2A endpoints and logic
cd ../agents/coordinator
pytest
```
