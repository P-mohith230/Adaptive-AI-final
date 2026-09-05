
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.workspace_context import WorkspaceContext, current_workspace, current_writable_workspace
from app.integrations.razorpay.client import RazorpayClient
from app.integrations.razorpay.normalizer import RazorpayNormalizer
from app.models.canonical_transaction import CanonicalTransaction
from app.models.merchant_ledger import MerchantLedgerEntry
from app.schemas.merchant_ledger import MerchantLedgerEntryCreate, MerchantLedgerEntryRead

router = APIRouter(prefix="/api/ledger", tags=["merchant-ledger"])


@router.get("/entries", response_model=list[MerchantLedgerEntryRead])
async def list_ledger_entries(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Lists merchant internal expected ledger entries."""
    res = await session.execute(
        select(MerchantLedgerEntry)
        .where(MerchantLedgerEntry.workspace_id == ctx.id)
        .order_by(desc(MerchantLedgerEntry.transaction_date))
        .limit(limit)
        .offset(offset)
    )
    return list(res.scalars().all())


@router.post("/entries", response_model=MerchantLedgerEntryRead)
async def create_ledger_entry(
    payload: MerchantLedgerEntryCreate,
    ctx: WorkspaceContext = Depends(current_writable_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Creates a new expected order in the merchant internal ledger."""
    entry = MerchantLedgerEntry(
        workspace_id=ctx.id,
        order_id=payload.order_id,
        invoice_id=payload.invoice_id,
        customer_reference=payload.customer_reference,
        expected_amount=payload.expected_amount,
        expected_currency=payload.expected_currency,
        expected_fee=payload.expected_fee,
        expected_tax=payload.expected_tax,
        expected_net_amount=payload.expected_net_amount,
        expected_status=payload.expected_status,
        transaction_date=payload.transaction_date,
        source=payload.source,
        metadata_json=payload.metadata_json or {},
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.post("/sync-razorpay")
async def sync_razorpay_gateway_records(
    ctx: WorkspaceContext = Depends(current_writable_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Connects to Razorpay API and synchronizes live test-mode payments and settlements."""
    client = RazorpayClient()
    synced_payments = 0
    synced_settlements = 0

    try:
        raw_payments = await client.fetch_payments(count=50)
        for raw_p in raw_payments:
            ext_id = raw_p.get("id")
            if not ext_id:
                continue
            existing = await session.scalar(
                select(CanonicalTransaction).where(
                    CanonicalTransaction.workspace_id == ctx.id,
                    CanonicalTransaction.external_id == ext_id,
                )
            )
            if not existing:
                canonical = RazorpayNormalizer.normalize_payment(raw_p, ctx.id)
                session.add(canonical)
                synced_payments += 1

        raw_settlements = await client.fetch_settlements(count=20)
        for raw_s in raw_settlements:
            ext_id = raw_s.get("id")
            if not ext_id:
                continue
            existing = await session.scalar(
                select(CanonicalTransaction).where(
                    CanonicalTransaction.workspace_id == ctx.id,
                    CanonicalTransaction.external_id == ext_id,
                )
            )
            if not existing:
                canonical = RazorpayNormalizer.normalize_settlement(raw_s, ctx.id)
                session.add(canonical)
                synced_settlements += 1

        await session.commit()
        return {
            "status": "success",
            "is_test_mode": client.is_test_mode,
            "synced_payments": synced_payments,
            "synced_settlements": synced_settlements,
            "message": f"Synchronized {synced_payments} payments and {synced_settlements} settlements from Razorpay",
        }
    except Exception as exc:
        return {
            "status": "partial_success",
            "is_test_mode": client.is_test_mode,
            "synced_payments": synced_payments,
            "synced_settlements": synced_settlements,
            "warning": f"Razorpay API call notice: {str(exc)}. Test mode synthetic records remain available.",
        }
