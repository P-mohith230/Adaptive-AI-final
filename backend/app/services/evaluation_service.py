import random
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_transaction import CanonicalTransaction
from app.models.merchant_ledger import MerchantLedgerEntry
from app.models.reconciliation import (
    ReconciliationBatch,
    ReconciliationException,
    ReconciliationRecord,
    ReconciliationAuditLog,
)
from app.services.ai_controller_service import AIControllerService
from app.services.reconciliation_service import ReconciliationService


class EvaluationService:
    """Generates controlled synthetic evaluation batches with ground truth anomalies.

    Enables reliable, reproducible verification of match rates and throughput
    across 50 to 250+ records for Razorpay Buildathon Track 04 evaluation.
    """

    SAMPLE_MERCHANTS = ["Acme Retail", "Bharat Tech", "Delhi Logistics", "Kolkata Crafts", "Mumbai Electronics"]
    SAMPLE_METHODS = ["upi", "card", "netbanking"]

    @classmethod
    async def generate_and_seed_dataset(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        total_records: int = 100,
        clear_existing: bool = True,
    ) -> dict[str, Any]:
        """Seeds a realistic evaluation batch with exact ground truth anomalies.

        Default distribution:
        - 86% Clean Auto-Reconciled
        - 4% Amount Mismatches
        - 3% Fee Discrepancies
        - 3% Missing Settlements
        - 2% Timing Differences
        - 2% Duplicate Payments
        """
        if clear_existing:
            # Delete old evaluation data for this workspace
            await session.execute(delete(ReconciliationAuditLog).where(ReconciliationAuditLog.workspace_id == workspace_id))
            await session.execute(delete(ReconciliationException).where(ReconciliationException.workspace_id == workspace_id))
            await session.execute(delete(ReconciliationRecord).where(ReconciliationRecord.workspace_id == workspace_id))
            await session.execute(delete(ReconciliationBatch).where(ReconciliationBatch.workspace_id == workspace_id))
            await session.execute(delete(MerchantLedgerEntry).where(MerchantLedgerEntry.workspace_id == workspace_id))
            await session.execute(delete(CanonicalTransaction).where(CanonicalTransaction.workspace_id == workspace_id))
            await session.flush()

        base_time = datetime.now(timezone.utc) - timedelta(days=5)
        ledgers_to_add: list[MerchantLedgerEntry] = []
        txs_to_add: list[CanonicalTransaction] = []

        ground_truth: dict[str, str] = {}

        for i in range(1, total_records + 1):
            order_id = f"order_DEMO_{1000 + i}"
            payment_id = f"pay_DEMO_{uuid.uuid4().hex[:12]}"
            settlement_id = f"set_DEMO_{uuid.uuid4().hex[:12]}"
            tx_time = base_time + timedelta(hours=i * 1.2)

            # Amounts vary between ₹450 and ₹55,000
            base_amount = Decimal(str(random.choice([499, 999, 1499, 2500, 4800, 8500, 15000, 28000, 45000])))
            standard_fee = (base_amount * Decimal("0.02")).quantize(Decimal("0.01"))  # 2% MDR
            standard_tax = (standard_fee * Decimal("0.18")).quantize(Decimal("0.01"))  # 18% GST on fee
            total_fee = standard_fee + standard_tax
            net_amount = base_amount - total_fee

            # Inject intentional anomalies
            if i in (12, 42, 78, 95):  # Amount Mismatch (e.g. ₹28,000 expected vs ₹25,000 captured)
                ground_truth[order_id] = "MISMATCH"
                captured_amount = base_amount - Decimal("2000.00")
                captured_fee = (captured_amount * Decimal("0.02")).quantize(Decimal("0.01"))
                captured_net = captured_amount - captured_fee

                ledger = MerchantLedgerEntry(
                    workspace_id=workspace_id,
                    order_id=order_id,
                    invoice_id=f"INV-{1000 + i}",
                    customer_reference=f"cust_{i}@example.com",
                    expected_amount=base_amount,
                    expected_currency="INR",
                    expected_fee=total_fee,
                    expected_tax=standard_tax,
                    expected_net_amount=net_amount,
                    expected_status="captured",
                    transaction_date=tx_time,
                    source="merchant_erp",
                )
                payment_tx = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_payment",
                    external_id=payment_id,
                    payment_id=payment_id,
                    order_id=order_id,
                    settlement_id=settlement_id,
                    amount=captured_amount,
                    currency="INR",
                    fee=captured_fee,
                    tax=standard_tax,
                    net_amount=captured_net,
                    status="captured",
                    payment_method="card",
                    transaction_time=tx_time,
                )
                settlement_tx = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_settlement",
                    external_id=settlement_id,
                    payment_id=None,
                    order_id=None,
                    settlement_id=settlement_id,
                    amount=captured_net,
                    currency="INR",
                    fee=Decimal("0.00"),
                    tax=Decimal("0.00"),
                    net_amount=captured_net,
                    status="settled",
                    transaction_time=tx_time + timedelta(days=1),
                    settlement_time=tx_time + timedelta(days=1),
                )
                ledgers_to_add.append(ledger)
                txs_to_add.extend([payment_tx, settlement_tx])

            elif i in (25, 60, 85):  # Fee Discrepancy (e.g. 3.5% international surcharge)
                ground_truth[order_id] = "FEE_DISCREPANCY"
                higher_fee = (base_amount * Decimal("0.035")).quantize(Decimal("0.01"))  # Surcharge
                higher_net = base_amount - higher_fee

                ledger = MerchantLedgerEntry(
                    workspace_id=workspace_id,
                    order_id=order_id,
                    invoice_id=f"INV-{1000 + i}",
                    customer_reference=f"intl_cust_{i}@global.com",
                    expected_amount=base_amount,
                    expected_currency="INR",
                    expected_fee=total_fee,
                    expected_tax=standard_tax,
                    expected_net_amount=net_amount,
                    expected_status="captured",
                    transaction_date=tx_time,
                    source="merchant_erp",
                )
                payment_tx = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_payment",
                    external_id=payment_id,
                    payment_id=payment_id,
                    order_id=order_id,
                    settlement_id=settlement_id,
                    amount=base_amount,
                    currency="INR",
                    fee=higher_fee,
                    tax=standard_tax,
                    net_amount=higher_net,
                    status="captured",
                    payment_method="card",
                    transaction_time=tx_time,
                )
                settlement_tx = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_settlement",
                    external_id=settlement_id,
                    payment_id=None,
                    order_id=None,
                    settlement_id=settlement_id,
                    amount=higher_net,
                    currency="INR",
                    fee=Decimal("0.00"),
                    tax=Decimal("0.00"),
                    net_amount=higher_net,
                    status="settled",
                    transaction_time=tx_time + timedelta(days=1),
                    settlement_time=tx_time + timedelta(days=1),
                )
                ledgers_to_add.append(ledger)
                txs_to_add.extend([payment_tx, settlement_tx])

            elif i in (35, 72, 90):  # Missing Settlement (> 3 days old, no payout)
                ground_truth[order_id] = "MISSING_SETTLEMENT"
                old_time = base_time - timedelta(days=4)
                ledger = MerchantLedgerEntry(
                    workspace_id=workspace_id,
                    order_id=order_id,
                    invoice_id=f"INV-{1000 + i}",
                    customer_reference=f"cust_{i}@example.com",
                    expected_amount=base_amount,
                    expected_currency="INR",
                    expected_fee=total_fee,
                    expected_tax=standard_tax,
                    expected_net_amount=net_amount,
                    expected_status="captured",
                    transaction_date=old_time,
                    source="merchant_erp",
                )
                payment_tx = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_payment",
                    external_id=payment_id,
                    payment_id=payment_id,
                    order_id=order_id,
                    settlement_id=None,  # No settlement ID
                    amount=base_amount,
                    currency="INR",
                    fee=total_fee,
                    tax=standard_tax,
                    net_amount=net_amount,
                    status="captured",
                    payment_method="upi",
                    transaction_time=old_time,
                )
                ledgers_to_add.append(ledger)
                txs_to_add.append(payment_tx)

            elif i in (48, 88):  # Timing Difference (captured a few hours ago, pending normal settlement)
                ground_truth[order_id] = "TIMING_DIFFERENCE"
                recent_time = datetime.now(timezone.utc) - timedelta(hours=4)
                ledger = MerchantLedgerEntry(
                    workspace_id=workspace_id,
                    order_id=order_id,
                    invoice_id=f"INV-{1000 + i}",
                    customer_reference=f"cust_{i}@example.com",
                    expected_amount=base_amount,
                    expected_currency="INR",
                    expected_fee=total_fee,
                    expected_tax=standard_tax,
                    expected_net_amount=net_amount,
                    expected_status="captured",
                    transaction_date=recent_time,
                    source="merchant_erp",
                )
                payment_tx = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_payment",
                    external_id=payment_id,
                    payment_id=payment_id,
                    order_id=order_id,
                    settlement_id=None,
                    amount=base_amount,
                    currency="INR",
                    fee=total_fee,
                    tax=standard_tax,
                    net_amount=net_amount,
                    status="captured",
                    payment_method="netbanking",
                    transaction_time=recent_time,
                )
                ledgers_to_add.append(ledger)
                txs_to_add.append(payment_tx)

            elif i in (19, 65):  # Duplicate Payment (Customer clicked twice, two payments for 1 order)
                ground_truth[order_id] = "DUPLICATE"
                second_pay_id = f"pay_DEMO_DUP_{uuid.uuid4().hex[:8]}"
                ledger = MerchantLedgerEntry(
                    workspace_id=workspace_id,
                    order_id=order_id,
                    invoice_id=f"INV-{1000 + i}",
                    customer_reference=f"cust_{i}@example.com",
                    expected_amount=base_amount,
                    expected_currency="INR",
                    expected_fee=total_fee,
                    expected_tax=standard_tax,
                    expected_net_amount=net_amount,
                    expected_status="captured",
                    transaction_date=tx_time,
                    source="merchant_erp",
                )
                payment_1 = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_payment",
                    external_id=payment_id,
                    payment_id=payment_id,
                    order_id=order_id,
                    settlement_id=settlement_id,
                    amount=base_amount,
                    currency="INR",
                    fee=total_fee,
                    tax=standard_tax,
                    net_amount=net_amount,
                    status="captured",
                    payment_method="upi",
                    transaction_time=tx_time,
                )
                payment_2 = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_payment",
                    external_id=second_pay_id,
                    payment_id=second_pay_id,
                    order_id=order_id,
                    settlement_id=settlement_id,
                    amount=base_amount,
                    currency="INR",
                    fee=total_fee,
                    tax=standard_tax,
                    net_amount=net_amount,
                    status="captured",
                    payment_method="upi",
                    transaction_time=tx_time + timedelta(minutes=2),
                )
                ledgers_to_add.append(ledger)
                txs_to_add.extend([payment_1, payment_2])

            else:  # Standard Clean Auto-Reconciled Match (~86%)
                ground_truth[order_id] = "AUTO_RECONCILED"
                ledger = MerchantLedgerEntry(
                    workspace_id=workspace_id,
                    order_id=order_id,
                    invoice_id=f"INV-{1000 + i}",
                    customer_reference=f"cust_{i}@example.com",
                    expected_amount=base_amount,
                    expected_currency="INR",
                    expected_fee=total_fee,
                    expected_tax=standard_tax,
                    expected_net_amount=net_amount,
                    expected_status="captured",
                    transaction_date=tx_time,
                    source="merchant_erp",
                )
                payment_tx = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_payment",
                    external_id=payment_id,
                    payment_id=payment_id,
                    order_id=order_id,
                    settlement_id=settlement_id,
                    amount=base_amount,
                    currency="INR",
                    fee=total_fee,
                    tax=standard_tax,
                    net_amount=net_amount,
                    status="captured",
                    payment_method=random.choice(cls.SAMPLE_METHODS),
                    transaction_time=tx_time,
                )
                settlement_tx = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_settlement",
                    external_id=settlement_id,
                    payment_id=None,
                    order_id=None,
                    settlement_id=settlement_id,
                    amount=net_amount,
                    currency="INR",
                    fee=Decimal("0.00"),
                    tax=Decimal("0.00"),
                    net_amount=net_amount,
                    status="settled",
                    transaction_time=tx_time + timedelta(days=1),
                    settlement_time=tx_time + timedelta(days=1),
                )
                ledgers_to_add.append(ledger)
                txs_to_add.extend([payment_tx, settlement_tx])

        session.add_all(ledgers_to_add)
        session.add_all(txs_to_add)
        await session.commit()

        return {
            "total_generated": len(ledgers_to_add),
            "ground_truth": ground_truth,
        }

    @classmethod
    async def run_full_demo_loop(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        total_records: int = 100,
    ) -> ReconciliationBatch:
        """Executes the complete end-to-end Track 04 finance loop:

        1. Seed synthetic merchant ledger + Razorpay gateway + settlement records
        2. Execute deterministic 3-way reconciliation
        3. Execute AI exception investigation and evidence synthesis
        4. Synchronize verified records and exceptions to Securo accounts and transactions
        5. Measure real dynamic performance metrics (accuracy, throughput, exposure)
        """
        # Step 1: Seed
        await cls.generate_and_seed_dataset(session, workspace_id, total_records=total_records)

        # Step 2: Deterministic 3-Way Reconciliation
        batch = await ReconciliationService.run_reconciliation(
            session=session,
            workspace_id=workspace_id,
            dataset_type="synthetic_evaluation",
        )

        # Step 3: AI Exception Investigation
        await AIControllerService.process_batch_exceptions(session=session, batch_id=batch.id)

        # Step 4: Sync to Securo General Ledger & Accounts
        if user_id:
            from app.services.reconciliation_ledger_bridge import ReconciliationLedgerBridge
            await ReconciliationLedgerBridge.sync_batch_to_securo_ledger(
                session=session,
                workspace_id=workspace_id,
                user_id=user_id,
                batch_id=batch.id,
            )

        # Re-fetch updated batch with loaded records
        await session.refresh(batch)
        return batch
