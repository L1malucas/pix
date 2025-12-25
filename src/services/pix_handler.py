"""PIX generation handler for conversation flow."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.schemas.client import ClientCreate
from src.schemas.payment import PaymentCreate
from src.services.client_service import client_service
from src.services.mercadopago_service import mercadopago_service
from src.services.payment_service import payment_service
from src.services.whatsapp import whatsapp_service

logger = get_logger(__name__)


class PIXHandler:
    """Handle PIX generation and WhatsApp notification."""

    async def generate_and_send_pix(
        self,
        db: Session,
        phone: str,
        name: str,
        condo: str,
        block: str,
        apartment: str,
        amount: float,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Generate PIX and send code via WhatsApp.

        Args:
            db: Database session
            phone: Client phone
            name: Client name
            condo: Condominium name
            block: Block/tower
            apartment: Apartment number
            amount: Payment amount
            request_id: Request ID for tracking

        Returns:
            Result dictionary with PIX data

        Raises:
            Exception: If PIX generation fails
        """
        logger.info(
            "generating_pix_for_conversation",
            request_id=request_id,
            phone=phone,
            amount=amount,
        )

        try:
            # 1. Create or update client
            client_data = ClientCreate(
                name=name,
                phone=phone,
                condo=condo,
                block=block,
                apartment=apartment,
            )

            client, created = client_service.get_or_create(db, client_data)

            # 2. Get current month
            month_ref = datetime.utcnow().strftime("%Y-%m")

            # 3. Check existing payment
            existing_payment = payment_service.get_client_payment_for_month(
                db, client.id, month_ref
            )

            if existing_payment:
                logger.warning(
                    "payment_already_exists_sending_reminder",
                    request_id=request_id,
                    client_id=client.id,
                    payment_id=existing_payment.id,
                )

                # Send message about existing payment
                message = (
                    f"Você já possui um pagamento aprovado para {month_ref}.\n\n"
                    f"Se tiver alguma dúvida, entre em contato com a administração."
                )

                await whatsapp_service.send_text_message(phone, message, request_id)

                return {
                    "success": False,
                    "reason": "payment_exists",
                    "payment_id": existing_payment.id,
                }

            # 4. Generate external reference
            external_reference = mercadopago_service.generate_external_reference(
                month_ref=month_ref,
                amount=amount,
                phone=phone,
                apartment=apartment,
            )

            # 5. Create PIX in Mercado Pago
            description = f"Pagamento PIX - {condo} - Bloco {block} - Apto {apartment} - {month_ref}"

            mp_response = await mercadopago_service.create_pix_payment(
                amount=amount,
                description=description,
                external_reference=external_reference,
                request_id=request_id,
            )

            # 6. Extract PIX data
            mp_payment_id = str(mp_response.get("id"))
            pix_code = mercadopago_service.extract_pix_code(mp_response)

            if not pix_code:
                logger.error(
                    "pix_code_not_generated",
                    request_id=request_id,
                    mp_payment_id=mp_payment_id,
                )
                raise Exception("Failed to generate PIX code")

            # 7. Create payment record
            payment_data = PaymentCreate(
                client_id=client.id,
                month_ref=month_ref,
                amount=amount,
                external_reference=external_reference,
            )

            payment = payment_service.create(db, payment_data, request_id)

            # 8. Update with Mercado Pago ID
            payment_service.update_status(
                db,
                payment,
                status="pending",
                mp_payment_id=mp_payment_id,
            )

            # 9. Send PIX code via WhatsApp
            pix_message = (
                f"✅ PIX gerado com sucesso!\n\n"
                f"💰 Valor: R$ {amount:.2f}\n"
                f"📅 Referência: {month_ref}\n"
                f"🏢 {condo} - Bloco {block} - Apto {apartment}\n\n"
                f"🔑 Código PIX Copia e Cola:\n\n"
                f"{pix_code}\n\n"
                f"⏰ Este PIX expira em 6 horas.\n\n"
                f"Após o pagamento, você receberá a confirmação automaticamente."
            )

            await whatsapp_service.send_text_message(phone, pix_message, request_id)

            logger.info(
                "pix_generated_and_sent",
                request_id=request_id,
                client_id=client.id,
                payment_id=payment.id,
                mp_payment_id=mp_payment_id,
            )

            return {
                "success": True,
                "client_id": client.id,
                "payment_id": payment.id,
                "mp_payment_id": mp_payment_id,
                "pix_code": pix_code,
                "amount": amount,
            }

        except Exception as e:
            logger.error(
                "pix_generation_failed",
                request_id=request_id,
                phone=phone,
                error=str(e),
                exc_info=True,
            )

            # Send error message to user
            error_message = (
                "❌ Desculpe, ocorreu um erro ao gerar seu PIX.\n\n"
                "Por favor, tente novamente em alguns minutos ou entre em contato com a administração."
            )

            try:
                await whatsapp_service.send_text_message(phone, error_message, request_id)
            except Exception as send_error:
                logger.error(
                    "failed_to_send_error_message",
                    error=str(send_error),
                    request_id=request_id,
                )

            raise


# Global instance
pix_handler = PIXHandler()
