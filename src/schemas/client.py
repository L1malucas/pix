"""Client schemas for API requests and responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClientBase(BaseModel):
    """Base client schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number with country code")
    condo: str = Field(..., min_length=1, max_length=255, description="Condominium name")
    block: str = Field(..., min_length=1, max_length=50, description="Block/Tower")
    apartment: str = Field(..., min_length=1, max_length=50, description="Apartment number")


class ClientCreate(ClientBase):
    """Schema for creating a new client."""

    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    condo: Optional[str] = Field(None, min_length=1, max_length=255)
    block: Optional[str] = Field(None, min_length=1, max_length=50)
    apartment: Optional[str] = Field(None, min_length=1, max_length=50)


class ClientResponse(ClientBase):
    """Schema for client responses."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientWithPayments(ClientResponse):
    """Schema for client with payment history."""

    payments: list["PaymentResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# Import here to avoid circular dependency
from src.schemas.payment import PaymentResponse  # noqa: E402

ClientWithPayments.model_rebuild()
