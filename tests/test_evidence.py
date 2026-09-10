import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fireworks.correlation import correlate
from fireworks.evidence import build_evidence_chain, evidence_dict
from fireworks.extract import extract
from fireworks.validate import ValidationResult
from fireworks.filing_download import DownloadRecord
from fireworks.package_verify import VerificationResult

FIXTURE = Path("tests/fixtures/apple_newstead_form4.xml")
SHA256 = "fcd091e16f995a813d107e5da4d78eaa41eb64a16a4f884cef359502642da7c1"


def filing(**overrides):
    values = {
        "entity_cik": "0000320193",
        "accession_number": "0001140361-26-035636",
        "filing_date": "2026-09-03",
        "report_date": "2026-09-01",
        "form": "4",
        "primary_document": "form4.xml",
        "primary_doc_url": "https://www.sec.gov/Archives/edgar/data/320193/000114036126035636/form4.xml",
        "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000114036126035636/",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def correlation_and_extract():
    extracted = extract(FIXTURE)
    result = correlate(extracted, filing(), "0001140361-26-035636", "2026-09-03")
    return extracted, result


def download_record(sha256=SHA256):
    return DownloadRecord(
        entity_cik="0000320193",
        accession_number="0001140361-26-035636",
        filing_date="2026-09-03",
        form="4",
        filing_url=filing().filing_url,
        local_path=str(FIXTURE),
        sha256=sha256,
        size_bytes=3153,
        downloaded_at="2026-09-10T00:00:00+00:00",
        status="success",
    )


def validation_results():
    return [
        ValidationResult("source_exists", "passed", str(FIXTURE)),
        ValidationResult("sha256", "passed", SHA256),
        ValidationResult("xml_parse", "passed", "XML parsed successfully"),
        ValidationResult("document_type", "passed", "4"),
    ]


def package_results():
    return [
        VerificationResult(
            path=str(FIXTURE),
            status="verified",
            expected_sha256=SHA256,
            actual_sha256=SHA256,
            expected_size=3153,
            actual_size=3153,
        )
    ]


def test_evidence_chain_verifies_complete_record():
    extracted, correlation = correlation_and_extract()
    chain = build_evidence_chain(
        extracted,
        filing(),
        correlation,
        validation_results(),
        sec_download=download_record(),
        package_results=package_results(),
        sec_metadata_sha256="metadata-sha256",
    )
    assert chain.status == "VERIFIED"
    assert chain.identity_status == "matched"
    assert chain.package_status == "verified"
    assert chain.validation_status == "passed"
    assert chain.sha256_match is True
    assert chain.local_artifact_sha256 == SHA256
    assert chain.sec_download_sha256 == SHA256
    assert chain.sec_metadata_sha256 == "metadata-sha256"


def test_evidence_chain_detects_byte_conflict():
    extracted, correlation = correlation_and_extract()
    chain = build_evidence_chain(
        extracted,
        filing(),
        correlation,
        validation_results(),
        sec_download=download_record("0" * 64),
        package_results=package_results(),
    )
    assert chain.status == "CONFLICTING"
    assert chain.sha256_match is False


def test_evidence_chain_does_not_promote_missing_package_to_verified():
    extracted, correlation = correlation_and_extract()
    chain = build_evidence_chain(
        extracted,
        filing(),
        correlation,
        validation_results(),
        sec_download=download_record(),
        package_results=[],
    )
    assert chain.status == "PARTIALLY_VERIFIED"
    assert chain.package_status == "not_available"


def test_evidence_chain_detects_validation_failure():
    extracted, correlation = correlation_and_extract()
    failed_validation = validation_results()
    failed_validation[2] = ValidationResult("xml_parse", "failed", "malformed XML")
    chain = build_evidence_chain(
        extracted,
        filing(),
        correlation,
        failed_validation,
        sec_download=download_record(),
        package_results=package_results(),
    )
    assert chain.status == "CONFLICTING"
    assert chain.validation_status == "failed"


def test_evidence_chain_is_machine_readable():
    extracted, correlation = correlation_and_extract()
    chain = build_evidence_chain(
        extracted,
        filing(),
        correlation,
        validation_results(),
        sec_download=download_record(),
        package_results=package_results(),
    )
    data = evidence_dict(chain)
    assert data["status"] == "VERIFIED"
    assert data["sha256_match"] is True
    assert data["local_artifact_sha256"] == SHA256
    assert data["sec_download_sha256"] == SHA256


def test_evidence_chain_uses_real_package_verifier(tmp_path):
    import json
    import shutil

    package_dir = tmp_path / "package"
    package_dir.mkdir()
    package_file = package_dir / "form4.xml"
    shutil.copyfile(FIXTURE, package_file)

    manifest = {
        "entity_cik": "0000320193",
        "accession_number": "0001140361-26-035636",
        "filing_url": filing().filing_url,
        "files": [
            {
                "url": filing().primary_doc_url,
                "local_path": str(package_file),
                "sha256": SHA256,
                "size_bytes": 3153,
                "status": "success",
            }
        ],
    }
    (package_dir / "package_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    from fireworks.package_verify import verify_package

    results = verify_package(package_dir)
    assert len(results) == 1
    assert results[0].status == "verified"

    extracted, correlation = correlation_and_extract()
    chain = build_evidence_chain(
        extracted,
        filing(),
        correlation,
        validation_results(),
        sec_download=download_record(),
        package_results=results,
    )
    assert chain.status == "VERIFIED"
    assert chain.package_status == "verified"


def test_evidence_chain_detects_real_package_tampering(tmp_path):
    import json
    import shutil

    package_dir = tmp_path / "package"
    package_dir.mkdir()
    package_file = package_dir / "form4.xml"
    shutil.copyfile(FIXTURE, package_file)

    manifest = {
        "entity_cik": "0000320193",
        "accession_number": "0001140361-26-035636",
        "filing_url": filing().filing_url,
        "files": [
            {
                "url": filing().primary_doc_url,
                "local_path": str(package_file),
                "sha256": SHA256,
                "size_bytes": 3153,
                "status": "success",
            }
        ],
    }
    (package_dir / "package_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    package_file.write_bytes(package_file.read_bytes() + b"TAMPERED")

    from fireworks.package_verify import verify_package

    results = verify_package(package_dir)
    assert len(results) == 1
    assert results[0].status == "mismatch"

    extracted, correlation = correlation_and_extract()
    chain = build_evidence_chain(
        extracted,
        filing(),
        correlation,
        validation_results(),
        sec_download=download_record(),
        package_results=results,
    )
    assert chain.status == "CONFLICTING"
    assert chain.package_status == "mismatch"


def test_evidence_chain_marks_missing_sec_download_as_partial():
    extracted, correlation = correlation_and_extract()
    chain = build_evidence_chain(
        extracted,
        filing(),
        correlation,
        validation_results(),
        sec_download=None,
        package_results=package_results(),
    )
    assert chain.status == "PARTIALLY_VERIFIED"
    assert chain.sha256_match is False
    assert chain.sec_download_sha256 == ""
