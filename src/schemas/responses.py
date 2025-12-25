"""Standard response schemas."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None


class StandardResponse(BaseModel):
    """
    Standard API response format.

    All endpoints should return this structure for consistency.
    """

    request_id: str = Field(..., description="Unique request identifier")
    success: bool = Field(..., description="Whether the request was successful")
    action: str = Field(..., description="Action performed")
    data: Optional[dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[ErrorDetail] = Field(default=None, description="Error details if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "request_id": "req_2025_03_08_a1b2c3",
                "success": True,
                "action": "create_pix",
                "data": {"pix_code": "00020126..."},
                "error": None,
                "timestamp": "2025-03-08T10:30:00Z",
            }
        }


def create_success_response(
    request_id: str,
    action: str,
    data: Optional[dict[str, Any]] = None,
) -> StandardResponse:
    """Create a success response."""
    return StandardResponse(
        request_id=request_id,
        success=True,
        action=action,
        data=data or {},
        error=None,
    )


def create_error_response(
    request_id: str,
    action: str,
    error_code: str,
    error_message: str,
    error_source: Optional[str] = None,
) -> StandardResponse:
    """Create an error response."""
    return StandardResponse(
        request_id=request_id,
        success=False,
        action=action,
        data=None,
        error=ErrorDetail(
            code=error_code,
            message=error_message,
            source=error_source,
        ),
    )
