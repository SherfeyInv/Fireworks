import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fireworks.file_inventory import inventory_directory, inventory_dict, duplicate_groups


def test_inventory_discovers_nested_files(tmp_path):
    root = tmp_path / "evidence"
    (root / "one" / "two").mkdir(parents=True)
    (root / "a.txt").write_text("alpha")
    (root / "one" / "two" / "b.txt").write_text("beta")
    report = inventory_directory(root)
    paths = [record.relative_path for record in report.files]
    assert paths == ["a.txt", "one/two/b.txt"]
    assert all(len(record.sha256) == 64 for record in report.files)


def test_duplicate_content_is_identified(tmp_path):
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "first.txt").write_text("same content")
    (root / "second.txt").write_text("same content")
    report = inventory_directory(root)
    groups = duplicate_groups(report)
    assert len(groups) == 1
    assert sorted(next(iter(groups.values()))) == ["first.txt", "second.txt"]


def test_inventory_metadata_is_machine_readable(tmp_path):
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "record.json").write_text("{}")
    report = inventory_directory(root)
    data = inventory_dict(report)
    assert data["inventory_version"] == "1.0"
    assert data["discovery_root"] == str(root.resolve())
    assert len(data["files"]) == 1
    assert data["files"][0]["name"] == "record.json"


def test_missing_root_fails(tmp_path):
    missing = tmp_path / "missing"
    try:
        inventory_directory(missing)
    except FileNotFoundError:
        return
    raise AssertionError("Missing discovery root must fail")


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        test_inventory_discovers_nested_files(Path(directory))
    with tempfile.TemporaryDirectory() as directory:
        test_duplicate_content_is_identified(Path(directory))
    with tempfile.TemporaryDirectory() as directory:
        test_inventory_metadata_is_machine_readable(Path(directory))
    with tempfile.TemporaryDirectory() as directory:
        test_missing_root_fails(Path(directory))
    print("PASS: file inventory tests")
