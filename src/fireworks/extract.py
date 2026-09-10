from dataclasses import dataclass, asdict
from decimal import Decimal
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

from .provenance import create_field_provenance, create_provenance
from .version import PARSER_VERSION, SCHEMA_VERSION


@dataclass
class Transaction:
    security_title: str
    transaction_date: str
    transaction_code: str
    shares: str
    price_per_share: str
    acquired_disposed: str
    shares_owned_following: str
    ownership: str
    transaction_value: str
    footnote_ids: list[str]


@dataclass
class ExtractedFiling:
    source_path: str
    source_sha256: str
    document_type: str
    schema_version: str
    period_of_report: str
    issuer_cik: str
    issuer_name: str
    issuer_symbol: str
    owner_cik: str
    owner_name: str
    is_officer: bool | None
    is_director: bool | None
    is_ten_b5_one: bool | None
    officer_title: str
    transactions: list[Transaction]
    footnotes: dict[str, str]
    signature_name: str
    signature_date: str
    provenance: dict


def _tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _find(element, name):
    for child in element.iter():
        if _tag(child) == name:
            return child
    return None


def _text(element, name, default=""):
    node = _find(element, name)
    if node is None or node.text is None:
        return default
    return node.text.strip()


def _bool(value):
    value = value.strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    return None


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _transaction_value(shares, price):
    if not shares or not price:
        return ""
    try:
        return str(Decimal(shares) * Decimal(price))
    except Exception:
        return ""


def extract_form4(source_path):
    path = Path(source_path)
    source_sha256 = _sha256(path)
    if not path.exists():
        raise FileNotFoundError(f"Source filing does not exist: {path}")

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Invalid SEC XML: {path}: {exc}") from exc

    issuer = _find(root, "issuer")
    owner = _find(root, "reportingOwner")
    relationship = _find(owner, "reportingOwnerRelationship") if owner is not None else None

    transactions = []
    field_provenance = []
    table = _find(root, "nonDerivativeTable")

    if table is not None:
        for node in table.iter():
            if _tag(node) != "nonDerivativeTransaction":
                continue

            security = _find(node, "securityTitle")
            date = _find(node, "transactionDate")
            coding = _find(node, "transactionCoding")
            amounts = _find(node, "transactionAmounts")
            post = _find(node, "postTransactionAmounts")
            nature = _find(node, "ownershipNature")

            shares = _text(amounts, "value") if amounts is not None else ""
            price = ""
            if amounts is not None:
                price_nodes = [x for x in amounts.iter() if _tag(x) == "transactionPricePerShare"]
                if price_nodes:
                    price = _text(price_nodes[0], "value")

            shares_nodes = []
            if amounts is not None:
                shares_nodes = [x for x in amounts.iter() if _tag(x) == "transactionShares"]
            if shares_nodes:
                shares = _text(shares_nodes[0], "value")

            disposed = ""
            if amounts is not None:
                nodes = [x for x in amounts.iter() if _tag(x) == "transactionAcquiredDisposedCode"]
                if nodes:
                    disposed = _text(nodes[0], "value")

            following = _text(_find(post, "sharesOwnedFollowingTransaction"), "value") if post is not None else ""
            ownership = _text(_find(nature, "directOrIndirectOwnership"), "value") if nature is not None else ""
            footnote_ids = [x.attrib.get("id", "") for x in node.iter() if _tag(x) == "footnoteId" and x.attrib.get("id")]

            transactions.append(
                Transaction(
                    security_title=_text(security, "value") if security is not None else "",
                    transaction_date=_text(date, "value") if date is not None else "",
                    transaction_code=_text(coding, "transactionCode") if coding is not None else "",
                    shares=shares,
                    price_per_share=price,
                    acquired_disposed=disposed,
                    shares_owned_following=following,
                    ownership=ownership,
                    transaction_value=_transaction_value(shares, price),
                    footnote_ids=footnote_ids,
                )
            )

    footnotes = {}
    notes = _find(root, "footnotes")
    if notes is not None:
        for node in notes.iter():
            if _tag(node) == "footnote" and node.attrib.get("id"):
                footnotes[node.attrib["id"]] = (node.text or "").strip()

    field_provenance.extend([
        create_field_provenance("issuer_name", "issuer/issuerName", _text(issuer, "issuerName") if issuer is not None else ""),
        create_field_provenance("issuer_symbol", "issuer/issuerTradingSymbol", _text(issuer, "issuerTradingSymbol") if issuer is not None else ""),
        create_field_provenance("issuer_cik", "issuer/issuerCik", _text(issuer, "issuerCik") if issuer is not None else ""),
        create_field_provenance("owner_name", "reportingOwner/rptOwnerName", _text(owner, "rptOwnerName") if owner is not None else ""),
        create_field_provenance("owner_cik", "reportingOwner/rptOwnerCik", _text(owner, "rptOwnerCik") if owner is not None else ""),
        create_field_provenance("period_of_report", "periodOfReport", _text(root, "periodOfReport")),
        create_field_provenance("document_type", "documentType", _text(root, "documentType")),
        create_field_provenance("signature_name", "signatureName", _text(root, "signatureName")),
        create_field_provenance("signature_date", "signatureDate", _text(root, "signatureDate")),
    ])
    for index, transaction in enumerate(transactions):
        base = f"nonDerivativeTable/nonDerivativeTransaction[{index + 1}]"
        field_provenance.extend([
            create_field_provenance(f"transactions[{index}].security_title", f"{base}/securityTitle/value", transaction.security_title),
            create_field_provenance(f"transactions[{index}].transaction_date", f"{base}/transactionDate/value", transaction.transaction_date),
            create_field_provenance(f"transactions[{index}].transaction_code", f"{base}/transactionCoding/transactionCode", transaction.transaction_code),
            create_field_provenance(f"transactions[{index}].shares", f"{base}/transactionAmounts/transactionShares/value", transaction.shares),
            create_field_provenance(f"transactions[{index}].price_per_share", f"{base}/transactionAmounts/transactionPricePerShare/value", transaction.price_per_share),
            create_field_provenance(f"transactions[{index}].acquired_disposed", f"{base}/transactionAmounts/transactionAcquiredDisposedCode/value", transaction.acquired_disposed),
            create_field_provenance(f"transactions[{index}].shares_owned_following", f"{base}/postTransactionAmounts/sharesOwnedFollowingTransaction/value", transaction.shares_owned_following),
            create_field_provenance(f"transactions[{index}].ownership", f"{base}/ownershipNature/directOrIndirectOwnership/value", transaction.ownership),
            create_field_provenance(f"transactions[{index}].transaction_value", "derived", transaction.transaction_value, derived=True, derivation=f"{transaction.shares} * {transaction.price_per_share}"),
        ])
    
    return ExtractedFiling(
        source_path=str(path.resolve()),
        source_sha256=source_sha256,
        document_type=_text(root, "documentType"),
        schema_version=_text(root, "schemaVersion"),
        period_of_report=_text(root, "periodOfReport"),
        issuer_cik=_text(issuer, "issuerCik") if issuer is not None else "",
        issuer_name=_text(issuer, "issuerName") if issuer is not None else "",
        issuer_symbol=_text(issuer, "issuerTradingSymbol") if issuer is not None else "",
        owner_cik=_text(owner, "rptOwnerCik") if owner is not None else "",
        owner_name=_text(owner, "rptOwnerName") if owner is not None else "",
        is_officer=_bool(_text(relationship, "isOfficer")) if relationship is not None else None,
        is_director=_bool(_text(relationship, "isDirector")) if relationship is not None else None,
        is_ten_b5_one=_bool(_text(root, "aff10b5One")),
        officer_title=_text(relationship, "officerTitle") if relationship is not None else "",
        transactions=transactions,
        footnotes=footnotes,
        signature_name=_text(root, "signatureName"),
        signature_date=_text(root, "signatureDate"),
        provenance=create_provenance(source_sha256=source_sha256, parser_version=PARSER_VERSION, schema_version=SCHEMA_VERSION, fields=field_provenance).__dict__,
    )


def extract(source_path):
    return extract_form4(source_path)


def save_extraction(result, destination):
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return path
