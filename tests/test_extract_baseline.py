import sys
from pathlib import Path

sys.path.insert(0, "src")
from fireworks.extract import extract

FIXTURE = Path("tests/fixtures/apple_newstead_form4.xml")
EXPECTED_SHA256 = "fcd091e16f995a813d107e5da4d78eaa41eb64a16a4f884cef359502642da7c1"


def main():
    result = extract(FIXTURE)
    assert result.source_sha256 == EXPECTED_SHA256
    assert result.document_type == "4"
    assert result.schema_version
    assert result.period_of_report == "2026-09-01"
    assert result.issuer_cik == "0000320193"
    assert result.issuer_name == "Apple Inc."
    assert result.issuer_symbol == "AAPL"
    assert result.owner_cik == "0001780525"
    assert result.owner_name == "Newstead Jennifer"
    assert result.is_officer is True
    assert result.is_director is None
    assert result.is_ten_b5_one is True
    assert result.officer_title == "SVP, GC and Government Affairs"
    assert len(result.transactions) == 1
    tx = result.transactions[0]
    assert tx.security_title == "Common Stock"
    assert tx.transaction_date == "2026-09-01"
    assert tx.transaction_code == "S"
    assert tx.shares == "1439"
    assert tx.price_per_share == "317.01"
    assert tx.acquired_disposed == "D"
    assert tx.shares_owned_following == "35790"
    assert tx.ownership == "D"
    assert tx.transaction_value == "456177.39"
    assert tx.footnote_ids == ["F1"]
    assert result.footnotes["F1"].startswith("This transaction was made pursuant to a Rule 10b5-1")
    assert result.signature_name == "/s/ Sam Whittington, Attorney-in-Fact for Jennifer Newstead"
    assert result.signature_date == "2026-09-03"
    print("PASS: complete Apple extraction baseline")


if __name__ == "__main__":
    main()
