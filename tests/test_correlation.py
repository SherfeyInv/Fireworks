import sys
from pathlib import Path
from types import SimpleNamespace
import shutil
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fireworks.correlation import correlation_dict, correlate
from fireworks.extract import extract

FIXTURE = Path("tests/fixtures/apple_newstead_form4.xml")


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


def canonical_extract():
    directory = tempfile.mkdtemp()
    path = Path(directory) / "form4.xml"
    shutil.copyfile(FIXTURE, path)
    return extract(path), directory


def test_correlation_matches():
    extracted, directory = canonical_extract()
    try:
        result = correlate(extracted, filing(), "0001140361-26-035636", "2026-09-03")
        assert result.status == "matched"
        assert result.entity_cik == "0000320193"
        assert result.accession_number == "0001140361-26-035636"
        assert result.form == "4"
        assert result.primary_document == "form4.xml"
        assert result.local_sha256 == "fcd091e16f995a813d107e5da4d78eaa41eb64a16a4f884cef359502642da7c1"
        assert len(result.identity_checks) == 5
        assert all(check.status == "passed" for check in result.identity_checks)
    finally:
        shutil.rmtree(directory)


def test_correlation_detects_identity_failure():
    extracted, directory = canonical_extract()
    try:
        result = correlate(extracted, filing(entity_cik="0000000000"), "0001140361-26-035636", "2026-09-03")
        assert result.status == "failed"
        assert result.identity_checks[0].status == "failed"
    finally:
        shutil.rmtree(directory)


def test_correlation_reports_unavailable_identity():
    extracted, directory = canonical_extract()
    try:
        result = correlate(extracted, filing(entity_cik=""), "0001140361-26-035636", "2026-09-03")
        assert result.status == "not_available"
        assert result.identity_checks[0].status == "not_available"
    finally:
        shutil.rmtree(directory)


def test_correlation_is_machine_readable():
    extracted, directory = canonical_extract()
    try:
        result = correlate(extracted, filing(), "0001140361-26-035636", "2026-09-03")
        data = correlation_dict(result)
        assert data["status"] == "matched"
        assert data["local_path"] == str(extracted.source_path)
        assert isinstance(data["identity_checks"], list)
        assert data["identity_checks"][0]["field"] == "issuer_cik"
    finally:
        shutil.rmtree(directory)
