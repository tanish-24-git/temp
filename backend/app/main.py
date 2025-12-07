from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .config import settings
from .api.routes import submissions, compliance, dashboard, admin
from .services.ollama_service import ollama_service

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Compliance Agent Backend")

    # Check Ollama connection
    ollama_healthy = await ollama_service.health_check()

    if ollama_healthy:
        logger.info("✅ Ollama service is available")
    else:
        logger.warning("⚠️ Ollama service is not available - using fallback responses")

    yield

    # Shutdown
    logger.info("Shutting down Compliance Agent Backend")


# Create FastAPI app
app = FastAPI(
    title="Compliance Agent API",
    description="AI-powered compliance checking for marketing content",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(submissions.router)
app.include_router(compliance.router)
app.include_router(dashboard.router)
app.include_router(admin.router)  # Phase 2: Admin routes for rule management


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    ollama_status = await ollama_service.health_check()

    return {
        "status": "healthy",
        "ollama_available": ollama_status
    }


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Compliance Agent API",
        "docs": "/docs",
        "version": "1.0.0"
    }
