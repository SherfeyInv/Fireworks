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


def audit_text(report: AuditReport) -> str:
    lines = [
        "FIREWORKS AUDIT REPORT",
        "=" * 22,
        f"Audit version: {report.audit_version}",
        f"Generated at: {report.generated_at}",
        f"Scope: {report.scope}",
        f"Determination: {report.determination}",
        f"Determination detail: {report.determination_detail}",
        "",
        "LOCAL EVIDENCE",
        "--------------",
        f"Source type: {report.local_source.source_type}",
        f"Identifier: {report.local_source.identifier}",
        f"Location: {report.local_source.location}",
        f"SHA-256: {report.local_source.sha256 or "[not available]"}",
        f"Retrieved at: {report.local_source.retrieved_at or "[not recorded]"}",
        "",
        "AUTHORITATIVE EVIDENCE",
        "---------------------",
        f"Source type: {report.authoritative_source.source_type}",
        f"Identifier: {report.authoritative_source.identifier}",
        f"Location: {report.authoritative_source.location}",
        f"SHA-256: {report.authoritative_source.sha256 or "[not available]"}",
        f"Retrieved at: {report.authoritative_source.retrieved_at or "[not recorded]"}",
        "",
        "FIELD COMPARISONS",
        "-----------------",
    ]
    if report.field_comparisons:
        for comparison in report.field_comparisons:
            lines.extend([
                f"Field: {comparison.field}",
                f"  Local: {comparison.local_value or "[not available]"}",
                f"  Authoritative: {comparison.authoritative_value or "[not available]"}",
                f"  Status: {comparison.status}",
                f"  Local source: {comparison.local_source}",
                f"  Authoritative source: {comparison.authoritative_source}",
                f"  Detail: {comparison.detail or "[none]"}",
                "",
            ])
    else:
        lines.extend(["No field comparisons were recorded.", ""])
    lines.extend([
        "EVIDENCE CHAIN",
        "--------------",
    ])
    for key, value in report.evidence_chain.items():
        lines.append(f"{key}: {value}")
    lines.extend([
        "",
        "PROVENANCE",
        "----------",
    ])
    for key, value in report.provenance.items():
        lines.append(f"{key}: {value}")
    lines.extend([
        "",
        "LIMITATIONS",
        "-----------",
    ])
    if report.limitations:
        lines.extend(f"- {item}" for item in report.limitations)
    else:
        lines.append("None recorded.")
    lines.extend([
        "",
        "DECISION AUTHORITY",
        "------------------",
        "Fireworks records and compares evidence. It does not determine legal ownership or adjudicate disputes.",
        "",
    ])
    return "\n".join(lines)


def write_audit_text(report: AuditReport, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(audit_text(report), encoding="utf-8")


def write_audit_json(report: AuditReport, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit_dict(report), indent=2, sort_keys=True), encoding="utf-8")
