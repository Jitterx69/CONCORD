import asyncio
import sys
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

sys.path.append(os.getcwd())

# Mock settings if needed, or import main
from app.main import app, lifespan

async def verify_startup():
    print("--- Verifying API Service Initialization ---")
    try:
        async with lifespan(app):
            print("Lifespan started successfully.")
            
            # Check services
            services = [
                "knowledge_graph",
                "simulation_engine",
                "propagator",
                "repair_agent",
                "bdi_engine",
                "quantum_state_manager",
                "probability_engine"
            ]
            
            for service in services:
                if hasattr(app.state, service):
                    print(f"SUCCESS: Service '{service}' initialized.")
                else:
                    print(f"FAILURE: Service '{service}' missing.")
                    
            print("--- Startup Verification Complete ---")
            
    except Exception as e:
        print(f"FAILURE during startup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_startup())
