"""Redis persistence layer for task lists."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

import redis.asyncio as aioredis

from app.models.task import ItemStatus, TaskItem, TaskList


class RedisService:
    _LIST_PREFIX = "tasklist:"

    def __init__(self, client: aioredis.Redis) -> None:
        self._r = client

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _key(self, list_id: str) -> str:
        return f"{self._LIST_PREFIX}{list_id}"

    def _name_index_key(self, name: str) -> str:
        return f"tasklist_name:{name.lower()}"

    async def _save(self, task_list: TaskList) -> None:
        pipe = self._r.pipeline()
        pipe.set(self._key(task_list.id), task_list.model_dump_json())
        pipe.set(self._name_index_key(task_list.name), task_list.id)
        await pipe.execute()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def create_list(self, name: str) -> TaskList:
        task_list = TaskList(name=name)
        await self._save(task_list)
        return task_list

    async def get_list_by_name(self, name: str) -> Optional[TaskList]:
        list_id = await self._r.get(self._name_index_key(name))
        if not list_id:
            return None
        return await self.get_list(list_id)

    async def get_list(self, list_id: str) -> Optional[TaskList]:
        data = await self._r.get(self._key(list_id))
        if not data:
            return None
        return TaskList.model_validate_json(data)

    async def list_all(self) -> List[TaskList]:
        keys = await self._r.keys(f"{self._LIST_PREFIX}*")
        if not keys:
            return []
        values = await self._r.mget(*keys)
        result = []
        for v in values:
            if v:
                result.append(TaskList.model_validate_json(v))
        return sorted(result, key=lambda x: x.created_at)

    async def add_item(self, list_id: str, text: str) -> Optional[TaskList]:
        task_list = await self.get_list(list_id)
        if not task_list:
            return None
        task_list.items.append(TaskItem(text=text))
        task_list.updated_at = datetime.now(timezone.utc)
        await self._save(task_list)
        return task_list

    async def update_item(
        self,
        list_id: str,
        item_id: str,
        text: Optional[str] = None,
        status: Optional[ItemStatus] = None,
    ) -> Optional[TaskList]:
        task_list = await self.get_list(list_id)
        if not task_list:
            return None
        for item in task_list.items:
            if item.id == item_id:
                if text is not None:
                    item.text = text
                if status is not None:
                    item.status = status
                item.updated_at = datetime.now(timezone.utc)
                break
        task_list.updated_at = datetime.now(timezone.utc)
        await self._save(task_list)
        return task_list

    async def remove_item(self, list_id: str, item_id: str) -> Optional[TaskList]:
        task_list = await self.get_list(list_id)
        if not task_list:
            return None
        task_list.items = [i for i in task_list.items if i.id != item_id]
        task_list.updated_at = datetime.now(timezone.utc)
        await self._save(task_list)
        return task_list

    async def delete_list(self, list_id: str) -> bool:
        task_list = await self.get_list(list_id)
        if not task_list:
            return False
        pipe = self._r.pipeline()
        pipe.delete(self._key(list_id))
        pipe.delete(self._name_index_key(task_list.name))
        await pipe.execute()
        return True
