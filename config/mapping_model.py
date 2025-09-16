from __future__ import annotations
from pydantic import BaseModel, Field
from pathlib import Path
import yaml

class CSVConfig(BaseModel):
    delimiter: str = ","
    encoding: str = "utf-8"

class Defaults(BaseModel):
    debtor_name: str = "Your Company GmbH"
    debtor_iban: str = "DE00 0000 0000 0000 0000 00"
    debtor_bic: str | None = None
    pain_version: str = "pain.001.001.03"
    currency: str = "EUR"

class Mapping(BaseModel):
    creditor_name: str = "name"
    creditor_iban: str = "iban"
    creditor_bic: str | None = "bic"
    amount: str = "amount"
    currency: str | None = "currency"
    remittance_information: str | None = "remittance"
    end_to_end_id: str | None = "e2e_id"

class MappingConfig(BaseModel):
    csv: CSVConfig = Field(default_factory=CSVConfig)
    defaults: Defaults = Field(default_factory=Defaults)
    map: Mapping = Field(default_factory=Mapping)

def load_mapping(path: Path) -> MappingConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return MappingConfig.model_validate(data)
