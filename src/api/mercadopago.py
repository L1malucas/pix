"""Mercado Pago webhook endpoints."""
from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse, PlainTextResponse

from src.core.database import DBSession
from src.core.logging import get_logger
from src.schemas.mercadopago import MercadoPagoWebhook
from src.schemas.responses import create_error_response, create_success_response
from src.services.webhook_processor import webhook_processor

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks/mercadopago", tags=["Mercado Pago"])


@router.post("/", response_class=PlainTextResponse)
async def receive_webhook(
    request: Request,
    webhook: MercadoPagoWebhook,
    db: DBSession,
    x_signature: str = Header(None, alias="x-signature"),
    x_request_id: str = Header(None, alias="x-request-id"),
) -> PlainTextResponse:
    """
    Receive Mercado Pago webhook notifications.

    This endpoint processes payment notifications from Mercado Pago.
    It validates the notification, updates payment status, and notifies the client.

    Args:
        request: FastAPI request
        webhook: Mercado Pago webhook payload
        db: Database session
        x_signature: Mercado Pago signature header (optional, for validation)
        x_request_id: Mercado Pago request ID header

    Returns:
        200 OK response (Mercado Pago expects plain text)
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        "mercadopago_webhook_received",
        request_id=request_id,
        notification_id=webhook.id,
        action=webhook.action,
        type=webhook.type,
        mp_request_id=x_request_id,
    )

    # Only process payment events
    if webhook.type != "payment":
        logger.info(
            "webhook_type_ignored",
            request_id=request_id,
            type=webhook.type,
        )
        return PlainTextResponse(content="OK", status_code=200)

    try:
        # Process payment notification
        result = await webhook_processor.process_payment_notification(
            db=db,
            mp_payment_id=webhook.data.id,
            notification_id=str(webhook.id),
            request_id=request_id,
        )

        logger.info(
            "webhook_processing_result",
            request_id=request_id,
            notification_id=webhook.id,
            processed=result.get("processed"),
            updated=result.get("updated"),
        )

        # Mercado Pago expects 200 OK
        return PlainTextResponse(content="OK", status_code=200)

    except Exception as e:
        logger.error(
            "webhook_processing_failed",
            request_id=request_id,
            notification_id=webhook.id,
            error=str(e),
            exc_info=True,
        )

        # Still return 200 to prevent Mercado Pago retries for permanent errors
        # Mercado Pago will retry on 4xx/5xx errors
        return PlainTextResponse(content="OK", status_code=200)


@router.get("/test")
async def test_endpoint(request: Request) -> JSONResponse:
    """
    Test endpoint to verify webhook configuration.

    This endpoint can be used to test if the webhook URL is accessible.

    Args:
        request: FastAPI request

    Returns:
        Success response
    """
    request_id = getattr(request.state, "request_id", "unknown")

    response = create_success_response(
        request_id=request_id,
        action="webhook_test",
        data={
            "message": "Mercado Pago webhook endpoint is accessible",
            "endpoint": "/webhooks/mercadopago/",
        },
    )

    return JSONResponse(content=response.model_dump(mode="json"))
