"""Message parser and handler for WhatsApp messages."""
from typing import Optional

from src.core.logging import get_logger
from src.schemas.whatsapp import WhatsAppMessage, WhatsAppWebhook

logger = get_logger(__name__)


class MessageParser:
    """Parse and extract information from WhatsApp webhook messages."""

    @staticmethod
    def extract_messages(webhook: WhatsAppWebhook) -> list[WhatsAppMessage]:
        """
        Extract all messages from webhook payload.

        Args:
            webhook: WhatsApp webhook payload

        Returns:
            List of messages
        """
        messages = []

        for entry in webhook.entry:
            for change in entry.changes:
                if change.value.messages:
                    messages.extend(change.value.messages)

        return messages

    @staticmethod
    def extract_text(message: WhatsAppMessage) -> Optional[str]:
        """
        Extract text content from message.

        Args:
            message: WhatsApp message object

        Returns:
            Text content or None
        """
        if message.type == "text" and message.text:
            return message.text.body.strip()
        return None

    @staticmethod
    def extract_phone(message: WhatsAppMessage) -> str:
        """
        Extract sender phone number from message.

        Args:
            message: WhatsApp message object

        Returns:
            Phone number
        """
        return message.from_

    @staticmethod
    def is_valid_plan_option(text: str) -> bool:
        """
        Check if text is a valid plan option (1, 2, or 3).

        Args:
            text: Message text

        Returns:
            True if valid plan option
        """
        return text in ["1", "2", "3"]

    @staticmethod
    def get_plan_value(option: str) -> float:
        """
        Get plan value based on option.

        Args:
            option: Plan option (1, 2, or 3)

        Returns:
            Plan value in BRL

        Raises:
            ValueError: If invalid option
        """
        plans = {
            "1": 70.00,  # Individual
            "2": 90.00,  # 2 pessoas
            "3": 100.00,  # 4 pessoas
        }

        if option not in plans:
            raise ValueError(f"Invalid plan option: {option}")

        return plans[option]

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize phone number to standard format.

        Removes all non-numeric characters.

        Args:
            phone: Phone number

        Returns:
            Normalized phone number
        """
        return "".join(filter(str.isdigit, phone))
