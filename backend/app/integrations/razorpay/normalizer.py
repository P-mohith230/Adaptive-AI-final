import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.models.canonical_transaction import CanonicalTransaction


class RazorpayNormalizer:
    """Normalizes raw Razorpay payload objects into canonical financial transactions."""

    @staticmethod
    def _paise_to_rupees(paise: Any) -> Decimal:
        if paise is None:
            return Decimal("0.00")
        try:
            return (Decimal(str(paise)) / Decimal("100")).quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0.00")

    @staticmethod
    def _parse_timestamp(ts: Any) -> datetime:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                pass
        return datetime.now(timezone.utc)

    @classmethod
    def normalize_payment(cls, payment: dict[str, Any], workspace_id: uuid.UUID) -> CanonicalTransaction:
        """Transforms a Razorpay payment item into a CanonicalTransaction."""
        payment_id = payment.get("id", f"pay_synth_{uuid.uuid4().hex[:12]}")
        order_id = payment.get("order_id")
        settlement_id = payment.get("settlement_id")

        amount = cls._paise_to_rupees(payment.get("amount", 0))
        fee = cls._paise_to_rupees(payment.get("fee", 0))
        tax = cls._paise_to_rupees(payment.get("tax", 0))
        net_amount = amount - fee

        status = payment.get("status", "captured")
        currency = payment.get("currency", "INR").upper()
        payment_method = payment.get("method")
        created_at_ts = payment.get("created_at")
        tx_time = cls._parse_timestamp(created_at_ts)

        return CanonicalTransaction(
            workspace_id=workspace_id,
            source="razorpay_payment",
            external_id=payment_id,
            payment_id=payment_id,
            order_id=order_id,
            settlement_id=settlement_id,
            amount=amount,
            currency=currency,
            fee=fee,
            tax=tax,
            net_amount=net_amount,
            status=status,
            payment_method=payment_method,
            transaction_time=tx_time,
            settlement_time=None,
            metadata_json={
                "bank": payment.get("bank"),
                "wallet": payment.get("wallet"),
                "vpa": payment.get("vpa"),
                "email": payment.get("email"),
                "contact": payment.get("contact"),
                "error_code": payment.get("error_code"),
                "error_description": payment.get("error_description"),
            },
        )

    @classmethod
    def normalize_settlement(cls, settlement: dict[str, Any], workspace_id: uuid.UUID) -> CanonicalTransaction:
        """Transforms a Razorpay settlement item into a CanonicalTransaction."""
        settlement_id = settlement.get("id", f"set_synth_{uuid.uuid4().hex[:12]}")
        amount = cls._paise_to_rupees(settlement.get("amount", 0))
        fees = cls._paise_to_rupees(settlement.get("fees", 0))
        tax = cls._paise_to_rupees(settlement.get("tax", 0))
        net_amount = amount - fees

        status = settlement.get("status", "settled")
        currency = settlement.get("currency", "INR").upper()
        settlement_time = cls._parse_timestamp(settlement.get("created_at"))

        return CanonicalTransaction(
            workspace_id=workspace_id,
            source="razorpay_settlement",
            external_id=settlement_id,
            payment_id=None,
            order_id=None,
            settlement_id=settlement_id,
            amount=amount,
            currency=currency,
            fee=fees,
            tax=tax,
            net_amount=net_amount,
            status=status,
            payment_method="bank_transfer",
            transaction_time=settlement_time,
            settlement_time=settlement_time,
            metadata_json={
                "utr": settlement.get("utr"),
                "fees": str(fees),
                "tax": str(tax),
            },
        )
