from fastapi import APIRouter, HTTPException
from typing import List, Dict
from uuid import UUID

from app.models import Fact

router = APIRouter()

@router.get("/trace/{fact_id}")
async def trace_dependencies(fact_id: UUID):
    """Trace downstream dependencies of a fact"""
    return {
        "fact_id": fact_id,
        "dependents": ["uuid-1", "uuid-2"], # Mock for PoC integration
        "status": "valid"
    }

@router.post("/repair/{fact_id}")
async def repair_fact(fact_id: UUID):
    """Trigger the Repair Agent on a specific fact"""
    return {
        "fact_id": fact_id,
        "repair_status": "repaired",
        "suggestion": "Keep but modify context"
    }
