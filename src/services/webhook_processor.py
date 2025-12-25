"""Webhook processor for Mercado Pago notifications."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.models.client import Client
from src.models.payment import Payment
from src.services.mercadopago_service import mercadopago_service
from src.services.payment_service import payment_service
from src.services.whatsapp import whatsapp_service

logger = get_logger(__name__)

# In-memory cache for processed webhook IDs (use Redis in production)
processed_webhooks: set[str] = set()


class WebhookProcessor:
    """Process Mercado Pago webhook notifications."""

    async def process_payment_notification(
        self,
        db: Session,
        mp_payment_id: str,
        notification_id: str,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Process payment notification from Mercado Pago.

        Args:
            db: Database session
            mp_payment_id: Mercado Pago payment ID
            notification_id: Webhook notification ID
            request_id: Request ID for tracking

        Returns:
            Processing result

        Raises:
            Exception: If processing fails
        """
        logger.info(
            "processing_payment_notification",
            request_id=request_id,
            mp_payment_id=mp_payment_id,
            notification_id=notification_id,
        )

        # 1. Check idempotency
        webhook_key = f"{notification_id}_{mp_payment_id}"
        if webhook_key in processed_webhooks:
            logger.info(
                "webhook_already_processed",
                request_id=request_id,
                webhook_key=webhook_key,
            )
            return {
                "processed": False,
                "reason": "already_processed",
                "notification_id": notification_id,
            }

        try:
            # 2. Get payment details from Mercado Pago
            mp_payment = await mercadopago_service.get_payment(
                payment_id=mp_payment_id,
                request_id=request_id,
            )

            mp_status = mp_payment.get("status")
            mp_status_detail = mp_payment.get("status_detail")

            logger.info(
                "mercadopago_payment_status",
                request_id=request_id,
                mp_payment_id=mp_payment_id,
                status=mp_status,
                status_detail=mp_status_detail,
            )

            # 3. Find payment in our database
            payment = payment_service.get_by_mp_payment_id(db, mp_payment_id)

            if not payment:
                logger.warning(
                    "payment_not_found_in_database",
                    request_id=request_id,
                    mp_payment_id=mp_payment_id,
                )
                # Mark as processed to avoid retries
                processed_webhooks.add(webhook_key)
                return {
                    "processed": False,
                    "reason": "payment_not_found",
                    "mp_payment_id": mp_payment_id,
                }

            old_status = payment.status

            # 4. Update payment status based on Mercado Pago status
            updated = False

            if mp_status == "approved" and payment.status != "approved":
                # Payment approved
                payment_service.update_status(
                    db,
                    payment,
                    status="approved",
                    mp_payment_id=mp_payment_id,
                    paid_at=datetime.utcnow(),
                )
                updated = True

                logger.info(
                    "payment_approved",
                    request_id=request_id,
                    payment_id=payment.id,
                    mp_payment_id=mp_payment_id,
                )

                # Send confirmation to client
                await self._send_payment_confirmation(
                    db,
                    payment,
                    request_id,
                )

            elif mp_status in ["cancelled", "rejected"] and payment.status == "pending":
                # Payment cancelled or rejected
                payment_service.update_status(
                    db,
                    payment,
                    status=mp_status,
                    mp_payment_id=mp_payment_id,
                )
                updated = True

                logger.info(
                    "payment_cancelled_or_rejected",
                    request_id=request_id,
                    payment_id=payment.id,
                    status=mp_status,
                    status_detail=mp_status_detail,
                )

                # Optionally notify client about cancellation/rejection

            elif mp_status == "pending":
                # Payment still pending, might update status_detail
                if payment.status != "pending":
                    payment_service.update_status(
                        db,
                        payment,
                        status="pending",
                        mp_payment_id=mp_payment_id,
                    )
                    updated = True

            # 5. Mark webhook as processed
            processed_webhooks.add(webhook_key)

            logger.info(
                "webhook_processed_successfully",
                request_id=request_id,
                payment_id=payment.id,
                old_status=old_status,
                new_status=payment.status,
                updated=updated,
            )

            return {
                "processed": True,
                "payment_id": payment.id,
                "old_status": old_status,
                "new_status": payment.status,
                "updated": updated,
                "notification_id": notification_id,
            }

        except Exception as e:
            logger.error(
                "webhook_processing_error",
                request_id=request_id,
                mp_payment_id=mp_payment_id,
                notification_id=notification_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def _send_payment_confirmation(
        self,
        db: Session,
        payment: Payment,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Send payment confirmation to client via WhatsApp.

        Args:
            db: Database session
            payment: Payment object
            request_id: Request ID for tracking
        """
        try:
            # Get client info
            client: Client = payment.client

            confirmation_message = (
                f"✅ Pagamento confirmado!\n\n"
                f"💰 Valor: R$ {payment.amount:.2f}\n"
                f"📅 Referência: {payment.month_ref}\n"
                f"🏢 {client.condo} - Bloco {client.block} - Apto {client.apartment}\n\n"
                f"Obrigado pelo pagamento! Seu recibo está registrado no sistema.\n\n"
                f"ID do pagamento: {payment.mp_payment_id}"
            )

            await whatsapp_service.send_text_message(
                to=client.phone,
                message=confirmation_message,
                request_id=request_id,
            )

            logger.info(
                "payment_confirmation_sent",
                request_id=request_id,
                payment_id=payment.id,
                client_id=client.id,
            )

        except Exception as e:
            logger.error(
                "failed_to_send_confirmation",
                request_id=request_id,
                payment_id=payment.id,
                error=str(e),
                exc_info=True,
            )
            # Don't raise - webhook was processed successfully


# Global instance
webhook_processor = WebhookProcessor()
