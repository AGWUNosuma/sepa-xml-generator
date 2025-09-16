from __future__ import annotations
from lxml import etree
from pathlib import Path
from typing import Tuple, List

def validate_with_xsd(xml_path: Path, xsd_path: Path) -> tuple[bool, list[str]]:
    """Validate the XML against the given XSD. Returns (ok, errors)."""
    try:
        xml_doc = etree.parse(str(xml_path))
        xsd_doc = etree.parse(str(xsd_path))
        schema = etree.XMLSchema(xsd_doc)
        ok = schema.validate(xml_doc)
        if ok:
            return True, []
        else:
            errors = [str(e) for e in schema.error_log]
            return False, errors
    except Exception as e:
        return False, [str(e)]
