import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fireworks.validate import validate_source
FIXTURE = Path(__file__).parent / "fixtures" / "apple_newstead_form4.xml"
EXPECTED_SHA256 = "fcd091e16f995a813d107e5da4d78eaa41eb64a16a4f884cef359502642da7c1"

def test_wrong_sha256_fails():
    results = validate_source(FIXTURE, "0000000000000000000000000000000000000000000000000000000000000000", "4")
    assert results[1].status == "failed"

def test_invalid_xml_fails(tmp_path):
    bad = tmp_path / "invalid.xml"
    bad.write_text("<ownershipDocument><broken>")
    results = validate_source(bad)
    assert results[0].status == "passed"
    assert results[1].status == "passed"
    assert results[2].status == "failed"

def test_wrong_document_type_fails():
    results = validate_source(FIXTURE, EXPECTED_SHA256, "3")
    assert results[3].status == "failed"

def test_missing_source_fails(tmp_path):
    missing = tmp_path / "missing.xml"
    results = validate_source(missing)
    assert len(results) == 1
    assert results[0].status == "failed"

if __name__ == "__main__":
    test_wrong_sha256_fails()
    test_wrong_document_type_fails()
    print("PASS: negative validation tests")
