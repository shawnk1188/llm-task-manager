"""Tests for the Redis service and API routes."""

from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.task import ItemStatus, TaskItem, TaskList
from app.services.redis_service import RedisService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def mock_redis():
    """Return a mock async Redis client."""
    client = AsyncMock()
    client.pipeline.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
    client.pipeline.return_value.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest_asyncio.fixture
async def svc(mock_redis):
    return RedisService(mock_redis)


# ── RedisService unit tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_list(svc, mock_redis):
    mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[True, True])
    task_list = await svc.create_list("Groceries")
    assert task_list.name == "Groceries"
    assert task_list.items == []
    assert task_list.id


@pytest.mark.asyncio
async def test_get_list_returns_none_when_missing(svc, mock_redis):
    mock_redis.get.return_value = None
    result = await svc.get_list("nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_add_item(svc, mock_redis):
    existing = TaskList(name="Work")
    mock_redis.get.return_value = existing.model_dump_json()
    mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[True, True])

    updated = await svc.add_item(existing.id, "Write tests")
    assert len(updated.items) == 1
    assert updated.items[0].text == "Write tests"
    assert updated.items[0].status == ItemStatus.pending


@pytest.mark.asyncio
async def test_delete_list(svc, mock_redis):
    existing = TaskList(name="ToDelete")
    mock_redis.get.return_value = existing.model_dump_json()
    mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[1, 1])

    result = await svc.delete_list(existing.id)
    assert result is True


@pytest.mark.asyncio
async def test_delete_list_not_found(svc, mock_redis):
    mock_redis.get.return_value = None
    result = await svc.delete_list("bad-id")
    assert result is False


@pytest.mark.asyncio
async def test_remove_item(svc, mock_redis):
    lst = TaskList(name="Test")
    item = TaskItem(text="Buy milk")
    lst.items.append(item)
    mock_redis.get.return_value = lst.model_dump_json()
    mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[True, True])

    updated = await svc.remove_item(lst.id, item.id)
    assert len(updated.items) == 0


@pytest.mark.asyncio
async def test_update_item_status(svc, mock_redis):
    lst = TaskList(name="Test")
    item = TaskItem(text="Do laundry")
    lst.items.append(item)
    mock_redis.get.return_value = lst.model_dump_json()
    mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[True, True])

    updated = await svc.update_item(lst.id, item.id, status=ItemStatus.done)
    assert updated.items[0].status == ItemStatus.done
