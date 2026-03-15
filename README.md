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

[Getting Started](#-getting-started) · [Architecture](#-architecture) · [Chat Commands](#-chat-commands) · [API Docs](#-api-reference) · [Contributing](#-contributing)

</div>

---

## ✨ Features

- 💬 **Natural language interface** — create, view, update, and delete task lists through conversation
- 🤖 **Google ADK agent** — Gemini Flash decides which tool to call based on your intent
- ⚡ **FastAPI backend** — async REST API with full OpenAPI docs
- 🗃️ **Redis persistence** — all lists and items survive container restarts
- 🐳 **Podman Compose** — fully containerised, runs entirely locally
- 📊 **Prometheus metrics** — request counts, latency, and error rates out of the box
- 🔁 **Automatic retry** — exponential backoff on Gemini rate limits (429s)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Podman network: task-net                      │
│                                                                  │
│   ┌─────────────┐     HTTP      ┌──────────────────────────┐    │
│   │  Streamlit  │ ────────────► │      FastAPI Backend     │    │
│   │  :8501      │               │      :8000               │    │
│   │  Chat UI    │               │                          │    │
│   └─────────────┘               │  ┌────────────────────┐  │    │
│                                 │  │  Google ADK Agent  │  │    │
│   ┌─────────────┐               │  │  gemini-2.0-flash  │  │    │
│   │ Prometheus  │ ◄──metrics──  │  │  -lite             │  │    │
│   │  :9090      │               │  └─────────┬──────────┘  │    │
│   └─────────────┘               │            │ tools        │    │
│                                 │  ┌─────────▼──────────┐  │    │
│                                 │  │   Redis Service    │  │    │
│                                 │  └────────────────────┘  │    │
│                                 └────────────┬─────────────┘    │
│                                              │                   │
│                                    ┌─────────▼──────────┐       │
│                                    │       Redis         │       │
│                                    │       :6379         │       │
│                                    └────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                                          │
                                 ┌────────▼────────┐
                                 │  Google Gemini  │
                                 │  API (external) │
                                 └─────────────────┘
```

### Container overview

| Container | Image | Port | Role |
|-----------|-------|------|------|
| `streamlit-app` | python:3.12-slim | 8501 | Chat UI |
| `fastapi-app` | python:3.12-slim | 8000 | REST API + ADK agent |
| `redis` | redis:7-alpine | 6379 | Task persistence |
| `prometheus` | prom/prometheus | 9090 | Metrics scraping |

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
│   │   ├── main.py              # FastAPI app factory, lifespan, CORS
│   │   ├── api/
│   │   │   ├── chat.py          # POST /api/chat → ADK agent
│   │   │   ├── lists.py         # CRUD routes for task lists
│   │   │   └── deps.py          # Dependency injection
│   │   ├── agent/
│   │   │   └── task_agent.py    # ADK agent, tools, Runner singleton
│   │   ├── models/
│   │   │   └── task.py          # Pydantic models (TaskList, TaskItem)
│   │   └── services/
│   │       └── redis_service.py # Async Redis CRUD layer
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
│   └── dev.sh                   # up / rebuild / down / logs / test
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

## 🤖 Agent & Tools

The ADK agent is defined in `backend/app/agent/task_agent.py`. It exposes 7 tools that map to REST calls against the FastAPI backend:

| Tool | Description |
|------|-------------|
| `list_all_lists` | Summarise all task lists |
| `get_list` | Show all items in a named list |
| `create_list` | Create a new list |
| `add_item` | Add an item to a list |
| `mark_item_done` | Mark an item as completed |
| `remove_item` | Delete a single item |
| `delete_list` | Delete an entire list |

The agent uses a **module-level `Runner` singleton** so session state is preserved across the lifetime of the container — multi-turn conversations work out of the box.

---

## 📡 API Reference

Full interactive docs available at **http://localhost:8000/docs** once running.

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
./scripts/dev.sh rebuild               # Force no-cache rebuild
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
| `BACKEND_URL` | `http://fastapi-app:8000` | Internal backend URL (used by Streamlit + agent) |
| `API_SECRET_KEY` | — | Secret key for future auth middleware |

---

## 🐛 Troubleshooting

**`ImportError: LiteLLM support requires pip install google-adk[extensions]`**
Stale Docker layer. Run `./scripts/dev.sh rebuild` to force a clean no-cache build.

**`SessionNotFoundError`**
The in-memory session service resets on container restart, but Streamlit may be replaying an old session ID. Click **New session** in the sidebar to generate a fresh one.

**`429 RESOURCE_EXHAUSTED`**
You've hit the Gemini free tier rate limit. The app retries automatically with exponential backoff. If it keeps happening, wait 60 seconds or consider enabling billing on your Google Cloud project.

**`{"status": "degraded", "redis": false}` on `/health`**
Redis isn't reachable yet. Check `podman logs redis` — it may still be initialising.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push and open a PR

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
