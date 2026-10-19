import asyncio
import hashlib
import json
import logging
import os
import secrets
import time
import uuid
from collections import deque
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="AI Chat Gateway API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if x.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Session-Token"],
)
logger = logging.getLogger(__name__)
SESSIONS_DB = {}
REQUEST_TIMES = deque()
ACTIVE_REQUESTS = 0
SESSION_TTL = 3600
MAX_SESSIONS = 500
MAX_MESSAGES = 100
MAX_ACTIVE_REQUESTS = 8
MAX_REQUEST_BYTES = 32768


@app.middleware("http")
async def limit_request_body(request, call_next):
    from starlette.responses import JSONResponse
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_REQUEST_BYTES:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)
    request._body = bytes(body)
    return await call_next(request)


async def require_auth(authorization: Optional[str] = Header(default=None)):
    expected = os.getenv("CHAT_API_TOKEN", "")
    if len(expected) < 32:
        raise HTTPException(503, "Server authentication is not configured")
    if not authorization or not secrets.compare_digest(authorization, "Bearer " + expected):
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: Optional[uuid.UUID] = None


def purge_expired():
    now = time.monotonic()
    for sid in list(SESSIONS_DB):
        if now - SESSIONS_DB[sid]["created"] >= SESSION_TTL:
            del SESSIONS_DB[sid]


def get_owned_session(sid, token):
    purge_expired()
    session = SESSIONS_DB.get(str(sid))
    digest = hashlib.sha256((token or "").encode()).hexdigest()
    if not session or not secrets.compare_digest(session["token_hash"], digest):
        raise HTTPException(404, "Session not found")
    return session


@app.post("/api/chat/stream", dependencies=[Depends(require_auth)])
async def chat_stream(request: ChatRequest, x_session_token: Optional[str] = Header(default=None)):
    global ACTIVE_REQUESTS
    if not request.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    now = time.monotonic()
    while REQUEST_TIMES and now - REQUEST_TIMES[0] >= 60:
        REQUEST_TIMES.popleft()
    if len(REQUEST_TIMES) >= 20 or ACTIVE_REQUESTS >= MAX_ACTIVE_REQUESTS:
        raise HTTPException(429, "Request limit reached", headers={"Retry-After": "60"})
    purge_expired()
    session_token = x_session_token
    if request.session_id:
        sid = str(request.session_id)
        session = get_owned_session(sid, session_token)
    else:
        if len(SESSIONS_DB) >= MAX_SESSIONS:
            raise HTTPException(503, "Session capacity reached; try again later")
        sid, session_token = str(uuid.uuid4()), secrets.token_urlsafe(32)
        session = {"token_hash": hashlib.sha256(session_token.encode()).hexdigest(), "created": now, "messages": [], "busy": False}
        SESSIONS_DB[sid] = session
    if session["busy"]:
        raise HTTPException(409, "A reply is already in progress for this session")
    if len(session["messages"]) >= MAX_MESSAGES:
        raise HTTPException(429, "Session message limit reached; start a new session")
    REQUEST_TIMES.append(now)
    session["messages"].append({"role": "user", "content": request.message})
    session["busy"] = True
    ACTIVE_REQUESTS += 1

    async def event_generator():
        global ACTIVE_REQUESTS
        try:
            yield {"event": "session", "data": json.dumps({"id": sid, "token": session_token})}
            host = os.getenv("COORDINATOR_HOST", "localhost")
            port = os.getenv("COORDINATOR_PORT", "8001")
            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                response = await client.post(f"http://{host}:{port}/run", json={"prompt": request.message})
                response.raise_for_status()
                result = response.json()
            answer = str(result.get("result", ""))[:32000]
            yield {"event": "agents", "data": json.dumps(result.get("agents", []))}
            yield {"event": "message", "data": json.dumps({"text": answer})}
            session["messages"].append({"role": "assistant", "content": answer})
        except asyncio.CancelledError:
            raise
        except Exception:
            # Do not log prompts, credentials, or upstream exception bodies.
            logger.warning("Coordinator request failed")
            yield {"event": "error", "data": "Assistant temporarily unavailable"}
        finally:
            session["busy"] = False
            ACTIVE_REQUESTS -= 1

    return EventSourceResponse(event_generator(), headers={"Cache-Control": "no-store"})


@app.get("/api/sessions/{session_id}", dependencies=[Depends(require_auth)])
async def get_session(session_id: uuid.UUID, x_session_token: Optional[str] = Header(default=None)):
    from fastapi.responses import JSONResponse
    return JSONResponse(get_owned_session(session_id, x_session_token)["messages"], headers={"Cache-Control": "no-store"})


@app.delete("/api/sessions/{session_id}", dependencies=[Depends(require_auth)])
async def delete_session(session_id: uuid.UUID, x_session_token: Optional[str] = Header(default=None)):
    session = get_owned_session(session_id, x_session_token)
    if session["busy"]:
        raise HTTPException(409, "Wait for the current reply to finish")
    del SESSIONS_DB[str(session_id)]
    return {"deleted": True}