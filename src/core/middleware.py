"""Middleware for request tracking and logging."""
import hashlib
import time
from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import get_logger

logger = get_logger(__name__)


def generate_request_id() -> str:
    """
    Generate a unique request ID.

    Format: req_YYYY_MM_DD_<hash>
    """
    now = datetime.utcnow()
    date_str = now.strftime("%Y_%m_%d")

    # Create hash from timestamp and random component
    timestamp_str = str(time.time()).encode()
    hash_obj = hashlib.sha256(timestamp_str)
    hash_short = hash_obj.hexdigest()[:8]

    return f"req_{date_str}_{hash_short}"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request_id to all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add request_id."""
        # Generate or extract request_id
        request_id = request.headers.get("X-Request-ID") or generate_request_id()

        # Attach to request state
        request.state.request_id = request_id

        # Log request
        logger.info(
            "incoming_request",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_host=request.client.host if request.client else None,
        )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id

        # Log response
        logger.info(
            "outgoing_response",
            request_id=request_id,
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
        )

        return response
