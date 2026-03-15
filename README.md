# 🗂️ LLM Task Manager

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.41-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-1.0+-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://google.github.io/adk-docs)
[![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash%20Lite-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev)
[![Podman](https://img.shields.io/badge/Podman-Compose-892CA0?style=for-the-badge&logo=podman&logoColor=white)](https://podman.io)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

**A production-grade conversational task manager powered by Google ADK + Gemini Flash.**
Talk to your lists. No forms, no clicks — just chat.

[Getting Started](#-getting-started) · [System Design](#-system-design) · [Chat Commands](#-chat-commands) · [API Docs](#-api-reference) · [Contributing](#-contributing)

</div>

---

## ✨ Features

- 💬 **Natural language interface** — create, view, update, and delete task lists through conversation
- 🤖 **Google ADK agent** — Gemini Flash decides which tool to call based on your intent
- ⚡ **FastAPI backend** — async REST API with full OpenAPI docs at `/docs`
- 🗃️ **Redis persistence** — all lists and items survive container restarts via a named volume
- 🐳 **Podman Compose** — fully containerised, runs entirely locally with one command
- 📊 **Prometheus metrics** — request counts, latency, and error rates out of the box
- 🔁 **Automatic retry** — exponential backoff on Gemini rate limits (429s)

---

## 🏗️ System Design

### 1. Container architecture

All services run inside a shared Podman network (`task-net`). The only public-facing ports are 8501 (UI) and 8000 (API). Redis is internal-only.

```
                        ┌─────────────────────────────────────────────────────┐
                        │               Podman network: task-net               │
                        │                                                      │
          Browser       │   ┌──────────────────┐                              │
        ──────────────► │   │   Streamlit :8501 │                              │
                        │   │   Chat UI         │                              │
                        │   └────────┬─────────┘                              │
                        │            │ HTTP POST /api/chat                     │
                        │   ┌────────▼──────────────────┐  scrape  ┌────────┐ │
                        │   │   FastAPI :8000            │ ◄─────── │Prom.   │ │
                        │   │   REST API + ADK Runner    │          │:9090   │ │
                        │   │                            │          └────────┘ │
                        │   │  ┌──────────────────────┐  │                    │
                        │   │  │  Google ADK Agent    │  │                    │
                        │   │  │  tools → REST calls  │  │                    │
                        │   │  └──────────┬───────────┘  │                    │
                        │   └────────────┼───────────────┘                    │
                        │                │ Redis commands                      │
                        │   ┌────────────▼──────────┐                         │
                        │   │   Redis :6379          │                         │
                        │   │   + redis-data volume  │                         │
                        │   └───────────────────────┘                         │
                        └─────────────────────────────────────────────────────┘
                                          │
                               ┌──────────▼──────────┐
                               │  Google Gemini API   │
                               │  gemini-2.0-flash    │
                               │  -lite (external)    │
                               └─────────────────────┘
```

### 2. Request lifecycle

Every chat message follows this path through the stack:

```
User types message
        │
        ▼
Streamlit (POST /api/chat)
  { message: "...", session_id: "uuid" }
        │
        ▼
FastAPI chat route
  validates request → calls run_agent_safe()
        │
        ▼
ADK Runner (module-level singleton)
  looks up / creates InMemorySession
        │
        ▼
Gemini Flash Lite
  reads system prompt + tool schemas
  decides which tool to invoke
        │
     ┌──┴───────────────────────────┐
     │                              │
     ▼                              ▼
  Read tool                    Write tool
  (get_list,                   (create_list,
   list_all_lists)               add_item,
     │                            delete_list …)
     └──────────────┬─────────────┘
                    │ HTTP → FastAPI REST → RedisService
                    ▼
               Redis :6379
                    │
                    ▼
         Tool result returned to ADK
                    │
                    ▼
         Gemini composes final reply
                    │
                    ▼
         FastAPI returns { reply, session_id }
                    │
                    ▼
         Streamlit renders markdown in chat
```

### 3. Redis data model

Lists are stored as JSON blobs. A secondary name index allows lookups by human-readable name without scanning all keys.

```
Key layout
──────────────────────────────────────────────────────────
tasklist_name:{name}   →  "{uuid}"           (name index)
tasklist:{uuid}        →  JSON blob          (main record)

TaskList JSON schema
──────────────────────────────────────────────────────────
{
  "id":         "550e8400-e29b-41d4-a716-446655440000",
  "name":       "Groceries",
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-01T10:05:00Z",
  "items": [
    {
      "id":         "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "text":       "Buy milk",
      "status":     "pending",            ← or "done"
      "created_at": "2025-01-01T10:01:00Z",
      "updated_at": "2025-01-01T10:01:00Z"
    }
  ]
}

Lookup paths
──────────────────────────────────────────────────────────
By name  →  GET tasklist_name:{name}  →  UUID
             →  GET tasklist:{UUID}  →  full object

By ID    →  GET tasklist:{UUID}       →  full object
```

Items are stored **inline** inside the list JSON. There are no separate item keys. This keeps all list data in a single Redis GET/SET and avoids multi-key transactions for most operations.

### 4. ADK agent internals

The agent is a **module-level singleton** — `Runner`, `Agent`, and `InMemorySessionService` are all initialised once at import time and reused across all requests.

```
task_agent.py (module scope)
─────────────────────────────────────────────────────────
_task_agent = Agent(
    model = "gemini-2.0-flash-lite",
    tools = [ list_all_lists, get_list, create_list,
              add_item, mark_item_done, remove_item,
              delete_list ]
)
_session_service = InMemorySessionService()
_runner = Runner(agent=_task_agent,
                 session_service=_session_service)

Per-request flow (run_agent_safe)
─────────────────────────────────────────────────────────
1. get_session(session_id)  →  None if first visit
2. create_session() if None
3. runner.run_async(user_message)
4. stream events → collect final_response parts
5. return joined text
6. on 429 → sleep(2^attempt) → retry up to 3×
```

---

## 📁 Project Structure

```
llm-task-manager/
├── frontend/
│   ├── app.py                   # Streamlit chat UI
│   ├── Dockerfile
│   ├── .dockerignore
│   └── requirements.txt
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, Redis lifespan, CORS, Prometheus
│   │   ├── api/
│   │   │   ├── chat.py          # POST /api/chat → run_agent_safe()
│   │   │   ├── lists.py         # Full CRUD routes for task lists + items
│   │   │   └── deps.py          # get_redis_service() dependency
│   │   ├── agent/
│   │   │   └── task_agent.py    # ADK agent, 7 tools, Runner singleton, retry
│   │   ├── models/
│   │   │   └── task.py          # TaskList, TaskItem, request/response schemas
│   │   └── services/
│   │       └── redis_service.py # Async Redis CRUD (create/get/add/update/delete)
│   ├── tests/
│   │   └── test_redis_service.py
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── pytest.ini
│   └── requirements.txt
├── infra/
│   └── prometheus/
│       └── prometheus.yml
├── scripts/
│   └── dev.sh                   # up / rebuild / down / logs / test / redis-cli
├── podman-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- [Podman](https://podman.io/getting-started/installation) + [podman-compose](https://github.com/containers/podman-compose)
- A [Google AI Studio](https://aistudio.google.com) API key (free tier works)

### 1. Clone and configure

```bash
git clone https://github.com/your-username/llm-task-manager.git
cd llm-task-manager

cp .env.example .env
```

Open `.env` and fill in your key:

```env
GOOGLE_API_KEY=your_google_api_key_here
REDIS_PASSWORD=changeme_in_prod
```

### 2. Build and start

```bash
podman-compose up --build -d
```

Or using the dev helper:

```bash
./scripts/dev.sh up
```

### 3. Open the app

| Service | URL |
|---------|-----|
| 💬 Chat UI | http://localhost:8501 |
| 📖 API Docs | http://localhost:8000/docs |
| 📊 Metrics | http://localhost:9090 |

---

## 💬 Chat Commands

The agent understands natural language — these are just examples:

| Intent | Example prompt |
|--------|---------------|
| See all lists | `What lists do I have?` |
| Create a list | `Create a list called Groceries` |
| View a list | `Show me my Groceries list` |
| Add an item | `Add milk and eggs to Groceries` |
| Mark as done | `Mark item a1b2c3d4 as done in Groceries` |
| Remove an item | `Remove item a1b2c3d4 from Groceries` |
| Delete a list | `Delete the Groceries list` |

> **Tip:** When viewing a list, each item shows a short 8-character ID (e.g. `a1b2c3d4`). Use that ID to reference items in follow-up commands.

---

## 🤖 Agent Tools

The ADK agent exposes 7 tools that map to FastAPI REST calls:

| Tool | HTTP call | Description |
|------|-----------|-------------|
| `list_all_lists` | `GET /api/lists` | Summarise all task lists |
| `get_list` | `GET /api/lists/by-name/{name}` | Show items in a named list |
| `create_list` | `POST /api/lists` | Create a new list |
| `add_item` | `POST /api/lists/{id}/items` | Add an item to a list |
| `mark_item_done` | `PATCH /api/lists/{id}/items/{item_id}` | Mark item completed |
| `remove_item` | `DELETE /api/lists/{id}/items/{item_id}` | Remove a single item |
| `delete_list` | `DELETE /api/lists/{id}` | Delete an entire list |

---

## 📡 API Reference

Full interactive docs at **http://localhost:8000/docs**.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send a message to the agent |
| `GET` | `/api/lists` | Get all task lists |
| `POST` | `/api/lists` | Create a new list |
| `GET` | `/api/lists/{id}` | Get a list by ID |
| `GET` | `/api/lists/by-name/{name}` | Get a list by name |
| `DELETE` | `/api/lists/{id}` | Delete a list |
| `POST` | `/api/lists/{id}/items` | Add an item |
| `PATCH` | `/api/lists/{id}/items/{item_id}` | Update an item |
| `DELETE` | `/api/lists/{id}/items/{item_id}` | Remove an item |
| `GET` | `/health` | Health check (Redis ping) |
| `GET` | `/metrics` | Prometheus metrics |

---

## 🛠️ Dev Scripts

```bash
./scripts/dev.sh up                    # Build and start all containers
./scripts/dev.sh rebuild               # Force no-cache rebuild (fixes stale image issues)
./scripts/dev.sh down                  # Stop all containers
./scripts/dev.sh logs                  # Tail fastapi-app logs
./scripts/dev.sh logs streamlit-app    # Tail a specific container
./scripts/dev.sh test                  # Run pytest suite
./scripts/dev.sh redis-cli             # Open Redis CLI inside container
./scripts/dev.sh reset-redis           # Flush all Redis data (destructive!)
```

---

## 🧪 Running Tests

```bash
./scripts/dev.sh test
```

Or directly:

```bash
cd backend
pip install pytest pytest-asyncio
pytest -v
```

Tests cover the full Redis service layer with async mocks — no live Redis required.

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | — | **Required.** Google AI Studio API key |
| `REDIS_HOST` | `redis` | Redis hostname (container name) |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | `changeme_in_prod` | Redis auth password |
| `REDIS_DB` | `0` | Redis database index |
| `BACKEND_URL` | `http://fastapi-app:8000` | Internal backend URL (Streamlit + agent) |
| `API_SECRET_KEY` | — | Secret key for future auth middleware |

---

## 🐛 Troubleshooting

**`ImportError: LiteLLM support requires pip install google-adk[extensions]`**
Stale Docker layer. Run `./scripts/dev.sh rebuild` to force a clean no-cache build.

**`SessionNotFoundError`**
The in-memory session service resets on container restart, but Streamlit may be replaying an old session ID. Click **New session** in the sidebar to generate a fresh one.

**`429 RESOURCE_EXHAUSTED`**
You've hit the Gemini free tier rate limit. The app retries automatically with exponential backoff (1s → 2s → error message). If it persists, wait 60 seconds or enable billing on your Google Cloud project.

**`{"status": "degraded", "redis": false}` on `/health`**
Redis isn't reachable yet. Check `podman logs redis` — it may still be initialising on first boot.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit: `git commit -m 'feat: add my feature'`
4. Push and open a PR

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
