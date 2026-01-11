import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict, Any

class DungeonMaster:
    """
    The AI Narrator that determines the outcome of actions in the simulation.
    """
    
    def __init__(self):
        print("Loading Dungeon Master (TinyLlama)...")
        self.device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
        model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            low_cpu_mem_usage=True
        ).to(self.device)
        print(f"Dungeon Master ready on {self.device}")

    def narrate_outcome(self, character: str, action: str, world_context: str) -> str:
        """
        Generates a narrative description of the action's outcome.
        """
        system_prompt = """You are a Dungeon Master for a realistic simulation. 
Describe the outcome of the character's action based on the world context.
Keep it brief (2-3 sentences).
If the action is impossible given the context, describe the failure."""

        user_prompt = f"""
Character: {character}
Current Situation: {world_context}
Action: {character} attempts to {action}

Outcome:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=100, do_sample=True, temperature=0.7)
            
        response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
        return response

    def check_feasibility(self, character: str, action: str, world_context: str) -> bool:
        """
        Checks if an action is physically/logically possible.
        """
        system_prompt = """You are a physics and logic engine. 
Determine if the action is POSSIBLE given the context.
Reply only with POSSIBLE or IMPOSSIBLE."""

        user_prompt = f"""
Context: {world_context}
Action: {character} tries to {action}

Verdict:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=10, do_sample=False)
            
        response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip().upper()
        return "IMPOSSIBLE" not in response
