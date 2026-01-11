from typing import List, Set, Dict
from uuid import UUID
from app.core.knowledge_graph import KnowledgeGraph
from app.models import Fact, FactValidity

class Propagator:
    """
    Handles the 'Butterfly Effect' propagation.
    When a fact is invalidated or changed, this engine recursively
    traverses the dependency graph to invalidate downstream facts.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
        
    async def invalidate_fact(self, fact_id: UUID) -> List[UUID]:
        """
        Mark a fact as INVALID and recursively invalidate all its dependents.
        Returns a list of all invalidated fact IDs.
        """
        invalidated_ids: Set[UUID] = set()
        queue: List[UUID] = [fact_id]
        
        while queue:
            current_id = queue.pop(0)
            
            if current_id in invalidated_ids:
                continue
                
            fact = await self.kg.get_fact(current_id)
            if not fact:
                continue
                
            # Mark as invalid
            fact.validity_status = FactValidity.INVALID
            invalidated_ids.add(current_id)
            
            # Find dependents
            dependents = await self.kg.get_dependents(current_id)
            for dep in dependents:
                if dep.id not in invalidated_ids:
                    queue.append(dep.id)
                    
        return list(invalidated_ids)

    async def propagate_change(self, fact_id: UUID) -> Dict[str, List[UUID]]:
        """
        When a fact is CHANGED (not just removed), we might just mark
        dependents as DIRTY instead of INVALID, implying they need re-checking
        but might still be true.
        """
        dirty_ids: Set[UUID] = set()
        queue: List[UUID] = [fact_id]
        
        # The root change is VALID (it's the new truth)
        # But its children become DIRTY
        
        # Get immediate dependents of the changed fact
        root_dependents = await self.kg.get_dependents(fact_id)
        queue = [d.id for d in root_dependents]
        
        while queue:
            current_id = queue.pop(0)
            if current_id in dirty_ids:
                continue
                
            fact = await self.kg.get_fact(current_id)
            if not fact:
                continue
                
            # Mark as dirty
            fact.validity_status = FactValidity.DIRTY
            dirty_ids.add(current_id)
            
            # Recurse
            dependents = await self.kg.get_dependents(current_id)
            for dep in dependents:
                if dep.id not in dirty_ids:
                    queue.append(dep.id)
                    
        return {"dirty": list(dirty_ids)}
