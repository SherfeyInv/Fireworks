from pathlib import Path
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCES_FILE = PROJECT_ROOT / "config" / "sources.yaml"
ENTITIES_FILE = PROJECT_ROOT / "config" / "entities.yaml"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ValueError(f"Configuration must contain a YAML mapping: {path}")

    return data


def load_sources() -> dict:
    return load_yaml(SOURCES_FILE)


def load_entities() -> dict:
    return load_yaml(ENTITIES_FILE)


def project_root() -> Path:
    return PROJECT_ROOT
