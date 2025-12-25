"""Client model."""
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.payment import Payment


class Client(Base, TimestampMixin):
    """Client model representing a customer."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    condo: Mapped[str] = mapped_column(String(255), nullable=False)
    block: Mapped[str] = mapped_column(String(50), nullable=False)
    apartment: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Client(id={self.id}, name='{self.name}', phone='{self.phone}', apartment='{self.apartment}')>"
