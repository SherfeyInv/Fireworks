from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class IdentityCheck:
    field: str
    status: str
    local_value: str
    sec_value: str
    detail: str = ""


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_accession(value: Any) -> str:
    return _normalize(value).replace("-", "")


def _compare(field: str, local_value: Any, sec_value: Any, normalizer=_normalize) -> IdentityCheck:
    local = normalizer(local_value)
    sec = normalizer(sec_value)

    if not local or not sec:
        return IdentityCheck(field, "not_available", local, sec, "One or both values are unavailable")

    if local == sec:
        return IdentityCheck(field, "passed", local, sec, "Exact match")

    return IdentityCheck(field, "failed", local, sec, "Values do not match")


def validate_identity(extracted, filing, local_accession_number=None, local_filing_date=None) -> list[IdentityCheck]:
    checks = [
        _compare("issuer_cik", extracted.issuer_cik, filing.entity_cik),
        _compare("accession_number", local_accession_number, filing.accession_number, _normalize_accession),
        _compare("document_type", extracted.document_type, filing.form),
        _compare("period_of_report", extracted.period_of_report, filing.report_date),
        _compare("filing_date", local_filing_date, filing.filing_date),
    ]
    return checks


def identity_dict(checks: list[IdentityCheck]) -> list[dict]:
    return [asdict(check) for check in checks]


def identity_status(checks: list[IdentityCheck]) -> str:
    if any(check.status == "failed" for check in checks):
        return "failed"
    if any(check.status == "not_available" for check in checks):
        return "not_available"
    return "passed"
