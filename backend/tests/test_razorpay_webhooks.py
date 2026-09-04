import hashlib
import hmac
import json
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.razorpay.webhooks import RazorpayWebhookHandler
from app.models.reconciliation import RazorpayWebhookEvent


@pytest.mark.asyncio
async def test_webhook_signature_verification():
    secret = "test_buildathon_secret_123"
    handler = RazorpayWebhookHandler(webhook_secret=secret)

    payload = json.dumps({"event": "payment.captured", "id": "event_test_01"}).encode("utf-8")
    valid_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert handler.verify_signature(payload, valid_sig) is True
    assert handler.verify_signature(payload, "invalid_sig_here") is False


@pytest.mark.asyncio
async def test_webhook_idempotency_guard(session: AsyncSession):
    secret = "test_buildathon_secret_123"
    handler = RazorpayWebhookHandler(webhook_secret=secret)

    event_id = f"event_IDEMP_{uuid.uuid4().hex[:8]}"
    raw_payload = json.dumps({
        "event_id": event_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_idemp",
                    "amount": 500000,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        },
    }).encode("utf-8")

    sig = hmac.new(secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()

    # First delivery: should process
    success1, msg1, details1 = await handler.process_webhook(session, raw_payload, sig)
    assert success1 is True
    assert details1["is_duplicate"] is False

    # Second delivery with identical event_id: should detect duplicate and ignore safely
    success2, msg2, details2 = await handler.process_webhook(session, raw_payload, sig)
    assert success2 is True
    assert details2["is_duplicate"] is True
    assert "Duplicate webhook event ignored safely" in msg2
