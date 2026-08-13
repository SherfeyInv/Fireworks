from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import urllib.request

from .config import project_root


@dataclass
class PackageFile:
    url: str
    local_path: str
    sha256: str
    size_bytes: int
    status: str
    error: str | None = None


def _request(url: str) -> bytes:
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
        raw = response.read()

        encoding = response.headers.get("Content-Encoding", "").lower()

        if encoding == "gzip" or raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)

        return raw


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _download_file(url: str, destination: Path) -> PackageFile:
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        raw = _request(url)
        destination.write_bytes(raw)

        return PackageFile(
            url=url,
            local_path=str(destination.resolve()),
            sha256=_sha256(destination),
            size_bytes=destination.stat().st_size,
            status="success",
        )

    except Exception as exc:
        return PackageFile(
            url=url,
            local_path=str(destination.resolve()),
            sha256="",
            size_bytes=0,
            status="error",
            error=str(exc),
        )


def _archive_base_url(cik: str, accession_number: str) -> tuple[str, str]:
    normalized_cik = str(cik).strip().lstrip("0").zfill(10)
    accession_clean = accession_number.replace("-", "")

    base_url = (
        "https://www.sec.gov/Archives/edgar/data/"
        f"{int(normalized_cik)}/{accession_clean}/"
    )

    return normalized_cik, base_url


def _discover_index_files(index_data: dict, base_url: str) -> list[str]:
    files = index_data.get("directory", {}).get("item", [])

    urls = []

    for item in files:
        name = item.get("name")

        if not isinstance(name, str):
            continue

        if not name or name.endswith("/"):
            continue

        urls.append(base_url + name)

    return sorted(set(urls))


def download_package(cik: str, accession_number: str) -> list[PackageFile]:
    normalized_cik, base_url = _archive_base_url(cik, accession_number)

    package_dir = (
        project_root()
        / "data"
        / "raw"
        / normalized_cik
        / accession_number
    )

    index_url = base_url + "index.json"

    try:
        index_raw = _request(index_url)
        index_data = json.loads(index_raw.decode("utf-8"))
        urls = _discover_index_files(index_data, base_url)

    except Exception as exc:
        manifest = {
            "entity_cik": normalized_cik,
            "accession_number": accession_number,
            "filing_url": base_url,
            "index_url": index_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error": str(exc),
            "files": [],
        }

        package_dir.mkdir(parents=True, exist_ok=True)

        with (package_dir / "package_manifest.json").open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        raise RuntimeError(
            f"Unable to retrieve SEC filing index: {index_url}: {exc}"
        ) from exc

    files: list[PackageFile] = []

    for url in urls:
        filename = Path(url.split("?", 1)[0]).name

        if not filename:
            continue

        destination = package_dir / filename
        files.append(_download_file(url, destination))

    manifest = {
        "entity_cik": normalized_cik,
        "accession_number": accession_number,
        "filing_url": base_url,
        "index_url": index_url,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": (
            "success"
            if files and all(item.status == "success" for item in files)
            else "partial"
        ),
        "files": [asdict(item) for item in files],
    }

    package_dir.mkdir(parents=True, exist_ok=True)

    with (package_dir / "package_manifest.json").open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return files
