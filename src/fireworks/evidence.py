from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceChain:
    local_path: str
    local_artifact_sha256: str
    sec_source_url: str
    sec_metadata_sha256: str
    sec_download_path: str
    sec_download_sha256: str
    sha256_match: bool
    identity_status: str
    package_status: str
    validation_status: str
    status: str
    detail: str = ""


def _status(identity_status: str, package_status: str, validation_status: str, sha256_match: bool, sec_download_available: bool) -> tuple[str, str]:
    statuses = {identity_status, package_status, validation_status}

    if "failed" in statuses or "mismatch" in statuses:
        return "CONFLICTING", "One or more evidence checks failed"

    if "not_available" in statuses or "missing" in statuses or not sec_download_available:
        return "PARTIALLY_VERIFIED", "Evidence is incomplete or unavailable"

    if not sha256_match:
        return "CONFLICTING", "Local artifact and SEC download bytes do not match"

    if identity_status == "matched" and package_status == "verified" and validation_status == "passed" and sha256_match:
        return "VERIFIED", "Identity, package, validation, and byte equality checks passed"

    return "UNVERIFIED", "Evidence chain did not satisfy the verification conditions"


def build_evidence_chain(extracted: Any, filing: Any, correlation: Any, validation_results: list[Any], sec_download: Any | None = None, package_results: list[Any] | None = None, sec_metadata_sha256: str = "") -> EvidenceChain:
    package_results = package_results or []

    if not package_results:
        package_status = "not_available"
    elif any(getattr(result, "status", "") in {"mismatch", "missing"} for result in package_results):
        package_status = "mismatch"
    elif all(getattr(result, "status", "") == "verified" for result in package_results):
        package_status = "verified"
    else:
        package_status = "missing"

    if not validation_results:
        validation_status = "not_available"
    elif any(getattr(result, "status", "") == "failed" for result in validation_results):
        validation_status = "failed"
    elif all(getattr(result, "status", "") == "passed" for result in validation_results):
        validation_status = "passed"
    else:
        validation_status = "not_available"

    local_sha256 = getattr(extracted, "source_sha256", "")
    sec_sha256 = getattr(sec_download, "sha256", "") if sec_download is not None else ""
    sha256_match = bool(local_sha256 and sec_sha256 and local_sha256 == sec_sha256)

    status, detail = _status(
        correlation.status,
        package_status,
        validation_status,
        sha256_match,
        sec_download is not None,
    )

    return EvidenceChain(
        local_path=str(extracted.source_path),
        local_artifact_sha256=local_sha256,
        sec_source_url=getattr(correlation, "primary_doc_url", filing.primary_doc_url),
        sec_metadata_sha256=sec_metadata_sha256,
        sec_download_path=getattr(sec_download, "local_path", "") if sec_download is not None else "",
        sec_download_sha256=sec_sha256,
        sha256_match=sha256_match,
        identity_status=correlation.status,
        package_status=package_status,
        validation_status=validation_status,
        status=status,
        detail=detail,
    )


def evidence_dict(chain: EvidenceChain) -> dict:
    return asdict(chain)
