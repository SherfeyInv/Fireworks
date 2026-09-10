from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET

from .config import project_root
from .filing_discovery import discover_filings


@dataclass
class DownloadRecord:
    entity_cik: str
    accession_number: str
    filing_date: str
    form: str
    filing_url: str
    local_path: str
    sha256: str
    size_bytes: int
    downloaded_at: str
    status: str
    error: str | None = None


def _download(url: str, destination: Path) -> tuple[str, int]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Fireworks SEC research system "
                "(contact: research@aysherintel.com)"
            ),
            "Accept-Encoding": "identity",
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)

    sha256 = hashlib.sha256(data).hexdigest()

    return sha256, len(data)


def _validate_download(data: bytes, form: str) -> None:
    if data[:3] == b"\x1f\x8b\x08":
        raise ValueError("Downloaded document is gzip-compressed; expected canonical document bytes")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"Downloaded document is not valid XML: {exc}") from exc
    root_tag = root.tag.rsplit("}", 1)[-1]
    if form in {"3", "4", "5"} and root_tag != "ownershipDocument":
        raise ValueError(f"Expected ownershipDocument for Form {form}, got {root_tag}")
    if form in {"3", "4", "5"}:
        document_type = next((node.text.strip() for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "documentType" and node.text), "")
        if document_type != form:
            raise ValueError(f"Expected Form {form}, XML documentType is {document_type!r}")

def download_filing(record) -> DownloadRecord:
    normalized_cik = record.entity_cik.zfill(10)
    accession_clean = record.accession_number.replace("-", "")

    filing_dir = (
        project_root()
        / "data"
        / "raw"
        / normalized_cik
        / accession_clean
    )

    destination = filing_dir / Path(record.primary_document).name

    try:
        sha256, size_bytes = _download(
            record.primary_doc_url,
            destination,
        )
        _validate_download(destination.read_bytes(), record.form)

        return DownloadRecord(
            entity_cik=record.entity_cik,
            accession_number=record.accession_number,
            filing_date=record.filing_date,
            form=record.form,
            filing_url=record.filing_url,
            local_path=str(destination),
            sha256=sha256,
            size_bytes=size_bytes,
            downloaded_at=datetime.now(timezone.utc).isoformat(),
            status="success",
        )

    except Exception as exc:
        return DownloadRecord(
            entity_cik=record.entity_cik,
            accession_number=record.accession_number,
            filing_date=record.filing_date,
            form=record.form,
            filing_url=record.filing_url,
            local_path=str(destination),
            sha256="",
            size_bytes=0,
            downloaded_at=datetime.now(timezone.utc).isoformat(),
            status="error",
            error=str(exc),
        )


def download_filings(cik: str) -> list[DownloadRecord]:
    records = discover_filings(cik)
    return [download_filing(record) for record in records]


def save_download_index(cik: str) -> Path:
    records = download_filings(cik)

    normalized_cik = str(cik).strip().lstrip("0").zfill(10)

    output_dir = project_root() / "data" / "index"
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / f"downloads_{normalized_cik}.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            [asdict(record) for record in records],
            f,
            indent=2,
            ensure_ascii=False,
        )

    return path
