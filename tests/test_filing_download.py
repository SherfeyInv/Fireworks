import sys
from pathlib import Path

sys.path.insert(0, "src")
from fireworks.filing_download import _validate_download

FIXTURE = Path("tests/fixtures/apple_newstead_form4.xml")


def test_valid_form4():
    _validate_download(FIXTURE.read_bytes(), "4")


def test_gzip_rejected():
    try:
        _validate_download(bytes.fromhex("1f8b08") + b"test", "4")
    except ValueError as exc:
        assert "gzip-compressed" in str(exc)
    else:
        raise AssertionError("gzip-compressed data was accepted")


def test_malformed_xml_rejected():
    try:
        _validate_download(b"<not-xml", "4")
    except ValueError as exc:
        assert "not valid XML" in str(exc)
    else:
        raise AssertionError("malformed XML was accepted")


def test_wrong_root_rejected():
    data = b"<?xml version=\"1.0\"?><wrongRoot><documentType>4</documentType></wrongRoot>"
    try:
        _validate_download(data, "4")
    except ValueError as exc:
        assert "ownershipDocument" in str(exc)
    else:
        raise AssertionError("wrong root element was accepted")


def test_wrong_document_type_rejected():
    data = b"<?xml version=\"1.0\"?><ownershipDocument><documentType>3</documentType></ownershipDocument>"
    try:
        _validate_download(data, "4")
    except ValueError as exc:
        assert "Expected Form 4" in str(exc)
    else:
        raise AssertionError("wrong documentType was accepted")


if __name__ == "__main__":
    test_valid_form4()
    test_gzip_rejected()
    test_malformed_xml_rejected()
    test_wrong_root_rejected()
    test_wrong_document_type_rejected()
    print("PASS: filing download integrity tests")
