import sys
from datetime import datetime

sys.path.insert(0, "src")
from fireworks.provenance import create_field_provenance, create_provenance, provenance_dict

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

    field = create_field_provenance("issuer_name", "issuer/issuerName", "Apple Inc.")
    derived = create_field_provenance("transactions[0].transaction_value", "derived", "456177.39", derived=True, derivation="1439 * 317.01")
    assert field.field == "issuer_name"
    assert field.source_path == "issuer/issuerName"
    assert field.source_value == "Apple Inc."
    assert field.derived is False
    assert derived.derived is True
    assert derived.source_value == "456177.39"
    assert derived.derivation == "1439 * 317.01"

    data = provenance_dict(result)
    assert data["maintainer"] == "Ronnie Lee Sherfey Jr."
    assert data["system"] == "Fireworks"
    assert data["source_attribution"] == "Originating SEC filing; not authored by the record maintainer"
    assert data["source_sha256"] == EXPECTED_SHA256

    print("PASS: provenance identity and integrity test")


if __name__ == "__main__":
    main()
