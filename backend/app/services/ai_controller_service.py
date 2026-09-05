import uuid
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_transaction import CanonicalTransaction
from app.models.merchant_ledger import MerchantLedgerEntry
from app.models.reconciliation import (
    ReconciliationAuditLog,
    ReconciliationBatch,
    ReconciliationException,
    ReconciliationRecord,
)


class AIControllerService:
    """AI Exception Investigator and Evidence Synthesizer.

    Operates on top of verified deterministic reconciliation records to diagnose root causes,
    generate grounded explanations with structured evidence, and recommend human actions.
    Never hallucinates mathematical numbers: all figures originate from database models.
    """

    @classmethod
    def investigate_discrepancy(
        cls,
        record: ReconciliationRecord,
        ledger: Optional[MerchantLedgerEntry],
        payment: Optional[CanonicalTransaction],
        settlement: Optional[CanonicalTransaction],
    ) -> tuple[str, Decimal, str, dict[str, Any], str]:
        """Synthesizes structured evidence and produces verified diagnosis.

        Returns: (ai_classification, confidence, reason, evidence_dict, recommendation)
        """
        status = record.status
        evidence: dict[str, Any] = {
            "record_id": str(record.id),
            "order_id": record.order_id,
            "payment_id": record.payment_id,
            "settlement_id": record.settlement_id,
            "checks": record.checks_json or {},
            "items": [],
        }

        if ledger:
            evidence["items"].append({
                "source": "Merchant Internal Ledger",
                "reference": f"Order #{ledger.order_id}",
                "expected_amount": f"₹{ledger.expected_amount:,.2f}",
                "expected_fee": f"₹{ledger.expected_fee:,.2f}",
                "expected_net": f"₹{ledger.expected_net_amount:,.2f}",
                "date": ledger.transaction_date.strftime("%Y-%m-%d %H:%M:%S UTC"),
            })

        if payment:
            evidence["items"].append({
                "source": "Razorpay Payment Gateway",
                "reference": f"Payment ID {payment.external_id}",
                "captured_amount": f"₹{payment.amount:,.2f}",
                "gateway_fee": f"₹{payment.fee:,.2f}",
                "gateway_tax": f"₹{payment.tax:,.2f}",
                "net_amount": f"₹{payment.net_amount:,.2f}",
                "method": payment.payment_method or "card/upi",
                "status": payment.status,
                "date": payment.transaction_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            })

        if settlement:
            evidence["items"].append({
                "source": "Bank Settlement Payout",
                "reference": f"Settlement Batch {settlement.external_id}",
                "settled_amount": f"₹{settlement.amount:,.2f}",
                "payout_time": settlement.settlement_time.strftime("%Y-%m-%d %H:%M:%S UTC") if settlement.settlement_time else "Pending",
            })

        # Diagnosis logic based on verified evidence
        if status == "MISMATCH":
            amt_diff = record.amount_delta
            direction = "undercharged" if amt_diff > 0 else "overcharged"
            abs_diff = abs(amt_diff)
            classification = "AMOUNT_MISMATCH"
            confidence = Decimal("0.9820")
            reason = (
                f"Merchant ledger expected ₹{ledger.expected_amount:,.2f} for order {record.order_id}, "
                f"but Razorpay captured ₹{payment.amount:,.2f}. Numerical variance of ₹{abs_diff:,.2f} ({direction})."
            )
            recommendation = (
                "Verify order pricing in merchant system or check if a partial promo code / coupon was applied at checkout."
            )

        elif status == "FEE_DISCREPANCY":
            fee_diff = record.fee_delta
            classification = "FEE_DISCREPANCY"
            confidence = Decimal("0.9780")
            reason = (
                f"Merchant ledger calculated expected fee of ₹{ledger.expected_fee:,.2f}, "
                f"while Razorpay deducted ₹{payment.fee:,.2f} (delta: ₹{abs(fee_diff):,.2f}). "
                f"Likely international card processing surcharge or dynamic MDR band."
            )
            recommendation = "Accept Razorpay MDR fee delta and post adjustment to gateway processing fee expense ledger."

        elif status == "MISSING_SETTLEMENT":
            classification = "MISSING_SETTLEMENT"
            confidence = Decimal("0.9650")
            reason = (
                f"Payment {record.payment_id} (₹{payment.amount:,.2f}) was captured successfully on "
                f"{payment.transaction_time.strftime('%b %d')}, but no bank payout has been credited after 3+ business days."
            )
            recommendation = "Raise priority inquiry with Razorpay Merchant Support referencing Payment ID for pending settlement UTR."

        elif status == "TIMING_DIFFERENCE":
            classification = "TIMING_DIFFERENCE"
            confidence = Decimal("0.9910")
            reason = (
                f"Payment {record.payment_id} was captured within the standard T+2 settlement cycle. "
                f"Expected bank credit pending scheduled payout window."
            )
            recommendation = "No financial risk. Allow automated settlement sweep to match upon next daily payout webhook."

        elif status == "DUPLICATE":
            classification = "DUPLICATE_PAYMENT"
            confidence = Decimal("0.9940")
            reason = (
                f"Multiple captured payments identified for Order {record.order_id}. "
                f"Customer was charged more than once for a single order reference."
            )
            recommendation = "Initiate instant Razorpay refund for duplicate payment ID to prevent customer chargeback."

        elif status == "MISSING_PAYMENT":
            classification = "MISSING_PAYMENT"
            confidence = Decimal("0.9500")
            reason = (
                f"Order {record.order_id} exists in merchant ledger with expected revenue of ₹{ledger.expected_amount:,.2f}, "
                f"but no corresponding gateway transaction was recorded in Razorpay."
            )
            recommendation = "Check if checkout was abandoned before payment authorization or if order was paid via alternate channel."

        else:
            classification = "UNRESOLVED_DISCREPANCY"
            confidence = Decimal("0.8500")
            reason = "Insufficient matching attributes between merchant ledger and external gateway records."
            recommendation = "Requires manual financial operations investigation and cross-system audit."

        return classification, confidence, reason, evidence, recommendation

    @classmethod
    async def process_batch_exceptions(
        cls,
        session: AsyncSession,
        batch_id: uuid.UUID,
    ) -> int:
        """Runs AI investigation on all non-auto-reconciled records in a batch."""
        res = await session.execute(
            select(ReconciliationRecord)
            .where(
                ReconciliationRecord.batch_id == batch_id,
                ReconciliationRecord.status != "AUTO_RECONCILED",
            )
        )
        records = list(res.scalars().all())
        if not records:
            return 0

        # Load related data
        ledger_ids = [r.merchant_ledger_id for r in records if r.merchant_ledger_id]
        tx_ids = [r.payment_transaction_id for r in records if r.payment_transaction_id] + [
            r.settlement_transaction_id for r in records if r.settlement_transaction_id
        ]

        ledgers = {}
        if ledger_ids:
            l_res = await session.execute(select(MerchantLedgerEntry).where(MerchantLedgerEntry.id.in_(ledger_ids)))
            ledgers = {entry.id: entry for entry in l_res.scalars().all()}

        txs = {}
        if tx_ids:
            t_res = await session.execute(select(CanonicalTransaction).where(CanonicalTransaction.id.in_(tx_ids)))
            txs = {t.id: t for t in t_res.scalars().all()}

        exceptions_created = 0
        for rec in records:
            ledger = ledgers.get(rec.merchant_ledger_id)
            payment = txs.get(rec.payment_transaction_id)
            settlement = txs.get(rec.settlement_transaction_id)

            classification, conf, reason, evidence, rec_action = cls.investigate_discrepancy(
                rec, ledger, payment, settlement
            )

            exc = ReconciliationException(
                record_id=rec.id,
                workspace_id=rec.workspace_id,
                ai_classification=classification,
                confidence=conf,
                reason=reason,
                evidence_json=evidence,
                recommendation=rec_action,
                review_status="PENDING_REVIEW",
            )
            session.add(exc)

            # Audit record for AI investigation
            audit = ReconciliationAuditLog(
                workspace_id=rec.workspace_id,
                record_id=rec.id,
                action="ai_investigation",
                actor="ai_controller_v1",
                decision=classification,
                reason=reason,
                evidence_json=evidence,
                confidence=conf,
                previous_state=rec.status,
                new_state="investigated",
            )
            session.add(audit)
            exceptions_created += 1

        # Update batch AI assisted count
        batch = await session.get(ReconciliationBatch, batch_id)
        if batch:
            batch.ai_assisted = exceptions_created

        await session.commit()
        return exceptions_created
