"""Collector service FastAPI application."""
from fastapi import FastAPI
from core.config import settings
from app.routers import collect
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Dataset Collector Service",
    description="Service for collecting data from external APIs",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
app.include_router(collect.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "service": "collector"
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info(f"Starting collector service in {settings.environment} mode")
    logger.info(f"API running on {settings.api_host}:{settings.api_port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down collector service")

