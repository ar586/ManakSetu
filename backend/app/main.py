from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1.api import api_router
from app.services.ai_engine import get_engine

logger = logging.getLogger(__name__)

import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Preloading AI embedding model...")
    try:
        def load_model():
            get_engine().model
            logger.info("AI embedding model preloaded successfully.")
            
        # Fire and forget
        asyncio.create_task(asyncio.to_thread(load_model))
    except Exception as e:
        logger.error(f"Failed to preload AI embedding model: {e}")
    yield
    logger.info("Shutting down ManakSetu API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to ManakSetu API"}
