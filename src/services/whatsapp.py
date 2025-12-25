"""WhatsApp Cloud API service for sending messages."""
import httpx
from typing import Optional

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class WhatsAppService:
    """Service for interacting with WhatsApp Cloud API."""

    def __init__(self) -> None:
        """Initialize WhatsApp service."""
        self.api_url = settings.whatsapp_api_url
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def send_text_message(
        self,
        to: str,
        message: str,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Send a text message to a WhatsApp number.

        Args:
            to: Phone number with country code (e.g., "5511999999999")
            message: Message text to send
            request_id: Request ID for tracking

        Returns:
            Response from WhatsApp API

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

        logger.info(
            "sending_whatsapp_message",
            request_id=request_id,
            to=to,
            message_length=len(message),
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                result = response.json()

                logger.info(
                    "whatsapp_message_sent",
                    request_id=request_id,
                    message_id=result.get("messages", [{}])[0].get("id"),
                    to=to,
                )

                return result

            except httpx.HTTPError as e:
                logger.error(
                    "whatsapp_send_error",
                    request_id=request_id,
                    error=str(e),
                    to=to,
                    exc_info=True,
                )
                raise

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "pt_BR",
        components: Optional[list] = None,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Send a template message to a WhatsApp number.

        Args:
            to: Phone number with country code
            template_name: Name of the approved template
            language_code: Language code (default: pt_BR)
            components: Template components (parameters, buttons, etc.)
            request_id: Request ID for tracking

        Returns:
            Response from WhatsApp API

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }

        if components:
            payload["template"]["components"] = components

        logger.info(
            "sending_whatsapp_template",
            request_id=request_id,
            to=to,
            template=template_name,
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                result = response.json()

                logger.info(
                    "whatsapp_template_sent",
                    request_id=request_id,
                    message_id=result.get("messages", [{}])[0].get("id"),
                    to=to,
                )

                return result

            except httpx.HTTPError as e:
                logger.error(
                    "whatsapp_template_error",
                    request_id=request_id,
                    error=str(e),
                    to=to,
                    exc_info=True,
                )
                raise

    async def mark_message_as_read(
        self,
        message_id: str,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Mark a message as read.

        Args:
            message_id: WhatsApp message ID
            request_id: Request ID for tracking

        Returns:
            Response from WhatsApp API
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                logger.info(
                    "whatsapp_message_marked_read",
                    request_id=request_id,
                    message_id=message_id,
                )

                return response.json()

            except httpx.HTTPError as e:
                logger.error(
                    "whatsapp_mark_read_error",
                    request_id=request_id,
                    error=str(e),
                    message_id=message_id,
                    exc_info=True,
                )
                raise


# Global instance
whatsapp_service = WhatsAppService()
