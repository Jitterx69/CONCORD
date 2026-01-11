# CONCORD: Constraint-Oriented Narrative Consistency Decision System

![Build Status](https://img.shields.io/badge/build-passing-brightgreen) ![Version](https://img.shields.io/badge/version-2.1.0-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## Project Overview

**CONCORD** is an advanced, polyglot platform designed to ensure narrative coherence and logical integrity within complex storytelling environments. Originally developed for the **Kharagpur Data Science Hackathon 2026** (Track: Narrative Consistency Detection), the system operates as an intelligent consistency layer, validating factual, temporal, and causal integrity across dynamic narratives.

The system implements a **"System over Model"** philosophy, prioritizing deterministic logic and structured reasoning over purely probabilistic language model outputs. This ensures high-precision consistency checking suitable for rigorous narrative validation.

---

## System Architecture

CONCORD is built on a distributed, microservices-based architecture, leveraging the strengths of five different programming languages to handle specific aspects of narrative validation:

| Service | Language | Role | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | **Python (FastAPI)** | API Gateway & AI | BDI Agents, Quantum State Management, LLM Integration |
| **Causal Core** | **Rust** | High-Performance Logic | Graph Algorithms, Cycle Detection, Causal Analysis |
| **Federation** | **Java** | Distributed Consensus | Raft-Lite Consensus, Ledger Synchronization |
| **Analytics** | **R** | Statistical Analysis | Time-Series Forecasting, Narrative Visualizations |
| **Physics Sim** | **C++** | Physical Validation | A* Pathfinding, Travel Time Estimation |
| **Vector Store** | **C** | Semantic Memory | Native Vector Operations (Dot Product, NN) |

The system uses **Apache Kafka** for event-driven communication and **Docker Compose** for unified container orchestration.

---

## Key Features (Mega Expansion)

The platform has been significantly expanded with over 30+ advanced features across its core services:

### Rust Causal Core (`rust_core`)
*   **Advanced Graph Algorithms**: PageRank, Betweenness Centrality, Closeness Centrality, K-Core Decomposition.
*   **Structural Analysis**: Cycle Detection (DFS), Community Detection (Connected Components), Triangle Counting.
*   **Pathfinding**: Maximum Flow (Edmonds-Karp placeholder), Minimum Spanning Tree, Network Diameter.
*   **Performance**: Highly optimized, parallel graph traversal using Rayon.

### Java Federation Service (`java_services`)
*   **Distributed Consensus**: Implements **Raft-Lite** for leader election and log replication.
*   **Resiliency**: Heartbeat monitoring, Vote Request handling, and Term management.
*   **Ledger Sync**: Commit indices and AppendEntries logic for ensuring consistency across nodes.

### R Analytics Engine (`r_analytics`)
*   **Visual Suite**: 10+ Plot types including Sentiment Arcs, Interaction Networks, and Narrative Density.
*   **Advanced Stats**: Time-series forecasting, Anomaly Detection, and Correlation Matrices.
*   **Insight Generation**: Automated narrative commentary and probability entropy calculation.

### C++ Physics Engine (`cpp_sim`)
*   **A* Pathfinding**: Calculates optimal routes across a 3D grid.
*   **Physical Realism**: Validates travel times based on distance and velocity constraints.
*   **Integration**: Exposed as a shared library (`libphys.so`) for high-speed Python calls.

### Backend Orchestrator (`backend`)
*   **BDI Agents**: Belief-Desire-Intention model for character psychology.
*   **Quantum State Manager**: Handles parallel narrative timelines ("World States") and probability divergence.
*   **Self-Healing**: Suggests repairs for identified causal violations.
*   **Efficient AI**: Optimized to run with **DistilGPT2** for lightweight, fast inference.

---

## Installation & Usage

### Prerequisites
*   **Docker** & **Docker Compose** (Required)
*   **Python 3.9+** (Optional, for local dev)

### Quick Start (Recommended)
This acts as the single source of truth for deploying the full stack.

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Jitterx69/CONCORD.git
    cd CONCORD
    ```

2.  **Launch Services**
    ```bash
    # Stop any existing containers
    docker-compose down

    # Build and start the full stack
    docker-compose up --build
    ```
    *This will compile the Rust, C++, and Java components, build the Python backend, and start Kafka/Zookeeper.*

3.  **Access the System**
    *   **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **Kafka Control**: `localhost:9092`

### Troubleshooting
*   **Backend OOM**: The backend is configured to use `distilgpt2` to save memory. If you experience crashes, ensure your Docker Desktop has at least 4GB of RAM allocated.
*   **Service Loops**: Java and R services act as workers; they are designed to stay alive and process requests/events.

---

## Directory Structure

```plaintext
CONCORD/
├── backend/          # Python FastAPI (Orchestrator)
├── rust_core/        # Rust Causal Analysis Service
├── java_services/    # Java Federation & Consensus Service
├── r_analytics/      # R Statistical Analysis Scripts
├── cpp_sim/          # C++ Physics & Pathfinding Engine
├── c_vector/         # C Vector Store Implementation
├── data/             # Datasets & Submission Files
├── docs/             # Technical Documentation
├── docker-compose.yml # Main Orchestration File
└── README.md         # This file
```

---

## Code Quality & Methodologies

CONCORD adheres to **Enterprise-Grade** coding standards:
*   **Human-Centric Code**: All components have been refactored for maximum readability, with clear variable names and structured comments.
*   **Idiomatic Patterns**: 
    *   Rust uses functional iterators and proper error propagation (`PyResult`).
    *   C++ adheres to modern C++17 standards (`constexpr`, `auto`).
    *   Java follows standard Enterprise patterns (Javadoc, SLF4J-style logging).
    *   R scripts use Tidyverse style guidelines.
*   **Documentation**: Comprehensive Doxygen (C++), Javadoc (Java), and Docstrings (Python/Rust) are present throughout.

---

## Compliance

CONCORD adheres to a strict **"No Training"** policy. It uses pre-trained models (DistilGPT2, TinyLlama) purely for zero-shot semantic reasoning, ensuring deterministic and verifiable output without the resource overhead of model fine-tuning.

---
**License**: MIT License
