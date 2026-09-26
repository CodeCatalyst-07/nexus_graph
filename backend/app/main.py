from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import CORS_ORIGINS
from app.database import init_constraints, close_driver
from app.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nexusgraph.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Neo4j database constraints...")
    try:
        init_constraints()
        logger.info("Database constraints successfully verified.")
    except Exception as e:
        logger.error(f"Failed to initialize database constraints: {e}")
    yield
    logger.info("Closing Neo4j database driver connection...")
    close_driver()

app = FastAPI(
    title="NexusGraph Support API",
    description="Context-Aware Customer Support Agent with Neo4j Persistent Memory",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for local Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root_endpoint():
    return {
        "service": "NexusGraph Support API",
        "status": "ONLINE",
        "version": "1.0.0",
        "neo4j_memory": "CONNECTED"
    }

if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
