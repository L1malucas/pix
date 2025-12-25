"""Application configuration settings."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "pix-whatsapp-automation"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "http://localhost:8000"

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "pix_automation"
    db_user: str = "postgres"
    db_password: str = "postgres"

    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # WhatsApp Cloud API
    whatsapp_api_url: str = "https://graph.facebook.com/v18.0"
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_business_account_id: str = ""

    # Mercado Pago
    mercadopago_access_token: str = ""
    mercadopago_public_key: str = ""
    mercadopago_webhook_secret: Optional[str] = None

    # PIX Configuration
    pix_expiration_hours: int = 6

    # Google Sheets API
    google_sheets_credentials_file: str = "credentials.json"
    google_sheets_spreadsheet_id: str = ""
    google_sheets_sheet_name: str = "Pagamentos"

    # Security
    secret_key: str = "change-this-secret-key-in-production"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # Monitoring
    sentry_dsn: Optional[str] = None

    @property
    def allowed_origins_list(self) -> list[str]:
        """Get allowed origins as list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Global settings instance
settings = Settings()
