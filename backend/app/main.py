"""
CONCORD - Main FastAPI Application
Constraint-Oriented Narrative Consistency Decision System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import (
    consistency,
    knowledge,
    narratives,
    health,
    simulation,
    causality,
    agents,
    quantum,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown"""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📊 Debug mode: {settings.DEBUG}")

    # Initialize services
    from app.services.ml_service import MLService

    app.state.ml_service = MLService()
    await app.state.ml_service.initialize()

    from app.core.knowledge_graph import KnowledgeGraph

    app.state.knowledge_graph = KnowledgeGraph()

    from app.core.constraint_engine import ConstraintEngine

    app.state.constraint_engine = ConstraintEngine()

    from app.core.temporal_reasoner import TemporalReasoner

    app.state.temporal_reasoner = TemporalReasoner()

    from app.core.entity_tracker import EntityTracker

    app.state.entity_tracker = EntityTracker()

    from app.core.explainer import Explainer

    app.state.explainer = Explainer()

    # Out of the World Features
    from app.simulation.engine import SimulationEngine

    app.state.simulation_engine = SimulationEngine(app.state.knowledge_graph)

    from app.causality.propagator import Propagator

    app.state.propagator = Propagator(app.state.knowledge_graph)

    from app.causality.repair_agent import RepairAgent

    app.state.repair_agent = RepairAgent(app.state.knowledge_graph)

    from app.agents.bdi_engine import BDIEngine

    app.state.bdi_engine = BDIEngine()

    from app.quantum.state_manager import StateManager

    app.state.quantum_state_manager = StateManager()

    from app.quantum.probability_engine import ProbabilityEngine

    app.state.probability_engine = ProbabilityEngine()

    # Initialize Kafka Event Bus
    from app.core.event_bus import EventBus

    # Use 'kafka:29092' if running inside docker, 'localhost:9092' if local
    bootstrap_server = "localhost:9092"
    EventBus().initialize(bootstrap_servers=bootstrap_server)

    yield

    # Shutdown
    print(f"👋 Shutting down {settings.APP_NAME}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Constraint-Oriented Narrative Consistency Decision System - "
    "An AI-powered platform for maintaining narrative coherence and logical integrity",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(consistency.router, prefix=settings.API_PREFIX, tags=["Consistency"])
app.include_router(
    knowledge.router, prefix=settings.API_PREFIX, tags=["Knowledge Graph"]
)
app.include_router(narratives.router, prefix=settings.API_PREFIX, tags=["Narratives"])
app.include_router(
    simulation.router,
    prefix=f"{settings.API_PREFIX}/simulation",
    tags=["Narrative Holodeck"],
)
app.include_router(
    causality.router,
    prefix=f"{settings.API_PREFIX}/causality",
    tags=["Butterfly Effect"],
)
app.include_router(
    agents.router, prefix=f"{settings.API_PREFIX}/agents", tags=["BDI Agents"]
)
app.include_router(
    quantum.router,
    prefix=f"{settings.API_PREFIX}/quantum",
    tags=["Quantum Consistency"],
)


@app.get("/")
async def root():
    """Root endpoint with API System Map"""
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Narrative Reality Engine (Headless Polyglot System)",
        "docs": "/docs",
        "redoc": "/redoc",
        "services": {
            "health": f"{settings.API_PREFIX}/health",
            "narratives": f"{settings.API_PREFIX}/narratives",
            "consistency": f"{settings.API_PREFIX}/consistency",
            "knowledge_graph": f"{settings.API_PREFIX}/knowledge",
            "simulation": {
                "base": f"{settings.API_PREFIX}/simulation",
                "actions": {
                    "start_session": f"{settings.API_PREFIX}/simulation/session/start",
                    "action": f"{settings.API_PREFIX}/simulation/action",
                    "undo": f"{settings.API_PREFIX}/simulation/undo",
                },
            },
            "causality": {
                "base": f"{settings.API_PREFIX}/causality",
                "actions": {
                    "analyze": f"{settings.API_PREFIX}/causality/analyze",
                    "repair": f"{settings.API_PREFIX}/causality/repair",
                },
            },
            "agents": {
                "base": f"{settings.API_PREFIX}/agents",
                "actions": {
                    "profile": f"{settings.API_PREFIX}/agents/profile/{{agent_id}}",
                    "check": f"{settings.API_PREFIX}/agents/consistency",
                },
            },
            "quantum": {
                "base": f"{settings.API_PREFIX}/quantum",
                "actions": {
                    "worlds": f"{settings.API_PREFIX}/quantum/worlds",
                    "fork": f"{settings.API_PREFIX}/quantum/fork",
                    "collapse": f"{settings.API_PREFIX}/quantum/collapse",
                },
            },
        },
        "polyglot_components": {
            "python": "Orchestrator & AI",
            "rust": "Causal Propagator (Integrated)",
            "cpp": "Physics Engine (Integrated)",
            "c": "Vector Store (Integrated)",
            "java": "Federation Service (External)",
            "r": "Analytics Service (External)",
        },
    }
