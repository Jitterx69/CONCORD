"""
CONCORD - Main FastAPI Application
Constraint-Oriented Narrative Consistency Decision System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import consistency, knowledge, narratives, health


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
    
    print("✅ All services initialized")
    
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
app.include_router(knowledge.router, prefix=settings.API_PREFIX, tags=["Knowledge Graph"])
app.include_router(narratives.router, prefix=settings.API_PREFIX, tags=["Narratives"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Constraint-Oriented Narrative Consistency Decision System",
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health"
    }
