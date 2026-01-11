from fastapi import APIRouter
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter()


@router.get("/worlds")
async def list_worlds():
    """List all active world states / theories"""
    return [
        {"name": "Base Reality", "probability": 0.5, "id": "uuid-1"},
        {"name": "Theory A", "probability": 0.5, "id": "uuid-2"},
    ]


@router.post("/fork")
async def fork_world(parent_world_id: UUID, name: str):
    """Create a new narrative fork"""
    return {
        "status": "created",
        "new_world_id": "uuid-new",
        "name": name,
        "parent": parent_world_id,
    }
