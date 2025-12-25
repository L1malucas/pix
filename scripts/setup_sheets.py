"""Script to initialize Google Sheets with proper headers."""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build

from src.core.config import settings

# Google Sheets API scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def setup_sheet():
    """
    Initialize Google Sheet with headers and formatting.

    This script:
    1. Creates headers in the first row
    2. Formats the header row (bold, background color)
    3. Sets column widths
    4. Freezes the header row
    """
    print("🚀 Initializing Google Sheets...")

    # 1. Get credentials
    credentials_file = settings.google_sheets_credentials_file

    if not os.path.exists(credentials_file):
        print(f"❌ Error: Credentials file not found: {credentials_file}")
        print("\nPlease follow the setup guide in docs/GOOGLE_SHEETS_SETUP.md")
        sys.exit(1)

    try:
        creds = ServiceAccountCredentials.from_service_account_file(
            credentials_file, scopes=SCOPES
        )
        print("✅ Credentials loaded successfully")
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        sys.exit(1)

    # 2. Build service
    service = build("sheets", "v4", credentials=creds)

    spreadsheet_id = settings.google_sheets_spreadsheet_id
    sheet_name = settings.google_sheets_sheet_name

    print(f"\n📊 Spreadsheet ID: {spreadsheet_id}")
    print(f"📋 Sheet name: {sheet_name}")

    # 3. Define headers
    headers = [
        "request_id",       # A
        "nome",             # B
        "telefone",         # C
        "condominio",       # D
        "bloco",            # E
        "apartamento",      # F
        "mes",              # G
        "valor",            # H
        "status",           # I
        "data_criacao",     # J
        "data_pagamento",   # K
        "mp_payment_id",    # L
    ]

    # 4. Write headers
    try:
        body = {"values": [headers]}

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1:L1",
            valueInputOption="RAW",
            body=body,
        ).execute()

        print("\n✅ Headers created successfully")
    except Exception as e:
        print(f"❌ Error writing headers: {e}")
        sys.exit(1)

    # 5. Format header row
    try:
        # Get sheet ID
        sheet_metadata = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        sheet_id = None
        for sheet in sheet_metadata.get("sheets", []):
            if sheet["properties"]["title"] == sheet_name:
                sheet_id = sheet["properties"]["sheetId"]
                break

        if sheet_id is None:
            print(f"⚠️  Warning: Could not find sheet '{sheet_name}' for formatting")
        else:
            # Format requests
            requests = [
                # 1. Bold header row
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {"bold": True},
                                "backgroundColor": {
                                    "red": 0.8,
                                    "green": 0.8,
                                    "blue": 0.8,
                                },
                            }
                        },
                        "fields": "userEnteredFormat(textFormat,backgroundColor)",
                    }
                },
                # 2. Freeze header row
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {"frozenRowCount": 1},
                        },
                        "fields": "gridProperties.frozenRowCount",
                    }
                },
                # 3. Set column widths
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,  # request_id
                            "endIndex": 1,
                        },
                        "properties": {"pixelSize": 200},
                        "fields": "pixelSize",
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 1,  # nome
                            "endIndex": 2,
                        },
                        "properties": {"pixelSize": 150},
                        "fields": "pixelSize",
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 2,  # telefone
                            "endIndex": 3,
                        },
                        "properties": {"pixelSize": 130},
                        "fields": "pixelSize",
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 11,  # mp_payment_id
                            "endIndex": 12,
                        },
                        "properties": {"pixelSize": 150},
                        "fields": "pixelSize",
                    }
                },
            ]

            body = {"requests": requests}

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            print("✅ Formatting applied successfully")

    except Exception as e:
        print(f"⚠️  Warning: Could not apply formatting: {e}")
        print("   (Headers were created, but formatting failed)")

    # 6. Summary
    print("\n" + "=" * 60)
    print("✨ Google Sheets setup completed!")
    print("=" * 60)
    print(f"\n📊 Your spreadsheet is ready at:")
    print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    print(f"\n📋 Columns configured:")
    for i, header in enumerate(headers, 1):
        print(f"   {chr(64 + i)}. {header}")
    print("\n✅ Next steps:")
    print("   1. Verify the spreadsheet is accessible")
    print("   2. Test PIX creation to see data flowing in")
    print("   3. Monitor payment updates via webhooks")
    print()


if __name__ == "__main__":
    setup_sheet()
