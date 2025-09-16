from __future__ import annotations
import csv, datetime, uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from .models import Payment
from ..config.mapping_model import MappingConfig

def _auto_e2e() -> str:
    # Simple unique-ish E2E id
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"E2E-{ts}-{uuid.uuid4().hex[:6].upper()}"

def load_payments_from_csv(path: Path, cfg: MappingConfig) -> list[Payment]:
    payments: list[Payment] = []
    with path.open("r", newline="", encoding=cfg.csv.encoding) as f:
        reader = csv.DictReader(f, delimiter=cfg.csv.delimiter)
        for i, row in enumerate(reader, start=1):
            # Required fields
            creditor_name = row.get(cfg.map.creditor_name, "").strip()
            creditor_iban = row.get(cfg.map.creditor_iban, "").replace(" ", "")
            amount_str = row.get(cfg.map.amount, "").replace(",", ".")
            try:
                amount = Decimal(amount_str)
            except (InvalidOperation, ValueError):
                raise ValueError(f"Row {i}: invalid amount '{amount_str}'")

            if not creditor_name or not creditor_iban or not amount:
                raise ValueError(f"Row {i}: missing required fields")

            payment = Payment(
                end_to_end_id=(row.get(cfg.map.end_to_end_id).strip() if cfg.map.end_to_end_id and row.get(cfg.map.end_to_end_id) else _auto_e2e()),
                creditor_name=creditor_name,
                creditor_iban=creditor_iban,
                creditor_bic=(row.get(cfg.map.creditor_bic).strip() if cfg.map.creditor_bic and row.get(cfg.map.creditor_bic) else None),
                amount=amount,
                currency=(row.get(cfg.map.currency).strip() if cfg.map.currency and row.get(cfg.map.currency) else cfg.defaults.currency),
                remittance_information=(row.get(cfg.map.remittance_information).strip() if cfg.map.remittance_information and row.get(cfg.map.remittance_information) else None),
            )
            payments.append(payment)
    if not payments:
        raise ValueError("No payments found in CSV")
    return payments
