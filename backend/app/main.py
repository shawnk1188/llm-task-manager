"""FastAPI application factory."""

import os

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.chat import router as chat_router
from app.api.lists import router as lists_router

app = FastAPI(
    title="LLM Task Manager API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prometheus metrics ────────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(lists_router)
app.include_router(chat_router)


# ── Lifespan (Redis connection pool) ──────────────────────────────────────────
@app.on_event("startup")
async def startup():
    app.state.redis = aioredis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD"),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True,
    )
    # Smoke-test the connection
    await app.state.redis.ping()


@app.on_event("shutdown")
async def shutdown():
    await app.state.redis.aclose()


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health():
    try:
        await app.state.redis.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {"status": "ok" if redis_ok else "degraded", "redis": redis_ok}
