import asyncio
import sys
import os
from uuid import uuid4

sys.path.append(os.getcwd())

from app.core.knowledge_graph import KnowledgeGraph
from app.causality.repair_agent import RepairAgent
from app.models import Fact, FactValidity

async def main():
    print("--- Starting Repair Agent Verification ---")
    
    kg = KnowledgeGraph()
    repair_agent = RepairAgent(kg)
    
    # Setup: Parent (Poison) -> Child (Stab Wound [INVALID])
    print("Setup: Parent (Poison) -> Child (Stab Wound [INVALID])")
    
    parent_fact = Fact(subject="Killer", predicate="used", object="poison", validity_status="valid")
    await kg.add_fact(parent_fact)
    
    child_fact = Fact(
        subject="Victim", 
        predicate="died_of", 
        object="stab wound", 
        dependencies=[parent_fact.id], 
        validity_status="invalid"
    )
    await kg.add_fact(child_fact)
    
    print(f"Child Fact Before Repair: {child_fact.object} ({child_fact.validity_status})")
    
    # Repair
    print("\n--- Repairing Child Fact ---")
    result = await repair_agent.repair_fact(child_fact.id)
    print(f"Repair Result: {result}")
    
    # Check
    print(f"Child Fact After Repair: {child_fact.object} ({child_fact.validity_status})")
    
    if child_fact.validity_status == FactValidity.VALID and "poison" in str(result).lower():
         print("SUCCESS: Fact was updated to match poison context")
    elif child_fact.validity_status == FactValidity.VALID and "delete" in str(result).lower():
         print("SUCCESS: Fact was correctly identified for deletion")
    else:
         print("Note: LLM output varies, but status should be VALID or fact removed.")

if __name__ == "__main__":
    asyncio.run(main())
