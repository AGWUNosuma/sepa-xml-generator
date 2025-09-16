from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QTextEdit, QMessageBox
)
from ..config.mapping_model import load_mapping
from ..core.csv_loader import load_payments_from_csv
from ..sepa.builder import build_pain_001_xml
from ..sepa.validator import validate_with_xsd

class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SEPA XML Generator")
        self.resize(700, 480)

        self.csv_edit = QLineEdit()
        self.map_edit = QLineEdit()
        self.out_edit = QLineEdit(str(Path.cwd() / "output.xml"))
        self.xsd_edit = QLineEdit()

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout = QVBoxLayout(self)

        # Row builders
        def row(label: str, edit: QLineEdit, browse_cb):
            h = QHBoxLayout()
            h.addWidget(QLabel(label))
            h.addWidget(edit)
            b = QPushButton("Browse…")
            b.clicked.connect(browse_cb)
            h.addWidget(b)
            layout.addLayout(h)

        row("CSV:", self.csv_edit, self.pick_csv)
        row("Mapping YAML:", self.map_edit, self.pick_map)
        row("Output XML:", self.out_edit, self.pick_out)
        row("XSD (optional):", self.xsd_edit, self.pick_xsd)

        run = QPushButton("Generate XML")
        run.clicked.connect(self.generate)
        layout.addWidget(run)

        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log)

    def pick_csv(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv);;All Files (*.*)")
        if p:
            self.csv_edit.setText(p)

    def pick_map(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Mapping YAML", "", "YAML Files (*.yaml *.yml)")
        if p:
            self.map_edit.setText(p)

    def pick_out(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save XML As", "", "XML Files (*.xml)")
        if p:
            self.out_edit.setText(p)

    def pick_xsd(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select XSD", "", "XSD Files (*.xsd);;All Files (*.*)")
        if p:
            self.xsd_edit.setText(p)

    def logln(self, msg: str):
        self.log.append(msg)

    def generate(self):
        csv_path = Path(self.csv_edit.text())
        map_path = Path(self.map_edit.text())
        out_path = Path(self.out_edit.text())
        xsd_path = Path(self.xsd_edit.text()) if self.xsd_edit.text() else None

        if not csv_path.exists() or not map_path.exists():
            QMessageBox.critical(self, "Error", "CSV or mapping file does not exist.")
            return

        try:
            cfg = load_mapping(map_path)
            payments = load_payments_from_csv(csv_path, cfg)
            xml_bytes = build_pain_001_xml(
                payments=payments,
                debtor_name=cfg.defaults.debtor_name,
                debtor_iban=cfg.defaults.debtor_iban,
                debtor_bic=cfg.defaults.debtor_bic,
                pain_version=cfg.defaults.pain_version,
            )
            out_path.write_bytes(xml_bytes)
            self.logln(f"Wrote {out_path} ({len(xml_bytes)} bytes)")

            if xsd_path and xsd_path.exists():
                ok, errors = validate_with_xsd(out_path, xsd_path)
                if ok:
                    self.logln(f"Validation OK against {xsd_path.name}")
                else:
                    self.logln("Validation FAILED:\n" + "\n".join(errors))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
