"""Google Sheets service for payment tracking."""
import os
from datetime import datetime
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Google Sheets API scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsService:
    """Service for interacting with Google Sheets."""

    def __init__(self) -> None:
        """Initialize Google Sheets service."""
        self.spreadsheet_id = settings.google_sheets_spreadsheet_id
        self.sheet_name = settings.google_sheets_sheet_name
        self.credentials_file = settings.google_sheets_credentials_file
        self.service = None

    def _get_credentials(self) -> Credentials | ServiceAccountCredentials:
        """
        Get Google API credentials.

        Tries service account first, falls back to OAuth flow.

        Returns:
            Google credentials

        Raises:
            Exception: If credentials cannot be obtained
        """
        creds = None

        # Try service account credentials first (recommended for production)
        if os.path.exists(self.credentials_file):
            try:
                creds = ServiceAccountCredentials.from_service_account_file(
                    self.credentials_file, scopes=SCOPES
                )
                logger.info("using_service_account_credentials")
                return creds
            except Exception as e:
                logger.warning(
                    "service_account_failed",
                    error=str(e),
                )

        # Fall back to OAuth flow (for development)
        token_file = "token.json"

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        # If credentials don't exist or are invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.info("credentials_refreshed")
            else:
                if not os.path.exists(self.credentials_file):
                    logger.error(
                        "credentials_file_not_found",
                        file=self.credentials_file,
                    )
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("new_credentials_obtained")

            # Save credentials for next run
            with open(token_file, "w") as token:
                token.write(creds.to_json())

        return creds

    def _get_service(self) -> Any:
        """
        Get Google Sheets service.

        Returns:
            Google Sheets API service
        """
        if not self.service:
            creds = self._get_credentials()
            self.service = build("sheets", "v4", credentials=creds)
            logger.info("google_sheets_service_initialized")

        return self.service

    def append_row(
        self,
        values: list[Any],
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Append a row to the spreadsheet.

        Args:
            values: List of values to append
            request_id: Request ID for tracking

        Returns:
            API response

        Raises:
            Exception: If append fails
        """
        logger.info(
            "appending_row_to_sheets",
            request_id=request_id,
            values_count=len(values),
        )

        try:
            service = self._get_service()

            body = {"values": [values]}

            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.sheet_name}!A:M",
                    valueInputOption="RAW",
                    body=body,
                )
                .execute()
            )

            logger.info(
                "row_appended_to_sheets",
                request_id=request_id,
                updates=result.get("updates", {}),
            )

            return result

        except Exception as e:
            logger.error(
                "sheets_append_error",
                request_id=request_id,
                error=str(e),
                exc_info=True,
            )
            raise

    def update_row_by_request_id(
        self,
        request_id_value: str,
        status: str,
        paid_at: Optional[datetime] = None,
        tracking_request_id: Optional[str] = None,
    ) -> dict:
        """
        Update a row in the spreadsheet by request_id.

        Finds the row with matching request_id and updates status and paid_at.

        Args:
            request_id_value: Request ID to search for
            status: New status value
            paid_at: Payment datetime
            tracking_request_id: Request ID for tracking this operation

        Returns:
            API response

        Raises:
            Exception: If update fails
        """
        logger.info(
            "updating_row_in_sheets",
            tracking_request_id=tracking_request_id,
            search_request_id=request_id_value,
            status=status,
        )

        try:
            service = self._get_service()

            # 1. Find the row with matching request_id
            result = (
                service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.sheet_name}!A:M",
                )
                .execute()
            )

            values = result.get("values", [])

            # Find row index (column A contains request_id)
            row_index = None
            for idx, row in enumerate(values):
                if row and row[0] == request_id_value:
                    row_index = idx + 1  # Sheets uses 1-based indexing
                    break

            if row_index is None:
                logger.warning(
                    "row_not_found_in_sheets",
                    tracking_request_id=tracking_request_id,
                    search_request_id=request_id_value,
                )
                return {"updated": False, "reason": "row_not_found"}

            # 2. Update status (column I) and paid_at (column K)
            updates = [
                {
                    "range": f"{self.sheet_name}!I{row_index}",  # Status column
                    "values": [[status]],
                }
            ]

            if paid_at:
                paid_at_str = paid_at.strftime("%Y-%m-%d %H:%M:%S")
                updates.append(
                    {
                        "range": f"{self.sheet_name}!K{row_index}",  # Paid date column
                        "values": [[paid_at_str]],
                    }
                )

            body = {"valueInputOption": "RAW", "data": updates}

            result = (
                service.spreadsheets()
                .values()
                .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
                .execute()
            )

            logger.info(
                "row_updated_in_sheets",
                tracking_request_id=tracking_request_id,
                search_request_id=request_id_value,
                row_index=row_index,
                status=status,
            )

            return result

        except Exception as e:
            logger.error(
                "sheets_update_error",
                tracking_request_id=tracking_request_id,
                error=str(e),
                exc_info=True,
            )
            raise

    def create_payment_row(
        self,
        request_id: str,
        name: str,
        phone: str,
        condo: str,
        block: str,
        apartment: str,
        month_ref: str,
        amount: float,
        status: str,
        mp_payment_id: Optional[str] = None,
        tracking_request_id: Optional[str] = None,
    ) -> dict:
        """
        Create a new payment row in the spreadsheet.

        Args:
            request_id: Payment request ID
            name: Client name
            phone: Client phone
            condo: Condominium name
            block: Block/tower
            apartment: Apartment number
            month_ref: Month reference (YYYY-MM)
            amount: Payment amount
            status: Payment status
            mp_payment_id: Mercado Pago payment ID
            tracking_request_id: Request ID for tracking

        Returns:
            API response
        """
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        values = [
            request_id,              # A - request_id
            name,                    # B - nome
            phone,                   # C - telefone
            condo,                   # D - condominio
            block,                   # E - bloco
            apartment,               # F - apartamento
            month_ref,               # G - mes
            amount,                  # H - valor
            status,                  # I - status
            now,                     # J - data_criacao
            "",                      # K - data_pagamento (empty initially)
            mp_payment_id or "",     # L - mp_payment_id
        ]

        return self.append_row(values, tracking_request_id)


# Global instance
sheets_service = GoogleSheetsService()
