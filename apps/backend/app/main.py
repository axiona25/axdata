"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from core.config import settings
from core.middleware import SecurityHeadersMiddleware
from api.routers import auth, users
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Dataset On-Demand Portal API",
    description="Backend API for Dataset On-Demand Portal",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global exception handler for better error messages
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to catch unhandled errors."""
    import traceback
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    logger.error(f"Request path: {request.url.path}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__
        }
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - DEVE essere aggiunto per primo (viene eseguito per ultimo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)

# Import routers
from api.routers import chat, datasets, billing, download, audit, packages, assets
app.include_router(packages.router)
app.include_router(chat.router)
app.include_router(datasets.router)
app.include_router(billing.router)
app.include_router(download.router)
app.include_router(audit.router)
app.include_router(assets.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "service": "backend"
    }


@app.get("/api/v1/health")
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "service": "backend",
        "version": "0.1.0"
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info(f"Starting backend in {settings.environment} mode")
    logger.info(f"API running on {settings.api_host}:{settings.api_port}")
    
    # Seed AXDATA logo into DB if missing
    try:
        from db.session import SessionLocal
        from db.models.app_asset import AppAsset

        project_root = Path(__file__).resolve().parents[3]
        logo_path = project_root / "UI" / "Logo Axdata.png"

        db = SessionLocal()
        try:
            existing = db.query(AppAsset).filter(AppAsset.key == "logo").first()
            if not existing and logo_path.exists():
                data = logo_path.read_bytes()
                db.add(AppAsset(key="logo", content_type="image/png", data=data))
                db.commit()
                logger.info(f"✅ Seeded AXDATA logo into DB from {logo_path}")
            elif existing:
                logger.info("✅ AXDATA logo already exists in DB")
            elif not logo_path.exists():
                logger.warning(f"⚠️ AXDATA logo file not found at {logo_path}; logo not seeded")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"⚠️ Could not seed AXDATA logo into DB: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down backend")

