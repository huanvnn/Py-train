import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
import main

AUTH = {"Authorization": "Bearer " + "t" * 40}


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    monkeypatch.setenv("CHAT_API_TOKEN", "t" * 40)
    main.SESSIONS_DB.clear()
    main.REQUEST_TIMES.clear()
    main.ACTIVE_REQUESTS = 0


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c


def chat(client, **kwargs):
    response = AsyncMock()
    response.raise_for_status = lambda: None
    response.json = lambda: {"result": "Safe reply", "agents": []}
    with patch.object(main.httpx.AsyncClient, "post", return_value=response):
        return client.post("/api/chat/stream", headers=AUTH, json={"message": "hello", **kwargs})


def session_meta(response):
    for line in response.text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    raise AssertionError("Missing session metadata")


def test_auth_fail_closed(client, monkeypatch):
    assert client.post("/api/chat/stream", json={"message": "hello"}).status_code == 401
    monkeypatch.delenv("CHAT_API_TOKEN")
    assert client.post("/api/chat/stream", headers=AUTH, json={"message": "hello"}).status_code == 503


def test_session_ownership_and_deletion(client):
    response = chat(client)
    assert response.status_code == 200
    meta = session_meta(response)
    url = "/api/sessions/" + meta["id"]
    assert client.get(url, headers=AUTH).status_code == 404
    assert client.delete(url, headers=AUTH).status_code == 404
    assert chat(client, session_id=meta["id"]).status_code == 404
    owner = {**AUTH, "X-Session-Token": meta["token"]}
    history = client.get(url, headers=owner)
    assert len(history.json()) == 2
    assert history.headers["cache-control"] == "no-store"
    assert client.delete(url, headers=owner).status_code == 200
    assert client.get(url, headers=owner).status_code == 404
    assert main.ACTIVE_REQUESTS == 0


def test_validation_and_body_limit(client):
    for msg in ("", " " * 3, "x" * 8001):
        assert client.post("/api/chat/stream", headers=AUTH, json={"message": msg}).status_code in (400, 422)
    assert client.post("/api/chat/stream", headers=AUTH, content=b"x" * 33000).status_code == 413


def test_limits(client):
    for _ in range(20):
        main.REQUEST_TIMES.append(main.time.monotonic())
    assert chat(client).status_code == 429
    main.REQUEST_TIMES.clear()
    main.ACTIVE_REQUESTS = main.MAX_ACTIVE_REQUESTS
    assert chat(client).status_code == 429


def test_capacity_and_expiry(client, monkeypatch):
    meta = session_meta(chat(client))
    monkeypatch.setattr(main, "MAX_SESSIONS", 1)
    assert chat(client).status_code == 503
    main.SESSIONS_DB[meta["id"]]["created"] -= main.SESSION_TTL + 1
    assert chat(client).status_code == 200


def test_upstream_failure_redacted(client):
    with patch.object(main.httpx.AsyncClient, "post", side_effect=RuntimeError("private-host-secret")):
        response = client.post("/api/chat/stream", headers=AUTH, json={"message": "hello"})
    assert "private-host-secret" not in response.text
    assert "Assistant temporarily unavailable" in response.text
    assert main.ACTIVE_REQUESTS == 0


def test_cors_rejects_foreign_origin(client):
    response = client.options("/api/chat/stream", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in response.headers