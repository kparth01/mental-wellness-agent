# Deploying Mental Wellness Agent with LangServe — A Complete Guide

This document explains what LangServe is, how it works, and walks through every decision made while creating `server.py` to deploy the Mental Wellness Agent as a REST API.

---

## Table of Contents

1. [What is LangServe?](#1-what-is-langserve)
2. [How LangServe Works — Core Concepts](#2-how-langserve-works--core-concepts)
3. [LangServe Examples from the Repository](#3-langserve-examples-from-the-repository)
4. [Mental Wellness Agent — Before LangServe](#4-mental-wellness-agent--before-langserve)
5. [Creating server.py — Step by Step](#5-creating-serverpy--step-by-step)
6. [What LangServe Auto-Generates for You](#6-what-langserve-auto-generates-for-you)
7. [Running and Testing the Server](#7-running-and-testing-the-server)
8. [Architecture Comparison: CLI vs API](#8-architecture-comparison-cli-vs-api)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. What is LangServe?

LangServe is a Python library that turns any **LangChain Runnable** (chains, agents, LangGraph workflows) into a production-ready **REST API** with a single function call.

It is built on top of:

- **FastAPI** — the web framework that serves HTTP requests
- **Pydantic** — data validation for request/response schemas
- **uvicorn** — the ASGI server that runs the app

### The Core Idea

Without LangServe, you'd need to manually:
- Create FastAPI route handlers
- Parse incoming JSON
- Validate input schemas
- Call your chain
- Handle streaming
- Serialize output
- Build OpenAPI docs

LangServe does **all of this** with one function: `add_routes()`.

```python
from langserve import add_routes

add_routes(app, my_chain, path="/my-chain")
# That's it. You now have /invoke, /stream, /batch, /playground, and more.
```

### Installation

```bash
pip install "langserve[all]"    # Server + Client
pip install "langserve[server]" # Server only
pip install "langserve[client]" # Client only
```

> **Note:** LangServe is now in maintenance mode. For new production projects, LangChain recommends LangGraph Platform. However, LangServe remains fully functional and is excellent for local deployments and learning.

---

## 2. How LangServe Works — Core Concepts

### 2.1 The `add_routes()` Function

This is the heart of LangServe. Its full signature:

```python
def add_routes(
    app: Union[FastAPI, APIRouter],  # Your FastAPI app
    runnable: Runnable,               # Any LangChain Runnable
    *,
    path: str = "",                   # URL prefix (e.g., "/wellness")
    input_type: Type = "auto",        # Pydantic model for input validation
    output_type: Type = "auto",       # Pydantic model for output validation
    enabled_endpoints: list = None,   # Whitelist specific endpoints
    disabled_endpoints: list = None,  # Blacklist specific endpoints
    playground_type: str = "default", # "default" or "chat"
    dependencies: list = None,        # FastAPI dependencies (auth, etc.)
    per_req_config_modifier = None,   # Modify config per-request (user-specific)
    # ... and more
) -> None
```

**What it creates** — for a path like `/wellness`, you get:

| Endpoint                     | Method | Purpose                                    |
|------------------------------|--------|--------------------------------------------|
| `/wellness/invoke`           | POST   | Run the chain once, get full result        |
| `/wellness/batch`            | POST   | Run the chain on multiple inputs at once   |
| `/wellness/stream`           | POST   | Stream output chunks as they're generated  |
| `/wellness/stream_log`       | POST   | Stream with intermediate step details      |
| `/wellness/stream_events`    | POST   | Stream events from intermediate steps      |
| `/wellness/input_schema`     | GET    | JSON Schema for valid input                |
| `/wellness/output_schema`    | GET    | JSON Schema for output format              |
| `/wellness/config_schema`    | GET    | JSON Schema for configuration options      |
| `/wellness/playground/`      | GET    | Interactive web UI to test the chain       |

### 2.2 What is a "Runnable"?

A **Runnable** is LangChain's universal interface. Anything that implements `.invoke()`, `.stream()`, `.batch()` is a Runnable. This includes:

- **LLMs**: `ChatOpenAI()`, `ChatAnthropic()`
- **Chains**: `prompt | llm` (LCEL pipe syntax)
- **Agents**: `AgentExecutor`
- **LangGraph workflows**: `StateGraph(...).compile()` — **this is what our project uses**
- **Retrievers**, **Tools**, and more

Because our `graph.py` compiles to a Runnable via `workflow.compile()`, it plugs directly into LangServe.

### 2.3 Input/Output Type Hints

LangServe uses Pydantic to auto-generate schemas. For simple chains (`prompt | llm`), it can infer the schema automatically. For complex workflows like LangGraph, the auto-inference may not capture your intent, so you define explicit types:

```python
from pydantic import BaseModel, Field

class WellnessInput(BaseModel):
    user_input: str = Field(description="What you'd like to talk about")

add_routes(app, graph.with_types(input_type=WellnessInput), path="/wellness")
```

The `.with_types()` method wraps the Runnable with explicit type information that LangServe uses for:
- Request validation (rejects malformed input)
- OpenAPI documentation (Swagger UI)
- Playground UI (auto-generates form fields)

---

## 3. LangServe Examples from the Repository

### 3.1 Simplest Example — Exposing an LLM

From `langserve/examples/llm/server.py`:

```python
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langserve import add_routes

app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="Spin up a simple api server using Langchain's Runnable interfaces",
)

# Expose OpenAI as an endpoint
add_routes(app, ChatOpenAI(model="gpt-3.5-turbo-0125"), path="/openai")

# Expose Anthropic as another endpoint
add_routes(app, ChatAnthropic(model="claude-3-haiku-20240307"), path="/anthropic")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
```

**Key takeaway:** Each `add_routes()` call creates a completely independent set of endpoints. You can expose multiple chains/models on the same server.

### 3.2 Agent Example — With Custom Input/Output Types

From `langserve/examples/agent/server.py`:

```python
from pydantic import BaseModel
from langchain.agents import AgentExecutor
from langserve import add_routes

class Input(BaseModel):
    input: str

class Output(BaseModel):
    output: Any

# The AgentExecutor lacks good schema inference,
# so we explicitly set input/output types
add_routes(
    app,
    agent_executor.with_types(input_type=Input, output_type=Output)
                  .with_config({"run_name": "agent"}),
)
```

**Key takeaway:** When LangServe can't infer your schema (agents, complex graphs), use `.with_types()` to tell it what the input/output looks like. This is exactly what we do for the Mental Wellness Agent.

### 3.3 Chat with Persistence — Session History

From `langserve/examples/chat_with_persistence/server.py`:

```python
from pydantic import BaseModel, Field
from langchain_core.runnables.history import RunnableWithMessageHistory

class InputChat(BaseModel):
    human_input: str = Field(
        ...,
        description="The human input to the chat system.",
        extra={"widget": {"type": "chat", "input": "human_input"}},
    )

chain_with_history = RunnableWithMessageHistory(
    chain,
    create_session_factory("chat_histories"),
    input_messages_key="human_input",
    history_messages_key="history",
).with_types(input_type=InputChat)

add_routes(app, chain_with_history)
```

**Key takeaway:** Pydantic Field's `extra` parameter can configure Playground UI widgets. The `RunnableWithMessageHistory` wrapper adds session-based memory.

### 3.4 Pattern Summary

Every LangServe server follows the same 4-step pattern:

```
1. Create FastAPI app          →  app = FastAPI(...)
2. Define your Runnable        →  chain = prompt | llm  (or a compiled graph)
3. (Optional) Define types     →  class MyInput(BaseModel): ...
4. Register routes             →  add_routes(app, chain, path="/...")
```

---

## 4. Mental Wellness Agent — Before LangServe

### Project Architecture

```
mental-wellness-agent/
├── agents/
│   ├── base.py                # BaseAgent — shared LLM + chain utilities
│   ├── supervisor.py          # Safety gatekeeper & intent classification
│   ├── planner.py             # Decides which executor agents to invoke
│   ├── emotion_reflection.py  # Empathetic validation
│   ├── coping_strategy.py     # Wellness technique suggestions
│   ├── resource_agent.py      # Resource recommendations
│   └── aggregator.py          # Combines all outputs into final response
├── graph.py                   # LangGraph StateGraph (the orchestrator)
├── main.py                    # CLI entry point
├── requirements.txt
└── .env
```

### The Workflow (graph.py)

The graph implements a **Supervisor → Planner → Parallel Executors → Aggregator** pattern:

```
User Input
    ↓
SupervisorAgent (safety check + intent classification)
    ↓ allowed?
    ├── NO  → blocked_node (crisis resources) → END
    └── YES → PlannerAgent (decide which agents to invoke)
                  ↓
              ┌───┼───────────────┐
              ↓   ↓               ↓
        Emotion  Coping      Resource     ← (run in parallel)
              └───┼───────────────┘
                  ↓
           AggregatorAgent (combine results)
                  ↓
                 END
```

### How the Graph is Built

```python
# graph.py — key sections

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_input: str
    supervisor_output: Dict[str, Any]
    plan: Dict[str, Any]
    emotion_result: Dict[str, Any]
    coping_result: Dict[str, Any]
    resource_result: Dict[str, Any]
    final_output: Dict[str, Any]
    next_step: str

def create_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("emotion_reflection", emotion_node)
    workflow.add_node("coping_strategy", coping_node)
    workflow.add_node("resource_agent", resource_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("blocked", blocked_node)

    workflow.set_entry_point("supervisor")
    # ... conditional edges ...
    return workflow.compile()

app = create_workflow()   # ← This compiled graph IS a Runnable
```

### The CLI Entry Point (main.py)

Before LangServe, the only way to use the agent was through `main.py`:

```python
# main.py — how it invoked the graph
result = app.invoke({
    "user_input": user_input,
    "messages": [HumanMessage(content=user_input)]
})
```

This worked for local testing but meant:
- No HTTP access (no API for frontends, mobile apps, or other services)
- No streaming over the network
- No auto-generated documentation
- No interactive playground UI
- No batch processing

---

## 5. Creating server.py — Step by Step

Here's the complete `server.py` with annotations explaining every line:

```python
"""
LangServe server for Mental Wellness Agent.
Exposes the multi-agent workflow as a REST API.
"""
import os
from dotenv import load_dotenv

# STEP 1: Load environment variables BEFORE importing agents.
# The agents (via base.py) read OPENAI_API_KEY on import.
# If we load .env after importing graph, the key won't be found.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from pydantic import BaseModel, Field

# STEP 2: Import the compiled LangGraph workflow.
# graph.py exports `app = create_workflow()` which is a compiled StateGraph.
# We alias it to `wellness_graph` to avoid naming conflict with FastAPI's `app`.
from graph import app as wellness_graph


# STEP 3: Define the input schema.
# Our AgentState has many fields (messages, supervisor_output, plan, etc.),
# but the user only provides `user_input`. This Pydantic model tells LangServe
# exactly what to expect from API callers.
class WellnessInput(BaseModel):
    user_input: str = Field(description="What you'd like to talk about")


# STEP 4: Create the FastAPI application.
app = FastAPI(
    title="Mental Wellness Agent",
    version="1.0",
    description="A multi-agent mental wellness support API powered by LangGraph",
)

# STEP 5: Add CORS middleware.
# Without this, browsers block requests from frontends on different origins.
# allow_origins=["*"] permits any domain — restrict this in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# STEP 6: Register the LangGraph workflow as API routes.
# .with_types(input_type=WellnessInput) tells LangServe:
#   - Only accept requests matching WellnessInput schema
#   - Generate correct OpenAPI docs and Playground UI forms
# path="/wellness" prefixes all generated endpoints with /wellness/
add_routes(
    app,
    wellness_graph.with_types(input_type=WellnessInput),
    path="/wellness",
)

# STEP 7: Run with uvicorn.
# host="0.0.0.0" makes the server accessible on the local network.
# The port is configurable via the PORT environment variable.
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Key Design Decisions Explained

#### Why `load_dotenv()` comes before the graph import

```python
load_dotenv()                              # Load .env FIRST
from graph import app as wellness_graph    # THEN import graph
```

When Python imports `graph.py`, it immediately runs:
```python
supervisor = SupervisorAgent()  # → BaseAgent.__init__() → reads OPENAI_API_KEY
```

If `.env` isn't loaded yet, `os.getenv("OPENAI_API_KEY")` returns `None` and the agent raises `ValueError`. Order matters.

#### Why we alias `app as wellness_graph`

Both `graph.py` and `server.py` define a variable named `app`:
- `graph.py`: `app = create_workflow()` — the LangGraph Runnable
- `server.py`: `app = FastAPI(...)` — the FastAPI web server

The alias avoids the name collision:
```python
from graph import app as wellness_graph  # Rename to avoid conflict
```

#### Why we define `WellnessInput` explicitly

The `AgentState` TypedDict has 9 fields:
```python
class AgentState(TypedDict):
    messages: ...
    user_input: str
    supervisor_output: Dict[str, Any]
    plan: Dict[str, Any]
    # ... 5 more fields
```

But an API caller should only send `user_input`. The other fields are internal workflow state. Without `WellnessInput`, LangServe would either:
- Expose all 9 fields in the API schema (confusing for callers)
- Fail to infer the schema entirely

The explicit Pydantic model ensures the API is clean:
```json
// What the caller sends:
{ "input": { "user_input": "I feel stressed about work" } }

// NOT this mess:
{ "input": { "user_input": "...", "messages": [], "supervisor_output": {}, ... } }
```

#### Why CORS middleware is added

Browsers enforce the **Same-Origin Policy**. If your frontend runs on `http://localhost:3000` but the API is on `http://localhost:8000`, the browser blocks the request unless the server explicitly allows it via CORS headers.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend's domain
    ...
)
```

---

## 6. What LangServe Auto-Generates for You

After running `python server.py`, these endpoints are live:

### API Endpoints

**POST `/wellness/invoke`** — Single request
```bash
curl -X POST http://localhost:8000/wellness/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"user_input": "I feel anxious about my job interview"}}'
```

Response:
```json
{
  "output": {
    "user_input": "I feel anxious about my job interview",
    "final_output": {
      "empathy": "It makes complete sense to feel anxious...",
      "practical_steps": [...],
      "optional_resources": [...],
      "closing": "Remember, preparation is your ally...",
      "disclaimer": "This is not professional medical advice."
    },
    "supervisor_output": {...},
    "plan": {...}
  }
}
```

**POST `/wellness/stream`** — Streaming response
```bash
curl -X POST http://localhost:8000/wellness/stream \
  -H "Content-Type: application/json" \
  -d '{"input": {"user_input": "I feel stressed"}}'
```

**POST `/wellness/batch`** — Multiple inputs at once
```bash
curl -X POST http://localhost:8000/wellness/batch \
  -H "Content-Type: application/json" \
  -d '{"inputs": [
    {"user_input": "I feel stressed"},
    {"user_input": "I cant sleep at night"}
  ]}'
```

### Auto-Generated Pages

| URL | What You See |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI — interactive API documentation |
| `http://localhost:8000/redoc` | ReDoc — alternative API documentation |
| `http://localhost:8000/wellness/playground/` | Interactive testing UI with form inputs |
| `http://localhost:8000/wellness/input_schema` | JSON Schema for valid input |
| `http://localhost:8000/wellness/output_schema` | JSON Schema for output format |

### Python Client Usage

```python
from langserve import RemoteRunnable

# Connect to the server — works like a local Runnable
wellness = RemoteRunnable("http://localhost:8000/wellness/")

# Synchronous call
result = wellness.invoke({"user_input": "I feel overwhelmed at work"})
print(result["final_output"]["empathy"])

# Async call
result = await wellness.ainvoke({"user_input": "I can't focus today"})

# Streaming
async for chunk in wellness.astream({"user_input": "I feel anxious"}):
    print(chunk)

# Batch
results = wellness.batch([
    {"user_input": "I feel stressed"},
    {"user_input": "I'm having trouble sleeping"},
])
```

### JavaScript/TypeScript Client

```typescript
import { RemoteRunnable } from "@langchain/core/runnables/remote";

const wellness = new RemoteRunnable({
  url: "http://localhost:8000/wellness/",
});

const result = await wellness.invoke({
  user_input: "I feel anxious about my presentation",
});
```

---

## 7. Running and Testing the Server

### Prerequisites

```bash
cd mental-wellness-agent

# Install dependencies
pip install -r requirements.txt
pip install "langserve[all]" fastapi uvicorn

# Ensure .env has your API key
# OPENAI_API_KEY=sk-...
```

### Start the Server

```bash
python server.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Quick Test

1. Open `http://localhost:8000/docs` in your browser — you'll see the Swagger UI
2. Open `http://localhost:8000/wellness/playground/` — you'll see the interactive playground
3. Use curl:
   ```bash
   curl -X POST http://localhost:8000/wellness/invoke \
     -H "Content-Type: application/json" \
     -d '{"input": {"user_input": "I feel stressed about exams"}}'
   ```

### Custom Port

```bash
PORT=9000 python server.py
```

Or set `PORT=9000` in your `.env` file.

---

## 8. Architecture Comparison: CLI vs API

### Before (CLI only — main.py)

```
User ──terminal──→ main.py ──invoke()──→ graph.py ──→ Agents ──→ terminal output
```

- Single user, single machine
- No network access
- Manual output formatting
- No documentation

### After (REST API — server.py)

```
Browser/Frontend ──HTTP──→ server.py (FastAPI + LangServe)
                              │
Mobile App     ──HTTP──→      ├── /wellness/invoke
                              ├── /wellness/stream
Other Services ──HTTP──→      ├── /wellness/batch
                              ├── /wellness/playground/
                              └── /docs
                              │
                          graph.py ──→ Agents ──→ JSON response
```

- Multiple clients simultaneously
- Network accessible (local network or internet)
- Automatic JSON serialization
- Auto-generated docs and playground
- Streaming support
- Batch processing

### What Changed in the Project

| Aspect | Before | After |
|--------|--------|-------|
| Entry point | `main.py` (CLI) | `server.py` (HTTP) + `main.py` (CLI still works) |
| Access | Terminal only | Any HTTP client, browser, frontend |
| New files | — | `server.py` (46 lines) |
| Modified files | — | None (zero changes to existing code) |
| New dependencies | — | `langserve[all]`, `fastapi`, `uvicorn` |
| graph.py changes | — | None (it was already a Runnable) |
| agents/ changes | — | None |

The key insight: **zero changes to existing code**. LangServe wraps the existing compiled graph as-is. The `graph.py` file already exported a Runnable (`app = create_workflow()`), which is exactly what LangServe needs.

---

## 9. Troubleshooting

### "OPENAI_API_KEY not found"
Make sure `.env` is in the project root and contains your key. The `load_dotenv()` in `server.py` must run before the graph import.

### "Module not found: langserve"
```bash
pip install "langserve[all]"
```

### CORS errors in browser console
Verify the CORS middleware is added to the FastAPI app. Check that `allow_origins` includes your frontend's origin.

### Playground shows wrong input fields
This happens when LangServe infers the schema from `AgentState` instead of `WellnessInput`. Ensure you're using `.with_types(input_type=WellnessInput)`.

### Server starts but requests hang
Check that your `OPENAI_API_KEY` is valid and has credits. The agents make real API calls to OpenAI.

### Port already in use
```bash
PORT=8001 python server.py
```

---

## Summary

Deploying a LangGraph workflow with LangServe requires just **one new file** (`server.py`, 46 lines) and **zero changes** to existing code. The key steps are:

1. Install `langserve[all]`, `fastapi`, `uvicorn`
2. Create a FastAPI app
3. Import your compiled graph
4. Define a Pydantic input model matching what users should send
5. Call `add_routes(app, graph.with_types(input_type=...), path="...")`
6. Run with uvicorn

Your entire multi-agent workflow — supervisor, planner, parallel executors, aggregator — is now accessible as a REST API with streaming, batching, documentation, and an interactive playground, all for free.
