"""Pydantic models for the task manager domain."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ItemStatus(str, Enum):
    pending = "pending"
    done = "done"


class TaskItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    status: ItemStatus = ItemStatus.pending
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskList(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    items: List[TaskItem] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Request / Response schemas ────────────────────────────────────────────────

class CreateListRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class AddItemRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class UpdateItemRequest(BaseModel):
    text: Optional[str] = None
    status: Optional[ItemStatus] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = Field(default_factory=lambda: str(uuid4()))


class ChatResponse(BaseModel):
    reply: str
    session_id: str
