import asyncio
import sys
import os

# Add local directory to path so we can import app
sys.path.append(os.getcwd())

from app.core.knowledge_graph import KnowledgeGraph
from app.simulation.engine import SimulationEngine
from app.models import Entity, EntityType
from uuid import uuid4


async def main():
    print("--- Starting Holodeck Verification ---")

    # 1. Setup
    kg = KnowledgeGraph()
    engine = SimulationEngine(kg)

    # Add a character
    alice_id = uuid4()
    alice = Entity(
        id=alice_id,
        name="Alice",
        type=EntityType.CHARACTER,
        attributes={"job": "Adventurer"},
        first_appearance=1,
    )
    await kg.add_entity(alice)
    print(f"Created entity: {alice.name}")

    # Init session
    await engine.initialize_session()
    print("Session initialized.")

    # 2. Action: Walk to park
    print("\n--- Action 1: Walk to park ---")
    result1 = await engine.process_action("Alice", "walk to the central park")
    print(f"Result: {result1['success']}")
    print(f"Narrative: {result1.get('narrative')}")

    # 3. Action: Fly (should be Impossible? depending on context)
    print("\n--- Action 2: Fly to the moon ---")
    result2 = await engine.process_action("Alice", "flap her arms and fly to the moon")
    print(f"Result: {result2['success']}")
    print(f"Narrative: {result2.get('narrative', result2.get('message'))}")

    # 4. Undo
    print("\n--- Testing Undo ---")
    undo_res = await engine.undo()
    print(f"Undo Result: {undo_res['success']}")
    print(f"Message: {undo_res['message']}")

    # Verify state (should be back to step 1)
    if engine.current_step == 1:
        print("SUCCESS: Rewound to step 1")
    else:
        print(f"FAILURE: Current step is {engine.current_step}")


if __name__ == "__main__":
    asyncio.run(main())
