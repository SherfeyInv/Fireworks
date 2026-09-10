import sys
from pathlib import Path
from types import SimpleNamespace
import shutil
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fireworks.extract import extract
from fireworks.identity import identity_status, validate_identity

FIXTURE = Path("tests/fixtures/apple_newstead_form4.xml")


def filing(**overrides):
    values = {
        "entity_cik": "0000320193",
        "accession_number": "0001140361-26-035636",
        "filing_date": "2026-09-03",
        "report_date": "2026-09-01",
        "form": "4",
        "primary_document": "form4.xml",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def canonical_extract():
    directory = tempfile.mkdtemp()
    path = Path(directory) / "form4.xml"
    shutil.copyfile(FIXTURE, path)
    return extract(path), directory


def test_identity_matches():
    extracted, directory = canonical_extract()
    try:
        checks = validate_identity(extracted, filing(), "0001140361-26-035636", "2026-09-03")
        assert identity_status(checks) == "passed"
        assert len(checks) == 5
        assert all(check.status == "passed" for check in checks)
    finally:
        shutil.rmtree(directory)


def test_identity_detects_cik_mismatch():
    extracted, directory = canonical_extract()
    try:
        checks = validate_identity(extracted, filing(entity_cik="0000000000"), "0001140361-26-035636", "2026-09-03")
        assert identity_status(checks) == "failed"
        assert checks[0].status == "failed"
    finally:
        shutil.rmtree(directory)


def test_identity_detects_accession_mismatch():
    extracted, directory = canonical_extract()
    try:
        checks = validate_identity(extracted, filing(), "0000000-00-000000", "2026-09-03")
        assert identity_status(checks) == "failed"
        assert checks[1].status == "failed"
    finally:
        shutil.rmtree(directory)


def test_identity_detects_form_mismatch():
    extracted, directory = canonical_extract()
    try:
        checks = validate_identity(extracted, filing(form="3"), "0001140361-26-035636", "2026-09-03")
        assert identity_status(checks) == "failed"
        assert checks[2].status == "failed"
    finally:
        shutil.rmtree(directory)


def test_identity_detects_report_date_mismatch():
    extracted, directory = canonical_extract()
    try:
        checks = validate_identity(extracted, filing(report_date="2026-09-02"), "0001140361-26-035636", "2026-09-03")
        assert identity_status(checks) == "failed"
        assert checks[3].status == "failed"
    finally:
        shutil.rmtree(directory)


def test_identity_detects_filing_date_mismatch():
    extracted, directory = canonical_extract()
    try:
        checks = validate_identity(extracted, filing(), "0001140361-26-035636", "2026-09-04")
        assert identity_status(checks) == "failed"
        assert checks[4].status == "failed"
    finally:
        shutil.rmtree(directory)


def test_identity_ignores_local_fixture_filename():
    extracted, directory = canonical_extract()
    try:
        checks = validate_identity(extracted, filing(), "0001140361-26-035636", "2026-09-03")
        assert identity_status(checks) == "passed"
        assert len(checks) == 5
        assert all(check.status == "passed" for check in checks)
    finally:
        shutil.rmtree(directory)


def test_identity_marks_missing_values_unavailable():
    extracted, directory = canonical_extract()
    try:
        checks = validate_identity(extracted, filing(entity_cik=""), "0001140361-26-035636", "2026-09-03")
        assert identity_status(checks) == "not_available"
        assert checks[0].status == "not_available"
        assert all(check.status != "failed" for check in checks)
    finally:
        shutil.rmtree(directory)
