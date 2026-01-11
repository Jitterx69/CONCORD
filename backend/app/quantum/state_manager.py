from typing import List, Dict, Optional
from uuid import UUID, uuid4
import copy
from app.models import WorldState, Fact


class StateManager:
    """
    Manages multiple parallel 'World States' (Theories).
    Handles forking (creation of new theories) and pruning (collapse).
    """

    def __init__(self):
        self.worlds: Dict[UUID, WorldState] = {}
        # Initialize with a default "Base Reality"
        base_world = WorldState(name="Base Reality", probability=1.0)
        self.worlds[base_world.id] = base_world

    def get_world(self, world_id: UUID) -> Optional[WorldState]:
        return self.worlds.get(world_id)

    def get_active_worlds(self) -> List[WorldState]:
        return [w for w in self.worlds.values() if w.active]

    def fork_world(
        self, parent_world_id: UUID, name: str, divergence_fact_id: UUID
    ) -> WorldState:
        """
        Create a new world state branching off from a parent state.
        The probability is initially split or assigned (managed by ProbabilityEngine).
        """
        parent = self.worlds.get(parent_world_id)
        if not parent:
            raise ValueError(f"Parent world {parent_world_id} not found")

        new_world = WorldState(
            name=name,
            probability=0.0,  # Will be calculated by engine
            parent_world_id=parent_world_id,
            divergence_point_fact_id=divergence_fact_id,
        )
        self.worlds[new_world.id] = new_world
        return new_world

    def prune_world(self, world_id: UUID) -> None:
        """
        Mark a world as inactive (collapsed).
        """
        if world_id in self.worlds:
            self.worlds[world_id].active = False
            self.worlds[world_id].probability = 0.0

    def get_facts_in_world(self, world_id: UUID, all_facts: List[Fact]) -> List[Fact]:
        """
        Get all facts that are valid in this world.
        Includes:
        1. Universal facts (world_id is None)
        2. Facts specific to this world
        3. Facts inherited from active parent worlds (recursively)
        """
        valid_facts = []

        # Build lineage
        lineage = set()
        current = self.get_world(world_id)
        while current:
            lineage.add(current.id)
            if current.parent_world_id:
                current = self.get_world(current.parent_world_id)
            else:
                break

        for fact in all_facts:
            # Universal facts
            if fact.world_id is None:
                valid_facts.append(fact)
            # Facts in lineage
            elif fact.world_id in lineage:
                valid_facts.append(fact)

        return valid_facts
