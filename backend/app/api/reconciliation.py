import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.workspace_context import WorkspaceContext, current_workspace
from app.models.canonical_transaction import CanonicalTransaction
from app.models.merchant_ledger import MerchantLedgerEntry
from app.models.reconciliation import (
    ReconciliationAuditLog,
    ReconciliationBatch,
    ReconciliationRecord,
)
from app.schemas.reconciliation import (
    ReconciliationAuditLogRead,
    ReconciliationBatchRead,
    ReconciliationKPISummary,
    ReconciliationRecordRead,
    ReviewActionPayload,
    TransactionDecisionCard,
)
from app.services.csv_generator import CSVReconciliationGenerator
from app.services.evaluation_service import EvaluationService
from app.services.reconciliation_ledger_bridge import ReconciliationLedgerBridge
from app.services.settlement_qa_service import SettlementQAService

class QAQueryPayload(BaseModel):
    question: str
    history: Optional[List[Dict[str, Any]]] = None

router = APIRouter(prefix="/api/reconciliation", tags=["reconciliation"])


@router.post("/demo-run", response_model=ReconciliationBatchRead)
async def run_demo_reconciliation(
    total_records: int = Query(100, ge=50, le=250, description="Batch size for evaluation run"),
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Executes full end-to-end Track 04 finance loop:

    1. Seed controlled synthetic dataset with ground-truth anomalies
    2. Deterministic 3-way reconciliation
    3. AI Exception Investigation & evidence synthesis
    4. Dynamically compute all KPIs and return the completed batch.
    """
    ctx.require_write()
    batch = await EvaluationService.run_full_demo_loop(
        session=session,
        workspace_id=ctx.id,
        user_id=ctx.user_id,
        total_records=total_records,
    )
    return batch


@router.get("/kpi", response_model=ReconciliationKPISummary)
async def get_reconciliation_kpi(
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Fetches dynamically computed KPI summary for the Finance Control Center."""
    # Find latest batch
    latest_batch = await session.scalar(
        select(ReconciliationBatch)
        .where(ReconciliationBatch.workspace_id == ctx.id)
        .order_by(desc(ReconciliationBatch.created_at))
        .limit(1)
    )

    if not latest_batch:
        return ReconciliationKPISummary(
            total_records=0,
            matched_records=0,
            auto_reconciled=0,
            ai_assisted=0,
            unresolved_count=0,
            match_rate=Decimal("0.0000"),
            total_financial_exposure=Decimal("0.00"),
            latest_duration_ms=0,
            latest_throughput_rps=Decimal("0.00"),
            high_priority_exceptions_count=0,
            dataset_type="none",
            last_reconciled_at=None,
        )

    # Count high-priority exceptions (priority > 1000)
    high_priority_count = await session.scalar(
        select(func.count(ReconciliationRecord.id))
        .where(
            ReconciliationRecord.batch_id == latest_batch.id,
            ReconciliationRecord.priority_score >= Decimal("1000.00"),
            ReconciliationRecord.status != "AUTO_RECONCILED",
        )
    ) or 0

    return ReconciliationKPISummary(
        total_records=latest_batch.total_records,
        matched_records=latest_batch.matched_records,
        auto_reconciled=latest_batch.auto_reconciled,
        ai_assisted=latest_batch.ai_assisted,
        unresolved_count=latest_batch.unresolved_count,
        match_rate=latest_batch.match_rate,
        total_financial_exposure=latest_batch.financial_exposure,
        latest_duration_ms=latest_batch.duration_ms,
        latest_throughput_rps=latest_batch.throughput_rps,
        high_priority_exceptions_count=high_priority_count,
        dataset_type=latest_batch.dataset_type,
        last_reconciled_at=latest_batch.created_at,
    )


@router.get("/batches", response_model=list[ReconciliationBatchRead])
async def list_batches(
    limit: int = Query(20, ge=1, le=100),
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Lists historical reconciliation batches."""
    res = await session.execute(
        select(ReconciliationBatch)
        .where(ReconciliationBatch.workspace_id == ctx.id)
        .order_by(desc(ReconciliationBatch.created_at))
        .limit(limit)
    )
    return list(res.scalars().all())


@router.get("/records", response_model=list[ReconciliationRecordRead])
async def list_reconciliation_records(
    batch_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_min: Optional[Decimal] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Lists reconciliation records with filtering by status and priority."""
    query = (
        select(ReconciliationRecord)
        .options(selectinload(ReconciliationRecord.exception))
        .where(ReconciliationRecord.workspace_id == ctx.id)
    )

    if batch_id:
        query = query.where(ReconciliationRecord.batch_id == batch_id)
    else:
        # Default to latest batch
        latest_batch_id = await session.scalar(
            select(ReconciliationBatch.id)
            .where(ReconciliationBatch.workspace_id == ctx.id)
            .order_by(desc(ReconciliationBatch.created_at))
            .limit(1)
        )
        if latest_batch_id:
            query = query.where(ReconciliationRecord.batch_id == latest_batch_id)

    if status_filter:
        query = query.where(ReconciliationRecord.status == status_filter)
    if priority_min is not None:
        query = query.where(ReconciliationRecord.priority_score >= priority_min)

    query = query.order_by(desc(ReconciliationRecord.priority_score), desc(ReconciliationRecord.created_at))
    query = query.limit(limit).offset(offset)

    res = await session.execute(query)
    return list(res.scalars().all())


@router.get("/records/{record_id}/decision-card", response_model=TransactionDecisionCard)
async def get_transaction_decision_card(
    record_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Signature endpoint: returns the complete 'Why did this not reconcile?' Decision Card payload."""
    rec = await session.scalar(
        select(ReconciliationRecord)
        .options(selectinload(ReconciliationRecord.exception))
        .where(
            ReconciliationRecord.id == record_id,
            ReconciliationRecord.workspace_id == ctx.id,
        )
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Reconciliation record not found")

    ledger = await session.get(MerchantLedgerEntry, rec.merchant_ledger_id) if rec.merchant_ledger_id else None
    payment = await session.get(CanonicalTransaction, rec.payment_transaction_id) if rec.payment_transaction_id else None

    expected_amt = ledger.expected_amount if ledger else Decimal("0.00")
    actual_amt = payment.amount if payment else Decimal("0.00")
    amt_diff = rec.amount_delta

    expected_fee = ledger.expected_fee if ledger else Decimal("0.00")
    actual_fee = payment.fee if payment else Decimal("0.00")
    fee_diff = rec.fee_delta

    checks_raw = rec.checks_json or {}
    checks = {
        "order_matched": bool(checks_raw.get("order_matched", False)),
        "payment_matched": bool(checks_raw.get("payment_matched", False)),
        "currency_matched": bool(checks_raw.get("currency_matched", False)),
        "amount_matched": bool(checks_raw.get("amount_matched", False)),
        "fee_matched": bool(checks_raw.get("fee_matched", False)),
        "settlement_found": bool(checks_raw.get("settlement_found", False)),
    }

    exception = rec.exception
    ai_classification = exception.ai_classification if exception else rec.status
    ai_confidence = exception.confidence if exception else Decimal("1.0000")
    ai_reason = exception.reason if exception else "Standard automated reconciliation completed successfully."
    ai_rec = exception.recommendation if exception else "Transaction matches expected ledger. No action required."
    evidence_items = (exception.evidence_json or {}).get("items", []) if exception else []

    return TransactionDecisionCard(
        record_id=rec.id,
        order_id=rec.order_id,
        payment_id=rec.payment_id,
        settlement_id=rec.settlement_id,
        status=rec.status,
        expected_amount=expected_amt,
        actual_amount=actual_amt,
        amount_variance=amt_diff,
        expected_fee=expected_fee,
        actual_fee=actual_fee,
        fee_variance=fee_diff,
        financial_exposure=rec.financial_impact,
        checks=checks,
        ai_classification=ai_classification,
        ai_confidence=ai_confidence,
        ai_reason=ai_reason,
        ai_recommendation=ai_rec,
        evidence_items=evidence_items,
        resolution_status=rec.resolution_status,
    )


@router.post("/records/{record_id}/review", response_model=ReconciliationRecordRead)
async def review_reconciliation_record(
    record_id: uuid.UUID,
    payload: ReviewActionPayload,
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Human-in-the-loop approval or rejection of an AI proposal.

    Appends an immutable audit entry and updates record resolution state.
    """
    ctx.require_write()
    rec = await session.scalar(
        select(ReconciliationRecord)
        .options(selectinload(ReconciliationRecord.exception))
        .where(
            ReconciliationRecord.id == record_id,
            ReconciliationRecord.workspace_id == ctx.id,
        )
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Reconciliation record not found")

    action_normalized = payload.action.upper()
    if action_normalized not in ("APPROVE", "REJECT", "RESOLVE"):
        raise HTTPException(status_code=400, detail="Invalid action. Use APPROVE, REJECT, or RESOLVE")

    previous_state = rec.resolution_status
    new_state = "approved" if action_normalized == "APPROVE" else ("rejected" if action_normalized == "REJECT" else "manually_resolved")
    rec.resolution_status = new_state

    if rec.exception:
        rec.exception.review_status = action_normalized
        rec.exception.reviewed_by_user_id = ctx.user_id
        rec.exception.reviewed_at = datetime.now(timezone.utc)

    # Immutable Audit Log
    audit = ReconciliationAuditLog(
        workspace_id=ctx.id,
        record_id=rec.id,
        action=f"human_{action_normalized.lower()}",
        actor=f"user:{ctx.user.email}",
        decision=f"HUMAN_{action_normalized}",
        reason=payload.notes or f"Human reviewer {action_normalized.lower()}d AI recommendation for {rec.order_id}",
        evidence_json={"record_id": str(rec.id), "notes": payload.notes},
        confidence=Decimal("1.0000"),
        previous_state=previous_state,
        new_state=new_state,
    )
    session.add(audit)
    await session.commit()
    await session.refresh(rec)
    return rec


@router.get("/audit-log", response_model=list[ReconciliationAuditLogRead])
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Queries the immutable audit log for financial compliance."""
    res = await session.execute(
        select(ReconciliationAuditLog)
        .where(ReconciliationAuditLog.workspace_id == ctx.id)
        .order_by(desc(ReconciliationAuditLog.created_at))
        .limit(limit)
    )
    return list(res.scalars().all())


@router.get("/cash-forecast")
async def get_cash_position_forecast(
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Calculates liquid cash, in-transit gateway float, trapped exposure, and 7-day projection."""
    return await ReconciliationLedgerBridge.calculate_cash_position_forecast(
        session=session,
        workspace_id=ctx.id,
    )


class ImportCsvBatchPayload(BaseModel):
    orders_csv: str
    payments_csv: str
    bank_csv: Optional[str] = None


@router.get("/sample-csvs")
async def get_sample_csvs(
    total_records: int = Query(100, ge=10, le=500, description="Batch size for sample CSV generation"),
):
    """Returns downloadable sample CSV content for 3-way reconciliation testing."""
    orders_csv, payments_csv, bank_csv = CSVReconciliationGenerator.generate_csv_data(total_records=total_records)
    return {
        "merchant_orders_csv": orders_csv,
        "razorpay_payments_csv": payments_csv,
        "bank_settlement_csv": bank_csv,
    }


@router.post("/import-csv-batch")
async def import_csv_batch(
    payload: ImportCsvBatchPayload,
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Uploads and executes 3-way reconciliation across merchant orders, gateway payments, and bank settlements from JSON strings."""
    ctx.require_write()
    result = await CSVReconciliationGenerator.ingest_csv_batch(
        session=session,
        workspace_id=ctx.id,
        user_id=ctx.user_id,
        orders_csv_content=payload.orders_csv,
        payments_csv_content=payload.payments_csv,
        bank_csv_content=payload.bank_csv,
    )
    return result


@router.post("/upload-csv-batch")
async def upload_csv_batch(
    orders_file: UploadFile = File(...),
    payments_file: UploadFile = File(...),
    bank_file: Optional[UploadFile] = File(None),
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Uploads and executes 3-way reconciliation from uploaded CSV files."""
    ctx.require_write()
    orders_bytes = await orders_file.read()
    payments_bytes = await payments_file.read()
    bank_bytes = await bank_file.read() if bank_file else None

    orders_str = orders_bytes.decode("utf-8", errors="ignore")
    payments_str = payments_bytes.decode("utf-8", errors="ignore")
    bank_str = bank_bytes.decode("utf-8", errors="ignore") if bank_bytes else None

    result = await CSVReconciliationGenerator.ingest_csv_batch(
        session=session,
        workspace_id=ctx.id,
        user_id=ctx.user_id,
        orders_csv_content=orders_str,
        payments_csv_content=payments_str,
        bank_csv_content=bank_str,
    )
    return result


@router.post("/sync-ledger")
async def sync_latest_batch_to_ledger(
    batch_id: Optional[uuid.UUID] = None,
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Synchronizes a reconciliation batch into Securo's general ledger (Transactions and Accounts)."""
    ctx.require_write()
    target_batch_id = batch_id
    if not target_batch_id:
        target_batch_id = await session.scalar(
            select(ReconciliationBatch.id)
            .where(ReconciliationBatch.workspace_id == ctx.id)
            .order_by(desc(ReconciliationBatch.created_at))
            .limit(1)
        )
    if not target_batch_id:
        raise HTTPException(status_code=404, detail="No reconciliation batch found to sync")

    res = await ReconciliationLedgerBridge.sync_batch_to_securo_ledger(
        session=session,
        workspace_id=ctx.id,
        user_id=ctx.user_id,
        batch_id=target_batch_id,
    )
    return {"batch_id": str(target_batch_id), **res}


@router.post("/settlement-qa")
async def settlement_qa_query(
    payload: QAQueryPayload,
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Settlement Q&A Agent answering queries regarding payouts, MDR fees, discrepancies, and liquidity."""
    return await SettlementQAService.ask_settlement_agent(
        session=session,
        workspace_id=ctx.id,
        question=payload.question,
        history=payload.history,
    )

