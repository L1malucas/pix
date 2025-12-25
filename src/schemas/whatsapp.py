"""WhatsApp webhook schemas."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class WhatsAppProfile(BaseModel):
    """WhatsApp profile information."""

    name: str


class WhatsAppText(BaseModel):
    """WhatsApp text message."""

    body: str


class WhatsAppMessage(BaseModel):
    """WhatsApp message object."""

    from_: str = Field(..., alias="from")
    id: str
    timestamp: str
    type: str
    text: Optional[WhatsAppText] = None


class WhatsAppContact(BaseModel):
    """WhatsApp contact information."""

    profile: WhatsAppProfile
    wa_id: str


class WhatsAppMetadata(BaseModel):
    """WhatsApp metadata."""

    display_phone_number: str
    phone_number_id: str


class WhatsAppValue(BaseModel):
    """WhatsApp value object."""

    messaging_product: str
    metadata: WhatsAppMetadata
    contacts: Optional[list[WhatsAppContact]] = None
    messages: Optional[list[WhatsAppMessage]] = None
    statuses: Optional[list[dict[str, Any]]] = None


class WhatsAppChange(BaseModel):
    """WhatsApp change object."""

    value: WhatsAppValue
    field: str


class WhatsAppEntry(BaseModel):
    """WhatsApp entry object."""

    id: str
    changes: list[WhatsAppChange]


class WhatsAppWebhook(BaseModel):
    """WhatsApp webhook payload."""

    object: str
    entry: list[WhatsAppEntry]


class ConversationState(BaseModel):
    """Conversation state for tracking user flow."""

    phone: str
    step: str = "START"
    data: dict[str, Any] = {}

    class Config:
        """Pydantic config."""

        extra = "allow"
