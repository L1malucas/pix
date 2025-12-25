"""PIX schemas for API requests and responses."""
from typing import Optional

from pydantic import BaseModel, Field


class PIXCreateRequest(BaseModel):
    """Request schema for creating PIX."""

    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    condo: str = Field(..., min_length=1, max_length=255, description="Condominium")
    block: str = Field(..., min_length=1, max_length=50, description="Block/Tower")
    apartment: str = Field(..., min_length=1, max_length=50, description="Apartment")
    plan_value: float = Field(..., gt=0, description="Plan value")
    month_ref: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$", description="Month reference (YYYY-MM)")


class PIXCreateResponse(BaseModel):
    """Response schema for PIX creation."""

    client_id: int
    payment_id: int
    mp_payment_id: str
    pix_code: str = Field(..., description="PIX copy-paste code")
    qr_code_base64: Optional[str] = Field(None, description="QR code image in base64")
    amount: float
    expiration_hours: int
    external_reference: str
    month_ref: str

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "client_id": 1,
                "payment_id": 1,
                "mp_payment_id": "123456789",
                "pix_code": "00020126...99999",
                "qr_code_base64": "iVBORw0KGgo...",
                "amount": 70.0,
                "expiration_hours": 6,
                "external_reference": "PIX|2025-01|70.00|5511999999999|101",
                "month_ref": "2025-01",
            }
        }
