"""WhatsApp webhook endpoints."""
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from src.core.config import settings
from src.core.logging import get_logger
from src.schemas.responses import create_error_response, create_success_response
from src.schemas.whatsapp import WhatsAppWebhook
from src.services.conversation_handler import conversation_handler
from src.services.message_parser import MessageParser

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp"])
parser = MessageParser()


@router.get("/", response_class=PlainTextResponse)
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
) -> str:
    """
    Verify WhatsApp webhook.

    This endpoint is called by Meta to verify the webhook URL.
    It must return the hub.challenge value if the verify token matches.

    Args:
        request: FastAPI request
        hub_mode: Mode (should be "subscribe")
        hub_challenge: Challenge string to echo back
        hub_verify_token: Verify token to validate

    Returns:
        Challenge string if valid

    Raises:
        HTTPException: If verify token is invalid
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        "webhook_verification_request",
        request_id=request_id,
        mode=hub_mode,
        token_valid=hub_verify_token == settings.whatsapp_verify_token,
    )

    # Verify token
    if hub_verify_token != settings.whatsapp_verify_token:
        logger.warning(
            "webhook_verification_failed",
            request_id=request_id,
            received_token=hub_verify_token[:10] + "...",
        )
        raise HTTPException(status_code=403, detail="Invalid verify token")

    # Verify mode
    if hub_mode != "subscribe":
        logger.warning(
            "webhook_verification_invalid_mode",
            request_id=request_id,
            mode=hub_mode,
        )
        raise HTTPException(status_code=400, detail="Invalid mode")

    logger.info(
        "webhook_verification_success",
        request_id=request_id,
    )

    # Return challenge
    return hub_challenge


@router.post("/")
async def receive_webhook(
    request: Request,
    webhook: WhatsAppWebhook,
) -> JSONResponse:
    """
    Receive WhatsApp webhook messages.

    This endpoint receives incoming messages from WhatsApp users.
    It processes the message through the conversation flow.

    Args:
        request: FastAPI request
        webhook: WhatsApp webhook payload

    Returns:
        Success response
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        "webhook_received",
        request_id=request_id,
        object=webhook.object,
        entries=len(webhook.entry),
    )

    # Extract messages from webhook
    messages = parser.extract_messages(webhook)

    if not messages:
        logger.info(
            "webhook_no_messages",
            request_id=request_id,
        )
        return JSONResponse(
            content=create_success_response(
                request_id=request_id,
                action="webhook_received",
                data={"messages_processed": 0},
            ).model_dump(mode='json')
        )

    # Process each message
    processed_count = 0
    for message in messages:
        try:
            # Extract message data
            phone = parser.extract_phone(message)
            text = parser.extract_text(message)

            if not text:
                logger.warning(
                    "message_no_text",
                    request_id=request_id,
                    message_type=message.type,
                )
                continue

            logger.info(
                "processing_message",
                request_id=request_id,
                phone=phone,
                message_id=message.id,
                text_length=len(text),
            )

            # Handle conversation
            result = await conversation_handler.handle_message(
                phone=phone,
                message_text=text,
                message_id=message.id,
                request_id=request_id,
            )

            logger.info(
                "message_processed",
                request_id=request_id,
                phone=phone,
                step=result.get("step"),
                action=result.get("action"),
            )

            # TODO: If action is "generate_pix", trigger PIX generation
            # This will be implemented in ÉPICO 4

            processed_count += 1

        except Exception as e:
            logger.error(
                "message_processing_error",
                request_id=request_id,
                error=str(e),
                message_id=message.id,
                exc_info=True,
            )
            # Continue processing other messages even if one fails

    response = create_success_response(
        request_id=request_id,
        action="webhook_received",
        data={
            "messages_processed": processed_count,
            "total_messages": len(messages),
        },
    )

    return JSONResponse(content=response.model_dump(mode='json'))
