import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CanonicalTransaction(Base):
    """Canonical representation of financial transactions across Razorpay and bank systems.

    Normalizes payments, settlements, refunds, and bank statements into a common schema.
    """

    __tablename__ = "canonical_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # razorpay_payment, razorpay_settlement, bank_payout, synthetic
    external_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    payment_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    settlement_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR", nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False)  # captured, settled, refunded, failed
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # upi, card, netbanking
    transaction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    settlement_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
