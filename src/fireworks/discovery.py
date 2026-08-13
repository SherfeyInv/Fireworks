from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
import gzip
import json
import urllib.request

from .config import load_sources, project_root


@dataclass
class DiscoveryResult:
    source: str
    entity_cik: str
    request_url: str
    discovered_at: str
    status: str
    content_type: Optional[str] = None
    error: Optional[str] = None
    data: Optional[dict] = None


def _sec_request(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Fireworks SEC research system "
                "(contact: research@aysherintel.com)"
            ),
            "Accept-Encoding": "gzip, deflate",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read(), response.headers.get("Content-Type", "")


def _decode_response(raw: bytes) -> bytes:
    if raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)

    return raw


def discover_submissions(cik: str) -> DiscoveryResult:
    normalized_cik = str(cik).strip().lstrip("0").zfill(10)

    base_url = load_sources()["sec"]["submissions"]["base_url"]
    url = f"{base_url}CIK{normalized_cik}.json"

    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        raw, content_type = _sec_request(url)
        raw = _decode_response(raw)
        data = json.loads(raw.decode("utf-8"))

        return DiscoveryResult(
            source="sec.submissions",
            entity_cik=normalized_cik,
            request_url=url,
            discovered_at=timestamp,
            status="success",
            content_type=content_type,
            data=data,
        )

    except Exception as exc:
        return DiscoveryResult(
            source="sec.submissions",
            entity_cik=normalized_cik,
            request_url=url,
            discovered_at=timestamp,
            status="error",
            error=str(exc),
        )


def save_discovery_result(result: DiscoveryResult) -> None:
    output_dir = project_root() / "data" / "index"
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / f"submissions_{result.entity_cik}.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2, ensure_ascii=False)


def discover_entity(cik: str) -> DiscoveryResult:
    result = discover_submissions(cik)
    save_discovery_result(result)
    return result
