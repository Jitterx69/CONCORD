import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict, Any
from uuid import UUID

from app.core.knowledge_graph import KnowledgeGraph
from app.models import Fact, FactValidity


class RepairAgent:
    """
    AI Agent that repairs 'DIRTY' or 'INVALID' facts.
    It looks at the new parent facts and decides:
    1. Should this fact remain true? (VALID)
    2. Should it be deleted? (INVALID)
    3. Should it be modified? (Update text)
    """

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
        print("Loading Repair Agent (TinyLlama)...")
        # Reuse the model logic or share instance in production
        self.device = (
            "mps"
            if torch.backends.mps.is_available()
            else "cuda" if torch.cuda.is_available() else "cpu"
        )
        model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            low_cpu_mem_usage=True,
        ).to(self.device)
        print(f"Repair Agent ready on {self.device}")

    async def repair_fact(self, fact_id: UUID) -> Dict[str, Any]:
        """
        Check a DIRTY fact and repair it if necessary.
        """
        fact = await self.kg.get_fact(fact_id)
        if not fact:
            return {"status": "missing"}

        # Get causes (parents)
        parents_text = []
        for parent_id in fact.dependencies:
            parent = await self.kg.get_fact(parent_id)
            if parent:
                parents_text.append(
                    f"{parent.subject} {parent.predicate} {parent.object}"
                )

        parents_str = "; ".join(parents_text)

        system = """You are a Consistency Repair Agent. 
A derived fact might be broken because its usage changed.
Decide if the derived fact is still logically consistent.
If YES, output 'KEEP'.
If NO, output 'REWRITE: <new fact>' or 'DELETE'."""

        prompt = f"""
CAUSES (New Reality): {parents_str}
DERIVED FACT (In Question): {fact.subject} {fact.predicate} {fact.object}

Verdict:"""

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        # Run inference
        input_ids = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(input_ids, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=50, do_sample=False)

        response = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
        ).strip()

        if "KEEP" in response:
            fact.validity_status = FactValidity.VALID
            return {"status": "kept", "fact": fact}
        elif "DELETE" in response:
            await self.kg.remove_fact(fact.id)
            return {"status": "deleted"}
        elif "REWRITE" in response:
            new_text = response.replace("REWRITE:", "").strip()
            # Naive update: just putting text in 'object' for now, ideally re-parse
            fact.object = new_text
            fact.validity_status = FactValidity.VALID
            return {"status": "updated", "new_text": new_text}

        return {"status": "uncertain", "response": response}
