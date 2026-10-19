# Tasks: Google ADK Agent-to-Agent Chat

**Input**: Design documents from `/specs/001-a2a-ai-chat/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Backend automated tests are **mandatory** per the project constitution and spec requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create folder structures for gateway, agents, and frontend per implementation plan
- [x] T002 Initialize python requirements for FastAPI gateway, coordinator, knowledge, and summary agents in `gateway/requirements.txt`, `agents/coordinator/requirements.txt`, `agents/knowledge/requirements.txt`, `agents/summary/requirements.txt`
- [x] T003 Create root `.env` template config file in `.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement base Dockerfiles for gateway and each of the agents in `gateway/Dockerfile`, `agents/coordinator/Dockerfile`, `agents/knowledge/Dockerfile`, `agents/summary/Dockerfile`
- [x] T005 Setup docker-compose infrastructure with simple multi-container builds and local networks in `docker-compose.yml`
- [x] T006 [P] Create pre-seeded local knowledge directory and text documentation files in `agents/knowledge/data/project_info.txt`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Multi-Agent Chat API Flow (Priority: P1) 🎯 MVP

**Goal**: Setup the core A2A agents and FastAPI gateway to enable streaming multi-agent chat interactions over the network.

**Independent Test**: Send a POST query to `http://localhost:8000/api/chat/stream` and verify the SSE streaming response chunks.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] [US1] Write automated A2A connection and search capability tests for the Knowledge Agent in `agents/knowledge/test_agent.py`
- [x] T008 [P] [US1] Write automated A2A connection and summary tests for the Summary Agent in `agents/summary/test_agent.py`
- [x] T009 [P] [US1] Write automated routing and orchestration tests for the Coordinator Agent in `agents/coordinator/test_agent.py`
- [x] T010 [P] [US1] Write automated routing and SSE stream tests for the FastAPI Gateway in `gateway/test_gateway.py`

### Implementation for User Story 1

- [x] T011 [US1] Implement Knowledge Agent using Google ADK `to_a2a` exposing local file search capability in `agents/knowledge/agent.py`
- [x] T012 [US1] Implement Summary Agent using Google ADK `to_a2a` exposing discussion summary capability in `agents/summary/agent.py`
- [x] T013 [US1] Implement Coordinator Agent using Google ADK `RemoteA2aAgent` to connect to knowledge and summary agents in `agents/coordinator/agent.py`
- [x] T014 [US1] Implement FastAPI Gateway route handler for SSE streaming connection to Coordinator Agent in `gateway/main.py`

**Checkpoint**: At this point, the backend API flow is fully operational and verified.

---

## Phase 4: User Story 2 - React Web Chat Interface (Priority: P2)

**Goal**: Build a responsive React + Vite chat interface that consumes the Gateway SSE stream.

**Independent Test**: Visit `http://localhost:3000` in the browser, send a prompt, and see typed output stream live.

### Implementation for User Story 2

- [x] T015 [US2] Initialize React + Vite project and configure dependencies in `frontend/package.json`
- [x] T016 [US2] Create Dockerfile configuration for local frontend hosting in `frontend/Dockerfile`
- [x] T017 [US2] Implement chat UI, input box, and layout in `frontend/src/App.jsx`
- [x] T018 [US2] Style layout with modern CSS (typing indicator, loading states, glassmorphism, responsive colors) in `frontend/src/index.css`
- [x] T019 [US2] Connect client state and events to FastAPI SSE gateway route in `frontend/src/App.jsx`

**Checkpoint**: At this point, the visual chat client is fully integrated and interactive.

---

## Phase 5: User Story 3 - Single-Command Docker Deployment (Priority: P3)

**Goal**: Enable running all services together locally with Docker Compose.

**Independent Test**: Execute `docker compose up` and confirm all 5 containers are up and connected.

### Implementation for User Story 3

- [x] T020 [US3] Finalize docker-compose environment configurations, mapping ports, mounts, and dependencies in `docker-compose.yml`

**Checkpoint**: All user stories are independently functional and fully containerized.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T021 [P] Add main setup guide and troubleshooting documentation in `README.md`
- [x] T022 Run the quickstart validation scripts in `specs/001-a2a-ai-chat/quickstart.md` and verify all tests pass

---

## Phase 6: Feature Enhancement - General Knowledge Agent Fallback

**Goal**: Implement fallback routing to a General Knowledge Agent when local documentation is not found, format responses using the Summary Agent, and display participating agents in the React UI.

**Independent Test**: Submit query "Explain quantum computing." and verify A2A badge list shows `coordinator_agent`, `knowledge_agent`, `general_knowledge_agent`, `summary_agent` in browser at `http://localhost:3000`.

- [x] T023 Configure `GENERAL_KNOWLEDGE_HOST` and `GENERAL_KNOWLEDGE_PORT` in root `.env` template
- [x] T024 Define `agent-general-knowledge` service container and setup networks in `docker-compose.yml`
- [x] T025 Implement the General Knowledge Agent container (`requirements.txt`, `Dockerfile`, `agent.py`) exposing the A2A `/run` endpoint
- [x] T026 Update Knowledge Agent (`agents/knowledge/agent.py`) to return structured `not_found` JSON when query results are empty
- [x] T027 Extend Summary Agent (`agents/summary/agent.py`) to expose a `/format` routing endpoint
- [x] T028 Update Coordinator Agent (`agents/coordinator/agent.py`) to execute the fallback routing chain and output participating agents list
- [x] T029 Modify FastAPI Gateway (`gateway/main.py`) to parse, capture, and stream the list of participating agents via SSE
- [x] T030 Update React UI (`App.jsx` and `index.css`) to render glassmorphic A2A participant badges for each assistant message bubble
- [x] T031 Perform automated test and manual UI E2E verification of scenarios 1, 2, and 3

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup (Phase 1).
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2).
- **User Story 2 (Phase 4)**: Depends on User Story 1 API completeness.
- **User Story 3 (Phase 5)**: Depends on all implementation phases.
- **Polish (Final Phase)**: Depends on all user stories being complete.

### Within Each User Story

- Tests must be written and verify failing before implementing.
- Specialist agents (Knowledge, Summary) before Coordinator orchestrator.
- Coordinator orchestrator before Gateway endpoint connection.

---

## Parallel Opportunities

- Shared python requirements and directory configurations (**T001**, **T002**, **T003**) can run in parallel.
- All backend test suite skeletons (**T007**, **T008**, **T009**, **T010**) can be developed in parallel.
- Setup documentation writing (**T021**) can occur in parallel during polish phase.
