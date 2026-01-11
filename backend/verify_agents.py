import sys
import os
from uuid import uuid4

sys.path.append(os.getcwd())

from app.agents.bdi_engine import BDIEngine
from app.models import PsychProfile

def main():
    print("--- Starting Deep Mind BDI Agent Verification ---")
    
    engine = BDIEngine()
    
    # 1. Create a Profile (The Pacifist)
    profile = PsychProfile(
        entity_id=uuid4(),
        personality_traits=["pacifist", "gentle", "anxious"],
        core_values=["non-violence", "preservation of life"],
        goals=["avoid conflict"]
    )
    
    # 2. Seed Memory
    print("Seeding memory...")
    engine.memory.remember(profile.entity_id, "I promised my mother I would never hurt anyone.")
    
    # 3. Test Consistency: CONSISTENT Action
    print("\n--- Test 1: Consistent Action ---")
    action1 = "He ran away from the fight, hiding in the alley."
    result1 = engine.check_psychological_consistency(profile, action1)
    
    print(f"Action: {action1}")
    print(f"Expected Goal Derived: {result1['expected_goal']}")
    print(f"Verdict: {result1['reasoning']}")
    
    if result1['consistent']:
        print("SUCCESS: Recognized consistent behavior")
    else:
        print("FAILURE: False positive inconsistency")
        
    # 4. Test Consistency: INCONSISTENT Action
    print("\n--- Test 2: Inconsistent Action ---")
    action2 = "He punched the guard specifically in the face repeatedly."
    result2 = engine.check_psychological_consistency(profile, action2)
    
    print(f"Action: {action2}")
    print(f"Expected Goal Derived: {result2['expected_goal']}")
    print(f"Verdict: {result2['reasoning']}")
    
    if not result2['consistent']:
        print("SUCCESS: Recognized inconsistent behavior")
    else:
        print("FAILURE: Failed to detect inconsistency")

if __name__ == "__main__":
    main()
