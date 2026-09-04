import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class MerchantLedgerEntryBase(BaseModel):
    order_id: str
    invoice_id: Optional[str] = None
    customer_reference: Optional[str] = None
    expected_amount: Decimal
    expected_currency: str = "INR"
    expected_fee: Decimal = Decimal("0.00")
    expected_tax: Decimal = Decimal("0.00")
    expected_net_amount: Decimal
    expected_status: str = "captured"
    transaction_date: datetime
    source: str = "merchant_erp"
    metadata_json: Optional[dict[str, Any]] = None


class MerchantLedgerEntryCreate(MerchantLedgerEntryBase):
    pass


class MerchantLedgerEntryRead(MerchantLedgerEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
