"""REST API routes for task list CRUD operations."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.task import AddItemRequest, CreateListRequest, TaskList, UpdateItemRequest
from app.services.redis_service import RedisService
from app.api.deps import get_redis_service

router = APIRouter(prefix="/api/lists", tags=["lists"])


@router.get("", response_model=List[TaskList])
async def get_all_lists(svc: RedisService = Depends(get_redis_service)):
    return await svc.list_all()


@router.post("", response_model=TaskList, status_code=status.HTTP_201_CREATED)
async def create_list(body: CreateListRequest, svc: RedisService = Depends(get_redis_service)):
    existing = await svc.get_list_by_name(body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"List '{body.name}' already exists.")
    return await svc.create_list(body.name)


@router.get("/by-name/{name}", response_model=TaskList)
async def get_list_by_name(name: str, svc: RedisService = Depends(get_redis_service)):
    lst = await svc.get_list_by_name(name)
    if not lst:
        raise HTTPException(status_code=404, detail=f"List '{name}' not found.")
    return lst


@router.get("/{list_id}", response_model=TaskList)
async def get_list(list_id: str, svc: RedisService = Depends(get_redis_service)):
    lst = await svc.get_list(list_id)
    if not lst:
        raise HTTPException(status_code=404, detail="List not found.")
    return lst


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(list_id: str, svc: RedisService = Depends(get_redis_service)):
    deleted = await svc.delete_list(list_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="List not found.")


@router.post("/{list_id}/items", response_model=TaskList, status_code=status.HTTP_201_CREATED)
async def add_item(list_id: str, body: AddItemRequest, svc: RedisService = Depends(get_redis_service)):
    lst = await svc.add_item(list_id, body.text)
    if not lst:
        raise HTTPException(status_code=404, detail="List not found.")
    return lst


@router.patch("/{list_id}/items/{item_id}", response_model=TaskList)
async def update_item(
    list_id: str,
    item_id: str,
    body: UpdateItemRequest,
    svc: RedisService = Depends(get_redis_service),
):
    lst = await svc.update_item(list_id, item_id, text=body.text, status=body.status)
    if not lst:
        raise HTTPException(status_code=404, detail="List or item not found.")
    return lst


@router.delete("/{list_id}/items/{item_id}", response_model=TaskList)
async def remove_item(list_id: str, item_id: str, svc: RedisService = Depends(get_redis_service)):
    lst = await svc.remove_item(list_id, item_id)
    if not lst:
        raise HTTPException(status_code=404, detail="List or item not found.")
    return lst
