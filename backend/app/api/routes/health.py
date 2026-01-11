"""
Health check endpoints
"""

from fastapi import APIRouter, Response
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "CONCORD",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    return {
        "status": "ready",
        "components": {
            "api": "up",
            "knowledge_graph": "up",
            "constraint_engine": "up",
            "ml_service": "up",
        },
    }


@router.get("/health/live")
async def liveness_check(response: Response):
    """Liveness probe for Kubernetes"""
    response.status_code = 200
    return {"status": "alive"}
