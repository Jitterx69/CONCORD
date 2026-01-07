"""
CONCORD Reasoning Pipeline with TinyLlama-1.1B
FIXED VERSION with all improvements
"""

import re, pandas as pd, numpy as np
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings("ignore")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

@dataclass
class Evidence:
    source: str
    text: str
    score: float

class NovelReader:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.novels, self.chunks, self.embeddings = {}, {}, {}
        print("Loading encoder...")
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        
    def load(self):
        print("Loading novels...")
        for f in self.data_dir.glob("*.txt"):
            self.novels[f.stem] = open(f, encoding="utf-8", errors="ignore").read()
            print(f"  {f.stem}: {len(self.novels[f.stem]):,} chars")
        
    def chunk(self, size=500):
        print("Chunking...")
        for name, text in self.novels.items():
            paras = [p.strip()[:size] for p in text.split("\n\n") if p.strip()]
            self.chunks[name] = paras[:2000]  # More chunks for better coverage
            print(f"  {name}: {len(self.chunks[name])} chunks")
    
    def embed(self):
        print("Embedding...")
        for name, cks in self.chunks.items():
            self.embeddings[name] = self.encoder.encode(cks, show_progress_bar=True)
    
    # FIX 1: Filter by book_name
    def retrieve(self, query, book_name=None, top_k=5):
        q = self.encoder.encode([query])[0]
        results = []
        
        # Filter by book if specified
        books_to_search = []
        if book_name:
            for name in self.chunks.keys():
                if book_name.lower() in name.lower() or name.lower() in book_name.lower():
                    books_to_search.append(name)
        if not books_to_search:
            books_to_search = list(self.chunks.keys())
        
        for name in books_to_search:
            emb = self.embeddings[name]
            sims = np.dot(emb, q) / (np.linalg.norm(emb, axis=1) * np.linalg.norm(q) + 1e-9)
            for i in np.argsort(sims)[-top_k:][::-1]:
                results.append(Evidence(name, self.chunks[name][i], float(sims[i])))
        return sorted(results, key=lambda x: x.score, reverse=True)[:top_k]


class RuleBasedChecker:
    """Rule-based validation layer to catch obvious contradictions"""
    
    @staticmethod
    def check(content, char):
        content_lower = content.lower()
        violations = []
        
        # Rule 1: Death finality - actions after death
        death_match = re.search(r'died?\s+(?:in\s+)?(\d{4})', content_lower)
        action_after = re.search(r'(?:continued|after\s+(?:his|her)\s+death|until\s+)(\d{4})', content_lower)
        if death_match and action_after:
            try:
                death_year = int(death_match.group(1))
                action_year = int(action_after.group(1))
                if action_year > death_year:
                    violations.append(f"Action in {action_year} after death in {death_year}")
            except: pass
        
        # Rule 2: Temporal impossibility - birth after death
        birth_match = re.search(r'born\s+(?:in\s+)?(\d{4})', content_lower)
        if birth_match and death_match:
            try:
                birth = int(birth_match.group(1))
                death = int(death_match.group(1))
                if birth > death:
                    violations.append(f"Birth {birth} after death {death}")
            except: pass
        
        # Rule 3: Age impossibility
        age_match = re.search(r'(\d+)\s+years?\s+old.*died', content_lower)
        if age_match and birth_match and death_match:
            try:
                age = int(age_match.group(1))
                birth = int(birth_match.group(1))
                death = int(death_match.group(1))
                if abs((death - birth) - age) > 2:
                    violations.append(f"Age {age} inconsistent with years {birth}-{death}")
            except: pass
        
        # Rule 4: Contradiction keywords
        contradiction_phrases = [
            "but actually", "however", "in reality", "never existed",
            "contradicts", "impossible", "cannot be", "didn't happen"
        ]
        for phrase in contradiction_phrases:
            if phrase in content_lower:
                violations.append(f"Contradiction signal: '{phrase}'")
                break
        
        return violations


class ConsistencyChecker:
    def __init__(self):
        print("Loading TinyLlama-1.1B...")
        self.device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
        model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tok = AutoTokenizer.from_pretrained(model)
        self.tok.pad_token = self.tok.eos_token
        self.llm = AutoModelForCausalLM.from_pretrained(
            model, 
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32, 
            low_cpu_mem_usage=True
        ).to(self.device)
        print(f"Loaded on {self.device}")
        self.rule_checker = RuleBasedChecker()
    
    # FIX 4: Better prompt tuning - more strict
    def check(self, claim_text, evidence_text, character):
        # First check rule-based violations
        rule_violations = self.rule_checker.check(claim_text, character)
        if rule_violations:
            return {"is_consistent": False, "reasoning": f"Rule violation: {rule_violations[0]}"}
        
    # DECOMPOSITION LAYER: LLM as a tool to split complex text into atomic facts
    def decompose_claim(self, text):
        system = """You are a logic parser. Split the narrative text into a list of atomic, standalone facts.
Each fact must be a complete sentence.
Ignore stylistic fluff, focus on events, relationships, timestamps, and locations.

Input: "Born in 1820, he was a sailor who hated onions."
Output:
- He was born in 1820.
- He was a sailor.
- He hated onions."""
        
        user = f"Input: \"{text}\"\nOutput:"
        
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tok(prompt, return_tensors="pt", truncation=True, max_length=1024).to(self.device)
        
        with torch.no_grad():
            outputs = self.llm.generate(**inputs, max_new_tokens=200, do_sample=False, temperature=0.1)
        
        response = self.tok.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
        # Parse bullet points or newlines
        facts = [line.strip("- ").strip() for line in response.split("\n") if line.strip()]
        return facts if facts else [text]

    # VERIFICATION LAYER: LLM as a tool to verify specific atomic facts
    def verify_fact(self, fact, evidence_text, character):
        system = """You are a strict consistency verifier.
CLAIM: A single atomic fact about a character.
EVIDENCE: Excerpts from the novel.

Task: Determine if the CLAIM contradicts the EVIDENCE.
- If the claim directly contradicts the evidence (e.g., wrong date, wrong parent, alive after death), return CONTRADICT.
- If the claim is compatible (even if not explicitly mentioned), return CONSISTENT.

Reply strictly: CONSISTENT or CONTRADICT."""
        
        user = f"Character: {character}\nCLAIM: {fact}\nEVIDENCE: {evidence_text[:800]}\nVERDICT:"
        
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tok(prompt, return_tensors="pt", truncation=True, max_length=1500).to(self.device)
        
        with torch.no_grad():
            outputs = self.llm.generate(**inputs, max_new_tokens=10, do_sample=False)
        
        response = self.tok.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip().upper()
        return "CONTRADICT" in response

    # SYNTHESIS LAYER: Deterministic Python logic combining rule violations and fact verification
    def check(self, claim_text, evidence_text, character):
        # 1. Rule-Based Check (Fast Fail)
        rule_violations = self.rule_checker.check(claim_text, character)
        if rule_violations:
            return {"is_consistent": False, "reasoning": f"Rule violation: {rule_violations[0]}"}
        
        # 2. Decomposition (LLM Tool)
        atomic_facts = self.decompose_claim(claim_text)
        
        # 3. Atomic Verification (LLM Tool)
        contradictions = []
        for fact in atomic_facts:
            # We verify each fact deeply
            is_contradiction = self.verify_fact(fact, evidence_text, character)
            if is_contradiction:
                contradictions.append(fact)
                # Optimization: Fail fast if we find a contradiction? 
                # For now, let's collect them to be thorough.
        
        # 4. Logic Synthesis (Deterministic)
        if contradictions:
            return {
                "is_consistent": False, 
                "reasoning": f"Contradicts evidence on: {'; '.join(contradictions[:2])}"
            }
        
        return {
            "is_consistent": True, 
            "reasoning": "All atomic facts are consistent with narrative constraints."
        }


class Pipeline:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.reader = NovelReader(data_dir)
        self.checker = ConsistencyChecker()
    
    def setup(self):
        self.reader.load()
        self.reader.chunk()
        self.reader.embed()
    
    # FIX 2: Use caption + content for query
    def process(self, row):
        char = row["char"]
        caption = row.get("caption", "")
        content = row["content"]
        book_name = row.get("book_name", "")
        
        # Combine caption + content for better query
        query = f"{char} {caption} {content[:150]}"
        
        # Filter by book_name
        evidence = self.reader.retrieve(query, book_name=book_name, top_k=7)
        evidence_text = " ".join([e.text for e in evidence])
        
        result = self.checker.check(content, evidence_text, char)
        return "consistent" if result["is_consistent"] else "contradict"
    
    def run(self):
        self.setup()
        test_df = pd.read_csv(self.data_dir / "test.csv")
        print(f"\nProcessing {len(test_df)} samples...")
        
        results = []
        for idx, row in test_df.iterrows():
            if idx % 10 == 0:
                print(f"  {idx+1}/{len(test_df)}...")
            label = self.process(row)
            # FIX 3: Output only id, label
            results.append({"id": row["id"], "label": label})
        
        out = pd.DataFrame(results)
        
        # Save submission file
        submission_path = self.data_dir / "submission.csv"
        out.to_csv(submission_path, index=False)
        print(f"\nSaved submission: {submission_path}")
        print(out["label"].value_counts())
        
        return out


def main():
    print("=" * 60)
    print("CONCORD Reasoning Pipeline - FIXED VERSION")
    print("=" * 60)
    pipeline = Pipeline("/Users/jitterx/Desktop/CONCORD/data")
    pipeline.run()
    print("Pipeline Complete!")


if __name__ == "__main__":
    main()
