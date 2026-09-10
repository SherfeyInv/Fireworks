from dataclasses import dataclass, asdict
from .identity import IdentityCheck, identity_status, validate_identity


@dataclass(frozen=True)
class CorrelationResult:
    status: str
    local_path: str
    local_sha256: str
    entity_cik: str
    accession_number: str
    filing_date: str
    report_date: str
    form: str
    primary_document: str
    primary_doc_url: str
    filing_url: str
    identity_checks: tuple[IdentityCheck, ...] = ()


def correlate(extracted, filing, local_accession_number=None, local_filing_date=None) -> CorrelationResult:
    checks = validate_identity(
        extracted,
        filing,
        local_accession_number,
        local_filing_date,
    )
    identity_result = identity_status(checks)

    if identity_result == "passed":
        status = "matched"
    elif identity_result == "failed":
        status = "failed"
    else:
        status = "not_available"

    return CorrelationResult(
        status=status,
        local_path=str(extracted.source_path),
        local_sha256=extracted.source_sha256,
        entity_cik=filing.entity_cik,
        accession_number=filing.accession_number,
        filing_date=filing.filing_date,
        report_date=filing.report_date,
        form=filing.form,
        primary_document=filing.primary_document,
        primary_doc_url=filing.primary_doc_url,
        filing_url=filing.filing_url,
        identity_checks=tuple(checks),
    )


def correlation_dict(result: CorrelationResult) -> dict:
    data = asdict(result)
    data["identity_checks"] = [asdict(check) for check in result.identity_checks]
    return data
