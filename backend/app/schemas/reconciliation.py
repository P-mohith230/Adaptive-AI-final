import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ReconciliationBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    batch_code: str
    dataset_type: str
    total_records: int
    matched_records: int
    auto_reconciled: int
    ai_assisted: int
    unresolved_count: int
    match_rate: Decimal
    precision_rate: Decimal
    recall_rate: Decimal
    financial_exposure: Decimal
    duration_ms: int
    throughput_rps: Decimal
    status: str
    created_at: datetime


class ReconciliationExceptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    record_id: uuid.UUID
    ai_classification: str
    confidence: Decimal
    reason: str
    evidence_json: Optional[dict[str, Any]] = None
    recommendation: str
    review_status: str
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class ReconciliationRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_id: uuid.UUID
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    settlement_id: Optional[str] = None
    status: str
    amount_delta: Decimal
    fee_delta: Decimal
    checks_json: Optional[dict[str, Any]] = None
    priority_score: Decimal
    financial_impact: Decimal
    resolution_status: str
    created_at: datetime
    exception: Optional[ReconciliationExceptionRead] = None


class ReconciliationAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    record_id: Optional[uuid.UUID] = None
    action: str
    actor: str
    decision: str
    reason: str
    evidence_json: Optional[dict[str, Any]] = None
    confidence: Optional[Decimal] = None
    agent_version: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    created_at: datetime


class TransactionDecisionCard(BaseModel):
    """Payload for the signature 'Why did this not reconcile?' Transaction Decision Card."""

    record_id: uuid.UUID
    order_id: Optional[str]
    payment_id: Optional[str]
    settlement_id: Optional[str]
    status: str
    expected_amount: Decimal
    actual_amount: Decimal
    amount_variance: Decimal
    expected_fee: Decimal
    actual_fee: Decimal
    fee_variance: Decimal
    financial_exposure: Decimal
    checks: dict[str, bool]
    ai_classification: str
    ai_confidence: Decimal
    ai_reason: str
    ai_recommendation: str
    evidence_items: list[dict[str, Any]]
    resolution_status: str


class ReviewActionPayload(BaseModel):
    action: str  # "APPROVE", "REJECT", "RESOLVE"
    notes: Optional[str] = None


class ReconciliationKPISummary(BaseModel):
    total_records: int
    matched_records: int
    auto_reconciled: int
    ai_assisted: int
    unresolved_count: int
    match_rate: Decimal
    total_financial_exposure: Decimal
    latest_duration_ms: int
    latest_throughput_rps: Decimal
    high_priority_exceptions_count: int
    dataset_type: str
    last_reconciled_at: Optional[datetime] = None
