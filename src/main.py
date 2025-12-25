"""Main FastAPI application."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import mercadopago, pix, whatsapp
from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.core.middleware import RequestIDMiddleware
from src.schemas.responses import create_error_response, create_success_response

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events."""
    # Startup
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        environment=settings.app_env,
        version="0.1.0",
    )

    yield

    # Shutdown
    logger.info("application_shutdown", app_name=settings.app_name)


# Create FastAPI app
app = FastAPI(
    title="PIX WhatsApp Automation",
    description="Sistema de Automação e Controle de Pagamentos PIX via WhatsApp",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Include routers
app.include_router(pix.router)
app.include_router(whatsapp.router)
app.include_router(mercadopago.router)


# Health check endpoint
@app.get("/health")
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    request_id = getattr(request.state, "request_id", "unknown")

    response = create_success_response(
        request_id=request_id,
        action="health_check",
        data={
            "status": "healthy",
            "app_name": settings.app_name,
            "environment": settings.app_env,
        },
    )

    return JSONResponse(content=response.model_dump(mode='json'))


# Root endpoint
@app.get("/")
async def root(request: Request) -> JSONResponse:
    """Root endpoint."""
    request_id = getattr(request.state, "request_id", "unknown")

    response = create_success_response(
        request_id=request_id,
        action="root",
        data={
            "message": "PIX WhatsApp Automation API",
            "version": "0.1.0",
            "docs": f"{settings.base_url}/docs" if settings.debug else None,
        },
    )

    return JSONResponse(content=response.model_dump(mode='json'))


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all uncaught exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "unhandled_exception",
        request_id=request_id,
        error=str(exc),
        exc_info=True,
    )

    response = create_error_response(
        request_id=request_id,
        action="error",
        error_code="INTERNAL_ERROR",
        error_message="An internal error occurred",
        error_source="application",
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(mode='json'),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
