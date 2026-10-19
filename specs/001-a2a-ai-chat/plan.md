# Implementation Plan: Google ADK Agent-to-Agent Chat

**Branch**: `001-a2a-ai-chat` | **Date**: 2026-06-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-a2a-ai-chat/spec.md`

## Summary
The goal of this project is to implement a local, containerized AI chat demo illustrating Multi-Agent Collaboration using the **Google ADK** (Agent Development Kit) and the **A2A protocol** (Agent-to-Agent protocol). 
The React + Vite frontend communicates *only* with a FastAPI gateway. The Gateway routes chat prompts to the **Coordinator Agent** via an HTTP client. The Coordinator Agent acts as the central orchestrator, delegating information retrieval to the **Knowledge Agent** (local files lookup). If the local Knowledge Agent cannot find relevant information (returning a structured `not_found` response), the Coordinator automatically falls back and routes to the **General Knowledge Agent** (which answers using general LLM knowledge). The raw response from either agent is then routed to the **Summary Agent** for markdown list formatting and returned. The Gateway streams the result back to the frontend in real-time via Server-Sent Events (SSE) alongside metadata showing which agents participated in the conversation.

## Technical Context

**Language/Version**: Python 3.11 (Gateway, Agents), Node.js 18+ (React Frontend)

**Primary Dependencies**: 
- Gateway & Agents: `fastapi`, `uvicorn`, `google-adk`, `sse-starlette`, `httpx`, `pytest`, `pytest-asyncio`
- Frontend: `react`, `react-dom`, `vite`

**Storage**: Local files mapped into the Knowledge Agent container (`agents/knowledge/data/` pre-seeded text/markdown files). No database is needed for the MVP.

**Testing**: `pytest` for all backend services (fastapi gateway + A2A agents).

**Target Platform**: Local environment running via `docker-compose.yml`.

**Project Type**: Multi-container web application and decoupled agent servers.

**Performance Goals**: SSE response start < 1.5 seconds, A2A messaging overhead < 300ms.

**Constraints**:
- Frontend MUST only query FastAPI gateway. Direct access to agents is prohibited.
- MCP (Model Context Protocol) is prohibited. All inter-agent requests must use Google ADK A2A.
- Running natively inside Docker containers with Docker Compose.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Mandatory Multi-Agent Architecture**: Does the system use a multi-agent architecture where the frontend only speaks to the Gateway API, and A2A is used for agent communication (no MCP)? *(Yes. The entry is FastAPI gateway, agents talk via A2A protocol.)*
- [x] **II. A2A Communication Endpoint**: Do all agents expose an A2A server endpoint? *(Yes. Coordinator, Knowledge, Summary, and General Knowledge agents run A2A server interfaces.)*
- [x] **III. Spec-Driven & Incremental Development**: Are features designed to be built and tested incrementally under the SDD flow? *(Yes. Structured in prioritized user story checklist items.)*
- [x] **IV. Backend Service Testing**: Are there planned automated tests for all backend services? *(Yes. pytest tests are designed to mock agent calls and test HTTP/A2A endpoints.)*
- [x] **V. Simplicity & Clarity**: Is the design kept simple and easy to explain? *(Yes. A minimal FastAPI gateway and local files for the Knowledge Agent keep the demo lightweight.)*

## Project Structure

### Documentation (this feature)

```text
specs/001-a2a-ai-chat/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions & best practices
├── data-model.md        # Phase 1: Data models, entities & state
├── quickstart.md        # Phase 1: Validation steps and scripts
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── contracts/
    ├── gateway_api.json # Gateway OpenAPI specs
    └── agent_a2a.json   # A2A payload schema definition
```

### Source Code (repository root)

```text
docker-compose.yml
gateway/
├── main.py
├── requirements.txt
└── Dockerfile
agents/
├── coordinator/
│   ├── agent.py
│   ├── requirements.txt
│   └── Dockerfile
├── knowledge/
│   ├── agent.py
│   ├── data/
│   │   └── project_info.txt
│   ├── requirements.txt
│   └── Dockerfile
├── summary/
│   ├── agent.py
│   ├── requirements.txt
│   └── Dockerfile
└── general_knowledge/
    ├── agent.py
    ├── requirements.txt
    └── Dockerfile
frontend/
├── package.json
├── index.html
├── vite.config.js
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   └── index.css
└── Dockerfile
```

**Structure Decision**: Option 2: Web application layout. Decoupled subdirectories for `gateway`, `frontend`, and `agents` (subdivided into `coordinator`, `knowledge`, `summary`).

## Complexity Tracking

*No violations of project principles. Simplest architecture selected.*
