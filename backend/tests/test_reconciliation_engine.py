import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest

from app.models.canonical_transaction import CanonicalTransaction
from app.models.merchant_ledger import MerchantLedgerEntry
from app.services.reconciliation_service import ReconciliationService


@pytest.mark.asyncio
async def test_reconciliation_exact_match():
    now = datetime.now(timezone.utc)
    ws_id = uuid.uuid4()
    order_id = "order_TEST_1001"
    pay_id = "pay_TEST_1001"
    set_id = "set_TEST_1001"

    ledger = MerchantLedgerEntry(
        workspace_id=ws_id,
        order_id=order_id,
        expected_amount=Decimal("5000.00"),
        expected_currency="INR",
        expected_fee=Decimal("118.00"),
        expected_tax=Decimal("18.00"),
        expected_net_amount=Decimal("4882.00"),
        expected_status="captured",
        transaction_date=now - timedelta(days=1),
    )

    payment = CanonicalTransaction(
        workspace_id=ws_id,
        source="razorpay_payment",
        external_id=pay_id,
        payment_id=pay_id,
        order_id=order_id,
        settlement_id=set_id,
        amount=Decimal("5000.00"),
        currency="INR",
        fee=Decimal("118.00"),
        tax=Decimal("18.00"),
        net_amount=Decimal("4882.00"),
        status="captured",
        transaction_time=now - timedelta(days=1),
    )

    settlement = CanonicalTransaction(
        workspace_id=ws_id,
        source="razorpay_settlement",
        external_id=set_id,
        amount=Decimal("4882.00"),
        currency="INR",
        fee=Decimal("0.00"),
        tax=Decimal("0.00"),
        net_amount=Decimal("4882.00"),
        status="settled",
        transaction_time=now,
    )

    status, amt_delta, fee_delta, checks, priority, exposure = ReconciliationService.evaluate_match(
        ledger=ledger,
        payment=payment,
        settlement=settlement,
        existing_payments_for_order=[payment],
    )

    assert status == "AUTO_RECONCILED"
    assert amt_delta == Decimal("0.00")
    assert fee_delta == Decimal("0.00")
    assert checks["order_matched"] is True
    assert checks["payment_matched"] is True
    assert checks["amount_matched"] is True
    assert checks["fee_matched"] is True
    assert checks["settlement_found"] is True
    assert exposure == Decimal("0.00")


@pytest.mark.asyncio
async def test_reconciliation_amount_mismatch():
    now = datetime.now(timezone.utc)
    ws_id = uuid.uuid4()
    order_id = "order_TEST_1002"

    ledger = MerchantLedgerEntry(
        workspace_id=ws_id,
        order_id=order_id,
        expected_amount=Decimal("30000.00"),
        expected_currency="INR",
        expected_fee=Decimal("708.00"),
        expected_tax=Decimal("108.00"),
        expected_net_amount=Decimal("29292.00"),
        expected_status="captured",
        transaction_date=now - timedelta(days=1),
    )

    # Razorpay captured ₹28,000 instead of ₹30,000
    payment = CanonicalTransaction(
        workspace_id=ws_id,
        source="razorpay_payment",
        external_id="pay_TEST_1002",
        order_id=order_id,
        amount=Decimal("28000.00"),
        currency="INR",
        fee=Decimal("660.80"),
        tax=Decimal("100.80"),
        net_amount=Decimal("27339.20"),
        status="captured",
        transaction_time=now - timedelta(days=1),
    )

    status, amt_delta, fee_delta, checks, priority, exposure = ReconciliationService.evaluate_match(
        ledger=ledger,
        payment=payment,
        settlement=None,
        existing_payments_for_order=[payment],
    )

    assert status == "MISMATCH"
    assert amt_delta == Decimal("2000.00")
    assert checks["amount_matched"] is False
    assert exposure == Decimal("2000.00")
    assert priority > Decimal("1000.00")  # High priority


@pytest.mark.asyncio
async def test_reconciliation_fee_discrepancy():
    now = datetime.now(timezone.utc)
    ws_id = uuid.uuid4()
    order_id = "order_TEST_1003"

    ledger = MerchantLedgerEntry(
        workspace_id=ws_id,
        order_id=order_id,
        expected_amount=Decimal("10000.00"),
        expected_currency="INR",
        expected_fee=Decimal("236.00"),  # Expected 2% + GST
        expected_tax=Decimal("36.00"),
        expected_net_amount=Decimal("9764.00"),
        expected_status="captured",
        transaction_date=now - timedelta(days=1),
    )

    # Razorpay deducted higher international fee ₹350.00
    payment = CanonicalTransaction(
        workspace_id=ws_id,
        source="razorpay_payment",
        external_id="pay_TEST_1003",
        order_id=order_id,
        amount=Decimal("10000.00"),
        currency="INR",
        fee=Decimal("350.00"),
        tax=Decimal("53.39"),
        net_amount=Decimal("9650.00"),
        status="captured",
        transaction_time=now - timedelta(days=1),
    )

    status, amt_delta, fee_delta, checks, priority, exposure = ReconciliationService.evaluate_match(
        ledger=ledger,
        payment=payment,
        settlement=None,
        existing_payments_for_order=[payment],
    )

    assert status == "FEE_DISCREPANCY"
    assert checks["amount_matched"] is True
    assert checks["fee_matched"] is False
    assert exposure == abs(Decimal("236.00") - Decimal("350.00"))


@pytest.mark.asyncio
async def test_reconciliation_duplicate_payments():
    now = datetime.now(timezone.utc)
    ws_id = uuid.uuid4()
    order_id = "order_TEST_DUP"

    ledger = MerchantLedgerEntry(
        workspace_id=ws_id,
        order_id=order_id,
        expected_amount=Decimal("2500.00"),
        expected_currency="INR",
        expected_fee=Decimal("59.00"),
        expected_tax=Decimal("9.00"),
        expected_net_amount=Decimal("2441.00"),
        expected_status="captured",
        transaction_date=now - timedelta(days=1),
    )

    pay1 = CanonicalTransaction(
        workspace_id=ws_id,
        source="razorpay_payment",
        external_id="pay_1",
        order_id=order_id,
        amount=Decimal("2500.00"),
        currency="INR",
        fee=Decimal("59.00"),
        tax=Decimal("9.00"),
        net_amount=Decimal("2441.00"),
        status="captured",
        transaction_time=now - timedelta(days=1),
    )
    pay2 = CanonicalTransaction(
        workspace_id=ws_id,
        source="razorpay_payment",
        external_id="pay_2",
        order_id=order_id,
        amount=Decimal("2500.00"),
        currency="INR",
        fee=Decimal("59.00"),
        tax=Decimal("9.00"),
        net_amount=Decimal("2441.00"),
        status="captured",
        transaction_time=now - timedelta(days=1),
    )

    status, amt_delta, fee_delta, checks, priority, exposure = ReconciliationService.evaluate_match(
        ledger=ledger,
        payment=pay1,
        settlement=None,
        existing_payments_for_order=[pay1, pay2],
    )

    assert status == "DUPLICATE"
    assert checks["is_duplicate"] is True
    assert exposure == Decimal("2500.00")  # Over-collected amount
