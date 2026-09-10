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


def audit_html(report: AuditReport) -> str:
    import html
    def esc(value: Any) -> str:
        return html.escape(str(value))
    rows = []
    for c in report.field_comparisons:
        rows.append("<tr><td>" + esc(c.field) + "</td><td>" + esc(c.local_value or "[not available]") + "</td><td>" + esc(c.authoritative_value or "[not available]") + "</td><td>" + esc(c.status) + "</td><td>" + esc(c.detail or "[none]") + "</td></tr>")
    if not rows:
        rows.append("<tr><td colspan=\"5\">No field comparisons were recorded.</td></tr>")
    evidence = "".join("<tr><th>" + esc(k) + "</th><td>" + esc(v) + "</td></tr>" for k, v in report.evidence_chain.items())
    provenance = "".join("<tr><th>" + esc(k) + "</th><td>" + esc(v) + "</td></tr>" for k, v in report.provenance.items())
    limitations = "".join("<li>" + esc(v) + "</li>" for v in report.limitations) or "<li>None recorded.</li>"
    return "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Fireworks Audit Report</title><style>body{font-family:system-ui,sans-serif;line-height:1.5;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#111}section{margin:2rem 0}table{width:100%;border-collapse:collapse;margin-top:1rem}th,td{border:1px solid #ccc;padding:.6rem;text-align:left;vertical-align:top}th{background:#f2f2f2}.notice{border:2px solid #333;padding:1rem}code{overflow-wrap:anywhere}</style></head><body><h1>Fireworks Audit Report</h1><section><p><strong>Audit version:</strong>" + esc(report.audit_version) + "</p><p><strong>Generated at:</strong>" + esc(report.generated_at) + "</p><p><strong>Scope:</strong>" + esc(report.scope) + "</p><p><strong>Determination:</strong>" + esc(report.determination) + "</p><p><strong>Determination detail:</strong>" + esc(report.determination_detail) + "</p></section><section><h2>Local Evidence</h2><table><tr><th>Source type</th><td>" + esc(report.local_source.source_type) + "</td></tr><tr><th>Identifier</th><td>" + esc(report.local_source.identifier) + "</td></tr><tr><th>Location</th><td>" + esc(report.local_source.location) + "</td></tr><tr><th>SHA-256</th><td><code>" + esc(report.local_source.sha256 or "[not available]") + "</code></td></tr><tr><th>Retrieved at</th><td>" + esc(report.local_source.retrieved_at or "[not recorded]") + "</td></tr></table></section><section><h2>Authoritative Evidence</h2><table><tr><th>Source type</th><td>" + esc(report.authoritative_source.source_type) + "</td></tr><tr><th>Identifier</th><td>" + esc(report.authoritative_source.identifier) + "</td></tr><tr><th>Location</th><td>" + esc(report.authoritative_source.location) + "</td></tr><tr><th>SHA-256</th><td><code>" + esc(report.authoritative_source.sha256 or "[not available]") + "</code></td></tr><tr><th>Retrieved at</th><td>" + esc(report.authoritative_source.retrieved_at or "[not recorded]") + "</td></tr></table></section><section><h2>Field Comparisons</h2><table><thead><tr><th>Field</th><th>Local</th><th>Authoritative</th><th>Status</th><th>Detail</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></section><section><h2>Evidence Chain</h2><table>" + evidence + "</table></section><section><h2>Provenance</h2><table>" + provenance + "</table></section><section><h2>Limitations</h2><ul>" + limitations + "</ul></section><section class=\"notice\"><h2>Decision Authority</h2><p>Fireworks records and compares evidence. It does not determine legal ownership or adjudicate disputes.</p></section></body></html>"


def write_audit_html(report: AuditReport, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(audit_html(report), encoding="utf-8")
