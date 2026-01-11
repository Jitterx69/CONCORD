import asyncio
import sys
import os
from uuid import uuid4

sys.path.append(os.getcwd())

from app.core.knowledge_graph import KnowledgeGraph
from app.causality.propagator import Propagator
from app.models import Fact, FactValidity


async def main():
    print("--- Starting Butterfly Effect Verification ---")

    kg = KnowledgeGraph()
    propagator = Propagator(kg)

    # 1. Setup Chain: A -> B -> C
    print("Creating causal chain: A -> B -> C")

    fact_a = Fact(subject="Killer", predicate="used", object="knife", validity_status="valid")
    await kg.add_fact(fact_a)

    fact_b = Fact(
        subject="Victim",
        predicate="died_of",
        object="stab wound",
        dependencies=[fact_a.id],
        validity_status="valid",
    )
    await kg.add_fact(fact_b)

    fact_c = Fact(
        subject="Police",
        predicate="found",
        object="bloody blade",
        dependencies=[fact_b.id],
        validity_status="valid",
    )
    await kg.add_fact(fact_c)

    print(f"Initial State:")
    print(f"A: {fact_a.object} ({fact_a.validity_status})")
    print(f"B: {fact_b.object} ({fact_b.validity_status})")
    print(f"C: {fact_c.object} ({fact_c.validity_status})")

    # 2. Change A (Butterfly Effect)
    print("\n--- Changing A (Knife -> Poison) ---")
    # Simulate change by invalidating A

    invalidated = await propagator.invalidate_fact(fact_a.id)
    print(f"Invalidated IDs: {len(invalidated)}")

    # Check states
    print(f"Final State:")
    print(f"A: {fact_a.validity_status}")
    print(f"B: {fact_b.validity_status}")
    print(f"C: {fact_c.validity_status}")

    if fact_c.validity_status == FactValidity.INVALID:
        print("SUCCESS: Propagation reached leaf node C")
    else:
        print("FAILURE: Propagation did not reach C")


if __name__ == "__main__":
    asyncio.run(main())
