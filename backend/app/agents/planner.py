from typing import List
from uuid import UUID
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from app.models import PsychProfile
from app.agents.memory import AgentMemory


class GoalPlanner:
    """
    Determines what a character WANTS to do based on their profile and memory.
    """

    def __init__(self, memory: AgentMemory):
        self.memory = memory
        self.device = (
            "mps"
            if torch.backends.mps.is_available()
            else "cuda" if torch.cuda.is_available() else "cpu"
        )
        model_name = (
            "distilgpt2"  # Switched from TinyLlama (4GB RAM) to DistilGPT2 (~500MB) for stability
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            low_cpu_mem_usage=True,
        ).to(self.device)

    def formulate_goal(self, profile: PsychProfile, context: str) -> str:
        """
        Ask LLM: Given this personality + context, what is the character's immediate goal?
        """
        # Recall relevant past
        past_experiences = self.memory.recall(profile.entity_id, context, top_k=2)
        past_context = "\n".join([f"- {m}" for m in past_experiences])

        system = """You are a Roleplay AI. 
Determine the character's immediate GOAL.
Reply with a single sentence starting with 'To ...'"""

        user = f"""
Character Traits: {', '.join(profile.personality_traits)}
Core Values: {', '.join(profile.core_values)}
Relevant Memories:
{past_context}

Current Situation: {context}

What is their immediate goal?"""

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]

        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).to(
            self.device
        )

        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=30, do_sample=False)

        response = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
        ).strip()
        return response
