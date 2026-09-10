import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fireworks.report import AuditFieldComparison, AuditSource, audit_dict, audit_text, build_audit_report, write_audit_json, write_audit_text


SHA256 = "fcd091e16f995a813d107e5da4d78eaa41eb64a16a4f884cef359502642da7c1"


def evidence_chain(status="VERIFIED", detail="Evidence checks passed"):
    return SimpleNamespace(status=status, detail=detail)


def provenance():
    return SimpleNamespace(
        maintainer="Fireworks",
        source_sha256=SHA256,
        fields=(),
    )


def sources():
    return (
        AuditSource(
            side="local",
            source_type="local_artifact",
            identifier="local-form4.xml",
            location="tests/fixtures/apple_newstead_form4.xml",
            sha256=SHA256,
        ),
        AuditSource(
            side="authoritative",
            source_type="SEC filing",
            identifier="0001140361-26-035636",
            location="https://www.sec.gov/Archives/edgar/data/320193/000114036126035636/form4.xml",
            sha256=SHA256,
            retrieved_at="2026-09-10T00:00:00+00:00",
        ),
    )


def test_audit_preserves_both_source_values():
    local, authoritative = sources()
    comparison = AuditFieldComparison(
        field="issuer_cik",
        local_value="0000320193",
        authoritative_value="0000320193",
        status="match",
        local_source=local.identifier,
        authoritative_source=authoritative.identifier,
    )
    report = build_audit_report(
        "SEC Form 4 identity verification",
        local,
        authoritative,
        [comparison],
        evidence_chain(),
        provenance(),
    )
    data = audit_dict(report)
    assert data["local_source"]["side"] == "local"
    assert data["authoritative_source"]["side"] == "authoritative"
    assert data["field_comparisons"][0]["local_value"] == "0000320193"
    assert data["field_comparisons"][0]["authoritative_value"] == "0000320193"


def test_audit_preserves_conflict_without_deciding_ownership():
    local, authoritative = sources()
    comparison = AuditFieldComparison(
        field="issuer_cik",
        local_value="0000320193",
        authoritative_value="0000000000",
        status="conflict",
        local_source=local.identifier,
        authoritative_source=authoritative.identifier,
        detail="Values differ",
    )
    report = build_audit_report(
        "SEC Form 4 identity verification",
        local,
        authoritative,
        [comparison],
        evidence_chain("CONFLICTING", "Evidence conflict detected"),
        provenance(),
    )
    data = audit_dict(report)
    assert data["determination"] == "CONFLICTING"
    assert data["field_comparisons"][0]["status"] == "conflict"
    assert data["field_comparisons"][0]["local_value"] != data["field_comparisons"][0]["authoritative_value"]


def test_audit_preserves_limitations_and_partial_status():
    local, authoritative = sources()
    report = build_audit_report(
        "SEC Form 4 identity verification",
        local,
        authoritative,
        [],
        evidence_chain("PARTIALLY_VERIFIED", "SEC download unavailable"),
        provenance(),
        limitations=["The unavailable source cannot be treated as negative evidence"],
    )
    data = audit_dict(report)
    assert data["determination"] == "PARTIALLY_VERIFIED"
    assert data["limitations"] == ["The unavailable source cannot be treated as negative evidence"]


def test_write_audit_json_is_machine_readable(tmp_path):
    local, authoritative = sources()
    comparison = AuditFieldComparison(
        field="document_type",
        local_value="4",
        authoritative_value="4",
        status="match",
        local_source=local.identifier,
        authoritative_source=authoritative.identifier,
    )
    report = build_audit_report(
        "SEC Form 4 identity verification",
        local,
        authoritative,
        [comparison],
        evidence_chain(),
        provenance(),
    )
    output = tmp_path / "audit.json"
    write_audit_json(report, output)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["audit_version"] == "1.0"
    assert data["determination"] == "VERIFIED"
    assert data["field_comparisons"][0]["field"] == "document_type"



def test_audit_accepts_production_evidence_and_provenance_dataclasses():
    from fireworks.evidence import EvidenceChain
    from fireworks.provenance import create_provenance
    local, authoritative = sources()
    chain = EvidenceChain(
        local_path=local.location,
        local_artifact_sha256=SHA256,
        sec_source_url=authoritative.location,
        sec_metadata_sha256=SHA256,
        sec_download_path="data/raw/0000320193/000114036126035636/form4.xml",
        sec_download_sha256=SHA256,
        sha256_match=True,
        identity_status="matched",
        package_status="verified",
        validation_status="passed",
        status="VERIFIED",
        detail="Identity, package, validation, and byte equality checks passed",
    )
    provenance_data = create_provenance(SHA256, "1.1", "1.0")
    report = build_audit_report(
        "SEC Form 4 identity verification",
        local,
        authoritative,
        [],
        chain,
        provenance_data,
    )
    data = audit_dict(report)
    assert data["determination"] == "VERIFIED"
    assert data["evidence_chain"]["sha256_match"] is True
    assert data["provenance"]["source_sha256"] == SHA256


def test_audit_text_preserves_both_sides_and_non_adjudication_language(tmp_path):
    local, authoritative = sources()
    comparison = AuditFieldComparison(
        field="issuer_cik",
        local_value="0000320193",
        authoritative_value="0000320193",
        status="match",
        local_source=local.identifier,
        authoritative_source=authoritative.identifier,
    )
    report = build_audit_report(
        "SEC Form 4 identity verification",
        local,
        authoritative,
        [comparison],
        evidence_chain(),
        provenance(),
        limitations=["Unavailable evidence remains unknown"],
    )
    text = audit_text(report)
    assert "LOCAL EVIDENCE" in text
    assert "AUTHORITATIVE EVIDENCE" in text
    assert "Local: 0000320193" in text
    assert "Authoritative: 0000320193" in text
    assert "Unavailable evidence remains unknown" in text
    assert "does not determine legal ownership" in text
    output = tmp_path / "audit.txt"
    write_audit_text(report, output)
    assert output.read_text(encoding="utf-8") == text
