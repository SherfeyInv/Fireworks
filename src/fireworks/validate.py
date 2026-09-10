from dataclasses import dataclass
from pathlib import Path
import hashlib
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class ValidationResult:
    check: str
    status: str
    detail: str = ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_source(source_path: str | Path, expected_sha256: str | None = None, expected_document_type: str | None = None) -> list[ValidationResult]:
    path = Path(source_path)
    results = []

    if not path.exists():
        return [ValidationResult("source_exists", "failed", f"Missing source: {path}")]

    results.append(ValidationResult("source_exists", "passed", str(path)))

    actual_sha256 = _sha256(path)
    if expected_sha256 is None or actual_sha256 == expected_sha256:
        results.append(ValidationResult("sha256", "passed", actual_sha256))
    else:
        results.append(ValidationResult("sha256", "failed", f"expected={expected_sha256} actual={actual_sha256}"))

    try:
        root = ET.parse(path).getroot()
        results.append(ValidationResult("xml_parse", "passed", "XML parsed successfully"))
    except ET.ParseError as exc:
        results.append(ValidationResult("xml_parse", "failed", str(exc)))
        return results

    document_type = next((node.text.strip() for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "documentType" and node.text), "")
    if expected_document_type is None or document_type == expected_document_type:
        results.append(ValidationResult("document_type", "passed", document_type))
    else:
        results.append(ValidationResult("document_type", "failed", f"expected={expected_document_type} actual={document_type}"))

    return results
