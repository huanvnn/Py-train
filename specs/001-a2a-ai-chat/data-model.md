# Data Model: Google ADK A2A Chat Application

This document outlines the structured entities, payloads, and state mappings for the multi-agent chat demo.

## Core Entities

### 1. ChatSession
Tracks an active chat session between a client and the Gateway.
- `session_id` (UUID, mandatory): Unique identifier.
- `created_at` (Timestamp, mandatory): When the session was initialized.
- `messages` (List of Message, mandatory): Thread history.

### 2. Message
An individual communication entry in a conversation thread.
- `message_id` (UUID, mandatory): Unique identifier.
- `role` (Enum, mandatory): Either `user`, `assistant`, or `system`.
- `content` (String, mandatory): Text message content.
- `timestamp` (Timestamp, mandatory): Time of creation.

### 3. AgentEndpoint
Configuration metadata used by the Coordinator Agent to discover and invoke A2A specialists.
- `agent_name` (String, mandatory): Local identifier (e.g. `agent-knowledge`).
- `endpoint_url` (String, mandatory): URL pointing to the A2A server (e.g., `http://agent-knowledge:8002`).
- `well_known_path` (String, mandatory): Typically `/.well-known/agent.json`.

## A2A Payload Structures

Inter-agent communication follows the Google ADK A2A format.

### 1. Agent Card (`/.well-known/agent.json`)
Exposed by each agent server for identification and capability discovery.
```json
{
  "name": "knowledge-agent",
  "description": "Exposes local document index lookup capabilities",
  "version": "1.0.0",
  "endpoints": [
    {
      "protocol": "a2a",
      "url": "http://agent-knowledge:8002/a2a/v1"
    }
  ],
  "capabilities": {
    "search": {
      "description": "Search local documents for a given query string",
      "parameters": {
        "query": "string"
      }
    }
  }
}
```

### 2. Task Request
Payload sent by the Coordinator Client to a specialist server.
```json
{
  "task_id": "uuid-string",
  "capability": "search",
  "parameters": {
    "query": "project architecture details"
  }
}
```

### 3. Task Response
Response returned by a specialist server.
```json
{
  "task_id": "uuid-string",
  "status": "success",
  "result": {
    "context": "The system uses Google ADK and A2A communication protocol. The frontend only talks to the FastAPI gateway."
  }
}
```
