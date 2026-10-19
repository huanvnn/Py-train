# Feature Specification: Google ADK Agent-to-Agent Chat

**Feature Branch**: `001-a2a-ai-chat`

**Created**: 2026-06-19

**Status**: Draft

**Input**: User description: "Build an AI chat application that demonstrates Agent-to-Agent communication using Google ADK."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Agent Chat API Flow (Priority: P1) 🎯 MVP

As an API user or developer, I want to submit a query to the Gateway API and have the Coordinator Agent collaborate with the Knowledge Agent and Summary Agent over the A2A protocol to stream back a complete response.

**Why this priority**: This establishes the core end-to-end multi-agent network (Coordinator, Knowledge, Summary) using Google ADK and A2A. Once this backend connectivity is functional, the frontend and deployment layers can be integrated.

**Independent Test**: Spin up the Coordinator Agent, Knowledge Agent, Summary Agent, and Gateway API locally. Send a HTTP POST request to `/api/chat` with a query. Verify that the response streams back chunks using Server-Sent Events (SSE), containing context retrieved from the Knowledge Agent.

**Acceptance Scenarios**:

1. **Given** all agents and the Gateway API are running, **When** the user sends a message "Tell me about the project architecture", **Then** the Coordinator Agent receives the request, queries the Knowledge Agent via A2A to retrieve facts, and streams the aggregated answer back to the Gateway.
2. **Given** the Coordinator Agent receives a request requiring a summary (e.g. containing a "summarize" keyword), **When** processing the query, **Then** it delegates to the Summary Agent via A2A and streams the summarized response.

---

### User Story 2 - React Web Chat Interface (Priority: P2)

As a chat user, I want to interact with the multi-agent system through a responsive, premium web interface that displays streaming answers with typing indicators and formatting.

**Why this priority**: Delivers the visual experience of the chat application, bringing it from a backend API to a polished user product.

**Independent Test**: Run the React web client, type a message in the chat box, and verify that typing indicators are visible while waiting, and that the response renders word-by-word via Server-Sent Events.

**Acceptance Scenarios**:

1. **Given** the React frontend is loaded and connected, **When** the user submits a message, **Then** the UI immediately renders the user's message, displays a typing indicator for the agent, and streams the text response in real-time.
2. **Given** a network disconnect or agent API error, **When** a message is sent, **Then** the UI shows a clear, non-technical error notification and allows the user to resend the message.

---

### User Story 3 - Single-Command Docker Deployment (Priority: P3)

As a developer, I want to run all agents, the gateway, and the frontend service in a unified containerized network using Docker Compose.

**Why this priority**: Simplifies environment configuration and local setup, guaranteeing that ports, A2A routes, and web client addresses resolve identically for everyone.

**Independent Test**: Run `docker compose up --build` from the root directory. Verify all 5 containers (frontend, gateway, coordinator, knowledge, summary) compile and establish connections successfully.

**Acceptance Scenarios**:

1. **Given** a local Docker environment, **When** running `docker compose up`, **Then** the container ports are exposed correctly, environment variables are loaded, and the React app can communicate with the gateway.

---

### Edge Cases

- **A2A Agent Offline**: What happens when the Coordinator Agent attempts to contact the Knowledge Agent, but the A2A server is down? (The Coordinator must gracefully fallback, logs the error, and tells the user: "Knowledge database is currently offline, answering from memory...")
- **LLM Rate Limits/Timeouts**: How are API provider rate limits handled? (The gateway/agent must retry with exponential backoff, and eventually return a user-friendly error chunk if it fails after 3 attempts).
- **Empty Query Handling**: What happens if the user sends whitespace? (The frontend prevents submission, and backend API returns a `400 Bad Request` validation error).

## Current Architecture

Kiến trúc hiện tại:

✅ Có Frontend.
✅ Có Backend for Frontend.
✅ Có A2A Client.
✅ Có nhiều A2A Server.
✅ Có giao tiếp A2A.

- A2A Client nằm ở Coordinator .

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement a multi-agent architecture composed of a Coordinator Agent, a Knowledge Agent, and a Summary Agent.
- **FR-002**: The Coordinator Agent MUST act as the primary dispatcher, orchestrating flows and contacting other agents as needed.
- **FR-003**: Agent-to-agent communication (Coordinator <-> Knowledge, Coordinator <-> Summary) MUST use Google ADK and follow the A2A protocol.
- **FR-004**: Each agent MUST run its own A2A server and expose an A2A server endpoint for agent-to-agent interaction.
- **FR-005**: The Knowledge Agent MUST search over a pre-seeded local folder of markdown/text files.
- **FR-006**: The Summary Agent MUST generate summaries of recent chat history when requested.
- **FR-007**: The Gateway API (FastAPI) MUST expose an SSE (Server-Sent Events) endpoint `/api/chat/stream` for real-time text delivery.
- **FR-008**: The Frontend client (React + Vite) MUST connect to the SSE endpoint and render streamed content chunks.
- **FR-009**: The entire application stack MUST be deployable and runnable locally via `docker-compose.yml`.
- **FR-010**: The Frontend client MUST communicate only with the Gateway API and is prohibited from communicating directly with the individual agents.
- **FR-011**: Integration with the Model Context Protocol (MCP) is strictly prohibited.

### Key Entities

- **Agent Endpoint**: Defines the connection metadata (host, port, A2A endpoint path) for an agent.
- **Chat Thread**: Tracks conversation history (messages, roles) to feed into the Summary Agent.
- **A2A Payload**: The message format defined by the A2A protocol for exchanging data and commands between agents.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The latency for A2A routing (handshake + payload exchange between Coordinator and Knowledge Agent) must be under 300ms, excluding LLM reasoning time.
- **SC-002**: The React UI must start rendering the first text chunk within 1.5 seconds of the user clicking send.
- **SC-003**: Run `docker compose up` starts all 5 containers and renders the UI ready to chat in under 2 minutes.
- **SC-004**: Automated tests for FastAPI routing and A2A server connections must run and pass successfully.

## Assumptions

- A Google Gemini API key (or other supported provider) is supplied via a `.env` file to be loaded by the agents.
- The Google ADK package and its A2A server components are available to be installed via Python's package manager.
- The Knowledge base will default to pre-seeded local files for this demo to maintain simplicity.
