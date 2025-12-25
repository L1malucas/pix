"""Payment service for managing payments."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.models.payment import Payment
from src.schemas.payment import PaymentCreate, PaymentUpdate

logger = get_logger(__name__)


class PaymentService:
    """Service for managing payments."""

    @staticmethod
    def get_by_id(db: Session, payment_id: int) -> Optional[Payment]:
        """
        Get payment by ID.

        Args:
            db: Database session
            payment_id: Payment ID

        Returns:
            Payment or None if not found
        """
        return db.query(Payment).filter(Payment.id == payment_id).first()

    @staticmethod
    def get_by_request_id(db: Session, request_id: str) -> Optional[Payment]:
        """
        Get payment by request_id.

        Args:
            db: Database session
            request_id: Request ID

        Returns:
            Payment or None if not found
        """
        return db.query(Payment).filter(Payment.request_id == request_id).first()

    @staticmethod
    def get_by_mp_payment_id(db: Session, mp_payment_id: str) -> Optional[Payment]:
        """
        Get payment by Mercado Pago payment ID.

        Args:
            db: Database session
            mp_payment_id: Mercado Pago payment ID

        Returns:
            Payment or None if not found
        """
        return db.query(Payment).filter(Payment.mp_payment_id == mp_payment_id).first()

    @staticmethod
    def get_client_payment_for_month(
        db: Session,
        client_id: int,
        month_ref: str,
    ) -> Optional[Payment]:
        """
        Get client's payment for a specific month.

        Args:
            db: Database session
            client_id: Client ID
            month_ref: Month reference (YYYY-MM)

        Returns:
            Payment or None if not found
        """
        return (
            db.query(Payment)
            .filter(
                Payment.client_id == client_id,
                Payment.month_ref == month_ref,
                Payment.status == "approved",
            )
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        payment_data: PaymentCreate,
        request_id: str,
    ) -> Payment:
        """
        Create a new payment.

        Args:
            db: Database session
            payment_data: Payment data
            request_id: Request ID for tracking

        Returns:
            Created payment
        """
        logger.info(
            "creating_payment",
            request_id=request_id,
            client_id=payment_data.client_id,
            amount=payment_data.amount,
        )

        payment = Payment(
            request_id=request_id,
            client_id=payment_data.client_id,
            month_ref=payment_data.month_ref,
            amount=payment_data.amount,
            status="pending",
            external_reference=payment_data.external_reference,
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        logger.info(
            "payment_created",
            payment_id=payment.id,
            request_id=request_id,
        )

        return payment

    @staticmethod
    def update_status(
        db: Session,
        payment: Payment,
        status: str,
        mp_payment_id: Optional[str] = None,
        paid_at: Optional[datetime] = None,
    ) -> Payment:
        """
        Update payment status.

        Args:
            db: Database session
            payment: Payment to update
            status: New status
            mp_payment_id: Mercado Pago payment ID (optional)
            paid_at: Payment datetime (optional)

        Returns:
            Updated payment
        """
        logger.info(
            "updating_payment_status",
            payment_id=payment.id,
            old_status=payment.status,
            new_status=status,
        )

        payment.status = status

        if mp_payment_id:
            payment.mp_payment_id = mp_payment_id

        if paid_at:
            payment.paid_at = paid_at

        db.commit()
        db.refresh(payment)

        logger.info(
            "payment_status_updated",
            payment_id=payment.id,
            status=status,
        )

        return payment


# Global instance
payment_service = PaymentService()
