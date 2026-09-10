from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditSource:
    side: str
    source_type: str
    identifier: str
    location: str
    sha256: str = ""
    retrieved_at: str = ""


@dataclass(frozen=True)
class AuditFieldComparison:
    field: str
    local_value: str
    authoritative_value: str
    status: str
    local_source: str
    authoritative_source: str
    detail: str = ""


@dataclass(frozen=True)
class AuditReport:
    audit_version: str
    generated_at: str
    scope: str
    determination: str
    determination_detail: str
    local_source: AuditSource
    authoritative_source: AuditSource
    field_comparisons: tuple[AuditFieldComparison, ...]
    evidence_chain: dict[str, Any]
    provenance: dict[str, Any]
    limitations: tuple[str, ...] = ()


def build_audit_report(scope: str, local_source: AuditSource, authoritative_source: AuditSource, field_comparisons: list[AuditFieldComparison], evidence_chain: Any, provenance: Any, limitations: list[str] | None = None) -> AuditReport:
    if isinstance(evidence_chain, dict):
        chain = evidence_chain
    elif is_dataclass(evidence_chain):
        chain = asdict(evidence_chain)
    else:
        chain = vars(evidence_chain)
    if isinstance(provenance, dict):
        provenance_data = provenance
    elif is_dataclass(provenance):
        provenance_data = asdict(provenance)
    else:
        provenance_data = vars(provenance)
    return AuditReport(
        audit_version="1.0",
        generated_at=datetime.now(timezone.utc).isoformat(),
        scope=scope,
        determination=chain.get("status", "UNKNOWN"),
        determination_detail=chain.get("detail", ""),
        local_source=local_source,
        authoritative_source=authoritative_source,
        field_comparisons=tuple(field_comparisons),
        evidence_chain=chain,
        provenance=provenance_data,
        limitations=tuple(limitations or []),
    )


def audit_dict(report: AuditReport) -> dict:
    data = asdict(report)
    data["field_comparisons"] = [asdict(item) for item in report.field_comparisons]
    data["limitations"] = list(report.limitations)
    return data


def write_audit_json(report: AuditReport, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit_dict(report), indent=2, sort_keys=True), encoding="utf-8")
