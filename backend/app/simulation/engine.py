from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
import datetime

from app.core.knowledge_graph import KnowledgeGraph
from app.simulation.dungeon_master import DungeonMaster


class SimulationEngine:
    """
    Manages the 'Holodeck' simulation loop.
    Handles state management (undo/redo), action processing, and coordination
    between the Knowledge Graph and the AI narrator.
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
        self.dm = DungeonMaster()
        self.history: List[Dict[str, Any]] = []  # Stack of snapshots
        self.current_step = 0

    async def initialize_session(self):
        """snapshot the initial state"""
        snapshot = await self.kg.create_snapshot()
        self.history.append(
            {"step": 0, "snapshot": snapshot, "action": "INIT", "narrative": "Simulation started."}
        )

    async def process_action(self, character: str, action: str) -> Dict[str, Any]:
        """
        Process an action within the narrative simulation.
        Uses C++ Physics Engine for realistic travel time calculation if available.
        """
        # Try to load C++ Engine
        try:
            import ctypes
            import os
            import sys

            lib_name = "libphys.so" if sys.platform != "darwin" else "libphys.dylib"
            lib_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../cpp_sim", lib_name)
            )

            self.phys_lib = ctypes.CDLL(lib_path)
            self.phys_lib.api_estimate_travel_time.argtypes = [
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_char_p,
            ]
            self.phys_lib.api_estimate_travel_time.restype = ctypes.c_double

            # Example: Calculate travel time for a "move" action
            if "walk" in action or "run" in action:
                # Mock coordinates
                p1 = (0.0, 0.0, 0.0)
                p2 = (5.0, 5.0, 0.0)
                mode = "running" if "run" in action else "walking"
                time_mins = self.phys_lib.api_estimate_travel_time(*p1, *p2, mode.encode("utf-8"))
                print(f"🚀 C++ Physics Engine: Estimated {mode} time = {time_mins:.2f} mins")

        except Exception as e:
            print(f"⚠️ Could not load C++ Physics Engine: {e}")

        # 1. Create a snapshot before action (Undo point)
        # This is not explicitly in the original list of steps, but good for undo.
        # For now, we'll keep the original step 1 as the first actual processing step.

        # 1. Gather Context (Naively get all facts for now, in prod use retrieval)
        # Ideally we'd use the KG query to get relevant facts about location/status
        entity = await self.kg.find_entity_by_name(character)
        if not entity:
            return {"success": False, "message": f"Character {character} not found."}

        # Simplified context construction
        context_facts = await self.kg.get_facts(limit=10)
        context_str = "\n".join([f"- {f.subject} {f.predicate} {f.object}" for f in context_facts])

        # 2. Check Feasibility
        is_possible = self.dm.check_feasibility(character_name, action_description, context_str)
        if not is_possible:
            return {
                "success": False,
                "message": "Action is impossible in the current context.",
                "narrative": f"{character_name} tries to {action_description}, but fails.",
            }

        # 3. Narrate Outcome
        narrative = self.dm.narrate_outcome(character_name, action_description, context_str)

        # 4. Snapshot state BEFORE applying changes (or after? Usually we snapshot the result)
        # Let's snapshot the NEW state.

        # TODO: Here we would parse the narrative back into facts to update the KG.
        # For this PoC, we just store the narrative.

        new_snapshot = await self.kg.create_snapshot()

        self.current_step += 1
        self.history.append(
            {
                "step": self.current_step,
                "snapshot": new_snapshot,
                "action": action_description,
                "narrative": narrative,
            }
        )

        return {"success": True, "narrative": narrative, "step": self.current_step}

    async def undo(self) -> Dict[str, Any]:
        """Revert to previous state"""
        if len(self.history) <= 1:
            return {"success": False, "message": "Cannot undo further."}

        # Pop current state
        self.history.pop()
        previous = self.history[-1]

        # Restore
        await self.kg.restore_snapshot(previous["snapshot"])
        self.current_step = previous["step"]

        return {
            "success": True,
            "message": f"Rewound to step {self.current_step}",
            "last_narrative": previous["narrative"],
        }
