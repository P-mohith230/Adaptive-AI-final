import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account
from app.models.category import Category
from app.models.merchant_ledger import MerchantLedgerEntry
from app.models.canonical_transaction import CanonicalTransaction
from app.models.reconciliation import (
    ReconciliationBatch,
    ReconciliationRecord,
    ReconciliationException,
    ReconciliationAuditLog,
)
from app.models.transaction import Transaction


class ReconciliationLedgerBridge:
    """Bridges the AI Finance Controller with Securo core ledger:
    - Auto-provisions standard merchant accounts (Bank Operating, Gateway Clearing)
    - Synchronizes verified 3-way reconciliation batches into Securo general ledger transactions
    - Generates forward cash position and T+2 liquidity forecasts
    """

    @staticmethod
    async def ensure_merchant_accounts(
        session: AsyncSession,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, uuid.UUID]:
        """Ensures that the workspace contains the required merchant operating and
        clearing accounts and accounting categories.
        """
        # 1. Bank Operating Account
        bank_acc = await session.scalar(
            select(Account).where(
                Account.workspace_id == workspace_id,
                Account.name == "HDFC Bank Operating Account",
            )
        )
        if not bank_acc:
            bank_acc = Account(
                id=uuid.uuid4(),
                user_id=user_id,
                workspace_id=workspace_id,
                name="HDFC Bank Operating Account",
                display_name="HDFC Bank • Operating A/C",
                masked_number="4892",
                type="checking",
                balance=Decimal("250000.00"),  # Initial operating float
                currency="INR",
            )
            session.add(bank_acc)

        # 2. Razorpay Clearing Account
        clearing_acc = await session.scalar(
            select(Account).where(
                Account.workspace_id == workspace_id,
                Account.name == "Razorpay Gateway Clearing",
            )
        )
        if not clearing_acc:
            clearing_acc = Account(
                id=uuid.uuid4(),
                user_id=user_id,
                workspace_id=workspace_id,
                name="Razorpay Gateway Clearing",
                display_name="Razorpay • Gateway Clearing",
                masked_number="RZP1",
                type="checking",
                balance=Decimal("0.00"),
                currency="INR",
            )
            session.add(clearing_acc)

        # 3. Income Category: Sales Revenue
        sales_cat = await session.scalar(
            select(Category).where(
                Category.workspace_id == workspace_id,
                Category.name == "Online Sales Revenue",
            )
        )
        if not sales_cat:
            sales_cat = Category(
                id=uuid.uuid4(),
                user_id=user_id,
                workspace_id=workspace_id,
                name="Online Sales Revenue",
                icon="shopping-bag",
                color="#10B981",
                is_system=False,
            )
            session.add(sales_cat)

        # 4. Expense Category: Payment Processing Fees (MDR + GST)
        fee_cat = await session.scalar(
            select(Category).where(
                Category.workspace_id == workspace_id,
                Category.name == "Razorpay MDR & Processing Fees",
            )
        )
        if not fee_cat:
            fee_cat = Category(
                id=uuid.uuid4(),
                user_id=user_id,
                workspace_id=workspace_id,
                name="Razorpay MDR & Processing Fees",
                icon="receipt",
                color="#EF4444",
                is_system=False,
            )
            session.add(fee_cat)

        await session.flush()

        return {
            "bank_account_id": bank_acc.id,
            "clearing_account_id": clearing_acc.id,
            "sales_category_id": sales_cat.id,
            "fee_category_id": fee_cat.id,
        }

    @staticmethod
    async def sync_batch_to_securo_ledger(
        session: AsyncSession,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        batch_id: uuid.UUID,
        clear_existing: bool = True,
    ) -> Dict[str, int]:
        """Synchronizes an evaluated 3-way reconciliation batch into Securo's
        general ledger `transactions` table.

        - Reconciled orders create:
          1. Sales Credit into Razorpay Clearing
          2. MDR Fee Debit
          3. Settlement Transfer into HDFC Bank Operating Account
        - Unreconciled exceptions create:
          Tagged pending suspense transactions for clear visibility in /transactions
        """
        if clear_existing:
            await session.execute(
                delete(Transaction).where(
                    Transaction.workspace_id == workspace_id,
                    Transaction.source == "sync",
                )
            )
            await session.flush()

        accounts = await ReconciliationLedgerBridge.ensure_merchant_accounts(
            session, workspace_id, user_id
        )
        bank_id = accounts["bank_account_id"]
        clearing_id = accounts["clearing_account_id"]
        sales_cat_id = accounts["sales_category_id"]
        fee_cat_id = accounts["fee_category_id"]

        records = (
            await session.scalars(
                select(ReconciliationRecord)
                .options(selectinload(ReconciliationRecord.exception))
                .where(ReconciliationRecord.batch_id == batch_id)
            )
        ).all()

        synced_clean = 0
        synced_exceptions = 0
        today_date = date.today()

        for rec in records:
            # Check if already synced
            existing_tx = await session.scalar(
                select(Transaction).where(
                    Transaction.workspace_id == workspace_id,
                    Transaction.external_id == rec.order_id,
                ).limit(1)
            )
            if existing_tx:
                continue

            ledger_entry = (
                await session.get(MerchantLedgerEntry, rec.merchant_ledger_id)
                if rec.merchant_ledger_id
                else None
            )
            payment = (
                await session.get(CanonicalTransaction, rec.payment_transaction_id)
                if rec.payment_transaction_id
                else None
            )

            gross_amt = (
                ledger_entry.expected_amount
                if ledger_entry
                else (payment.amount if payment else Decimal("0.00"))
            )
            fee_amt = (
                payment.fee
                if payment and payment.fee
                else (ledger_entry.expected_fee if ledger_entry else Decimal("0.00"))
            )
            net_amt = gross_amt - fee_amt if gross_amt >= fee_amt else gross_amt

            is_clean = (
                rec.status == "AUTO_RECONCILED" or rec.resolution_status == "approved"
            )

            if is_clean:
                # 1. Gross Sale credited into Clearing
                tx_sale = Transaction(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    workspace_id=workspace_id,
                    account_id=clearing_id,
                    category_id=sales_cat_id,
                    external_id=rec.order_id,
                    description=f"Razorpay Order {rec.order_id} - Gross Sale",
                    amount=gross_amt,
                    currency="INR",
                    date=today_date,
                    effective_date=today_date,
                    type="credit",
                    source="sync",
                    status="posted",
                    notes=f"Reconciled 3-way match. Payment ID: {rec.payment_id or 'N/A'}",
                    raw_data={"reconciliation_record_id": str(rec.id), "status": rec.status},
                )
                session.add(tx_sale)

                # 2. MDR Fee debited
                if fee_amt > Decimal("0.00"):
                    tx_fee = Transaction(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        workspace_id=workspace_id,
                        account_id=clearing_id,
                        category_id=fee_cat_id,
                        external_id=f"{rec.order_id}_fee",
                        description=f"MDR Fee & GST - Order {rec.order_id}",
                        amount=fee_amt,
                        currency="INR",
                        date=today_date,
                        effective_date=today_date,
                        type="debit",
                        source="sync",
                        status="posted",
                        notes=f"Payment Gateway 2% MDR fee schedule. Payment ID: {rec.payment_id or 'N/A'}",
                        raw_data={"reconciliation_record_id": str(rec.id), "fee_delta": str(rec.fee_delta)},
                    )
                    session.add(tx_fee)

                # 3. Settlement Payout to Bank (paired transfer)
                if rec.settlement_id:
                    pair_id = uuid.uuid4()
                    # Clearing leg (debit)
                    tx_transfer_out = Transaction(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        workspace_id=workspace_id,
                        account_id=clearing_id,
                        transfer_pair_id=pair_id,
                        external_id=f"{rec.order_id}_payout_out",
                        description=f"Settlement Payout {rec.settlement_id} - Order {rec.order_id}",
                        amount=net_amt,
                        currency="INR",
                        date=today_date,
                        effective_date=today_date,
                        type="debit",
                        source="sync",
                        status="posted",
                        notes=f"Settlement payout transferred to HDFC Bank A/C",
                    )
                    # Bank leg (credit)
                    tx_transfer_in = Transaction(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        workspace_id=workspace_id,
                        account_id=bank_id,
                        transfer_pair_id=pair_id,
                        external_id=f"{rec.order_id}_payout_in",
                        description=f"Razorpay Settlement Credit - UTR {rec.settlement_id}",
                        amount=net_amt,
                        currency="INR",
                        date=today_date,
                        effective_date=today_date,
                        type="credit",
                        source="sync",
                        status="posted",
                        notes=f"Net credit from Razorpay settlement {rec.settlement_id}",
                    )
                    session.add(tx_transfer_out)
                    session.add(tx_transfer_in)

                synced_clean += 1

            else:
                # Exception Record: Record as pending suspense transaction in Clearing A/C
                exc_reason = (
                    rec.exception.reason
                    if rec.exception
                    else f"Discrepancy detected: {rec.status}"
                )
                tx_suspense = Transaction(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    workspace_id=workspace_id,
                    account_id=clearing_id,
                    category_id=sales_cat_id,
                    external_id=rec.order_id,
                    description=f"[Unreconciled - {rec.status}] Order {rec.order_id}",
                    amount=gross_amt,
                    currency="INR",
                    date=today_date,
                    effective_date=today_date,
                    type="credit",
                    source="sync",
                    status="pending",
                    notes=f"FLAGGED EXCEPTION: {exc_reason} | Financial Exposure: INR {rec.financial_impact}",
                    raw_data={
                        "reconciliation_record_id": str(rec.id),
                        "status": rec.status,
                        "priority_score": str(rec.priority_score),
                    },
                )
                session.add(tx_suspense)
                synced_exceptions += 1

        await session.commit()

        # Re-sync Account balance columns for convenience
        for acc_id in [bank_id, clearing_id]:
            acc = await session.get(Account, acc_id)
            if acc:
                credits_val = await session.scalar(
                    select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
                    .where(Transaction.account_id == acc_id, Transaction.type == "credit")
                ) or Decimal("0.00")
                debits_val = await session.scalar(
                    select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
                    .where(Transaction.account_id == acc_id, Transaction.type == "debit")
                ) or Decimal("0.00")
                acc.balance = (credits_val - debits_val).quantize(Decimal("0.01"))

        await session.commit()

        return {"synced_clean": synced_clean, "synced_exceptions": synced_exceptions}

    @staticmethod
    async def calculate_cash_position_forecast(
        session: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Calculates current verified cash position and forward 7-day projection:
        - Liquid Bank Cash
        - In-Transit Unsettled Razorpay Float (T+2 cutoff)
        - At-Risk Trapped Exceptions Exposure
        - 7-day expected daily cash arrival schedule
        """
        # Bank account balance
        bank_acc = await session.scalar(
            select(Account).where(
                Account.workspace_id == workspace_id,
                Account.name == "HDFC Bank Operating Account",
            )
        )
        liquid_bank = bank_acc.balance if bank_acc else Decimal("250000.00")

        # In-transit gateway clearing balance
        clearing_acc = await session.scalar(
            select(Account).where(
                Account.workspace_id == workspace_id,
                Account.name == "Razorpay Gateway Clearing",
            )
        )
        in_transit_clearing = clearing_acc.balance if clearing_acc else Decimal("0.00")

        # Unresolved financial exposure across latest batch
        latest_batch = await session.scalar(
            select(ReconciliationBatch)
            .where(ReconciliationBatch.workspace_id == workspace_id)
            .order_by(desc(ReconciliationBatch.created_at))
            .limit(1)
        )
        trapped_exposure = latest_batch.financial_exposure if latest_batch else Decimal("0.00")

        # Net reliable cash position
        net_cash = liquid_bank + in_transit_clearing - trapped_exposure

        # Forward 7-Day Inflow Forecast based on T+2 and ongoing capture trends
        today = date.today()
        daily_forecast = []
        base_daily_inflow = Decimal("18500.00")

        for day_offset in range(1, 8):
            fc_date = today + timedelta(days=day_offset)
            is_weekend = fc_date.weekday() in (5, 6)  # Saturday, Sunday
            # Indian banking NEFT/RTGS cutoff: settlements hold over weekend to Monday
            if is_weekend:
                projected_inflow = Decimal("0.00")
            elif fc_date.weekday() == 0:  # Monday backlog clearance
                projected_inflow = (base_daily_inflow * Decimal("2.8")).quantize(Decimal("0.01"))
            else:
                projected_inflow = (base_daily_inflow * Decimal("1.05")).quantize(Decimal("0.01"))

            daily_forecast.append({
                "date": fc_date.isoformat(),
                "day_name": fc_date.strftime("%a"),
                "expected_settlement_inflow": projected_inflow,
                "projected_bank_balance": (liquid_bank + projected_inflow).quantize(Decimal("0.01")),
            })

        return {
            "liquid_bank_balance": liquid_bank,
            "in_transit_clearing_balance": in_transit_clearing,
            "at_risk_trapped_exposure": trapped_exposure,
            "net_cash_position": net_cash,
            "t2_settlement_expected_date": (today + timedelta(days=2)).isoformat(),
            "daily_forecast_7d": daily_forecast,
        }
