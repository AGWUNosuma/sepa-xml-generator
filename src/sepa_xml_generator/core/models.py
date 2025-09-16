from __future__ import annotations
from pydantic import BaseModel, Field
from decimal import Decimal

class Payment(BaseModel):
    end_to_end_id: str = Field(..., description="Unique ID per transaction")
    creditor_name: str
    creditor_iban: str
    creditor_bic: str | None = None
    amount: Decimal
    currency: str = "EUR"
    remittance_information: str | None = None
