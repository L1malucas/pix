"""Mercado Pago webhook schemas."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class MercadoPagoWebhookData(BaseModel):
    """Mercado Pago webhook data object."""

    id: str = Field(..., description="Payment or merchant order ID")


class MercadoPagoWebhook(BaseModel):
    """Mercado Pago webhook notification."""

    action: str = Field(..., description="Event action (e.g., payment.updated)")
    api_version: str = Field(..., description="API version")
    data: MercadoPagoWebhookData = Field(..., description="Event data")
    date_created: str = Field(..., description="Event creation date")
    id: int = Field(..., description="Notification ID")
    live_mode: bool = Field(..., description="Production mode flag")
    type: str = Field(..., description="Event type (e.g., payment)")
    user_id: str = Field(..., description="User ID")


class PaymentStatusUpdate(BaseModel):
    """Payment status update information."""

    payment_id: int
    old_status: str
    new_status: str
    mp_payment_id: str
    amount: float
    client_id: int
    updated: bool
