from dataclasses import dataclass, asdict
from pathlib import Path
import json

from .config import project_root
from .discovery import discover_entity


@dataclass
class FilingRecord:
    entity_cik: str
    accession_number: str
    filing_date: str
    report_date: str
    form: str
    primary_document: str
    primary_doc_url: str
    filing_url: str


def discover_filings(cik: str) -> list[FilingRecord]:
    result = discover_entity(cik)

    if result.status != "success" or not result.data:
        raise RuntimeError(
            f"Unable to discover SEC filings for CIK {cik}: {result.error}"
        )

    recent = result.data.get("filings", {}).get("recent", {})

    accession_numbers = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    forms = recent.get("form", [])
    primary_documents = recent.get("primaryDocument", [])

    records = []

    for i, accession in enumerate(accession_numbers):
        accession_clean = accession.replace("-", "")
        document = primary_documents[i] if i < len(primary_documents) else ""

        records.append(
            FilingRecord(
                entity_cik=result.entity_cik,
                accession_number=accession,
                filing_date=filing_dates[i] if i < len(filing_dates) else "",
                report_date=report_dates[i] if i < len(report_dates) else "",
                form=forms[i] if i < len(forms) else "",
                primary_document=document,
                primary_doc_url=(
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{int(result.entity_cik)}/{accession_clean}/{document}"
                ),
                filing_url=(
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{int(result.entity_cik)}/{accession_clean}/"
                ),
            )
        )

    return records


def save_filings(cik: str) -> Path:
    records = discover_filings(cik)

    output_dir = project_root() / "data" / "index"
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / f"filings_{str(cik).strip().lstrip('0').zfill(10)}.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            [asdict(record) for record in records],
            f,
            indent=2,
            ensure_ascii=False,
        )

    return path
