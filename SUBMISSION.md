# CONCORD Final Submission Package

**Team**: Jitterx  
**Hackathon**: Kharagpur Data Science Hackathon 2026  
**Track**: Narrative Consistency Detection

---

## 📦 Submission Contents

### Core Deliverable
- **`data/submission.csv`** - Strict final predictions (id, label)
- **`data/submission_detailed.csv`** - Includes **Rationale**, Confidence, and Violation Type (Addresses Outcome 2)

### Solution Code
- **`backend/pipeline/reasoning_pipeline.py`** - Main hackathon solution (290 lines)
  - Atomic Decomposition architecture
  - TinyLlama-1.1B for semantic reasoning
  - Rule-based validation layer
  - Book-filtered evidence retrieval

### Documentation
- **`docs/REVERSE_ENGINEERING.md`** - Complete system documentation
- **`README.md`** - Project overview

---

## 🚀 How to Run

### Quick Start (Reasoning Pipeline)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install sentence-transformers transformers torch pandas numpy
python pipeline/reasoning_pipeline.py
# Output: data/submission.csv
```

### Full API Server
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Visit: http://localhost:8000/docs
```

---

## 🏗️ Architecture (v2.0 Enhanced)

```
┌─────────────────────────────────────────────────────────────┐
│             CONCORD REASONING PIPELINE v2.0                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. DISTRIBUTED EVIDENCE RETRIEVAL                        │
│      └── Stratified sampling (Early/Mid/Late Narrative)    │
│                                                             │
│   2. TEMPORAL CONSISTENCY CHECK                             │
│      └── Character arc & personality drift validation       │
│                                                             │
│   3. IMPLICIT CONSTRAINT DETECTION                          │
│      └── Irreversibility, psychological lock-in logic      │
│                                                             │
│   4. CAUSAL REACHABILITY ASSESSMENT                         │
│      └── Counterfactual: "Could backstory LEAD TO future?" │
│                                                             │
│   5. ATOMIC DECOMPOSITION & CONSERVATIVE SYNTHESIS          │
│      └── One hard violation = INSTANT REJECTION            │
│                                                             │
│   submission.csv (Global Consistency Verdict)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Design: "System over Model"

We do **NOT** rely on a generic LLM validation. Instead, we implemented 5 specialized reasoning engines:

1.  **Distributed Retrieval**: Ensures evidence is gathered from the character's entire timeline, not just keyword matches.
2.  **Causal Reachability**: Distinguishes "plausible" (sounds good) from "reachable" (causally possible).
3.  **Implicit Constraints**: Hard-coded logic for irreversible events (death, birth) and soft logic for psychological commitments.
4.  **Conservative Synthesis**: Asymmetric decision logic—acceptance requires all checks to pass; rejection requires only one hard violation.

---

## 📊 Results

| Metric | Value |
|--------|-------|
| Total Samples | 60 |
| Consistent | 22 (37%) |
| Contradict | 38 (63%) |
| Processing Time | ~3 min |

**Note**: The shift towards "Contradict" reflects the strict "Conservative Rejection" logic implemented to meet the "one hard violation is enough" requirement.

---

## 🔧 Technology Stack

- **Language**: Python 3.9+
- **LLM**: TinyLlama-1.1B-Chat (frozen, no training)
- **Embeddings**: all-MiniLM-L6-v2 (frozen)
- **Framework**: FastAPI
- **Logic**: Rule-based + LLM-as-tool

---

## ✅ Compliance

- ❌ NO ML model training
- ❌ NO statistical learning
- ✅ LLMs used as tools
- ✅ Logic-driven system
- ✅ Deterministic output

---

## ✅ Compliance Matrix

## ✅ Compliance Matrix

### Explicit & Reasoning Outcomes
| Requirement | Metric | Implementation Status |
|-------------|--------|-----------------------|
| **1.1 Binary Consistency** | Output 1/0 | ✅ `submission.csv` (strict) |
| **1.2 Rationale** | Explanation | ✅ `submission_detailed.csv` (reasoning column) |
| **2.1 Temporal Logic** | Character Arc | ✅ `TemporalConsistencyChecker` |
| **2.2 Causal Check** | Reachability | ✅ `CausalReachabilityChecker` (Counterfactuals) |
| **2.3 Constraints** | Irreversibility | ✅ `ImplicitConstraintChecker` |
| **3.2 Conservative** | Assymetric Decision | ✅ One hard violation = Instant Reject |

### System & Meta Outcomes
| Requirement | Metric | Implementation Status |
|-------------|--------|-----------------------|
| **8. Controlled LLM Use** | Tool vs Oracle | ✅ LLM used only for *decomposition/verification*; Logic does *synthesis* |
| **9. Long Context** | Strategy | ✅ **Stratified Sampling** (Early/Mid/Late chunks) |
| **13. Reachability** | vs Plausibility | ✅ Prompt explicitly asks "Could this LEAD TO events?" |
| **15. Systems Thinking** | Architecture | ✅ 5-Engine Pipeline Design (not just a prompt) |

---

## ⚖️ Limitations & Uncertainty

In the spirit of **Outcome 4.2 (Honest Handling of Ambiguity)**, we acknowledge:

1.  **Implicit Context Limits**: while we use distributed sampling, extremely subtle contradictions spanning hundreds of pages might still be missed effectively without full-text processing (which is computationally prohibitive).
2.  **Ambiguous Timelines**: For events with no clear dates (e.g., "years later"), the Temporal Reasoner relies on relative positioning, which has lower confidence than absolute dates.
3.  **Irony & Metaphor**: The LLM tools may struggle with highly stylized ironic statements in 19th-century literature, potentially flagging them as contradictions (though our Conservative Logic prefers false negatives to false positives in this specific domain to ensure safety).
4.  **World Knowledge**: The system relies on the LLM's frozen internal knowledge for general world facts (e.g., "horses can't fly"), which may be limited for obscure historical contexts.

---

## 📁 Repository

GitHub: https://github.com/Jitterx69/CONCORD

---

*CONCORD v1.0.0 - Constraint-Oriented Narrative Consistency Decision System*
