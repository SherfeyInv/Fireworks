from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass(frozen=True)
class ResearchProvenance:
    maintainer: str
    system: str
    role: str
    source_type: str
    source_attribution: str
    recorded_at: str
    parser_version: str
    schema_version: str
    source_sha256: str


def create_provenance(source_sha256: str, parser_version: str, schema_version: str) -> ResearchProvenance:
    return ResearchProvenance(
        maintainer="Ronnie Lee Sherfey Jr.",
        system="Fireworks",
        role="Researcher / Record Maintainer / Presenter",
        source_type="SEC filing",
        source_attribution="Originating SEC filing; not authored by the record maintainer",
        recorded_at=datetime.now(timezone.utc).isoformat(),
        parser_version=parser_version,
        schema_version=schema_version,
        source_sha256=source_sha256,
    )


def provenance_dict(provenance: ResearchProvenance) -> dict:
    return asdict(provenance)
