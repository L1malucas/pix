"""Mercado Pago service for PIX generation."""
from datetime import datetime, timedelta
from typing import Optional

import httpx

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class MercadoPagoService:
    """Service for interacting with Mercado Pago API."""

    def __init__(self) -> None:
        """Initialize Mercado Pago service."""
        self.access_token = settings.mercadopago_access_token
        self.api_url = "https://api.mercadopago.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": "",  # Will be set per request
        }

    def generate_external_reference(
        self,
        month_ref: str,
        amount: float,
        phone: str,
        apartment: str,
    ) -> str:
        """
        Generate external reference for PIX.

        Format: PIX|YYYY-MM|VALOR|TELEFONE|APARTAMENTO

        Args:
            month_ref: Month reference (YYYY-MM)
            amount: Payment amount
            phone: Phone number
            apartment: Apartment number

        Returns:
            External reference string
        """
        return f"PIX|{month_ref}|{amount:.2f}|{phone}|{apartment}"

    async def create_pix_payment(
        self,
        amount: float,
        description: str,
        external_reference: str,
        payer_email: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Create a PIX payment in Mercado Pago.

        Args:
            amount: Payment amount
            description: Payment description
            external_reference: External reference for tracking
            payer_email: Payer email (optional)
            request_id: Request ID for tracking

        Returns:
            Mercado Pago payment response

        Raises:
            httpx.HTTPError: If request fails
        """
        # Calculate expiration (6 hours from now)
        expiration = datetime.utcnow() + timedelta(hours=settings.pix_expiration_hours)

        payload = {
            "transaction_amount": amount,
            "description": description,
            "payment_method_id": "pix",
            "external_reference": external_reference,
            "date_of_expiration": expiration.isoformat() + "Z",
            "notification_url": f"{settings.base_url}/webhooks/mercadopago",
        }

        # Add payer info if email provided
        if payer_email:
            payload["payer"] = {"email": payer_email}

        # Set idempotency key
        headers = self.headers.copy()
        headers["X-Idempotency-Key"] = request_id or external_reference

        logger.info(
            "creating_mercadopago_payment",
            request_id=request_id,
            amount=amount,
            external_reference=external_reference,
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/payments",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                result = response.json()

                logger.info(
                    "mercadopago_payment_created",
                    request_id=request_id,
                    mp_payment_id=result.get("id"),
                    status=result.get("status"),
                )

                return result

            except httpx.HTTPError as e:
                logger.error(
                    "mercadopago_create_error",
                    request_id=request_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def extract_pix_code(self, payment_response: dict) -> Optional[str]:
        """
        Extract PIX code (QR code text) from payment response.

        Args:
            payment_response: Mercado Pago payment response

        Returns:
            PIX code or None if not available
        """
        point_of_interaction = payment_response.get("point_of_interaction", {})
        transaction_data = point_of_interaction.get("transaction_data", {})
        qr_code = transaction_data.get("qr_code")

        return qr_code

    def extract_qr_code_base64(self, payment_response: dict) -> Optional[str]:
        """
        Extract QR code image (base64) from payment response.

        Args:
            payment_response: Mercado Pago payment response

        Returns:
            Base64 QR code image or None
        """
        point_of_interaction = payment_response.get("point_of_interaction", {})
        transaction_data = point_of_interaction.get("transaction_data", {})
        qr_code_base64 = transaction_data.get("qr_code_base64")

        return qr_code_base64

    async def get_payment(
        self,
        payment_id: str,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Get payment details from Mercado Pago.

        Args:
            payment_id: Mercado Pago payment ID
            request_id: Request ID for tracking

        Returns:
            Payment details

        Raises:
            httpx.HTTPError: If request fails
        """
        logger.info(
            "getting_mercadopago_payment",
            request_id=request_id,
            payment_id=payment_id,
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/payments/{payment_id}",
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                result = response.json()

                logger.info(
                    "mercadopago_payment_retrieved",
                    request_id=request_id,
                    payment_id=payment_id,
                    status=result.get("status"),
                )

                return result

            except httpx.HTTPError as e:
                logger.error(
                    "mercadopago_get_error",
                    request_id=request_id,
                    payment_id=payment_id,
                    error=str(e),
                    exc_info=True,
                )
                raise


# Global instance
mercadopago_service = MercadoPagoService()
