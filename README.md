# 🎭 CONCORD

## Constraint-Oriented Narrative Consistency Decision System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **CONCORD** is an AI-powered platform for maintaining narrative coherence and logical integrity in complex storytelling scenarios.

---

## 🌟 Overview

CONCORD acts as an intelligent consistency layer for narratives, ensuring every story element harmonizes with established truths. Think of it as an **orchestra conductor for storytelling** - detecting discord, identifying the source, and guiding corrections.

### Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **Knowledge Graph** | Dynamic tracking of entities, facts, and relationships |
| ⚖️ **Constraint Engine** | Rule-based validation with soft/hard constraints |
| ⏱️ **Temporal Reasoner** | Timeline and causality consistency checking |
| 👤 **Entity Tracker** | Character behavior and attribute monitoring |
| 💡 **Explainer** | Human-readable reasoning for all decisions |
| 💝 **Emotional AI** | Sentiment arcs and mood consistency |
| 🔧 **Self-Healing** | Automatic fix suggestions for issues |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for full stack)

### Option 1: Local Development

```bash
# Clone the repository
cd CONCORD

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Access Points

- 🌐 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc
- 🎨 **Frontend**: http://localhost:3000 (when available)

---

## 📖 API Usage

### Check Narrative Consistency

```bash
curl -X POST "http://localhost:8000/api/v1/check" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Alice was 25 years old. She worked as a detective. Later that day, Alice mentioned she was 30.",
    "check_emotional": true,
    "check_temporal": true,
    "auto_fix": false
  }'
```

### Response Example

```json
{
  "report": {
    "overall_score": 0.85,
    "level": "warning",
    "issues": [
      {
        "type": "factual",
        "level": "inconsistent",
        "description": "Contradiction: 'Alice' has conflicting values for 'age'. Existing: '25', New: '30'",
        "suggested_fix": "Clarify whether Alice's age is '25' or '30'"
      }
    ],
    "facts_checked": 3,
    "entities_tracked": 1
  },
  "processing_time_ms": 45.2
}
```

### Add Facts to Knowledge Graph

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/facts" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Alice",
    "predicate": "occupation",
    "object": "detective"
  }'
```

---

## 🏗️ Architecture

```
CONCORD
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── api/routes/          # API endpoints
│   │   ├── core/                # Core components
│   │   │   ├── knowledge_graph.py
│   │   │   ├── constraint_engine.py
│   │   │   ├── temporal_reasoner.py
│   │   │   ├── entity_tracker.py
│   │   │   └── explainer.py
│   │   ├── enhancements/        # Super features
│   │   │   ├── emotional/
│   │   │   └── self_healing/
│   │   ├── models/              # Data models
│   │   └── services/            # ML services
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # React dashboard (coming soon)
├── docker-compose.yml
└── README.md
```

---

## 🎯 Core Components

### 1. Knowledge Graph
Maintains a dynamic graph of all narrative facts:
- Entities (characters, locations, objects)
- Relationships (friend_of, located_in, owns)
- Facts (Alice.age = 25)

### 2. Constraint Engine
Validates narrative against rules:
- **Hard Constraints**: Must be satisfied
- **Soft Constraints**: Preferred but can be relaxed
- Detects implicit contradictions

### 3. Temporal Reasoner
Ensures timeline consistency:
- Event sequencing
- Cause-effect validation
- Duration checking

### 4. Entity Tracker
Monitors character consistency:
- Behavioral patterns
- Attribute changes
- Location tracking (no teleportation!)

### 5. Explainer
Provides transparent reasoning:
- Step-by-step logic chains
- Evidence presentation
- Confidence scoring

---

## ✨ Super Enhancements

### Emotional Intelligence
- Character mood tracking
- Sentiment arc analysis
- Tone consistency validation
- Relationship emotional mapping

### Self-Healing Narratives
- Automatic fix generation
- Multiple fix options with ranking
- Minimal disruption priority
- Learn from accepted fixes

---

## 📊 Consistency Check Types

| Type | Description | Example |
|------|-------------|---------|
| **Factual** | Facts match established truths | Age, occupation, names |
| **Temporal** | Timeline integrity | Events in correct order |
| **Causal** | Cause-effect logic | Actions have proper consequences |
| **Spatial** | Location consistency | Characters can't teleport |
| **Behavioral** | Entity behavior patterns | Characters act in-character |
| **Relational** | Relationship consistency | Friends don't become strangers |

---

## 🔧 Configuration

Set environment variables or create a `.env` file:

```env
# Application
DEBUG=true
APP_NAME=CONCORD

# Database
DATABASE_URL=postgresql://concord:concord@localhost:5432/concord
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=concord123

# Redis
REDIS_URL=redis://localhost:6379/0

# ML Models (optional)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SENTIMENT_MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest
```

---

## 🧪 Testing

```bash
# Run tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_consistency.py -v
```

---

## 📈 Roadmap

- [x] Core consistency engine
- [x] Knowledge graph implementation
- [x] Temporal reasoning
- [x] Entity tracking
- [x] Explainable AI
- [x] Emotional intelligence
- [x] Self-healing narratives
- [ ] React frontend dashboard
- [ ] Multi-modal fusion (images + text)
- [ ] Real-time collaboration
- [ ] Federated learning
- [ ] Plugin ecosystem

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting a PR.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Kharagpur Data Science Hackathon 2026
- The open-source NLP community
- All contributors and supporters

---

<div align="center">

**CONCORD** - *Ensuring every narrative element harmonizes with the established truth.*

Made with ❤️ for storytellers everywhere

</div>
