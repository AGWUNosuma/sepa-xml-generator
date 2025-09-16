from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Iterable
from lxml import etree
import datetime, uuid

from ..core.models import Payment

NSMAPS = {
    "pain.001.001.03": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03",
    "pain.001.001.09": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09",
}

def _ns(pain_version: str) -> str:
    try:
        return NSMAPS[pain_version]
    except KeyError:
        raise ValueError(f"Unsupported pain version: {pain_version}")

def build_pain_001_xml(
    payments: Iterable[Payment],
    debtor_name: str,
    debtor_iban: str,
    debtor_bic: str | None,
    pain_version: str = "pain.001.001.03",
) -> bytes:
    payments = list(payments)
    if not payments:
        raise ValueError("No payments")

    ns = _ns(pain_version)
    NSMAP = {None: ns}

    doc = etree.Element("Document", nsmap=NSMAP)
    ccti = etree.SubElement(doc, "CstmrCdtTrfInitn")

    # --- Group Header ---
    grp = etree.SubElement(ccti, "GrpHdr")
    msg_id = f"MSG-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    etree.SubElement(grp, "MsgId").text = msg_id
    etree.SubElement(grp, "CreDtTm").text = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    etree.SubElement(grp, "NbOfTxs").text = str(len(payments))
    ctrl_sum = sum((p.amount for p in payments), Decimal("0.00"))
    etree.SubElement(grp, "CtrlSum").text = f"{ctrl_sum:.2f}"
    initg = etree.SubElement(grp, "InitgPty")
    etree.SubElement(initg, "Nm").text = debtor_name

    # --- Payment Info (single batch for simplicity) ---
    pmt = etree.SubElement(ccti, "PmtInf")
    etree.SubElement(pmt, "PmtInfId").text = msg_id + "-B1"
    etree.SubElement(pmt, "PmtMtd").text = "TRF"
    etree.SubElement(pmt, "BtchBookg").text = "true"
    etree.SubElement(pmt, "NbOfTxs").text = str(len(payments))
    etree.SubElement(pmt, "CtrlSum").text = f"{ctrl_sum:.2f}"
    pmt_tp_inf = etree.SubElement(pmt, "PmtTpInf")
    svc_lvl = etree.SubElement(pmt_tp_inf, "SvcLvl")
    etree.SubElement(svc_lvl, "Cd").text = "SEPA"
    etree.SubElement(pmt, "ReqdExctnDt").text = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    dbtr = etree.SubElement(pmt, "Dbtr")
    etree.SubElement(dbtr, "Nm").text = debtor_name
    dbtr_acct = etree.SubElement(pmt, "DbtrAcct")
    id_ = etree.SubElement(dbtr_acct, "Id")
    etree.SubElement(id_, "IBAN").text = debtor_iban.replace(" ", "")
    dbtr_agt = etree.SubElement(pmt, "DbtrAgt")
    fin = etree.SubElement(dbtr_agt, "FinInstnId")
    if debtor_bic:
        etree.SubElement(fin, "BIC").text = debtor_bic.replace(" ", "")
    etree.SubElement(pmt, "ChrgBr").text = "SLEV"

    for idx, pay in enumerate(payments, start=1):
        tx = etree.SubElement(pmt, "CdtTrfTxInf")
        pmt_id = etree.SubElement(tx, "PmtId")
        etree.SubElement(pmt_id, "EndToEndId").text = pay.end_to_end_id

        amt = etree.SubElement(tx, "Amt")
        instd = etree.SubElement(amt, "InstdAmt", Ccy=pay.currency)
        instd.text = f"{Decimal(pay.amount):.2f}"

        cdtr_agt = etree.SubElement(tx, "CdtrAgt")
        fin2 = etree.SubElement(cdtr_agt, "FinInstnId")
        if pay.creditor_bic:
            etree.SubElement(fin2, "BIC").text = pay.creditor_bic.replace(" ", "")

        cdtr = etree.SubElement(tx, "Cdtr")
        etree.SubElement(cdtr, "Nm").text = pay.creditor_name

        cdtr_acct = etree.SubElement(tx, "CdtrAcct")
        id2 = etree.SubElement(cdtr_acct, "Id")
        etree.SubElement(id2, "IBAN").text = pay.creditor_iban.replace(" ", "")

        if pay.remittance_information:
            rmt = etree.SubElement(tx, "RmtInf")
            etree.SubElement(rmt, "Ustrd").text = pay.remittance_information[:140]

    # Pretty print
    xml_bytes = etree.tostring(doc, encoding="utf-8", xml_declaration=True, pretty_print=True)
    return xml_bytes
