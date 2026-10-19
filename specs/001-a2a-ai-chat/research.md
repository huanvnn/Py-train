# Research: Google ADK Agent-to-Agent (A2A) Integration

## Key Decisions

### 1. Framework & Communication Method
- **Decision**: Use `google-adk[a2a]` for implementing the multi-agent system. Expose agents as HTTP services using `to_a2a()` and consume remote agents using `RemoteA2aAgent`.
- **Rationale**: Google's ADK native A2A support provides standardized `A2AServer` wrappers and discovery cards (`/.well-known/agent.json`), allowing seamless inter-agent task delegation without manual networking code.
- **Alternatives Considered**: 
  - *Custom REST API*: Rejected because it requires manual capability routing, does not adhere to the A2A standard, and lacks agent discovery card features.
  - *Model Context Protocol (MCP)*: Prohibited by the project constitution.

### 2. Frontend-Gateway Interaction
- **Decision**: React + Vite frontend communicates solely with the FastAPI Gateway using Server-Sent Events (SSE) for streaming message text.
- **Rationale**: Keeps the frontend completely decoupled from the inter-agent architecture and respects the constitutional constraint that the frontend only speaks to the gateway.
- **Alternatives Considered**:
  - *WebSockets*: Overkill for uni-directional streaming (server to client) and increases state management complexity. SSE is simpler and natively supported by browsers.

### 3. Knowledge Storage
- **Decision**: Local text file mounts loaded into the Knowledge Agent's Python environment.
- **Rationale**: Keeps local execution fast, predictable, and requires no database engines or vector indexes, in line with the "Simplicity and Clarity" core principle.
- **Alternatives Considered**:
  - *ChromaDB / Vector database*: Rejected as speculative/over-complicated for a simple demo. Pre-seeded keyword or pattern matching over text files meets requirements.

## Docker Networking Layout
- **Decision**: Custom Docker bridge network linking `frontend`, `gateway`, `agent-coordinator`, `agent-knowledge`, and `agent-summary` services.
- **Rationale**: Allows A2A client (`RemoteA2aAgent`) in the Coordinator to locate Specialist servers using local container hostnames (e.g. `http://agent-knowledge:8002/.well-known/agent.json`).
