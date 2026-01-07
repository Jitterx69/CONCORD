# CONCORD Final Submission Package

**Team**: Jitterx  
**Hackathon**: Kharagpur Data Science Hackathon 2026  
**Track**: Narrative Consistency Detection

---

## 📦 Submission Contents

### Core Deliverable
- **`data/submission.csv`** - Final predictions (60 samples: 45 consistent, 15 contradict)

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

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│           CONCORD REASONING PIPELINE                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│   test.csv → NovelReader → ConsistencyChecker       │
│                    ↓              ↓                 │
│              [Evidence]    [Atomic Decomposition]   │
│                    ↓              ↓                 │
│              Retrieval      Verification            │
│                    ↓              ↓                 │
│                  ←──── Synthesis ────→              │
│                           ↓                         │
│                    submission.csv                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Key Innovation: Atomic Decomposition

Instead of asking "Is this paragraph consistent?", we:

1. **Decompose** claims into atomic facts (LLM)
2. **Verify** each fact independently (LLM)
3. **Synthesize** results (Python logic: `any(CONTRADICT) → CONTRADICT`)

This makes the system **transparent, auditable, and logic-driven**.

---

## 📊 Results

| Metric | Value |
|--------|-------|
| Total Samples | 60 |
| Consistent | 45 (75%) |
| Contradict | 15 (25%) |
| Processing Time | ~3 min |

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

## 📁 Repository

GitHub: https://github.com/Jitterx69/CONCORD

---

*CONCORD v1.0.0 - Constraint-Oriented Narrative Consistency Decision System*
