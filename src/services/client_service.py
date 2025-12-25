"""Client service for CRUD operations."""
from typing import Optional

from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.models.client import Client
from src.schemas.client import ClientCreate, ClientUpdate

logger = get_logger(__name__)


class ClientService:
    """Service for managing clients."""

    @staticmethod
    def get_by_id(db: Session, client_id: int) -> Optional[Client]:
        """
        Get client by ID.

        Args:
            db: Database session
            client_id: Client ID

        Returns:
            Client or None if not found
        """
        return db.query(Client).filter(Client.id == client_id).first()

    @staticmethod
    def get_by_phone(db: Session, phone: str) -> Optional[Client]:
        """
        Get client by phone number.

        Args:
            db: Database session
            phone: Phone number

        Returns:
            Client or None if not found
        """
        return db.query(Client).filter(Client.phone == phone).first()

    @staticmethod
    def create(db: Session, client_data: ClientCreate) -> Client:
        """
        Create a new client.

        Args:
            db: Database session
            client_data: Client data

        Returns:
            Created client
        """
        logger.info(
            "creating_client",
            phone=client_data.phone,
            name=client_data.name,
        )

        client = Client(
            name=client_data.name,
            phone=client_data.phone,
            condo=client_data.condo,
            block=client_data.block,
            apartment=client_data.apartment,
        )

        db.add(client)
        db.commit()
        db.refresh(client)

        logger.info(
            "client_created",
            client_id=client.id,
            phone=client.phone,
        )

        return client

    @staticmethod
    def update(
        db: Session,
        client: Client,
        client_data: ClientUpdate,
    ) -> Client:
        """
        Update existing client.

        Args:
            db: Database session
            client: Client to update
            client_data: Updated data

        Returns:
            Updated client
        """
        logger.info(
            "updating_client",
            client_id=client.id,
            phone=client.phone,
        )

        update_data = client_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(client, field, value)

        db.commit()
        db.refresh(client)

        logger.info(
            "client_updated",
            client_id=client.id,
        )

        return client

    @staticmethod
    def get_or_create(
        db: Session,
        client_data: ClientCreate,
    ) -> tuple[Client, bool]:
        """
        Get existing client by phone or create new one.

        Args:
            db: Database session
            client_data: Client data

        Returns:
            Tuple of (client, created) where created is True if new client
        """
        existing_client = ClientService.get_by_phone(db, client_data.phone)

        if existing_client:
            logger.info(
                "client_exists",
                client_id=existing_client.id,
                phone=client_data.phone,
            )
            # Update existing client data
            update_data = ClientUpdate(**client_data.model_dump())
            updated_client = ClientService.update(db, existing_client, update_data)
            return updated_client, False

        # Create new client
        new_client = ClientService.create(db, client_data)
        return new_client, True


# Global instance
client_service = ClientService()
