from pathlib import Path
from sepa_xml_generator.config.mapping_model import load_mapping
from sepa_xml_generator.core.csv_loader import load_payments_from_csv
from sepa_xml_generator.sepa.builder import build_pain_001_xml

def test_smoke(tmp_path: Path):
    mapping = load_mapping(Path("data/mapping.sample.yaml"))
    payments = load_payments_from_csv(Path("data/sample.csv"), mapping)
    xml_bytes = build_pain_001_xml(payments, mapping.defaults.debtor_name, mapping.defaults.debtor_iban, mapping.defaults.debtor_bic)
    out = tmp_path / "out.xml"
    out.write_bytes(xml_bytes)
    assert out.exists() and out.stat().st_size > 0
