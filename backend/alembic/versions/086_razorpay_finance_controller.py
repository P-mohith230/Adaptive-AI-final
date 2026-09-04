"""Razorpay Track 04 AI Finance Controller tables

Revision ID: 086
Revises: 085
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "086"
down_revision: Union[str, None] = "085"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Merchant Expected Ledger
    op.create_table(
        "merchant_ledger_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", sa.String(100), nullable=False),
        sa.Column("invoice_id", sa.String(100), nullable=True),
        sa.Column("customer_reference", sa.String(255), nullable=True),
        sa.Column("expected_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("expected_currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("expected_fee", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("expected_tax", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("expected_net_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("expected_status", sa.String(30), nullable=False, server_default="captured"),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="merchant_erp"),
        sa.Column("metadata_json", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_merchant_ledger_entries_workspace_id", "merchant_ledger_entries", ["workspace_id"])
    op.create_index("ix_merchant_ledger_entries_order_id", "merchant_ledger_entries", ["order_id"])

    # 2. Canonical Normalized Financial Transactions
    op.create_table(
        "canonical_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("payment_id", sa.String(100), nullable=True),
        sa.Column("order_id", sa.String(100), nullable=True),
        sa.Column("settlement_id", sa.String(100), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("fee", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("tax", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("net_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("transaction_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("settlement_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_canonical_transactions_workspace_id", "canonical_transactions", ["workspace_id"])
    op.create_index("ix_canonical_transactions_external_id", "canonical_transactions", ["external_id"])
    op.create_index("ix_canonical_transactions_payment_id", "canonical_transactions", ["payment_id"])
    op.create_index("ix_canonical_transactions_order_id", "canonical_transactions", ["order_id"])
    op.create_index("ix_canonical_transactions_settlement_id", "canonical_transactions", ["settlement_id"])

    # 3. Reconciliation Batches
    op.create_table(
        "reconciliation_batches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_code", sa.String(60), nullable=False),
        sa.Column("dataset_type", sa.String(30), nullable=False, server_default="synthetic_evaluation"),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("matched_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("auto_reconciled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_assisted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unresolved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("match_rate", sa.Numeric(5, 4), nullable=False, server_default="0.0000"),
        sa.Column("precision_rate", sa.Numeric(5, 4), nullable=False, server_default="0.0000"),
        sa.Column("recall_rate", sa.Numeric(5, 4), nullable=False, server_default="0.0000"),
        sa.Column("financial_exposure", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("throughput_rps", sa.Numeric(8, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reconciliation_batches_workspace_id", "reconciliation_batches", ["workspace_id"])
    op.create_index("ix_reconciliation_batches_batch_code", "reconciliation_batches", ["batch_code"], unique=True)

    # 4. Reconciliation Records
    op.create_table(
        "reconciliation_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_id", UUID(as_uuid=True), sa.ForeignKey("reconciliation_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("merchant_ledger_id", UUID(as_uuid=True), sa.ForeignKey("merchant_ledger_entries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payment_transaction_id", UUID(as_uuid=True), sa.ForeignKey("canonical_transactions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("settlement_transaction_id", UUID(as_uuid=True), sa.ForeignKey("canonical_transactions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("order_id", sa.String(100), nullable=True),
        sa.Column("payment_id", sa.String(100), nullable=True),
        sa.Column("settlement_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("amount_delta", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("fee_delta", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("checks_json", JSONB, nullable=True, server_default="{}"),
        sa.Column("priority_score", sa.Numeric(8, 2), nullable=False, server_default="0.00"),
        sa.Column("financial_impact", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("resolution_status", sa.String(20), nullable=False, server_default="unneeded"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reconciliation_records_workspace_id", "reconciliation_records", ["workspace_id"])
    op.create_index("ix_reconciliation_records_batch_id", "reconciliation_records", ["batch_id"])
    op.create_index("ix_reconciliation_records_status", "reconciliation_records", ["status"])
    op.create_index("ix_reconciliation_records_order_id", "reconciliation_records", ["order_id"])
    op.create_index("ix_reconciliation_records_payment_id", "reconciliation_records", ["payment_id"])
    op.create_index("ix_reconciliation_records_settlement_id", "reconciliation_records", ["settlement_id"])

    # 5. Reconciliation Exceptions (AI Investigation)
    op.create_table(
        "reconciliation_exceptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("record_id", UUID(as_uuid=True), sa.ForeignKey("reconciliation_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_classification", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_json", JSONB, nullable=True, server_default="{}"),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="PENDING_REVIEW"),
        sa.Column("reviewed_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reconciliation_exceptions_record_id", "reconciliation_exceptions", ["record_id"], unique=True)
    op.create_index("ix_reconciliation_exceptions_workspace_id", "reconciliation_exceptions", ["workspace_id"])

    # 6. Reconciliation Audit Logs (Immutable)
    op.create_table(
        "reconciliation_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("record_id", UUID(as_uuid=True), sa.ForeignKey("reconciliation_records.id", ondelete="CASCADE"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_json", JSONB, nullable=True, server_default="{}"),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("agent_version", sa.String(30), nullable=False, server_default="v1.0-track04"),
        sa.Column("previous_state", sa.String(50), nullable=True),
        sa.Column("new_state", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reconciliation_audit_logs_workspace_id", "reconciliation_audit_logs", ["workspace_id"])
    op.create_index("ix_reconciliation_audit_logs_record_id", "reconciliation_audit_logs", ["record_id"])

    # 7. Razorpay Webhook Idempotency Events
    op.create_table(
        "razorpay_webhook_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_id", sa.String(100), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("signature_verified", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("payload_json", JSONB, nullable=True, server_default="{}"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_razorpay_webhook_events_workspace_id", "razorpay_webhook_events", ["workspace_id"])
    op.create_index("ix_razorpay_webhook_events_event_id", "razorpay_webhook_events", ["event_id"], unique=True)
    op.create_index("ix_razorpay_webhook_events_event_type", "razorpay_webhook_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("razorpay_webhook_events")
    op.drop_table("reconciliation_audit_logs")
    op.drop_table("reconciliation_exceptions")
    op.drop_table("reconciliation_records")
    op.drop_table("reconciliation_batches")
    op.drop_table("canonical_transactions")
    op.drop_table("merchant_ledger_entries")
