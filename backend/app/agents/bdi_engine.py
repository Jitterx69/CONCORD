from typing import Dict, Any
from uuid import UUID
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from app.models import PsychProfile
from app.agents.memory import AgentMemory
from app.agents.planner import GoalPlanner


class BDIEngine:
    """
    Belief-Desire-Intention Engine.
    Checks if a character's OBSERVED action matches their EXPECTED behavior.
    """

    def __init__(self):
        self.memory = AgentMemory()
        self.planner = GoalPlanner(self.memory)

        # Reuse model from planner (or share reference in prod)
        self.model = self.planner.model
        self.tokenizer = self.planner.tokenizer
        self.device = self.planner.device

    def check_psychological_consistency(
        self, profile: PsychProfile, action_text: str
    ) -> Dict[str, Any]:
        """
        Does this action make sense for this character?
        """
        # 1. Infer Intention from Action (What were they trying to do?)
        intention = self._infer_intention(action_text)

        # 2. Derive Expected Goal (What SHOULD they have done?)
        expected_goal = self.planner.formulate_goal(profile, f"Opportunity to {intention}")

        # 3. Compare
        # Simple LLM check for alignment
        system = """Consistency Checker. 
Action: Does the character's behavior align with their personality/goals?
Reply: CONSISTENT or INCONSISTENT (with reason)."""

        user = f"""
Traits: {', '.join(profile.personality_traits)}
Action Taken: {action_text}
Expected Goal: {expected_goal}

Verdict:"""

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]

        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).to(
            self.device
        )

        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=50, do_sample=False)

        response = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
        ).strip()

        is_consistent = "INCONSISTENT" not in response.upper()
        return {"consistent": is_consistent, "reasoning": response, "expected_goal": expected_goal}

    def _infer_intention(self, action_text: str) -> str:
        """Helper to summarize action into an intention string"""
        return action_text  # Naive pass-through for PoC
