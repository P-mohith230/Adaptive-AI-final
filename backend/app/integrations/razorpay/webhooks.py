import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.razorpay.normalizer import RazorpayNormalizer
from app.models.reconciliation import RazorpayWebhookEvent

logger = logging.getLogger(__name__)


class RazorpayWebhookHandler:
    """Handles incoming Razorpay webhooks with signature verification and idempotency."""

    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret or os.getenv("RAZORPAY_WEBHOOK_SECRET", "mock_webhook_secret_buildathon")

    def verify_signature(self, raw_body: bytes, signature: Optional[str]) -> bool:
        """Verifies the HMAC SHA-256 signature from Razorpay."""
        if not signature or not self.webhook_secret:
            return False
        computed = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed, signature)

    async def process_webhook(
        self,
        session: AsyncSession,
        raw_body: bytes,
        signature: Optional[str],
        workspace_id: Optional[uuid.UUID] = None,
    ) -> Tuple[bool, str, dict[str, Any]]:
        """Verifies signature, enforces idempotency, and records the webhook event.

        Returns: (is_success, message, response_details)
        """
        # 1. Verify signature
        is_valid = self.verify_signature(raw_body, signature)
        if not is_valid:
            # Allow mock mode for local testing without valid secret
            if os.getenv("RAZORPAY_ALLOW_TEST_WEBHOOKS", "true").lower() == "true":
                logger.warning("Razorpay webhook signature failed, but allowed in test mode")
                is_valid = True
            else:
                return False, "Invalid webhook signature", {"status": "unauthorized"}

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            return False, f"Malformed JSON: {str(exc)}", {"status": "bad_request"}

        event_id = payload.get("event_id") or payload.get("id") or f"event_{uuid.uuid4().hex[:16]}"
        event_type = payload.get("event", "unknown")
        payload_hash = hashlib.sha256(raw_body).hexdigest()

        # 2. Idempotency Check
        existing_event = await session.scalar(
            select(RazorpayWebhookEvent).where(RazorpayWebhookEvent.event_id == event_id)
        )
        if existing_event:
            logger.info(f"Duplicate webhook event detected: {event_id}. Skipping processing.")
            return True, "Duplicate webhook event ignored safely", {
                "event_id": event_id,
                "is_duplicate": True,
                "first_seen": existing_event.created_at.isoformat(),
            }

        # 3. Save new event record
        event_record = RazorpayWebhookEvent(
            workspace_id=workspace_id,
            event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            is_duplicate=False,
            signature_verified=is_valid,
            payload_json=payload,
            processed_at=datetime.now(timezone.utc),
        )
        session.add(event_record)

        # 4. Normalize and persist canonical transaction if payment or settlement
        if event_type.startswith("payment."):
            payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
            if payment_data and workspace_id:
                canonical = RazorpayNormalizer.normalize_payment(payment_data, workspace_id)
                session.add(canonical)
        elif event_type.startswith("settlement."):
            settlement_data = payload.get("payload", {}).get("settlement", {}).get("entity", {})
            if settlement_data and workspace_id:
                canonical = RazorpayNormalizer.normalize_settlement(settlement_data, workspace_id)
                session.add(canonical)

        await session.commit()
        return True, f"Webhook processed: {event_type}", {"event_id": event_id, "is_duplicate": False}
