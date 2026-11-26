---
name: coordinator-develop
description: Develop and debug this repository's Google ADK coordinator, A2A specialist routing, fallback behavior, and preservation of RAG source citations. Use for changes to agents/coordinator or its specialist contracts; not for unrelated frontend work.
---

# Develop the Coordinator

Scope: `agents/coordinator`. Resolve repository-relative paths from the root containing `docker-compose.yml`. This is a coding workflow, not a runtime LLM tool or a specialist agent.

## Read the relevant implementation

- `agents/coordinator/agent.py`: routing, A2A transport, injectable specialist clients, and internal `/run` endpoint.
- `agents/coordinator/test_agent.py`: normal, summary, and no-evidence routing cases.
- `agents/coordinator/test_citations.py`: exact preservation of grounded answers and fallback.
- For RAG contract changes, read `agents/knowledge/README.md` and the relevant functions in `agents/knowledge/rag.py` and `agent.py`.
- For deployment/API changes, inspect `docker-compose.yml`, `gateway/main.py`, and `SECURITY.md`.

## Preserve the contracts that matter

`run_coordinator(prompt, knowledge_client=None, summary_client=None, general_knowledge_client=None)` returns `{"result": str, "agents": list[str]}`. Keep the client injection points so tests do not contact actual services.

Current routing is intentionally simple: English `summarize`/`summary` triggers the Summary specialist; other requests start with Knowledge. A structured `{"status": "not_found"}` response, or a Knowledge transport failure, activates General Knowledge fallback. A user request to improve routing can change these decisions; update the affected tests and documentation together. Do not silently label general-knowledge fallback as document-grounded evidence.

A Knowledge result containing the `\n\nSources:\n` section currently returns unchanged, bypassing the Summary rewrite. Preserve both the cited statements and source references. If replacing this text marker with structured metadata, migrate the Knowledge producer and coordinator consumer together and test both sides. A source list does not itself prove factual correctness.

`agents` lists specialist paths attempted by the coordinator, including failed attempts; it is not a guarantee that every listed specialist produced the answer. Keep that distinction when changing telemetry or UI labels.

Specialists communicate via A2A; this repo's plan prohibits MCP integrations. The gateway's internal `/run` call is an existing HTTP compatibility entrypoint. Retain that behavior unless the task explicitly changes it.

The current transport uses `TextPart`/`Part.root` and private ADK members `_ensure_resolved` and `_a2a_client`. These are compatibility-sensitive. Agent requirements constrain `a2a-sdk` to `>=0.3.4,<1`; do not remove that bound as a routine upgrade. For a requested SDK migration, inspect the installed SDK signatures and migrate every affected agent and transport test together. Mocked routing tests do not validate real A2A transport.

## Implement and verify

Keep changes focused on the requested behavior. Separate routing decisions from transport mechanics when it makes the change easier to verify. Avoid model or API calls at import time.

Use `AsyncMock`/fake clients for routing tests. Assert observable behavior: which specialists were called, whether fallback ran, the returned `result`/`agents` shape, and unchanged citation-bearing text. For transport edits, also test representative A2A message/artifact responses, including empty/failed streams. Use a live provider only when the task calls for it; report offline versus live coverage accurately.

From `agents/coordinator`, in an environment with its dependencies installed:

```sh
python -m pip install -r requirements.txt
python -m pytest -q test_agent.py test_citations.py
```

The existing async tests need `pytest-asyncio` (declared in requirements). Run Knowledge tests in a separate invocation when touching its contract:

```sh
cd ../knowledge
python -m pytest -q
```

Both directories contain `agent.py` and `test_agent.py`; combining their tests in a single default pytest invocation can cause import/module collisions. Use separate processes or deliberately fix test packaging when that is part of the task.

If deployment verification is relevant, run `docker compose config --quiet` from the repo root; avoid printing the expanded configuration because it includes environment secrets. Rebuild containers only when needed for the requested validation.

## Security and delivery

Keep Gemini keys and chat tokens in local environment configuration. Do not print `.env`, generated credentials, prompts, or private document contents while debugging. Return generic upstream failures to clients. Preserve internal-only specialist ports and the gateway's authentication/session ownership controls.

For a requested public-facing endpoint change, validate request shape and bounds before invoking models and add meaningful rejection tests. Do not expose specialist ports to bypass the gateway.

Summarize the behavior changed, checks run, and any untested live integration. A request to develop code does not itself authorize publishing, pushing, or rewriting history; use the authorization actually given in the conversation.