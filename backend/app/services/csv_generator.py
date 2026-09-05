import csv
import io
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_transaction import CanonicalTransaction
from app.models.merchant_ledger import MerchantLedgerEntry
from app.models.reconciliation import (
    ReconciliationAuditLog,
    ReconciliationBatch,
    ReconciliationException,
    ReconciliationRecord,
)
from app.services.ai_controller_service import AIControllerService
from app.services.reconciliation_ledger_bridge import ReconciliationLedgerBridge
from app.services.reconciliation_service import ReconciliationService


class CSVReconciliationGenerator:
    """Generates and ingests realistic 3-way reconciliation CSV batches
    specifically modeled after Indian fintech and Razorpay production environments:
    1. Merchant Order / Internal ERP export
    2. Razorpay Gateway Captured Payments export
    3. Bank Statement (HDFC Bank) Settlement Credits
    """

    DEFAULT_OUTPUT_DIR = "m:/securo/test_data"

    @classmethod
    def generate_csv_data(cls, total_records: int = 100) -> Tuple[str, str, str]:
        """Generates 3 CSV strings with 50+ records and realistic ground truth anomalies:
        - Merchant Orders CSV
        - Razorpay Payments CSV
        - Bank Settlements Statement CSV
        """
        base_time = datetime.now(timezone.utc) - timedelta(days=5)

        orders_buf = io.StringIO()
        payments_buf = io.StringIO()
        bank_buf = io.StringIO()

        orders_writer = csv.writer(orders_buf)
        payments_writer = csv.writer(payments_buf)
        bank_writer = csv.writer(bank_buf)

        # Write Headers
        orders_writer.writerow([
            "order_id",
            "invoice_id",
            "customer_email",
            "gross_amount",
            "currency",
            "expected_fee",
            "expected_tax",
            "expected_net",
            "status",
            "order_date",
        ])

        payments_writer.writerow([
            "payment_id",
            "order_id",
            "settlement_id",
            "amount",
            "currency",
            "fee",
            "tax",
            "net_amount",
            "method",
            "card_type",
            "status",
            "created_at",
        ])

        bank_writer.writerow([
            "settlement_utr",
            "settlement_id",
            "net_credit_amount",
            "currency",
            "bank_account",
            "settlement_date",
            "narration",
            "status",
        ])

        for i in range(1, total_records + 1):
            order_id = f"order_CSV_{1000 + i}"
            payment_id = f"pay_CSV_{uuid.uuid4().hex[:12]}"
            settlement_id = f"set_CSV_{uuid.uuid4().hex[:12]}"
            utr_no = f"HDFCR52026090{i:04d}"
            tx_time = base_time + timedelta(hours=i * 1.2)
            settlement_time = tx_time + timedelta(days=1, hours=2)

            base_amount = Decimal(str(random.choice([499, 999, 1499, 2500, 4800, 8500, 15000, 28000, 45000])))
            standard_fee = (base_amount * Decimal("0.02")).quantize(Decimal("0.01"))
            standard_tax = (standard_fee * Decimal("0.18")).quantize(Decimal("0.01"))
            total_fee = standard_fee + standard_tax
            net_amount = base_amount - total_fee

            # Inject Controlled Anomalies
            if i in (12, 42, 78, 95):
                # 1. Amount Mismatch: Customer underpaid or promotional coupon unrecorded in gateway
                captured_amount = base_amount - Decimal("2000.00")
                captured_fee = (captured_amount * Decimal("0.02")).quantize(Decimal("0.01"))
                captured_tax = (captured_fee * Decimal("0.18")).quantize(Decimal("0.01"))
                captured_net = captured_amount - (captured_fee + captured_tax)

                orders_writer.writerow([
                    order_id, f"INV-{1000 + i}", f"cust_{i}@example.com",
                    str(base_amount), "INR", str(total_fee), str(standard_tax), str(net_amount),
                    "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                payments_writer.writerow([
                    payment_id, order_id, settlement_id,
                    str(captured_amount), "INR", str(captured_fee), str(captured_tax), str(captured_net),
                    "card", "visa_credit", "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                bank_writer.writerow([
                    utr_no, settlement_id, str(captured_net), "INR",
                    "HDFC Current A/C 4892", settlement_time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"CMS/RAZORPAY/SETTLEMENT/{settlement_id}/UTR{i:04d}", "credited",
                ])

            elif i in (25, 60, 85):
                # 2. Fee Discrepancy: International card surcharge applied by gateway (3.5% vs standard 2%)
                higher_fee = (base_amount * Decimal("0.035")).quantize(Decimal("0.01"))
                higher_tax = (higher_fee * Decimal("0.18")).quantize(Decimal("0.01"))
                higher_net = base_amount - (higher_fee + higher_tax)

                orders_writer.writerow([
                    order_id, f"INV-{1000 + i}", f"intl_cust_{i}@global.com",
                    str(base_amount), "INR", str(total_fee), str(standard_tax), str(net_amount),
                    "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                payments_writer.writerow([
                    payment_id, order_id, settlement_id,
                    str(base_amount), "INR", str(higher_fee), str(higher_tax), str(higher_net),
                    "card", "intl_amex", "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                bank_writer.writerow([
                    utr_no, settlement_id, str(higher_net), "INR",
                    "HDFC Current A/C 4892", settlement_time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"CMS/RAZORPAY/SETTLEMENT/{settlement_id}/UTR{i:04d}", "credited",
                ])

            elif i in (33, 70):
                # 3. Missing Settlement: Captured on gateway, but bank statement has no credit record
                orders_writer.writerow([
                    order_id, f"INV-{1000 + i}", f"cust_{i}@example.com",
                    str(base_amount), "INR", str(total_fee), str(standard_tax), str(net_amount),
                    "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                payments_writer.writerow([
                    payment_id, order_id, None,
                    str(base_amount), "INR", str(standard_fee), str(standard_tax), str(net_amount),
                    "upi", "upi_handle", "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                # No entry in bank_writer!

            elif i in (18, 52):
                # 4. Timing Difference: In-transit T+2 cutoff, captured recently
                recent_tx_time = datetime.now(timezone.utc) - timedelta(hours=8)
                orders_writer.writerow([
                    order_id, f"INV-{1000 + i}", f"cust_{i}@example.com",
                    str(base_amount), "INR", str(total_fee), str(standard_tax), str(net_amount),
                    "captured", recent_tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                payments_writer.writerow([
                    payment_id, order_id, None,
                    str(base_amount), "INR", str(standard_fee), str(standard_tax), str(net_amount),
                    "netbanking", "hdfc_nb", "captured", recent_tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                # In transit - no settlement credit yet

            elif i == 50:
                # 5. Duplicate Payment: Double payment webhook received
                dup_payment_id = f"pay_CSV_DUP_{uuid.uuid4().hex[:8]}"
                orders_writer.writerow([
                    order_id, f"INV-{1000 + i}", f"cust_{i}@example.com",
                    str(base_amount), "INR", str(total_fee), str(standard_tax), str(net_amount),
                    "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                payments_writer.writerow([
                    payment_id, order_id, settlement_id,
                    str(base_amount), "INR", str(standard_fee), str(standard_tax), str(net_amount),
                    "upi", "google_pay", "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                payments_writer.writerow([
                    dup_payment_id, order_id, settlement_id,
                    str(base_amount), "INR", str(standard_fee), str(standard_tax), str(net_amount),
                    "upi", "google_pay", "captured", (tx_time + timedelta(seconds=45)).strftime("%Y-%m-%d %H:%M:%S"),
                ])
                bank_writer.writerow([
                    utr_no, settlement_id, str(net_amount), "INR",
                    "HDFC Current A/C 4892", settlement_time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"CMS/RAZORPAY/SETTLEMENT/{settlement_id}/UTR{i:04d}", "credited",
                ])

            else:
                # 6. Clean Auto-Reconciled 3-Way Match
                method = random.choice(["upi", "card", "netbanking"])
                orders_writer.writerow([
                    order_id, f"INV-{1000 + i}", f"cust_{i}@example.com",
                    str(base_amount), "INR", str(total_fee), str(standard_tax), str(net_amount),
                    "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                payments_writer.writerow([
                    payment_id, order_id, settlement_id,
                    str(base_amount), "INR", str(standard_fee), str(standard_tax), str(net_amount),
                    method, "standard", "captured", tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                ])
                bank_writer.writerow([
                    utr_no, settlement_id, str(net_amount), "INR",
                    "HDFC Current A/C 4892", settlement_time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"CMS/RAZORPAY/SETTLEMENT/{settlement_id}/UTR{i:04d}", "credited",
                ])

        return orders_buf.getvalue(), payments_buf.getvalue(), bank_buf.getvalue()

    @classmethod
    def save_csv_files_to_disk(cls, output_dir: str = DEFAULT_OUTPUT_DIR, total_records: int = 100) -> Dict[str, str]:
        """Saves generated batch files into disk for local inspection or download."""
        os.makedirs(output_dir, exist_ok=True)
        orders_csv, payments_csv, bank_csv = cls.generate_csv_data(total_records=total_records)

        orders_path = os.path.join(output_dir, "merchant_orders_batch.csv")
        payments_path = os.path.join(output_dir, "razorpay_payments_batch.csv")
        bank_path = os.path.join(output_dir, "bank_settlement_statement.csv")

        with open(orders_path, "w", encoding="utf-8", newline="") as f:
            f.write(orders_csv)

        with open(payments_path, "w", encoding="utf-8", newline="") as f:
            f.write(payments_csv)

        with open(bank_path, "w", encoding="utf-8", newline="") as f:
            f.write(bank_csv)

        return {
            "merchant_orders": orders_path,
            "razorpay_payments": payments_path,
            "bank_settlement": bank_path,
        }

    @classmethod
    async def ingest_csv_batch(
        cls,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        orders_csv_content: str,
        payments_csv_content: str,
        bank_csv_content: Optional[str] = None,
        clear_existing: bool = True,
    ) -> Dict[str, Any]:
        """Parses CSV contents, persists canonical & ledger models, and triggers
        the complete 3-way reconciliation pipeline + Securo ledger synchronization.
        """
        if clear_existing:
            await session.execute(delete(ReconciliationAuditLog).where(ReconciliationAuditLog.workspace_id == workspace_id))
            await session.execute(delete(ReconciliationException).where(ReconciliationException.workspace_id == workspace_id))
            await session.execute(delete(ReconciliationRecord).where(ReconciliationRecord.workspace_id == workspace_id))
            await session.execute(delete(ReconciliationBatch).where(ReconciliationBatch.workspace_id == workspace_id))
            await session.execute(delete(MerchantLedgerEntry).where(MerchantLedgerEntry.workspace_id == workspace_id))
            await session.execute(delete(CanonicalTransaction).where(CanonicalTransaction.workspace_id == workspace_id))
            await session.flush()

        # 1. Parse Merchant Orders CSV
        orders_reader = csv.DictReader(io.StringIO(orders_csv_content.strip()))
        orders_count = 0
        for row in orders_reader:
            if not row.get("order_id"):
                continue
            tx_date_str = row.get("order_date")
            try:
                tx_date = datetime.fromisoformat(tx_date_str.replace("Z", "+00:00")) if tx_date_str else datetime.now(timezone.utc)
            except Exception:
                tx_date = datetime.now(timezone.utc)

            gross_amt = Decimal(row.get("gross_amount", "0.00"))
            exp_fee = Decimal(row.get("expected_fee", "0.00"))
            exp_tax = Decimal(row.get("expected_tax", "0.00"))
            exp_net = Decimal(row.get("expected_net", str(gross_amt - exp_fee - exp_tax)))

            ledger = MerchantLedgerEntry(
                workspace_id=workspace_id,
                order_id=row["order_id"].strip(),
                invoice_id=row.get("invoice_id", f"INV-{row['order_id']}").strip(),
                customer_reference=row.get("customer_email", "customer@example.com").strip(),
                expected_amount=gross_amt,
                expected_currency=row.get("currency", "INR").strip(),
                expected_fee=exp_fee,
                expected_tax=exp_tax,
                expected_net_amount=exp_net,
                expected_status=row.get("status", "captured").strip(),
                transaction_date=tx_date,
                source="merchant_csv",
            )
            session.add(ledger)
            orders_count += 1

        # 2. Parse Razorpay Payments CSV
        payments_reader = csv.DictReader(io.StringIO(payments_csv_content.strip()))
        payments_count = 0
        for row in payments_reader:
            if not row.get("payment_id"):
                continue
            created_at_str = row.get("created_at")
            try:
                tx_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")) if created_at_str else datetime.now(timezone.utc)
            except Exception:
                tx_time = datetime.now(timezone.utc)

            amt = Decimal(row.get("amount", "0.00"))
            fee = Decimal(row.get("fee", "0.00"))
            tax = Decimal(row.get("tax", "0.00"))
            net_amt = Decimal(row.get("net_amount", str(amt - fee - tax)))

            payment_tx = CanonicalTransaction(
                workspace_id=workspace_id,
                source="razorpay_payment",
                external_id=row["payment_id"].strip(),
                payment_id=row["payment_id"].strip(),
                order_id=row.get("order_id", "").strip() or None,
                settlement_id=row.get("settlement_id", "").strip() or None,
                amount=amt,
                currency=row.get("currency", "INR").strip(),
                fee=fee,
                tax=tax,
                net_amount=net_amt,
                status=row.get("status", "captured").strip(),
                payment_method=row.get("method", "card").strip(),
                transaction_time=tx_time,
            )
            session.add(payment_tx)
            payments_count += 1

        # 3. Parse Bank Settlements CSV (if provided)
        settlements_count = 0
        if bank_csv_content:
            bank_reader = csv.DictReader(io.StringIO(bank_csv_content.strip()))
            for row in bank_reader:
                set_id = row.get("settlement_id", "").strip()
                if not set_id:
                    continue
                date_str = row.get("settlement_date")
                try:
                    s_time = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else datetime.now(timezone.utc)
                except Exception:
                    s_time = datetime.now(timezone.utc)

                net_credit = Decimal(row.get("net_credit_amount", "0.00"))

                settlement_tx = CanonicalTransaction(
                    workspace_id=workspace_id,
                    source="razorpay_settlement",
                    external_id=row.get("settlement_utr", set_id).strip(),
                    payment_id=None,
                    order_id=None,
                    settlement_id=set_id,
                    amount=net_credit,
                    currency=row.get("currency", "INR").strip(),
                    fee=Decimal("0.00"),
                    tax=Decimal("0.00"),
                    net_amount=net_credit,
                    status="settled",
                    transaction_time=s_time,
                    settlement_time=s_time,
                )
                session.add(settlement_tx)
                settlements_count += 1

        await session.flush()

        # 4. Run Deterministic 3-Way Reconciliation
        batch = await ReconciliationService.run_reconciliation(
            session=session,
            workspace_id=workspace_id,
            dataset_type="csv_upload",
        )

        # 5. Run AI Exception Investigation
        investigated_count = await AIControllerService.process_batch_exceptions(
            session=session,
            batch_id=batch.id,
        )

        # 6. Auto-sync clean matches & flagged exceptions to Securo core ledger
        ledger_sync_result = {}
        if user_id:
            try:
                ledger_sync_result = await ReconciliationLedgerBridge.sync_batch_to_securo_ledger(
                    session=session,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    batch_id=batch.id,
                )
            except Exception as e:
                ledger_sync_result = {"error": str(e)}

        return {
            "batch_id": batch.id,
            "status": batch.status,
            "total_records": batch.total_records,
            "matched_records": batch.matched_records,
            "match_rate": float(batch.match_rate),
            "unresolved_count": batch.unresolved_count,
            "financial_exposure": float(batch.financial_exposure),
            "orders_ingested": orders_count,
            "payments_ingested": payments_count,
            "settlements_ingested": settlements_count,
            "investigated_count": investigated_count,
            "ledger_sync": ledger_sync_result,
        }
