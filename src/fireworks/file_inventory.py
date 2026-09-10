from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import mimetypes


@dataclass(frozen=True)
class FileRecord:
    relative_path: str
    name: str
    size_bytes: int
    sha256: str
    mime_type: str
    modified_at: str
    discovered_at: str


@dataclass(frozen=True)
class InventoryReport:
    inventory_version: str
    discovery_root: str
    discovered_at: str
    files: tuple[FileRecord, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_directory(root: str | Path) -> InventoryReport:
    root = Path(root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Discovery root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Discovery root is not a directory: {root}")

    discovered_at = datetime.now(timezone.utc).isoformat()
    records = []

    for path in sorted(root.rglob("*"), key=lambda item: str(item)):
        if not path.is_file():
            continue
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(path.name)
        records.append(FileRecord(
            relative_path=path.relative_to(root).as_posix(),
            name=path.name,
            size_bytes=stat.st_size,
            sha256=_sha256(path),
            mime_type=mime_type or "application/octet-stream",
            modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            discovered_at=discovered_at,
        ))

    return InventoryReport(
        inventory_version="1.0",
        discovery_root=str(root),
        discovered_at=discovered_at,
        files=tuple(records),
    )


def inventory_dict(report: InventoryReport) -> dict:
    data = asdict(report)
    data["files"] = [asdict(record) for record in report.files]
    return data


def write_inventory(report: InventoryReport, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory_dict(report), indent=2, sort_keys=True), encoding="utf-8")


def duplicate_groups(report: InventoryReport) -> dict[str, list[str]]:
    groups = {}
    for record in report.files:
        groups.setdefault(record.sha256, []).append(record.relative_path)
    return {sha256: paths for sha256, paths in groups.items() if len(paths) > 1}
