"""
CONCORD Reasoning Pipeline v2.0 - ENHANCED VERSION
Full alignment with 7 expected hackathon outcomes:
1. Binary consistency judgments
2. Evidence-grounded (distributed multi-excerpt)
3. Implicit constraint detection
4. Counterfactual causal reasoning
5. Conservative impossibility detection
6. Long narrative handling
7. Plausibility vs Reachability distinction
"""

import re, pandas as pd, numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
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
    position: int  # NEW: Track position in narrative (early/mid/late)


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
            self.chunks[name] = paras[:2000]
            print(f"  {name}: {len(self.chunks[name])} chunks")
    
    def embed(self):
        print("Embedding...")
        for name, cks in self.chunks.items():
            self.embeddings[name] = self.encoder.encode(cks, show_progress_bar=True)
    
    # PHASE 4: DISTRIBUTED EVIDENCE RETRIEVAL - Stratified sampling across timeline
    def retrieve_distributed(self, query, book_name=None, top_k=9):
        """Retrieve evidence from EARLY, MIDDLE, and LATE sections of narrative"""
        q = self.encoder.encode([query])[0]
        
        # Filter by book
        books_to_search = []
        if book_name:
            for name in self.chunks.keys():
                if book_name.lower() in name.lower() or name.lower() in book_name.lower():
                    books_to_search.append(name)
        if not books_to_search:
            books_to_search = list(self.chunks.keys())
        
        all_results = []
        for name in books_to_search:
            chunks = self.chunks[name]
            emb = self.embeddings[name]
            n = len(chunks)
            
            # Divide into 3 sections: early (0-33%), middle (33-66%), late (66-100%)
            sections = [
                ("early", 0, n // 3),
                ("middle", n // 3, 2 * n // 3),
                ("late", 2 * n // 3, n)
            ]
            
            per_section = max(1, top_k // 3)
            
            for section_name, start, end in sections:
                if start >= end:
                    continue
                section_emb = emb[start:end]
                sims = np.dot(section_emb, q) / (np.linalg.norm(section_emb, axis=1) * np.linalg.norm(q) + 1e-9)
                
                top_indices = np.argsort(sims)[-per_section:][::-1]
                for i in top_indices:
                    global_idx = start + i
                    all_results.append(Evidence(
                        source=name,
                        text=chunks[global_idx],
                        score=float(sims[i]),
                        position=global_idx  # Track position
                    ))
        
        return sorted(all_results, key=lambda x: x.score, reverse=True)[:top_k]


class ImplicitConstraintChecker:
    """PHASE 3: Detect irreversible decisions and path-dependence"""
    
    IRREVERSIBLE_EVENTS = [
        "death", "died", "killed", "executed", "murdered", "deceased",
        "married", "wedding", "wed", "spouse",
        "born", "birth", "gave birth",
        "lost", "amputated", "blinded", "crippled",
        "banished", "exiled", "imprisoned", "enslaved",
        "inherited", "succession", "crowned"
    ]
    
    PSYCHOLOGICAL_LOCKIN = [
        "vowed", "swore", "oath", "promised",
        "trauma", "haunted", "obsessed", "devoted",
        "sworn enemy", "lifelong grudge", "never forgave"
    ]
    
    @staticmethod
    def detect_violations(backstory: str, evidence: str) -> List[str]:
        violations = []
        backstory_lower = backstory.lower()
        evidence_lower = evidence.lower()
        
        # Check for irreversible events in backstory that conflict with evidence
        for event in ImplicitConstraintChecker.IRREVERSIBLE_EVENTS:
            if event in backstory_lower:
                # Extract year if mentioned
                year_match = re.search(rf'{event}.*?(\d{{4}})', backstory_lower)
                if year_match:
                    event_year = int(year_match.group(1))
                    # Check if character appears after this event in evidence
                    later_years = re.findall(r'(\d{4})', evidence_lower)
                    for year_str in later_years:
                        year = int(year_str)
                        if year > event_year and event in ["death", "died", "killed", "executed"]:
                            violations.append(f"IMPLICIT: Character active in {year} after {event} in {event_year}")
        
        # Check for psychological lock-in conflicts
        for lockin in ImplicitConstraintChecker.PSYCHOLOGICAL_LOCKIN:
            if lockin in backstory_lower:
                # Check if evidence shows opposite behavior
                opposites = {
                    "sworn enemy": ["friend", "ally", "loved"],
                    "lifelong grudge": ["forgave", "reconciled", "peace"],
                    "devoted": ["abandoned", "betrayed", "left"]
                }
                for key, opposite_words in opposites.items():
                    if key in backstory_lower:
                        for opp in opposite_words:
                            if opp in evidence_lower:
                                violations.append(f"IMPLICIT: Backstory has '{key}' but evidence shows '{opp}'")
        
        return violations


class CausalReachabilityChecker:
    """PHASE 2: Counterfactual reasoning - could backstory LEAD TO known future?"""
    
    def __init__(self, tokenizer, model, device):
        self.tok = tokenizer
        self.llm = model
        self.device = device
    
    def check_reachability(self, backstory: str, evidence: str, character: str) -> Tuple[bool, str]:
        """
        Key distinction:
        - Plausibility: "Does this sound reasonable?" (BAD)
        - Reachability: "Could this backstory causally lead to the known events?" (GOOD)
        """
        system = """You are a CAUSAL REASONING expert for narratives.

TASK: Determine if the BACKSTORY could causally LEAD TO the events in EVIDENCE.

This is NOT about whether the backstory "sounds plausible."
This IS about whether the backstory makes the known future CAUSALLY POSSIBLE.

Ask yourself: "Given this backstory, could the character's known journey still happen?"

Examples of UNREACHABLE:
- Backstory says "orphan with no family" but evidence shows "inherited estate from father"
- Backstory says "never left village" but evidence shows "famous sea captain"
- Backstory says "died young" but evidence shows "lived to old age"

Answer: REACHABLE or UNREACHABLE (then brief reason)"""

        user = f"""Character: {character}

BACKSTORY (proposed early life):
{backstory[:400]}

KNOWN NARRATIVE EVENTS (from novel):
{evidence[:600]}

Could this backstory causally lead to these events?"""

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tok(prompt, return_tensors="pt", truncation=True, max_length=1500).to(self.device)
        
        with torch.no_grad():
            outputs = self.llm.generate(**inputs, max_new_tokens=50, do_sample=False)
        
        response = self.tok.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
        
        is_reachable = "UNREACHABLE" not in response.upper()
        return is_reachable, response[:100]


class TemporalConsistencyChecker:
    """PHASE 1: Track character evolution over narrative timeline"""
    
    def __init__(self, tokenizer, model, device):
        self.tok = tokenizer
        self.llm = model
        self.device = device
    
    def check_character_arc(self, backstory: str, early_evidence: str, late_evidence: str, character: str) -> Tuple[bool, str]:
        """Check if backstory's early-life assumptions are compatible with character evolution"""
        
        system = """You analyze CHARACTER EVOLUTION consistency.

Given a character's proposed BACKSTORY, EARLY narrative events, and LATE narrative events:
Determine if the character's development arc is consistent.

Check for:
- Personality drift violations (shy→bold without justification)  
- Belief changes that contradict backstory
- Skills appearing that backstory makes impossible

Answer: CONSISTENT or INCONSISTENT (then brief reason)"""

        user = f"""Character: {character}

PROPOSED BACKSTORY:
{backstory[:300]}

EARLY NARRATIVE (beginning of story):
{early_evidence[:300]}

LATE NARRATIVE (later in story):
{late_evidence[:300]}

Is the character arc consistent with the backstory?"""

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tok(prompt, return_tensors="pt", truncation=True, max_length=1200).to(self.device)
        
        with torch.no_grad():
            outputs = self.llm.generate(**inputs, max_new_tokens=50, do_sample=False)
        
        response = self.tok.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
        
        is_consistent = "INCONSISTENT" not in response.upper()
        return is_consistent, response[:100]


class RuleBasedChecker:
    """Enhanced rule-based validation with implicit constraints"""
    
    @staticmethod
    def check(content, char):
        violations = []
        content_lower = content.lower()
        
        # Rule 1: Death finality
        death_match = re.search(r'died?\s+(?:in\s+)?(\d{4})', content_lower)
        action_after = re.search(r'(?:continued|after\s+(?:his|her)\s+death|until\s+)(\d{4})', content_lower)
        if death_match and action_after:
            try:
                if int(action_after.group(1)) > int(death_match.group(1)):
                    violations.append(f"HARD: Action after death")
            except: pass
        
        # Rule 2: Birth-death order
        birth_match = re.search(r'born\s+(?:in\s+)?(\d{4})', content_lower)
        if birth_match and death_match:
            try:
                if int(birth_match.group(1)) > int(death_match.group(1)):
                    violations.append(f"HARD: Birth after death")
            except: pass
        
        # Rule 3: Contradiction keywords
        hard_contradictions = ["never existed", "impossible", "cannot be", "didn't happen"]
        for phrase in hard_contradictions:
            if phrase in content_lower:
                violations.append(f"HARD: Contradiction signal '{phrase}'")
                break
        
        return violations


class ConsistencyChecker:
    """Enhanced checker with all 5 phases"""
    
    def __init__(self):
        print("Loading TinyLlama-1.1B...")
        self.device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
        model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tok = AutoTokenizer.from_pretrained(model)
        self.tok.pad_token = self.tok.eos_token
        self.llm = AutoModelForCausalLM.from_pretrained(
            model, torch_dtype=torch.float16 if self.device != "cpu" else torch.float32, 
            low_cpu_mem_usage=True
        ).to(self.device)
        print(f"Loaded on {self.device}")
        
        # Initialize all checkers
        self.rule_checker = RuleBasedChecker()
        self.implicit_checker = ImplicitConstraintChecker()
        self.causal_checker = CausalReachabilityChecker(self.tok, self.llm, self.device)
        self.temporal_checker = TemporalConsistencyChecker(self.tok, self.llm, self.device)
    
    def decompose_claim(self, text):
        """Split backstory into atomic facts"""
        system = """Split the text into atomic facts. Each fact = one complete sentence.
Focus on: events, relationships, dates, locations, actions.

Input: "Born in 1820, he was a sailor who hated onions."
Output:
- He was born in 1820.
- He was a sailor.
- He hated onions."""
        
        user = f"Input: \"{text[:500]}\"\nOutput:"
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tok(prompt, return_tensors="pt", truncation=True, max_length=1024).to(self.device)
        
        with torch.no_grad():
            outputs = self.llm.generate(**inputs, max_new_tokens=200, do_sample=False)
        
        response = self.tok.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
        facts = [line.strip("- ").strip() for line in response.split("\n") if line.strip()]
        return facts if facts else [text[:200]]

    def verify_fact(self, fact, evidence_text, character):
        """Verify single atomic fact against evidence"""
        system = """Strict verifier. Does the CLAIM contradict the EVIDENCE?
- CONTRADICT: Direct conflict (wrong date, wrong person, impossible action)
- CONSISTENT: Compatible or not mentioned
Reply: CONSISTENT or CONTRADICT"""
        
        user = f"Character: {character}\nCLAIM: {fact}\nEVIDENCE: {evidence_text[:600]}\nVERDICT:"
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tok(prompt, return_tensors="pt", truncation=True, max_length=1200).to(self.device)
        
        with torch.no_grad():
            outputs = self.llm.generate(**inputs, max_new_tokens=10, do_sample=False)
        
        response = self.tok.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip().upper()
        return "CONTRADICT" in response

    # PHASE 5: CONSERVATIVE SYNTHESIS - One hard violation = instant rejection
    def check(self, backstory, evidence_list: List[Evidence], character):
        """
        Full consistency check with all 5 phases:
        1. Rule-based hard violations
        2. Implicit constraint violations
        3. Temporal consistency (character arc)
        4. Causal reachability
        5. Atomic fact verification + Conservative synthesis
        """
        
        # Combine evidence
        all_evidence = " ".join([e.text for e in evidence_list])
        
        # Separate early/late evidence
        sorted_evidence = sorted(evidence_list, key=lambda x: x.position)
        early_evidence = " ".join([e.text for e in sorted_evidence[:len(sorted_evidence)//2]])
        late_evidence = " ".join([e.text for e in sorted_evidence[len(sorted_evidence)//2:]])
        
        hard_violations = []
        soft_violations = []
        
        # PHASE 1: Rule-based check (instant fail)
        rule_violations = self.rule_checker.check(backstory, character)
        for v in rule_violations:
            if v.startswith("HARD"):
                hard_violations.append(v)
        
        # PHASE 2: Implicit constraint check
        implicit_violations = self.implicit_checker.detect_violations(backstory, all_evidence)
        for v in implicit_violations:
            hard_violations.append(v)
        
        # PHASE 3: Temporal consistency (character arc)
        if early_evidence and late_evidence:
            arc_consistent, arc_reason = self.temporal_checker.check_character_arc(
                backstory, early_evidence, late_evidence, character
            )
            if not arc_consistent:
                soft_violations.append(f"TEMPORAL: {arc_reason}")
        
        # PHASE 4: Causal reachability
        is_reachable, reach_reason = self.causal_checker.check_reachability(
            backstory, all_evidence, character
        )
        if not is_reachable:
            hard_violations.append(f"CAUSAL: {reach_reason}")
        
        # PHASE 5: Atomic decomposition + verification
        atomic_facts = self.decompose_claim(backstory)
        atomic_contradictions = []
        for fact in atomic_facts[:5]:  # Limit to 5 facts for speed
            if self.verify_fact(fact, all_evidence, character):
                atomic_contradictions.append(fact)
        
        if atomic_contradictions:
            soft_violations.extend([f"FACT: {f}" for f in atomic_contradictions])
        
        # CONSERVATIVE SYNTHESIS: One hard violation = reject
        if hard_violations:
            return {
                "is_consistent": False,
                "reasoning": hard_violations[0],
                "confidence": 1.0,
                "type": "HARD_VIOLATION"
            }
        
        # Multiple soft violations = reject
        if len(soft_violations) >= 2:
            return {
                "is_consistent": False,
                "reasoning": f"Multiple issues: {soft_violations[0]}; {soft_violations[1]}",
                "confidence": 0.85,
                "type": "SOFT_ACCUMULATION"
            }
        
        # Single soft violation = warning but still reject (conservative)
        if len(soft_violations) == 1:
            return {
                "is_consistent": False,
                "reasoning": soft_violations[0],
                "confidence": 0.7,
                "type": "SOFT_VIOLATION"
            }
        
        return {
            "is_consistent": True,
            "reasoning": "All checks passed: causal reachability, temporal arc, implicit constraints, atomic facts",
            "confidence": 0.9,
            "type": "VERIFIED"
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
    
    def process(self, row):
        char = row["char"]
        caption = row.get("caption", "")
        content = row["content"]
        book_name = row.get("book_name", "")
        
        # Combine caption + content for query
        query = f"{char} {caption} {content[:150]}"
        
        # DISTRIBUTED retrieval (early/mid/late)
        evidence = self.reader.retrieve_distributed(query, book_name=book_name, top_k=9)
        
        # Full enhanced check
        result = self.checker.check(content, evidence, char)
        return {
            "id": row["id"],
            "label": "consistent" if result["is_consistent"] else "contradict",
            "reasoning": result.get("reasoning", "No detailed reasoning"),
            "confidence": result.get("confidence", 1.0),
            "violation_type": result.get("type", "N/A")
        }
    
    def run(self):
        self.setup()
        test_df = pd.read_csv(self.data_dir / "test.csv")
        print(f"\nProcessing {len(test_df)} samples...")
        
        results = []
        for idx, row in test_df.iterrows():
            if idx % 10 == 0:
                print(f"  {idx+1}/{len(test_df)}...")
            res = self.process(row)
            results.append(res)
        
        # 1. Strict Submission (for auto-grader)
        out_strict = pd.DataFrame(results)[["id", "label"]]
        submission_path = self.data_dir / "submission.csv"
        out_strict.to_csv(submission_path, index=False)
        print(f"\nSaved strict submission: {submission_path}")
        
        # 2. Detailed Submission (for Outcome 2: Rationale)
        out_detailed = pd.DataFrame(results)
        detailed_path = self.data_dir / "submission_detailed.csv"
        out_detailed.to_csv(detailed_path, index=False)
        print(f"Saved detailed log: {detailed_path}")
        
        print(out_strict["label"].value_counts())
        
        return out_strict


def main():
    print("=" * 60)
    print("CONCORD Reasoning Pipeline v2.0 - ENHANCED")
    print("Full alignment with 7 expected outcomes")
    print("=" * 60)
    pipeline = Pipeline("/Users/jitterx/Desktop/CONCORD/data")
    pipeline.run()
    print("Pipeline Complete!")


if __name__ == "__main__":
    main()
