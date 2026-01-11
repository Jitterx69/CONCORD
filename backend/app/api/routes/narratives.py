"""
Narrative management endpoints
"""

from fastapi import APIRouter, Request, HTTPException
from typing import List, Optional
from uuid import UUID
import time

from app.models import (
    Narrative,
    NarrativeSegment,
    NarrativeCreateRequest,
    NarrativeUpdateRequest,
    ConsistencyCheckRequest,
)

router = APIRouter()

# In-memory storage for demo (use database in production)
_narratives: dict[UUID, Narrative] = {}


@router.post("/narratives", response_model=Narrative)
async def create_narrative(request: NarrativeCreateRequest, req: Request):
    """
    Create a new narrative.

    Optionally provide initial text which will be analyzed
    and stored as the first segment.
    """
    narrative = Narrative(title=request.title, description=request.description)

    # If initial text provided, create first segment
    if request.initial_text:
        segment = NarrativeSegment(text=request.initial_text, position=0)
        narrative.segments.append(segment)

        # Extract and store initial facts
        ml_service = req.app.state.ml_service
        knowledge_graph = req.app.state.knowledge_graph

        facts = await ml_service.extract_facts(request.initial_text)
        entities = await ml_service.extract_entities(request.initial_text)

        for fact in facts:
            await knowledge_graph.add_fact(fact)

        for entity in entities:
            await knowledge_graph.add_entity(entity)

    _narratives[narrative.id] = narrative
    return narrative


@router.get("/narratives")
async def list_narratives(limit: int = 50, offset: int = 0):
    """
    List all narratives.
    """
    narratives = list(_narratives.values())
    paginated = narratives[offset : offset + limit]

    return {
        "narratives": [
            {
                "id": str(n.id),
                "title": n.title,
                "description": n.description,
                "segment_count": len(n.segments),
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat(),
            }
            for n in paginated
        ],
        "total": len(narratives),
        "limit": limit,
        "offset": offset,
    }


@router.get("/narratives/{narrative_id}", response_model=Narrative)
async def get_narrative(narrative_id: UUID):
    """
    Get a specific narrative by ID.
    """
    if narrative_id not in _narratives:
        raise HTTPException(
            status_code=404, detail=f"Narrative {narrative_id} not found"
        )

    return _narratives[narrative_id]


@router.put("/narratives/{narrative_id}")
async def update_narrative(
    narrative_id: UUID, request: NarrativeUpdateRequest, req: Request
):
    """
    Add new text to an existing narrative.

    The new text will be checked for consistency against
    the existing narrative before being added.
    """
    if narrative_id not in _narratives:
        raise HTTPException(
            status_code=404, detail=f"Narrative {narrative_id} not found"
        )

    narrative = _narratives[narrative_id]

    # First, check consistency of new text
    existing_text = " ".join([seg.text for seg in narrative.segments])
    full_text = existing_text + " " + request.text

    # Get consistency report
    knowledge_graph = req.app.state.knowledge_graph
    constraint_engine = req.app.state.constraint_engine
    temporal_reasoner = req.app.state.temporal_reasoner
    ml_service = req.app.state.ml_service

    # Extract facts from new text
    new_facts = await ml_service.extract_facts(request.text)

    # Check for conflicts
    conflicts = await knowledge_graph.check_conflicts(new_facts)

    # If no critical conflicts, add the segment
    critical_conflicts = [c for c in conflicts if c.level.value == "critical"]

    if critical_conflicts:
        return {
            "success": False,
            "message": "New text has critical consistency issues",
            "conflicts": [
                {
                    "type": c.type.value,
                    "description": c.description,
                    "suggested_fix": c.suggested_fix,
                }
                for c in critical_conflicts
            ],
        }

    # Add segment
    position = (
        request.position if request.position is not None else len(narrative.segments)
    )
    segment = NarrativeSegment(text=request.text, position=position)

    if request.position is not None:
        # Insert at position
        narrative.segments.insert(position, segment)
        # Update positions of subsequent segments
        for i, seg in enumerate(narrative.segments[position + 1 :], start=position + 1):
            seg.position = i
    else:
        narrative.segments.append(segment)

    # Update narrative timestamp
    from datetime import datetime

    narrative.updated_at = datetime.utcnow()

    # Store new facts
    for fact in new_facts:
        await knowledge_graph.add_fact(fact)

    return {
        "success": True,
        "narrative": narrative,
        "warnings": [
            {"type": c.type.value, "description": c.description}
            for c in conflicts
            if c.level.value == "warning"
        ],
    }


@router.delete("/narratives/{narrative_id}")
async def delete_narrative(narrative_id: UUID):
    """
    Delete a narrative.
    """
    if narrative_id not in _narratives:
        raise HTTPException(
            status_code=404, detail=f"Narrative {narrative_id} not found"
        )

    del _narratives[narrative_id]
    return {"deleted": True, "narrative_id": str(narrative_id)}


@router.get("/narratives/{narrative_id}/analyze")
async def analyze_narrative(narrative_id: UUID, req: Request):
    """
    Perform a complete consistency analysis on an existing narrative.
    """
    if narrative_id not in _narratives:
        raise HTTPException(
            status_code=404, detail=f"Narrative {narrative_id} not found"
        )

    narrative = _narratives[narrative_id]
    full_text = " ".join([seg.text for seg in narrative.segments])

    # Use consistency check endpoint logic
    from app.api.routes.consistency import check_consistency

    check_request = ConsistencyCheckRequest(
        text=full_text, check_emotional=True, check_temporal=True, auto_fix=False
    )

    result = await check_consistency(check_request, req)

    return {
        "narrative_id": str(narrative_id),
        "title": narrative.title,
        "segment_count": len(narrative.segments),
        "analysis": result,
    }


@router.get("/narratives/{narrative_id}/timeline")
async def get_narrative_timeline(narrative_id: UUID, req: Request):
    """
    Extract and visualize the timeline from a narrative.
    """
    if narrative_id not in _narratives:
        raise HTTPException(
            status_code=404, detail=f"Narrative {narrative_id} not found"
        )

    narrative = _narratives[narrative_id]
    full_text = " ".join([seg.text for seg in narrative.segments])

    temporal_reasoner = req.app.state.temporal_reasoner
    timeline = await temporal_reasoner.extract_timeline(full_text)

    return {"narrative_id": str(narrative_id), "timeline": timeline}


@router.get("/narratives/{narrative_id}/entities")
async def get_narrative_entities(narrative_id: UUID, req: Request):
    """
    Get all entities mentioned in a narrative.
    """
    if narrative_id not in _narratives:
        raise HTTPException(
            status_code=404, detail=f"Narrative {narrative_id} not found"
        )

    narrative = _narratives[narrative_id]
    full_text = " ".join([seg.text for seg in narrative.segments])

    ml_service = req.app.state.ml_service
    entities = await ml_service.extract_entities(full_text)

    return {
        "narrative_id": str(narrative_id),
        "entities": entities,
        "count": len(entities),
    }
