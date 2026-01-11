from fastapi import APIRouter
from typing import Dict, Any
from uuid import UUID

from app.models import PsychProfile

router = APIRouter()

@router.get("/profile/{entity_id}")
async def get_psych_profile(entity_id: UUID):
    """Get the psychological profile of an agent"""
    return {
        "entity_id": entity_id,
        "traits": ["brave", "loyal"],
        "goals": ["protect the queen"]
    }

@router.post("/check-consistency")
async def check_agent_consistency(entity_id: UUID, action: str):
    """Check if an action is consistent with the agent's psychology"""
    return {
        "entity_id": entity_id,
        "action": action,
        "verdict": "CONSISTENT",
        "reasoning": "The action aligns with the trait 'brave'."
    }
