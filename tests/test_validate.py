import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fireworks.validate import validate_source


FIXTURE = Path(__file__).parent / "fixtures" / "apple_newstead_form4.xml"
EXPECTED_SHA256 = "fcd091e16f995a813d107e5da4d78eaa41eb64a16a4f884cef359502642da7c1"


def test_source_validation():
    results = validate_source(FIXTURE, EXPECTED_SHA256, "4")
    assert [r.status for r in results] == ["passed", "passed", "passed", "passed"]
    assert results[0].check == "source_exists"
    assert results[1].check == "sha256"
    assert results[1].detail == EXPECTED_SHA256
    assert results[2].check == "xml_parse"
    assert results[3].check == "document_type"
    assert results[3].detail == "4"


if __name__ == "__main__":
    test_source_validation()
    print("PASS: source validation test")
