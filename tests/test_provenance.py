import sys
from datetime import datetime

sys.path.insert(0, "src")
from fireworks.provenance import create_provenance, provenance_dict

EXPECTED_SHA256 = "fcd091e16f995a813d107e5da4d78eaa41eb64a16a4f884cef359502642da7c1"


def main():
    result = create_provenance(EXPECTED_SHA256, "1.0.0", "1.0")

    assert result.maintainer == "Ronnie Lee Sherfey Jr."
    assert result.system == "Fireworks"
    assert result.role == "Researcher / Record Maintainer / Presenter"
    assert result.source_type == "SEC filing"
    assert result.source_attribution == "Originating SEC filing; not authored by the record maintainer"
    assert result.source_sha256 == EXPECTED_SHA256
    assert result.parser_version == "1.0.0"
    assert result.schema_version == "1.0"

    parsed = datetime.fromisoformat(result.recorded_at)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None

    data = provenance_dict(result)
    assert data["maintainer"] == "Ronnie Lee Sherfey Jr."
    assert data["system"] == "Fireworks"
    assert data["source_attribution"] == "Originating SEC filing; not authored by the record maintainer"
    assert data["source_sha256"] == EXPECTED_SHA256

    print("PASS: provenance identity and integrity test")


if __name__ == "__main__":
    main()
