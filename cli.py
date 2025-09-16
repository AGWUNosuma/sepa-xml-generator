from pathlib import Path
import typer
from rich.console import Console
from .core.csv_loader import load_payments_from_csv
from .sepa.builder import build_pain_001_xml
from .sepa.validator import validate_with_xsd
from .config.mapping_model import MappingConfig, load_mapping

app = typer.Typer(add_completion=False)
console = Console()

@app.command()
def convert(
    csv_path: Path = typer.Argument(..., exists=True, readable=True),
    mapping: Path = typer.Option(..., "--mapping", "-m", exists=True, readable=True),
    out: Path = typer.Option(Path("output.xml"), "--out", "-o"),
    debtor_name: str = typer.Option("", help="Override debtor name"),
    debtor_iban: str = typer.Option("", help="Override debtor IBAN"),
    debtor_bic: str = typer.Option("", help="Override debtor BIC (optional)"),
    pain_version: str = typer.Option("pain.001.001.03", help="pain.001 version to emit"),
    xsd: Path = typer.Option(None, help="Path to XSD for validation", exists=False),
):
    """Convert CSV into SEPA pain.001 XML."""
    cfg: MappingConfig = load_mapping(mapping)
    payments = load_payments_from_csv(csv_path, cfg)

    xml_bytes = build_pain_001_xml(
        payments=payments,
        debtor_name=debtor_name or cfg.defaults.debtor_name,
        debtor_iban=debtor_iban or cfg.defaults.debtor_iban,
        debtor_bic=debtor_bic or cfg.defaults.debtor_bic,
        pain_version=pain_version or cfg.defaults.pain_version,
    )

    out.write_bytes(xml_bytes)
    console.print(f"[green]Wrote[/green] {out} ({len(xml_bytes)} bytes)")

    if xsd and xsd.exists():
        ok, errors = validate_with_xsd(out, xsd)
        if ok:
            console.print(f"[green]Validation OK[/green] against {xsd.name}")
        else:
            console.print(f"[red]Validation FAILED[/red]:\n" + "\n".join(errors))

@app.command()
def gui():
    from .main_qt import main as gui_main
    raise SystemExit(gui_main())

if __name__ == "__main__":
    app()
