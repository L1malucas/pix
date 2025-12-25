"""Payment schemas for API requests and responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaymentBase(BaseModel):
    """Base payment schema with common fields."""

    month_ref: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Month reference (YYYY-MM)")
    amount: float = Field(..., gt=0, description="Payment amount")


class PaymentCreate(PaymentBase):
    """Schema for creating a new payment."""

    client_id: int = Field(..., gt=0, description="Client ID")
    external_reference: str = Field(..., min_length=1, max_length=500, description="PIX external reference")


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""

    status: Optional[str] = Field(None, description="Payment status")
    mp_payment_id: Optional[str] = Field(None, description="Mercado Pago payment ID")
    paid_at: Optional[datetime] = Field(None, description="Payment date")


class PaymentResponse(PaymentBase):
    """Schema for payment responses."""

    id: int
    request_id: str
    client_id: int
    status: str
    mp_payment_id: Optional[str]
    external_reference: str
    created_at: datetime
    paid_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PaymentWithClient(PaymentResponse):
    """Schema for payment with client information."""

    client: "ClientResponse"

    model_config = ConfigDict(from_attributes=True)


# Import here to avoid circular dependency
from src.schemas.client import ClientResponse  # noqa: E402

PaymentWithClient.model_rebuild()
