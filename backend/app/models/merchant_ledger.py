import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MerchantLedgerEntry(Base):
    """Merchant's internal expected ledger entry (orders/invoices).

    Represents what the merchant expected to happen before payment gateway
    processing and bank settlement.
    """

    __tablename__ = "merchant_ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    invoice_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    expected_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    expected_currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR", nullable=False)
    expected_fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    expected_tax: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    expected_net_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    expected_status: Mapped[str] = mapped_column(String(30), default="captured", server_default="captured", nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="merchant_erp", server_default="merchant_erp", nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
