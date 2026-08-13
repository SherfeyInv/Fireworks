from dataclasses import dataclass
from pathlib import Path
import hashlib
import json


@dataclass
class VerificationResult:
    path: str
    status: str
    expected_sha256: str
    actual_sha256: str
    expected_size: int
    actual_size: int
    error: str | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def verify_package(package_dir: str | Path) -> list[VerificationResult]:
    package_dir = Path(package_dir)
    manifest_path = package_dir / "package_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing package manifest: {manifest_path}")

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    results = []

    for item in manifest.get("files", []):
        path = Path(item["local_path"])

        if not path.exists():
            results.append(
                VerificationResult(
                    path=str(path),
                    status="missing",
                    expected_sha256=item["sha256"],
                    actual_sha256="",
                    expected_size=item["size_bytes"],
                    actual_size=0,
                    error="Downloaded file is missing",
                )
            )
            continue

        actual_size = path.stat().st_size
        actual_sha256 = _sha256(path)

        if (
            actual_size == item["size_bytes"]
            and actual_sha256 == item["sha256"]
        ):
            status = "verified"
            error = None
        else:
            status = "mismatch"
            error = "Size or SHA-256 mismatch"

        results.append(
            VerificationResult(
                path=str(path),
                status=status,
                expected_sha256=item["sha256"],
                actual_sha256=actual_sha256,
                expected_size=item["size_bytes"],
                actual_size=actual_size,
                error=error,
            )
        )

    return results
