"""Pydantic schemas for API validation."""
from src.schemas.client import (
    ClientBase,
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    ClientWithPayments,
)
from src.schemas.payment import (
    PaymentBase,
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
    PaymentWithClient,
)
from src.schemas.responses import (
    ErrorDetail,
    StandardResponse,
    create_error_response,
    create_success_response,
)

__all__ = [
    # Client schemas
    "ClientBase",
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "ClientWithPayments",
    # Payment schemas
    "PaymentBase",
    "PaymentCreate",
    "PaymentUpdate",
    "PaymentResponse",
    "PaymentWithClient",
    # Response schemas
    "ErrorDetail",
    "StandardResponse",
    "create_error_response",
    "create_success_response",
]
