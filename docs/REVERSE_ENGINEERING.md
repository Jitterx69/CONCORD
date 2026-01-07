# CONCORD: Complete Reverse Engineering Document

**System**: Constraint-Oriented Narrative Consistency Decision System  
**Purpose**: Detect logical inconsistencies in character backstories against novel content  
**Architecture**: Logic-Driven RAG Pipeline with LLM-as-Tool
> [!IMPORTANT]
> **v2.0 Update**: This documentation covers the core system. The final submission includes a v2.0 enhanced pipeline (`reasoning_pipeline.py`) with:
> - **Distributed Retrieval**: Stratified sampling (Early/Mid/Late)
> - **Temporal & Causal Checkers**: Explicit logic for character arcs and reachability
> - **Conservative Synthesis**: "One hard violation = Reject" logic
> - **Implicit Constraint Detection**: Irreversibility rules


---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Directory Structure](#3-directory-structure)
4. [Core Reasoning Pipeline](#4-core-reasoning-pipeline)
5. [Backend Application (FastAPI)](#5-backend-application-fastapi)
6. [Core Engines](#6-core-engines)
7. [Data Models](#7-data-models)
8. [API Routes](#8-api-routes)
9. [Services Layer](#9-services-layer)
10. [Enhancements](#10-enhancements)
11. [Configuration & Infrastructure](#11-configuration--infrastructure)
12. [Data Flow Diagrams](#12-data-flow-diagrams)
13. [Reconstruction Guide](#13-reconstruction-guide)

---

## 1. Executive Summary

### What is CONCORD?

CONCORD is a **narrative consistency checking system** built for the Kharagpur Data Science Hackathon 2026. It determines whether a character's hypothetical backstory is **consistent** or **contradicts** the actual novel content.

### Key Philosophy

> **"Use LLMs as tools, write logic around them, build a system—not a model."**

This system does **NOT** train ML models. It uses:
- **Frozen LLMs** (TinyLlama-1.1B) for semantic understanding
- **Frozen Embeddings** (all-MiniLM-L6-v2) for retrieval
- **Deterministic Python logic** for final decisions

### Core Innovation: Atomic Decomposition

Instead of asking "Is this whole paragraph consistent?", CONCORD:
1. **Decomposes** claims into atomic facts using LLM
2. **Verifies** each fact independently against retrieved evidence
3. **Synthesizes** results using deterministic logic (`if any(CONTRADICT) -> CONTRADICT`)

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CONCORD SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 REASONING PIPELINE                       │   │
│   │  (backend/pipeline/reasoning_pipeline.py)               │   │
│   │                                                         │   │
│   │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │   │
│   │  │ NovelReader │──▶│ Consistency │──▶│  Pipeline   │   │   │
│   │  │   - load    │   │   Checker   │   │   - run     │   │   │
│   │  │   - chunk   │   │ - decompose │   │  - process  │   │   │
│   │  │   - embed   │   │ - verify    │   │  - output   │   │   │
│   │  │   - retrieve│   │ - check     │   │             │   │   │
│   │  └─────────────┘   └─────────────┘   └─────────────┘   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   FASTAPI BACKEND                        │   │
│   │  (backend/app/)                                          │   │
│   │                                                         │   │
│   │  ┌───────────────────────────────────────────────────┐   │   │
│   │  │                  CORE ENGINES                      │   │   │
│   │  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐ │   │   │
│   │  │  │ Constraint │ │ Knowledge  │ │    Entity      │ │   │   │
│   │  │  │  Engine    │ │   Graph    │ │   Tracker      │ │   │   │
│   │  │  └────────────┘ └────────────┘ └────────────────┘ │   │   │
│   │  │  ┌────────────┐ ┌────────────┐                    │   │   │
│   │  │  │  Temporal  │ │  Explainer │                    │   │   │
│   │  │  │  Reasoner  │ │            │                    │   │   │
│   │  │  └────────────┘ └────────────┘                    │   │   │
│   │  └───────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Directory Structure

```
CONCORD/
├── .gitignore                 # Excludes venv, models, large files
├── README.md                  # Project overview
├── docker-compose.yml         # Container orchestration
│
├── backend/
│   ├── Dockerfile             # Container build
│   ├── requirements.txt       # Python dependencies
│   ├── pyproject.toml         # Project metadata
│   │
│   ├── pipeline/
│   │   └── reasoning_pipeline.py   # 🔥 MAIN HACKATHON SOLUTION
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application entry
│   │   ├── config.py          # Settings management
│   │   │
│   │   ├── core/              # 🧠 REASONING ENGINES
│   │   │   ├── constraint_engine.py
│   │   │   ├── knowledge_graph.py
│   │   │   ├── entity_tracker.py
│   │   │   ├── temporal_reasoner.py
│   │   │   └── explainer.py
│   │   │
│   │   ├── api/routes/        # REST API endpoints
│   │   │   ├── health.py
│   │   │   ├── consistency.py
│   │   │   ├── knowledge.py
│   │   │   └── narratives.py
│   │   │
│   │   ├── models/            # Pydantic schemas
│   │   │   └── models.py
│   │   │
│   │   ├── services/          # Business logic
│   │   │   ├── ml_service.py
│   │   │   └── trained_model.py
│   │   │
│   │   └── enhancements/      # Optional features
│   │       ├── emotional/
│   │       └── self_healing/
│   │
│   ├── training/              # (Legacy, now empty)
│   └── tests/
│
├── data/
│   ├── train.csv              # Training data (reference)
│   ├── test.csv               # Test data (60 samples)
│   └── submission.csv         # 🎯 OUTPUT FILE
│
└── pdf/                       # Problem statement images
```

---

## 4. Core Reasoning Pipeline

**File**: `backend/pipeline/reasoning_pipeline.py`  
**Lines**: 290  
**Purpose**: Complete hackathon solution

### 4.1 Class: `Evidence`

```python
@dataclass
class Evidence:
    source: str      # Novel name (e.g., "The Count of Monte Cristo")
    text: str        # Retrieved chunk text
    score: float     # Cosine similarity score
```

### 4.2 Class: `NovelReader`

**Purpose**: Load novels, chunk them, embed them, and retrieve relevant passages.

```python
class NovelReader:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.novels = {}       # {"novel_name": "full_text"}
        self.chunks = {}       # {"novel_name": ["chunk1", "chunk2", ...]}
        self.embeddings = {}   # {"novel_name": np.array([[...], [...]])}
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `load()` | `def load(self)` | Reads all `.txt` files from `data_dir` into `self.novels` |
| `chunk(size=500)` | `def chunk(self, size=500)` | Splits novels by `\n\n`, truncates to `size` chars, limits to 2000 chunks |
| `embed()` | `def embed(self)` | Encodes all chunks using sentence-transformers |
| `retrieve(query, book_name, top_k)` | `def retrieve(self, query, book_name=None, top_k=5)` | Finds top-k similar chunks via cosine similarity. Filters by `book_name` if provided. |

### 4.3 Class: `RuleBasedChecker`

**Purpose**: Fast-fail logical contradictions using regex patterns.

```python
class RuleBasedChecker:
    @staticmethod
    def check(content, char) -> List[str]:
        """Returns list of rule violations"""
```

**Rules Implemented**:
1. **Death Finality**: Actions cannot occur after death (e.g., "died in 1840" + "continued until 1845")
2. **Birth-Death Order**: Birth year must precede death year
3. **Age Consistency**: Age must match birth-death span
4. **Contradiction Keywords**: Detects phrases like "but actually", "contradicts", "never existed"

### 4.4 Class: `ConsistencyChecker`

**Purpose**: Orchestrates LLM-based consistency checking using Atomic Decomposition.

```python
class ConsistencyChecker:
    def __init__(self):
        self.device = "mps" | "cuda" | "cpu"
        self.tok = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        self.llm = AutoModelForCausalLM.from_pretrained(...)
        self.rule_checker = RuleBasedChecker()
```

| Method | Purpose | LLM Usage |
|--------|---------|-----------|
| `decompose_claim(text)` | Split backstory into atomic facts | YES - generates list of facts |
| `verify_fact(fact, evidence, char)` | Check single fact against evidence | YES - returns CONSISTENT/CONTRADICT |
| `check(claim, evidence, char)` | Full consistency check | Orchestrates above methods |

#### 4.4.1 `decompose_claim(text)` - Detailed

```python
def decompose_claim(self, text):
    """
    LLM Prompt:
    "You are a logic parser. Split the narrative text into atomic facts.
    Each fact must be a complete sentence."
    
    Example:
    Input: "Born in 1820, he was a sailor who hated onions."
    Output:
    - He was born in 1820.
    - He was a sailor.
    - He hated onions.
    """
    # Uses chat template, generates up to 200 tokens
    # Parses bullet points from response
    return facts  # List[str]
```

#### 4.4.2 `verify_fact(fact, evidence, char)` - Detailed

```python
def verify_fact(self, fact, evidence_text, character):
    """
    LLM Prompt:
    "You are a strict consistency verifier.
    If the claim contradicts evidence, return CONTRADICT.
    If compatible, return CONSISTENT."
    
    Returns: bool (True if CONTRADICT found in response)
    """
```

#### 4.4.3 `check(claim, evidence, char)` - Detailed

```python
def check(self, claim_text, evidence_text, character):
    # 1. Rule-Based Check (Fast Fail)
    violations = self.rule_checker.check(claim_text, character)
    if violations:
        return {"is_consistent": False, "reasoning": violations[0]}
    
    # 2. Decomposition (LLM Tool)
    atomic_facts = self.decompose_claim(claim_text)
    
    # 3. Atomic Verification (LLM Tool)
    contradictions = []
    for fact in atomic_facts:
        if self.verify_fact(fact, evidence_text, character):
            contradictions.append(fact)
    
    # 4. Logic Synthesis (Deterministic)
    if contradictions:
        return {"is_consistent": False, "reasoning": contradictions}
    return {"is_consistent": True, "reasoning": "All facts consistent"}
```

### 4.5 Class: `Pipeline`

**Purpose**: Orchestrates the full end-to-end flow.

```python
class Pipeline:
    def __init__(self, data_dir):
        self.reader = NovelReader(data_dir)
        self.checker = ConsistencyChecker()
```

| Method | Description |
|--------|-------------|
| `setup()` | Calls `reader.load()`, `reader.chunk()`, `reader.embed()` |
| `process(row)` | Retrieves evidence, calls `checker.check()`, returns label |
| `run()` | Iterates test.csv, processes each row, saves submission.csv |

### 4.6 Entry Point

```python
def main():
    pipeline = Pipeline("/Users/jitterx/Desktop/CONCORD/data")
    pipeline.run()

if __name__ == "__main__":
    main()
```

---

## 5. Backend Application (FastAPI)

**File**: `backend/app/main.py`

### 5.1 Application Setup

```python
app = FastAPI(
    title="CONCORD",
    description="Constraint-Oriented Narrative Consistency Decision System",
    version="1.0.0",
    lifespan=lifespan,
)
```

### 5.2 Lifespan Handler

Initializes all services on startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize services
    app.state.ml_service = MLService()
    app.state.knowledge_graph = KnowledgeGraph()
    app.state.constraint_engine = ConstraintEngine()
    app.state.temporal_reasoner = TemporalReasoner()
    app.state.entity_tracker = EntityTracker()
    app.state.explainer = Explainer()
    yield
```

### 5.3 Registered Routers

| Router | Prefix | Tags |
|--------|--------|------|
| `health.router` | `/api/v1` | Health |
| `consistency.router` | `/api/v1` | Consistency |
| `knowledge.router` | `/api/v1` | Knowledge Graph |
| `narratives.router` | `/api/v1` | Narratives |

---

## 6. Core Engines

### 6.1 ConstraintEngine

**File**: `backend/app/core/constraint_engine.py`  
**Purpose**: Validates facts against registered constraints.

```python
class ConstraintEngine:
    def __init__(self):
        self.constraints = {}      # {UUID: Constraint}
        self.compiled_rules = {}   # {UUID: compiled_pattern}
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `add_constraint(constraint)` | `Constraint -> None` | Registers a new constraint |
| `validate(facts)` | `List[Fact] -> List[ConsistencyIssue]` | Checks facts against all constraints |
| `_check_constraint(constraint, facts_by_subject)` | Internal | Evaluates single constraint |
| `_check_implicit_constraints(facts)` | Internal | Detects internal contradictions |
| `check_single(text, rule)` | `str, str -> (bool, str)` | Checks one rule against text |

**Constraint Types Supported**:
- `FACTUAL`: Attribute equality (e.g., `entity.Alice.age == 25`)
- `TEMPORAL`: Time-based rules
- `CAUSAL`: Cause-effect relationships
- `SPATIAL`: Location consistency
- `BEHAVIORAL`: Character behavior patterns
- `RELATIONAL`: Entity relationships

### 6.2 KnowledgeGraph

**File**: `backend/app/core/knowledge_graph.py`  
**Purpose**: In-memory graph of entities, relationships, and facts.

```python
class KnowledgeGraph:
    def __init__(self):
        self.entities = {}        # {UUID: Entity}
        self.relationships = []   # List[Relationship]
        self.facts = {}           # {UUID: Fact}
        self.facts_by_subject = {}  # {"subject_name": [Fact, ...]}
```

| Method | Description |
|--------|-------------|
| `add_entity(entity)` | Add entity to graph |
| `find_entity_by_name(name)` | Case-insensitive entity lookup |
| `add_relationship(rel)` | Add edge between entities |
| `add_fact(fact)` | Add fact, indexed by subject |
| `check_conflicts(new_facts)` | Detect contradictions with existing facts |
| `query(parsed_query)` | Execute structured query |
| `stats()` | Return entity/relationship/fact counts |

### 6.3 EntityTracker

**File**: `backend/app/core/entity_tracker.py`  
**Purpose**: Monitors entity behavior and state consistency.

```python
@dataclass
class EntityState:
    entity_id: UUID
    position: int
    attributes: Dict[str, Any]
    location: Optional[str]
    mood: Optional[str]
    alive: bool = True

@dataclass
class EntityProfile:
    entity: Entity
    states: List[EntityState]
    behaviors: List[str]
    mention_count: int
```

```python
class EntityTracker:
    def __init__(self):
        self.profiles = {}   # {UUID: EntityProfile}
```

| Method | Description |
|--------|-------------|
| `track_entity(entity, position)` | Start tracking an entity |
| `update_state(entity_id, ...)` | Update entity's current state |
| `add_behavior(entity_id, behavior)` | Record observed behavior |
| `check_behavior(entities, text)` | Detect behavioral inconsistencies |
| `_check_alive_status(entity, text)` | Detect dead characters acting |
| `_check_location_consistency(entity, text)` | Detect teleportation |

### 6.4 TemporalReasoner

**File**: `backend/app/core/temporal_reasoner.py`  
**Purpose**: Timeline consistency and causality validation.

```python
@dataclass
class TemporalEvent:
    id: UUID
    description: str
    position: int
    timestamp: Optional[datetime]
    relative_time: Optional[str]
    duration: Optional[timedelta]

@dataclass
class TimelineEntry:
    event: TemporalEvent
    order: int
    confidence: float
```

```python
class TemporalReasoner:
    def __init__(self):
        self.events = {}     # {UUID: TemporalEvent}
        self.timeline = []   # List[TimelineEntry]
```

| Method | Description |
|--------|-------------|
| `check_timeline(text, facts)` | Full temporal consistency check |
| `_extract_events(text)` | Parse temporal markers from text |
| `_build_timeline(events)` | Construct chronological order |
| `_check_causality(text, facts)` | Verify cause-effect sequences |
| `_check_durations(text)` | Detect impossible durations |
| `extract_timeline(text)` | Return visualization-ready timeline |

### 6.5 Explainer

**File**: `backend/app/core/explainer.py`  
**Purpose**: Generate human-readable explanations for consistency issues.

```python
class Explainer:
    ISSUE_TEMPLATES = {
        ConstraintType.FACTUAL: {...},
        ConstraintType.TEMPORAL: {...},
        # etc.
    }
    
    def __init__(self):
        self.explanations = {}  # Cache
```

| Method | Description |
|--------|-------------|
| `explain(issue)` | Generate full explanation with evidence |
| `_build_reasoning(issue)` | Step-by-step reasoning chain |
| `suggest_fix(issue, facts)` | Propose correction |
| `generate_report_summary(issues)` | Multi-issue summary report |

---

## 7. Data Models

**File**: `backend/app/models/models.py`

### 7.1 Enums

```python
class EntityType(str, Enum):
    CHARACTER = "character"
    LOCATION = "location"
    OBJECT = "object"
    EVENT = "event"
    CONCEPT = "concept"
    TIME = "time"

class ConstraintType(str, Enum):
    FACTUAL = "factual"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    SPATIAL = "spatial"
    BEHAVIORAL = "behavioral"
    RELATIONAL = "relational"

class ConsistencyLevel(str, Enum):
    CONSISTENT = "consistent"
    WARNING = "warning"
    INCONSISTENT = "inconsistent"
    CRITICAL = "critical"

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
```

### 7.2 Core Models

```python
class Entity(BaseModel):
    id: UUID
    name: str
    type: EntityType
    attributes: Dict[str, Any]
    first_appearance: Optional[int]

class Relationship(BaseModel):
    id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str
    properties: Dict[str, Any]

class Fact(BaseModel):
    id: UUID
    subject: str
    predicate: str
    object: str
    confidence: float
    source_text: Optional[str]
    position: Optional[int]

class Constraint(BaseModel):
    id: UUID
    type: ConstraintType
    description: str
    rule: str
    is_hard: bool
    priority: int

class ConsistencyIssue(BaseModel):
    id: UUID
    type: ConstraintType
    level: ConsistencyLevel
    description: str
    conflicting_facts: List[UUID]
    evidence: List[str]
    suggested_fix: Optional[str]
    confidence: float
```

---

## 8. API Routes

### 8.1 Health (`/api/v1/health`)

```python
@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CONCORD"}
```

### 8.2 Consistency (`/api/v1/consistency`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/check` | POST | Check text consistency |
| `/issues` | GET | List all detected issues |
| `/explain/{issue_id}` | GET | Get explanation for issue |

### 8.3 Knowledge (`/api/v1/knowledge`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/entities` | GET/POST | List/Create entities |
| `/entities/{id}` | GET/DELETE | Get/Remove entity |
| `/facts` | GET/POST | List/Create facts |
| `/query` | POST | Natural language query |

### 8.4 Narratives (`/api/v1/narratives`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Analyze narrative text |
| `/timeline` | POST | Extract timeline |
| `/entities/extract` | POST | Extract entities from text |

---

## 9. Services Layer

### 9.1 MLService

**File**: `backend/app/services/ml_service.py`  
**Purpose**: NLP operations using heuristic patterns.

```python
class MLService:
    ENTITY_PATTERNS = {...}   # Regex for NER
    FACT_PATTERNS = [...]     # Regex for fact extraction
    POSITIVE_WORDS = {...}    # Sentiment lexicon
    NEGATIVE_WORDS = {...}
```

| Method | Description |
|--------|-------------|
| `extract_entities(text)` | Named entity recognition |
| `extract_facts(text)` | Subject-predicate-object extraction |
| `analyze_emotional_arc(text)` | Sentiment analysis |
| `parse_query(query)` | NL query to structured format |
| `compute_similarity(text1, text2)` | Jaccard similarity |

---

## 10. Enhancements

### 10.1 Emotional Analyzer

**File**: `backend/app/enhancements/emotional/analyzer.py`  
Tracks emotional arcs and sentiment patterns.

### 10.2 Self-Healing Fixer

**File**: `backend/app/enhancements/self_healing/fixer.py`  
Attempts to automatically fix detected inconsistencies.

---

## 11. Configuration & Infrastructure

### 11.1 Settings

**File**: `backend/app/config.py`

```python
class Settings(BaseSettings):
    APP_NAME: str = "CONCORD"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql://..."
    NEO4J_URI: str = "bolt://localhost:7687"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CONSISTENCY_THRESHOLD: float = 0.7
```

### 11.2 Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
  
  postgres:
    image: postgres:15
  
  neo4j:
    image: neo4j:5
  
  redis:
    image: redis:7
```

### 11.3 Requirements

```
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
sentence-transformers  # For embeddings
transformers           # For LLM
torch                  # For inference
```

---

## 12. Data Flow Diagrams

### 12.1 Main Pipeline Flow

```
test.csv
   │
   ▼
┌─────────────────┐
│  Load Novels    │ .txt files → {"name": "text"}
└────────┬────────┘
         ▼
┌─────────────────┐
│  Chunk Novels   │ Split by paragraphs, max 500 chars
└────────┬────────┘
         ▼
┌─────────────────┐
│ Embed Chunks    │ all-MiniLM-L6-v2 → vectors
└────────┬────────┘
         ▼
   ┌─────────────────────────────────────┐
   │       FOR EACH ROW IN test.csv      │
   │                                     │
   │  ┌─────────────────────────────┐    │
   │  │ Build Query                 │    │
   │  │ = char + caption + content  │    │
   │  └──────────────┬──────────────┘    │
   │                 ▼                   │
   │  ┌─────────────────────────────┐    │
   │  │ Retrieve Evidence           │    │
   │  │ Cosine similarity → top-7   │    │
   │  │ Filter by book_name         │    │
   │  └──────────────┬──────────────┘    │
   │                 ▼                   │
   │  ┌─────────────────────────────┐    │
   │  │ Rule-Based Check            │    │
   │  │ Regex for temporal/logical  │    │
   │  └──────────────┬──────────────┘    │
   │                 ▼                   │
   │  ┌─────────────────────────────┐    │
   │  │ Decompose Claim (LLM)       │    │
   │  │ "Split into atomic facts"   │    │
   │  └──────────────┬──────────────┘    │
   │                 ▼                   │
   │  ┌─────────────────────────────┐    │
   │  │ Verify Each Fact (LLM)      │    │
   │  │ "CONSISTENT or CONTRADICT"  │    │
   │  └──────────────┬──────────────┘    │
   │                 ▼                   │
   │  ┌─────────────────────────────┐    │
   │  │ Synthesize (Python Logic)   │    │
   │  │ if any(CONTRADICT) → False  │    │
   │  └──────────────┬──────────────┘    │
   │                 ▼                   │
   │           {id, label}               │
   │                                     │
   └─────────────────────────────────────┘
         │
         ▼
   submission.csv
```

---

## 13. Reconstruction Guide

### Step 1: Environment Setup

```bash
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic pydantic-settings
pip install sentence-transformers transformers torch
pip install pandas numpy
```

### Step 2: Core Pipeline

1. Create `backend/pipeline/reasoning_pipeline.py`
2. Implement `Evidence` dataclass
3. Implement `NovelReader` with load/chunk/embed/retrieve
4. Implement `RuleBasedChecker` with regex patterns
5. Implement `ConsistencyChecker` with decompose/verify/check
6. Implement `Pipeline` with setup/process/run
7. Add `main()` entry point

### Step 3: Data Files

Place in `data/`:
- `train.csv` (reference)
- `test.csv` (input)
- Novel `.txt` files

### Step 4: Execute

```bash
python backend/pipeline/reasoning_pipeline.py
# Output: data/submission.csv
```

### Step 5: FastAPI (Optional)

```bash
cd backend
uvicorn app.main:app --reload
# Visit: http://localhost:8000/docs
```

---

## Appendix: Key Insights

1. **No Training**: System uses frozen models only
2. **Atomic Verification**: More accurate than holistic checks
3. **Hybrid Approach**: Rules + LLM + Logic
4. **Book Filtering**: Evidence scoped to specific novel
5. **Deterministic Output**: Same input → Same output
6. **Auditable**: Every decision traceable to evidence

---

*Document generated for CONCORD v1.0.0 - Kharagpur Data Science Hackathon 2026*
