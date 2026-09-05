import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.integrations.razorpay.webhooks import RazorpayWebhookHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/razorpay")
async def receive_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    session: AsyncSession = Depends(get_async_session),
):
    """Receives Razorpay webhooks, verifies HMAC SHA-256 signature, and enforces idempotency."""
    raw_body = await request.body()
    handler = RazorpayWebhookHandler()

    is_success, message, details = await handler.process_webhook(
        session=session,
        raw_body=raw_body,
        signature=x_razorpay_signature,
    )

    if not is_success:
        logger.warning(f"Razorpay webhook rejected: {message}")
        raise HTTPException(status_code=400, detail=message)

    return {
        "status": "ok",
        "message": message,
        "details": details,
    }
