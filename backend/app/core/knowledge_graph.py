"""
Narrative Knowledge Graph - Core CONCORD Component

Maintains a dynamic graph of all established facts, entities,
relationships, and states in the narrative.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncio

from app.models import (
    Entity,
    EntityType,
    Relationship,
    Fact,
    ConsistencyIssue,
    ConsistencyLevel,
    ConstraintType,
)


class KnowledgeGraph:
    """
    In-memory knowledge graph for storing narrative facts and entities.

    In production, this would be backed by Neo4j for persistence
    and advanced graph queries.
    """

    def __init__(self):
        self._entities: Dict[UUID, Entity] = {}
        self._relationships: Dict[UUID, Relationship] = {}
        self._facts: Dict[UUID, Fact] = {}
        self._fact_index: Dict[str, List[UUID]] = {}  # subject -> fact_ids
        self._dependent_index: Dict[UUID, List[UUID]] = (
            {}
        )  # fact_id -> list of dependent fact_ids (reverse dependency)

    async def add_entity(self, entity: Entity) -> None:
        """Add an entity to the knowledge graph."""
        self._entities[entity.id] = entity

    async def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        return self._entities.get(entity_id)

    async def get_entities(
        self, entity_type: Optional[EntityType] = None, limit: int = 100
    ) -> List[Entity]:
        """Get all entities, optionally filtered by type."""
        entities = list(self._entities.values())

        if entity_type:
            entities = [e for e in entities if e.type == entity_type]

        return entities[:limit]

    async def find_entity_by_name(self, name: str) -> Optional[Entity]:
        """Find an entity by name (case-insensitive)."""
        name_lower = name.lower()
        for entity in self._entities.values():
            if entity.name.lower() == name_lower:
                return entity
        return None

    async def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship between entities."""
        self._relationships[relationship.id] = relationship

    async def get_entity_relationships(self, entity_id: UUID) -> List[Relationship]:
        """Get all relationships involving an entity."""
        return [
            r
            for r in self._relationships.values()
            if r.source_entity_id == entity_id or r.target_entity_id == entity_id
        ]

    async def get_all_relationships(self) -> List[Relationship]:
        """Get all relationships."""
        return list(self._relationships.values())

    async def add_fact(
        self,
        subject: str,
        predicate: str,
        object_: str,
        world_id: Optional[str] = None,
        dependencies: Optional[List[UUID]] = None,
    ) -> Fact:
        """Add a fact to the graph and publish an event"""
        fact_id = uuid4()
        fact = Fact(
            id=fact_id,
            subject=subject,
            predicate=predicate,
            object=object_,
            timestamp=datetime.now(),
            world_id=world_id,
            validity_status="VALID",
            dependencies=dependencies if dependencies is not None else [],
        )
        self._facts[fact_id] = fact

        # Index by subject for quick lookup
        if fact.subject not in self._fact_index:
            self._fact_index[fact.subject] = []
        self._fact_index[fact.subject].append(fact.id)

        # Index dependencies (reverse lookup)
        for dep_id in fact.dependencies:
            if dep_id not in self._dependent_index:
                self._dependent_index[dep_id] = []
            self._dependent_index[dep_id].append(fact.id)

        # Publish Event
        EventBus().publish(
            "narrative.facts.created",
            {
                "fact_id": str(fact_id),
                "subject": subject,
                "predicate": predicate,
                "object": object_,
                "world_id": world_id,
                "timestamp": str(fact.timestamp),
            },
        )

        return fact

    async def get_fact(self, fact_id: UUID) -> Optional[Fact]:
        """Retrieve a fact by ID."""
        return self._facts.get(fact_id)

    async def get_facts(self, limit: int = 100, offset: int = 0) -> List[Fact]:
        """Get all facts with pagination."""
        facts = list(self._facts.values())
        return facts[offset : offset + limit]

    async def get_dependents(self, fact_id: UUID) -> List[Fact]:
        """Get all facts that depend on the given fact ID."""
        dep_ids = self._dependent_index.get(fact_id, [])
        return [self._facts[fid] for fid in dep_ids if fid in self._facts]

    async def get_facts_by_subject(self, subject: str) -> List[Fact]:
        """Get all facts about a subject."""
        fact_ids = self._fact_index.get(subject, [])
        return [self._facts[fid] for fid in fact_ids if fid in self._facts]

    async def remove_fact(self, fact_id: UUID) -> bool:
        """Remove a fact from the knowledge graph."""
        if fact_id not in self._facts:
            return False

        fact = self._facts[fact_id]
        del self._facts[fact_id]

        # Remove from index
        if fact.subject in self._fact_index:
            self._fact_index[fact.subject] = [
                fid for fid in self._fact_index[fact.subject] if fid != fact_id
            ]

        # Remove from dependent index
        if fact_id in self._dependent_index:
            del self._dependent_index[fact_id]

        return True

    async def check_conflicts(self, new_facts: List[Fact]) -> List[ConsistencyIssue]:
        """
        Check if new facts conflict with existing facts.

        Returns a list of consistency issues if conflicts are found.
        """
        issues = []

        for new_fact in new_facts:
            existing_facts = await self.get_facts_by_subject(new_fact.subject)

            for existing in existing_facts:
                # Check if same predicate but different object (contradiction)
                if existing.predicate == new_fact.predicate:
                    if existing.object != new_fact.object:
                        issue = ConsistencyIssue(
                            type=ConstraintType.FACTUAL,
                            level=ConsistencyLevel.INCONSISTENT,
                            description=f"Contradiction: '{new_fact.subject}' has conflicting values for '{new_fact.predicate}'. "
                            f"Existing: '{existing.object}', New: '{new_fact.object}'",
                            conflicting_facts=[existing.id, new_fact.id],
                            evidence=[
                                f"Existing fact: {existing.subject} {existing.predicate} {existing.object}",
                                f"New fact: {new_fact.subject} {new_fact.predicate} {new_fact.object}",
                            ],
                            suggested_fix=f"Clarify whether {new_fact.subject}'s {new_fact.predicate} is '{existing.object}' or '{new_fact.object}'",
                            confidence=0.9,
                        )
                        issues.append(issue)

        return issues

    async def query(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute a parsed query on the knowledge graph.

        Query format:
        {
            "type": "attribute" | "relationship" | "exists",
            "subject": "entity_name",
            "predicate": "attribute_or_relationship",
            "object": optional specific value to match
        }
        """
        results = []
        query_type = parsed_query.get("type", "attribute")
        subject = parsed_query.get("subject", "")
        predicate = parsed_query.get("predicate")

        if query_type == "attribute":
            facts = await self.get_facts_by_subject(subject)
            for fact in facts:
                if predicate is None or fact.predicate == predicate:
                    results.append(
                        {
                            "subject": fact.subject,
                            "predicate": fact.predicate,
                            "object": fact.object,
                            "confidence": fact.confidence,
                        }
                    )

        elif query_type == "relationship":
            entity = await self.find_entity_by_name(subject)
            if entity:
                relationships = await self.get_entity_relationships(entity.id)
                for rel in relationships:
                    if predicate is None or rel.relationship_type == predicate:
                        # Get the other entity in the relationship
                        other_id = (
                            rel.target_entity_id
                            if rel.source_entity_id == entity.id
                            else rel.source_entity_id
                        )
                        other_entity = await self.get_entity(other_id)
                        results.append(
                            {
                                "relationship": rel.relationship_type,
                                "entity": (
                                    other_entity.name if other_entity else "Unknown"
                                ),
                                "properties": rel.properties,
                            }
                        )

        elif query_type == "exists":
            entity = await self.find_entity_by_name(subject)
            results.append(
                {
                    "exists": entity is not None,
                    "entity": entity.dict() if entity else None,
                }
            )

        return results

    async def clear(self) -> None:
        """Clear all data from the knowledge graph."""
        self._entities.clear()
        self._relationships.clear()
        self._facts.clear()
        self._fact_index.clear()
        self._dependent_index.clear()

    def stats(self) -> Dict[str, int]:
        """Get statistics about the knowledge graph."""
        return {
            "entities": len(self._entities),
            "relationships": len(self._relationships),
            "facts": len(self._facts),
        }

    async def create_snapshot(self) -> Dict[str, Any]:
        """Create a deep copy snapshot of the current graph state."""
        import copy

        return {
            "entities": copy.deepcopy(self._entities),
            "relationships": copy.deepcopy(self._relationships),
            "facts": copy.deepcopy(self._facts),
            "fact_index": copy.deepcopy(self._fact_index),
            "dependent_index": copy.deepcopy(self._dependent_index),
        }

    async def restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore the graph state from a snapshot."""
        import copy

        self._entities = copy.deepcopy(snapshot["entities"])
        self._relationships = copy.deepcopy(snapshot["relationships"])
        self._facts = copy.deepcopy(snapshot["facts"])
        self._fact_index = copy.deepcopy(snapshot["fact_index"])
        self._dependent_index = copy.deepcopy(snapshot["dependent_index"])
