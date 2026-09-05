from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reconciliation import (
    ReconciliationBatch,
    ReconciliationRecord,
)
from mcp_server.auth import CallContext
from mcp_server.registry import tool
from mcp_server.tools._helpers import resolve_workspace_id


@tool(
    name="reconciliation_kpi",
    description=(
        "Get high-level financial control metrics for the current merchant workspace: "
        "total records processed, verified match rate (percentage), total financial exposure (unreconciled INR), "
        "auto-reconciled count, AI-assisted count, and unresolved exceptions count."
    ),
    parameters={
        "type": "object",
        "properties": {
            "workspace_id": {"type": "string", "format": "uuid", "description": "Optional workspace ID override"},
        },
        "additionalProperties": False,
    },
    tags=["read", "finance_controller"],
)
async def reconciliation_kpi(
    *,
    session: AsyncSession,
    ctx: CallContext,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    ws_id = resolve_workspace_id(ctx, workspace_id)
    latest_batch = await session.scalar(
        select(ReconciliationBatch)
        .where(ReconciliationBatch.workspace_id == ws_id)
        .order_by(desc(ReconciliationBatch.created_at))
        .limit(1)
    )

    if not latest_batch:
        return {
            "status": "no_data",
            "message": "No reconciliation batches executed yet for this workspace. Run demo reconciliation first.",
        }

    return {
        "batch_code": latest_batch.batch_code,
        "total_records": latest_batch.total_records,
        "matched_records": latest_batch.matched_records,
        "auto_reconciled": latest_batch.auto_reconciled,
        "ai_assisted": latest_batch.ai_assisted,
        "unresolved_exceptions": latest_batch.unresolved_count,
        "match_rate": f"{float(latest_batch.match_rate) * 100:.2f}%",
        "total_financial_exposure": f"₹{latest_batch.financial_exposure:,.2f}",
        "duration_ms": latest_batch.duration_ms,
        "throughput_records_per_second": float(latest_batch.throughput_rps),
        "reconciled_at": latest_batch.created_at.isoformat(),
    }


@tool(
    name="get_highest_risk_exceptions",
    description=(
        "Retrieve the highest-risk financial exceptions ranked strictly by calculated financial exposure (INR). "
        "Answers questions like 'Which exception has the highest financial impact?' or 'Show me high-risk exceptions'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
            "workspace_id": {"type": "string", "format": "uuid"},
        },
        "additionalProperties": False,
    },
    tags=["read", "finance_controller"],
)
async def get_highest_risk_exceptions(
    *,
    session: AsyncSession,
    ctx: CallContext,
    limit: int = 5,
    workspace_id: str | None = None,
) -> list[dict[str, Any]]:
    ws_id = resolve_workspace_id(ctx, workspace_id)

    res = await session.execute(
        select(ReconciliationRecord)
        .options(selectinload(ReconciliationRecord.exception))
        .where(
            ReconciliationRecord.workspace_id == ws_id,
            ReconciliationRecord.status != "AUTO_RECONCILED",
        )
        .order_by(desc(ReconciliationRecord.financial_impact))
        .limit(limit)
    )
    records = list(res.scalars().all())

    output: list[dict[str, Any]] = []
    for r in records:
        exc = r.exception
        output.append({
            "record_id": str(r.id),
            "order_id": r.order_id,
            "payment_id": r.payment_id,
            "status": r.status,
            "financial_exposure": f"₹{r.financial_impact:,.2f}",
            "amount_delta": f"₹{r.amount_delta:,.2f}",
            "priority_score": float(r.priority_score),
            "ai_classification": exc.ai_classification if exc else r.status,
            "ai_confidence": f"{float(exc.confidence) * 100:.1f}%" if exc else "N/A",
            "reason": exc.reason if exc else "Discrepancy detected",
            "recommendation": exc.recommendation if exc else "Review record",
            "resolution_status": r.resolution_status,
        })
    return output


@tool(
    name="explain_transaction_discrepancy",
    description=(
        "Answers 'Why did this transaction not reconcile?' for a specific order ID or payment ID. "
        "Returns verified check results, exact numerical differences, and structured evidence references."
    ),
    parameters={
        "type": "object",
        "properties": {
            "identifier": {
                "type": "string",
                "description": "Order ID (e.g. order_DEMO_1012) or Payment ID (e.g. pay_DEMO_xxx)",
            },
            "workspace_id": {"type": "string", "format": "uuid"},
        },
        "required": ["identifier"],
        "additionalProperties": False,
    },
    tags=["read", "finance_controller"],
)
async def explain_transaction_discrepancy(
    *,
    session: AsyncSession,
    ctx: CallContext,
    identifier: str,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    ws_id = resolve_workspace_id(ctx, workspace_id)

    res = await session.scalar(
        select(ReconciliationRecord)
        .options(selectinload(ReconciliationRecord.exception))
        .where(
            ReconciliationRecord.workspace_id == ws_id,
            (ReconciliationRecord.order_id == identifier) | (ReconciliationRecord.payment_id == identifier),
        )
        .limit(1)
    )

    if not res:
        return {
            "found": False,
            "message": f"No reconciliation record found for identifier '{identifier}'.",
        }

    exc = res.exception
    return {
        "found": True,
        "record_id": str(res.id),
        "order_id": res.order_id,
        "payment_id": res.payment_id,
        "settlement_id": res.settlement_id,
        "status": res.status,
        "financial_exposure": f"₹{res.financial_impact:,.2f}",
        "amount_difference": f"₹{res.amount_delta:,.2f}",
        "fee_difference": f"₹{res.fee_delta:,.2f}",
        "checks_performed": res.checks_json or {},
        "ai_diagnosis": {
            "classification": exc.ai_classification if exc else res.status,
            "confidence": f"{float(exc.confidence) * 100:.1f}%" if exc else "100%",
            "reason": exc.reason if exc else "Standard verification",
            "recommendation": exc.recommendation if exc else "No action required",
            "evidence": (exc.evidence_json or {}).get("items", []) if exc else [],
        },
        "resolution_status": res.resolution_status,
    }
