"""Payment model."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.client import Client


class Payment(Base, TimestampMixin):
    """Payment model representing a PIX payment."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month_ref: Mapped[str] = mapped_column(
        String(7), nullable=False, index=True, comment="Format: YYYY-MM"
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        comment="pending, approved, expired, cancelled",
    )
    mp_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Mercado Pago payment ID"
    )
    external_reference: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="PIX|YYYY-MM|VALOR|TELEFONE|APARTAMENTO"
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="payments")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Payment(id={self.id}, request_id='{self.request_id}', "
            f"status='{self.status}', amount={self.amount})>"
        )
