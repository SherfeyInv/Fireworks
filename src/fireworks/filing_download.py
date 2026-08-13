from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import urllib.request

from .config import load_sources, project_root
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
            "Accept-Encoding": "gzip, deflate",
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)

    sha256 = hashlib.sha256(data).hexdigest()
    return sha256, len(data)


def download_filings(cik: str) -> list[DownloadRecord]:
    records = discover_filings(cik)

    output = []

    for record in records:
        normalized_cik = record.entity_cik.lstrip("0") or "0"
        accession_clean = record.accession_number.replace("-", "")

        filing_dir = (
            project_root()
            / "data"
            / "raw"
            / normalized_cik
            / accession_clean
        )

        filename = Path(record.primary_document).name

        destination = filing_dir / filename

        try:
            sha256, size_bytes = _download(
                record.primary_doc_url,
                destination,
            )

            output.append(
                DownloadRecord(
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
            )

        except Exception as exc:
            output.append(
                DownloadRecord(
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
            )

    return output


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
