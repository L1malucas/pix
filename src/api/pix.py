"""PIX endpoints for payment generation."""
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from src.core.database import DBSession
from src.core.logging import get_logger
from src.schemas.client import ClientCreate
from src.schemas.payment import PaymentCreate
from src.schemas.pix import PIXCreateRequest, PIXCreateResponse
from src.schemas.responses import create_error_response, create_success_response
from src.services.client_service import client_service
from src.services.mercadopago_service import mercadopago_service
from src.services.payment_service import payment_service

logger = get_logger(__name__)
router = APIRouter(prefix="/pix", tags=["PIX"])


@router.post("/create")
async def create_pix(
    request: Request,
    pix_request: PIXCreateRequest,
    db: DBSession,
) -> JSONResponse:
    """
    Create PIX payment.

    This endpoint:
    1. Creates or updates client
    2. Generates PIX via Mercado Pago
    3. Creates payment record
    4. Returns PIX code

    Args:
        request: FastAPI request
        pix_request: PIX creation request
        db: Database session

    Returns:
        PIX creation response with code

    Raises:
        HTTPException: If PIX creation fails
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        "pix_creation_request",
        request_id=request_id,
        phone=pix_request.phone,
        amount=pix_request.plan_value,
    )

    try:
        # 1. Get or create client
        client_data = ClientCreate(
            name=pix_request.name,
            phone=pix_request.phone,
            condo=pix_request.condo,
            block=pix_request.block,
            apartment=pix_request.apartment,
        )

        client, created = client_service.get_or_create(db, client_data)

        logger.info(
            "client_processed",
            request_id=request_id,
            client_id=client.id,
            created=created,
        )

        # 2. Determine month reference
        month_ref = pix_request.month_ref or datetime.utcnow().strftime("%Y-%m")

        # 3. Check if client already paid for this month
        existing_payment = payment_service.get_client_payment_for_month(
            db, client.id, month_ref
        )

        if existing_payment:
            logger.warning(
                "payment_already_exists",
                request_id=request_id,
                client_id=client.id,
                month_ref=month_ref,
                payment_id=existing_payment.id,
            )
            raise HTTPException(
                status_code=400,
                detail=f"Client already has an approved payment for {month_ref}",
            )

        # 4. Generate external reference
        external_reference = mercadopago_service.generate_external_reference(
            month_ref=month_ref,
            amount=pix_request.plan_value,
            phone=pix_request.phone,
            apartment=pix_request.apartment,
        )

        # 5. Create PIX payment in Mercado Pago
        description = (
            f"Pagamento PIX - {pix_request.condo} - "
            f"Bloco {pix_request.block} - Apto {pix_request.apartment} - "
            f"{month_ref}"
        )

        mp_response = await mercadopago_service.create_pix_payment(
            amount=pix_request.plan_value,
            description=description,
            external_reference=external_reference,
            request_id=request_id,
        )

        # 6. Extract PIX data
        mp_payment_id = str(mp_response.get("id"))
        pix_code = mercadopago_service.extract_pix_code(mp_response)
        qr_code_base64 = mercadopago_service.extract_qr_code_base64(mp_response)

        if not pix_code:
            logger.error(
                "pix_code_not_found",
                request_id=request_id,
                mp_payment_id=mp_payment_id,
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to generate PIX code from Mercado Pago",
            )

        # 7. Create payment record
        payment_data = PaymentCreate(
            client_id=client.id,
            month_ref=month_ref,
            amount=pix_request.plan_value,
            external_reference=external_reference,
        )

        payment = payment_service.create(db, payment_data, request_id)

        # 8. Update payment with Mercado Pago ID
        payment_service.update_status(
            db,
            payment,
            status="pending",
            mp_payment_id=mp_payment_id,
        )

        logger.info(
            "pix_created_successfully",
            request_id=request_id,
            client_id=client.id,
            payment_id=payment.id,
            mp_payment_id=mp_payment_id,
        )

        # 9. Prepare response
        pix_response = PIXCreateResponse(
            client_id=client.id,
            payment_id=payment.id,
            mp_payment_id=mp_payment_id,
            pix_code=pix_code,
            qr_code_base64=qr_code_base64,
            amount=pix_request.plan_value,
            expiration_hours=6,
            external_reference=external_reference,
            month_ref=month_ref,
        )

        response = create_success_response(
            request_id=request_id,
            action="create_pix",
            data=pix_response.model_dump(),
        )

        return JSONResponse(content=response.model_dump(mode="json"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "pix_creation_error",
            request_id=request_id,
            error=str(e),
            exc_info=True,
        )

        response = create_error_response(
            request_id=request_id,
            action="create_pix",
            error_code="PIX_CREATION_FAILED",
            error_message=str(e),
            error_source="pix_service",
        )

        return JSONResponse(
            status_code=500,
            content=response.model_dump(mode="json"),
        )
