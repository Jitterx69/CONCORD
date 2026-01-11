import sys
import os
from uuid import uuid4

sys.path.append(os.getcwd())

from app.quantum.state_manager import StateManager
from app.quantum.probability_engine import ProbabilityEngine
from app.models import Fact, FactValidity


def main():
    print("--- Starting Quantum Consistency Verification ---")

    state_manager = StateManager()
    prob_engine = ProbabilityEngine()

    active_worlds = state_manager.get_active_worlds()
    base_world = active_worlds[0]
    print(f"Base World: {base_world.name} (P={base_world.probability})")

    # 1. Create Facts
    print("\n--- Forking Worlds ---")
    # Universal Fact
    fact_dead = Fact(subject="Victim", predicate="is", object="dead", world_id=None)

    # Fork 1: Butler did it
    world_butler = state_manager.fork_world(base_world.id, "Theory: Butler", fact_dead.id)
    world_butler.probability = 0.5
    fact_knife = Fact(subject="Weapon", predicate="is", object="knife", world_id=world_butler.id)

    # Fork 2: Maid did it
    world_maid = state_manager.fork_world(base_world.id, "Theory: Maid", fact_dead.id)
    world_maid.probability = 0.5
    fact_poison = Fact(subject="Weapon", predicate="is", object="poison", world_id=world_maid.id)

    prob_engine.normalize_probabilities([world_butler, world_maid])

    print(f"World {world_butler.name}: P={world_butler.probability}")
    print(f"World {world_maid.name}: P={world_maid.probability}")

    # 2. Test Inheritance
    print("\n--- Testing Fact Inheritance ---")
    all_facts = [fact_dead, fact_knife, fact_poison]

    facts_in_butler = state_manager.get_facts_in_world(world_butler.id, all_facts)
    print(f"Facts in Butler World: {[f.object for f in facts_in_butler]}")

    if "dead" in [f.object for f in facts_in_butler] and "knife" in [
        f.object for f in facts_in_butler
    ]:
        print("SUCCESS: Butler world inherited 'dead' and has 'knife'")

    if "poison" not in [f.object for f in facts_in_butler]:
        print("SUCCESS: Butler world does NOT have 'poison'")

    # 3. Probability Update (Found a sheath matching knife)
    print("\n--- Evidence Found: Knife Sheath ---")
    print("Updating probabilities based on evidence supporting Butler...")
    prob_engine.update_probabilities([world_butler, world_maid], fact_knife, [world_butler.id])

    print(f"World {world_butler.name}: P={world_butler.probability:.2f}")
    print(f"World {world_maid.name}: P={world_maid.probability:.2f}")

    if world_butler.probability > world_maid.probability:
        print("SUCCESS: Butler theory probability increased")
    else:
        print("FAILURE: Probability did not update correctly")


if __name__ == "__main__":
    main()
