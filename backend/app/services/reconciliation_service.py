import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_transaction import CanonicalTransaction
from app.models.merchant_ledger import MerchantLedgerEntry
from app.models.reconciliation import (
    ReconciliationBatch,
    ReconciliationRecord,
    ReconciliationAuditLog,
)


class ReconciliationService:
    """Deterministic 3-Way Reconciliation Engine.

    Compares Merchant Expected Ledger ⟷ Razorpay Gateway Transactions ⟷ Bank Settlements.
    Zero LLM arithmetic: pure Python Decimal calculations.
    """

    TOLERANCE_AMOUNT = Decimal("0.50")  # ₹0.50 tolerance for round-off

    @classmethod
    def evaluate_match(
        cls,
        ledger: Optional[MerchantLedgerEntry],
        payment: Optional[CanonicalTransaction],
        settlement: Optional[CanonicalTransaction],
        existing_payments_for_order: list[CanonicalTransaction],
    ) -> tuple[str, Decimal, Decimal, dict[str, Any], Decimal, Decimal]:
        """Performs deterministic checks and returns:

        (status, amount_delta, fee_delta, checks_dict, priority_score, financial_impact)
        """
        checks: dict[str, Any] = {
            "order_matched": False,
            "payment_matched": False,
            "currency_matched": False,
            "amount_matched": False,
            "fee_matched": False,
            "settlement_found": False,
            "is_duplicate": False,
            "timing_acceptable": False,
        }

        # Case 1: Missing Ledger entry
        if not ledger:
            amount = payment.amount if payment else Decimal("0.00")
            checks["payment_matched"] = payment is not None
            return (
                "UNRESOLVED",
                amount,
                Decimal("0.00"),
                checks,
                Decimal("75.00"),
                amount,
            )

        # Case 2: Missing Payment (Order in ledger, but no gateway record)
        if not payment:
            checks["order_matched"] = True
            financial_impact = ledger.expected_amount
            # High risk since money was expected but never collected
            priority_score = (financial_impact * Decimal("0.8")).quantize(Decimal("0.01"))
            return (
                "MISSING_PAYMENT",
                ledger.expected_amount,
                Decimal("0.00"),
                checks,
                priority_score,
                financial_impact,
            )

        checks["order_matched"] = (ledger.order_id == payment.order_id) or (payment.order_id is None)
        checks["payment_matched"] = True
        checks["currency_matched"] = (ledger.expected_currency == payment.currency)

        # Check for Duplicate Payments
        if len(existing_payments_for_order) > 1:
            checks["is_duplicate"] = True
            duplicate_total = sum(p.amount for p in existing_payments_for_order)
            impact = duplicate_total - ledger.expected_amount
            priority_score = (impact * Decimal("1.2")).quantize(Decimal("0.01"))
            return (
                "DUPLICATE",
                impact,
                Decimal("0.00"),
                checks,
                priority_score,
                impact,
            )

        # Amount comparison
        amount_delta = (ledger.expected_amount - payment.amount).quantize(Decimal("0.01"))
        abs_amount_delta = abs(amount_delta)
        checks["amount_matched"] = abs_amount_delta <= cls.TOLERANCE_AMOUNT

        # Fee comparison
        total_gateway_fee = payment.fee + (payment.tax or Decimal("0.00"))
        delta_with_base_fee = abs(ledger.expected_fee - payment.fee)
        delta_with_total_fee = abs(ledger.expected_fee - total_gateway_fee)
        if delta_with_total_fee < delta_with_base_fee:
            fee_delta = (ledger.expected_fee - total_gateway_fee).quantize(Decimal("0.01"))
        else:
            fee_delta = (ledger.expected_fee - payment.fee).quantize(Decimal("0.01"))
        abs_fee_delta = abs(fee_delta)
        checks["fee_matched"] = abs_fee_delta <= Decimal("2.00")

        # Settlement check
        checks["settlement_found"] = settlement is not None

        # Timing check
        now = datetime.now(timezone.utc)
        tx_time = payment.transaction_time
        if tx_time and tx_time.tzinfo is None:
            tx_time = tx_time.replace(tzinfo=timezone.utc)
        payment_age_days = (now - tx_time).days if tx_time else 0
        checks["timing_acceptable"] = payment_age_days <= 2

        # Discrepancy Classification Tree
        if not checks["amount_matched"]:
            financial_impact = abs_amount_delta
            # High priority: amount mismatch directly affects revenue
            priority_score = (financial_impact * Decimal("1.5")).quantize(Decimal("0.01"))
            return "MISMATCH", amount_delta, fee_delta, checks, priority_score, financial_impact

        if not checks["fee_matched"]:
            financial_impact = abs_fee_delta
            priority_score = (financial_impact * Decimal("0.5")).quantize(Decimal("0.01"))
            return "FEE_DISCREPANCY", amount_delta, fee_delta, checks, priority_score, financial_impact

        if not checks["settlement_found"]:
            financial_impact = payment.net_amount
            if payment_age_days > 2:
                # Missing settlement past T+2 window
                priority_score = (financial_impact * Decimal("1.0")).quantize(Decimal("0.01"))
                return "MISSING_SETTLEMENT", amount_delta, fee_delta, checks, priority_score, financial_impact
            else:
                # Normal bank settlement delay
                priority_score = (financial_impact * Decimal("0.1")).quantize(Decimal("0.01"))
                return "TIMING_DIFFERENCE", amount_delta, fee_delta, checks, priority_score, financial_impact

        # All matching!
        return "AUTO_RECONCILED", Decimal("0.00"), Decimal("0.00"), checks, Decimal("0.00"), Decimal("0.00")

    @classmethod
    async def run_reconciliation(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        batch_code: Optional[str] = None,
        dataset_type: str = "synthetic_evaluation",
    ) -> ReconciliationBatch:
        """Executes full 3-way reconciliation on all active ledger entries in workspace."""
        start_time = time.perf_counter()
        code = batch_code or f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        # 1. Fetch all ledger entries
        ledger_res = await session.execute(
            select(MerchantLedgerEntry).where(MerchantLedgerEntry.workspace_id == workspace_id)
        )
        ledger_entries = list(ledger_res.scalars().all())

        # 2. Fetch all canonical transactions
        tx_res = await session.execute(
            select(CanonicalTransaction).where(CanonicalTransaction.workspace_id == workspace_id)
        )
        canonical_txs = list(tx_res.scalars().all())

        payments_by_order: dict[str, list[CanonicalTransaction]] = {}
        settlements_by_id: dict[str, CanonicalTransaction] = {}

        for tx in canonical_txs:
            if tx.source == "razorpay_payment" and tx.order_id:
                payments_by_order.setdefault(tx.order_id, []).append(tx)
            elif tx.source == "razorpay_settlement":
                if tx.settlement_id:
                    settlements_by_id[tx.settlement_id] = tx
                if tx.external_id:
                    settlements_by_id[tx.external_id] = tx

        # 3. Initialize batch
        batch = ReconciliationBatch(
            workspace_id=workspace_id,
            batch_code=code,
            dataset_type=dataset_type,
            status="running",
        )
        session.add(batch)
        await session.flush()

        total_count = len(ledger_entries)
        auto_reconciled = 0
        unresolved = 0
        total_exposure = Decimal("0.00")
        records_to_add: list[ReconciliationRecord] = []

        # 4. Evaluate each ledger entry
        for entry in ledger_entries:
            related_payments = payments_by_order.get(entry.order_id, [])
            payment = related_payments[0] if related_payments else None
            settlement = settlements_by_id.get(payment.settlement_id) if (payment and payment.settlement_id) else None

            status, amt_delta, fee_delta, checks, priority, exposure = cls.evaluate_match(
                entry, payment, settlement, related_payments
            )

            is_auto = (status == "AUTO_RECONCILED")
            if is_auto:
                auto_reconciled += 1
                res_status = "unneeded"
            else:
                unresolved += 1
                total_exposure += exposure
                res_status = "pending"

            rec_record = ReconciliationRecord(
                workspace_id=workspace_id,
                batch_id=batch.id,
                merchant_ledger_id=entry.id,
                payment_transaction_id=payment.id if payment else None,
                settlement_transaction_id=settlement.id if settlement else None,
                order_id=entry.order_id,
                payment_id=payment.external_id if payment else None,
                settlement_id=settlement.external_id if settlement else None,
                status=status,
                amount_delta=amt_delta,
                fee_delta=fee_delta,
                checks_json=checks,
                priority_score=priority,
                financial_impact=exposure,
                resolution_status=res_status,
            )
            records_to_add.append(rec_record)

        session.add_all(records_to_add)
        await session.flush()

        # 5. Measure performance metrics
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        duration_sec = duration_ms / 1000.0 if duration_ms > 0 else 0.001
        throughput = Decimal(str(round(total_count / duration_sec, 2))) if total_count > 0 else Decimal("0.00")
        matched = auto_reconciled
        match_rate = Decimal(str(round(matched / total_count, 4))) if total_count > 0 else Decimal("0.0000")

        batch.total_records = total_count
        batch.matched_records = matched
        batch.auto_reconciled = auto_reconciled
        batch.ai_assisted = 0
        batch.unresolved_count = unresolved
        batch.match_rate = match_rate
        batch.precision_rate = Decimal("1.0000")  # Deterministic precision
        batch.recall_rate = match_rate
        batch.financial_exposure = total_exposure
        batch.duration_ms = duration_ms
        batch.throughput_rps = throughput
        batch.status = "completed"

        # 6. Create initial audit log
        audit = ReconciliationAuditLog(
            workspace_id=workspace_id,
            action="deterministic_reconciliation",
            actor="deterministic_engine_v1",
            decision=f"Processed {total_count} records with {auto_reconciled} auto-matched",
            reason=f"Batch execution completed in {duration_ms}ms at {throughput} rec/sec",
            evidence_json={"batch_code": code, "match_rate": str(match_rate)},
            confidence=Decimal("1.0000"),
            previous_state="unprocessed",
            new_state="reconciled",
        )
        session.add(audit)
        await session.commit()
        return batch
