import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReconciliationBatch(Base):
    """Execution batch for financial reconciliation (50+ records up to thousands).

    Stores batch configuration, performance metrics (duration, throughput),
    and verified evaluation accuracy.
    """

    __tablename__ = "reconciliation_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    batch_code: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    dataset_type: Mapped[str] = mapped_column(
        String(30), default="synthetic_evaluation", server_default="synthetic_evaluation", nullable=False
    )

    total_records: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    matched_records: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    auto_reconciled: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    ai_assisted: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    unresolved_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    match_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), server_default="0.0000", nullable=False)
    precision_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), server_default="0.0000", nullable=False)
    recall_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), server_default="0.0000", nullable=False)
    financial_exposure: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)

    duration_ms: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    throughput_rps: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", server_default="completed", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    records: Mapped[list["ReconciliationRecord"]] = relationship(
        "ReconciliationRecord", back_populates="batch", cascade="all, delete-orphan"
    )


class ReconciliationRecord(Base):
    """3-Way reconciliation record matching Merchant Ledger, Razorpay Gateway, and Bank Settlement."""

    __tablename__ = "reconciliation_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_batches.id", ondelete="CASCADE"), index=True
    )

    merchant_ledger_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchant_ledger_entries.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payment_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_transactions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    settlement_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_transactions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    order_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    payment_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    settlement_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    # Status: AUTO_RECONCILED, PARTIAL_MATCH, MISMATCH, DUPLICATE, MISSING_PAYMENT,
    # MISSING_SETTLEMENT, TIMING_DIFFERENCE, FEE_DISCREPANCY, REFUND_MISMATCH, UNRESOLVED
    status: Mapped[str] = mapped_column(String(30), index=True, nullable=False)

    amount_delta: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    fee_delta: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    checks_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    priority_score: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    financial_impact: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)

    # Resolution status: unneeded, pending, approved, rejected, manually_resolved
    resolution_status: Mapped[str] = mapped_column(String(20), default="unneeded", server_default="unneeded", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    batch: Mapped["ReconciliationBatch"] = relationship("ReconciliationBatch", back_populates="records")
    exception: Mapped[Optional["ReconciliationException"]] = relationship(
        "ReconciliationException", back_populates="record", uselist=False, cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["ReconciliationAuditLog"]] = relationship(
        "ReconciliationAuditLog", back_populates="record", cascade="all, delete-orphan"
    )


class ReconciliationException(Base):
    """AI investigation and diagnosis for non-auto-reconciled financial records."""

    __tablename__ = "reconciliation_exceptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_records.id", ondelete="CASCADE"), unique=True, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )

    ai_classification: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)  # 0.0000 - 1.0000
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)

    # Review status: PENDING_REVIEW, APPROVED, REJECTED, RESOLVED
    review_status: Mapped[str] = mapped_column(String(20), default="PENDING_REVIEW", server_default="PENDING_REVIEW", nullable=False)
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    record: Mapped["ReconciliationRecord"] = relationship("ReconciliationRecord", back_populates="exception")


class ReconciliationAuditLog(Base):
    """Immutable, append-only audit trail recording every state change and approval."""

    __tablename__ = "reconciliation_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    record_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_records.id", ondelete="CASCADE"), index=True, nullable=True
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False)  # deterministic_reconciliation, ai_investigation, human_approval, human_rejection
    actor: Mapped[str] = mapped_column(String(100), nullable=False)  # deterministic_engine, ai_controller_v1, user:<uuid>
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    agent_version: Mapped[str] = mapped_column(String(30), default="v1.0-track04", server_default="v1.0-track04", nullable=False)

    previous_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    record: Mapped[Optional["ReconciliationRecord"]] = relationship("ReconciliationRecord", back_populates="audit_logs")


class RazorpayWebhookEvent(Base):
    """Idempotency log for Razorpay webhooks to guarantee safe deduplication."""

    __tablename__ = "razorpay_webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True
    )
    event_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    signature_verified: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
