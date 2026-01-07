"""
Knowledge Graph endpoints
"""

from fastapi import APIRouter, Request, HTTPException
from typing import List, Optional
from uuid import UUID

from app.models import (
    Fact,
    Entity,
    Relationship,
    AddFactRequest,
    EntityType,
)

router = APIRouter()


@router.post("/knowledge/facts", response_model=Fact)
async def add_fact(request: AddFactRequest, req: Request):
    """
    Add a new fact to the knowledge graph.
    
    Facts represent established truths in the narrative that
    should be maintained for consistency.
    """
    knowledge_graph = req.app.state.knowledge_graph
    
    fact = Fact(
        subject=request.subject,
        predicate=request.predicate,
        object=request.object,
        source_text=request.source_text
    )
    
    await knowledge_graph.add_fact(fact)
    
    return fact


@router.get("/knowledge/facts")
async def get_all_facts(req: Request, limit: int = 100, offset: int = 0):
    """
    Retrieve all facts from the knowledge graph.
    """
    knowledge_graph = req.app.state.knowledge_graph
    facts = await knowledge_graph.get_facts(limit=limit, offset=offset)
    
    return {
        "facts": facts,
        "total": len(facts),
        "limit": limit,
        "offset": offset
    }


@router.get("/knowledge/facts/{fact_id}")
async def get_fact(fact_id: UUID, req: Request):
    """
    Retrieve a specific fact by ID.
    """
    knowledge_graph = req.app.state.knowledge_graph
    fact = await knowledge_graph.get_fact(fact_id)
    
    if not fact:
        raise HTTPException(status_code=404, detail=f"Fact {fact_id} not found")
    
    return fact


@router.delete("/knowledge/facts/{fact_id}")
async def delete_fact(fact_id: UUID, req: Request):
    """
    Remove a fact from the knowledge graph.
    """
    knowledge_graph = req.app.state.knowledge_graph
    success = await knowledge_graph.remove_fact(fact_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Fact {fact_id} not found")
    
    return {"deleted": True, "fact_id": str(fact_id)}


@router.post("/knowledge/entities", response_model=Entity)
async def add_entity(entity: Entity, req: Request):
    """
    Add a new entity to the knowledge graph.
    """
    knowledge_graph = req.app.state.knowledge_graph
    await knowledge_graph.add_entity(entity)
    return entity


@router.get("/knowledge/entities")
async def get_all_entities(
    req: Request,
    entity_type: Optional[EntityType] = None,
    limit: int = 100
):
    """
    Retrieve all entities, optionally filtered by type.
    """
    knowledge_graph = req.app.state.knowledge_graph
    entities = await knowledge_graph.get_entities(entity_type=entity_type, limit=limit)
    
    return {
        "entities": entities,
        "total": len(entities),
        "filter": entity_type.value if entity_type else None
    }


@router.get("/knowledge/entities/{entity_id}")
async def get_entity(entity_id: UUID, req: Request):
    """
    Retrieve a specific entity with all its relationships.
    """
    knowledge_graph = req.app.state.knowledge_graph
    entity = await knowledge_graph.get_entity(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    
    relationships = await knowledge_graph.get_entity_relationships(entity_id)
    
    return {
        "entity": entity,
        "relationships": relationships
    }


@router.post("/knowledge/relationships", response_model=Relationship)
async def add_relationship(relationship: Relationship, req: Request):
    """
    Add a relationship between two entities.
    """
    knowledge_graph = req.app.state.knowledge_graph
    
    # Verify both entities exist
    source = await knowledge_graph.get_entity(relationship.source_entity_id)
    target = await knowledge_graph.get_entity(relationship.target_entity_id)
    
    if not source:
        raise HTTPException(
            status_code=404, 
            detail=f"Source entity {relationship.source_entity_id} not found"
        )
    if not target:
        raise HTTPException(
            status_code=404,
            detail=f"Target entity {relationship.target_entity_id} not found"
        )
    
    await knowledge_graph.add_relationship(relationship)
    return relationship


@router.get("/knowledge/graph")
async def get_graph_data(req: Request):
    """
    Get the complete knowledge graph in a visualization-friendly format.
    
    Returns nodes (entities) and edges (relationships) for graph rendering.
    """
    knowledge_graph = req.app.state.knowledge_graph
    
    entities = await knowledge_graph.get_entities(limit=1000)
    relationships = await knowledge_graph.get_all_relationships()
    
    # Transform for visualization
    nodes = [
        {
            "id": str(e.id),
            "label": e.name,
            "type": e.type.value,
            "attributes": e.attributes
        }
        for e in entities
    ]
    
    edges = [
        {
            "id": str(r.id),
            "source": str(r.source_entity_id),
            "target": str(r.target_entity_id),
            "label": r.relationship_type,
            "properties": r.properties
        }
        for r in relationships
    ]
    
    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


@router.post("/knowledge/query")
async def query_knowledge(query: str, req: Request):
    """
    Query the knowledge graph using natural language.
    
    Example queries:
    - "What is Alice's occupation?"
    - "Who is friends with Bob?"
    - "Where did the murder take place?"
    """
    knowledge_graph = req.app.state.knowledge_graph
    ml_service = req.app.state.ml_service
    
    # Parse natural language query
    parsed = await ml_service.parse_query(query)
    
    # Execute query on knowledge graph
    results = await knowledge_graph.query(parsed)
    
    return {
        "query": query,
        "parsed": parsed,
        "results": results
    }


@router.delete("/knowledge/clear")
async def clear_knowledge_graph(req: Request, confirm: bool = False):
    """
    Clear all data from the knowledge graph.
    
    Requires confirmation flag to prevent accidental deletion.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear knowledge graph"
        )
    
    knowledge_graph = req.app.state.knowledge_graph
    await knowledge_graph.clear()
    
    return {"cleared": True, "message": "Knowledge graph has been cleared"}
