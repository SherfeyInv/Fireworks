import importlib
import inspect
import subprocess
import sys
import tempfile
from pathlib import Path

TESTS = [
    "tests.test_validate",
    "tests.test_provenance",
    "tests.test_extract",
    "tests.test_extract_baseline",
    "tests.test_filing_download",
    "tests.test_version",
    "tests.test_negative",
    "tests.test_file_inventory",
    "tests.test_identity",
]


def run_test_module(name):
    print(f"=== {name} ===")
    module = importlib.import_module(name)
    tests = [
        getattr(module, attr)
        for attr in sorted(dir(module))
        if attr.startswith("test_") and callable(getattr(module, attr))
    ]

    if not tests:
        result = subprocess.run([sys.executable, "-m", name])
        if result.returncode == 0:
            print(f"PASS: {name}")
            return 1, []
        print(f"FAIL: {name}")
        return 0, [name]

    passed = 0
    failed = []

    for test in tests:
        try:
            parameters = inspect.signature(test).parameters
            if "tmp_path" in parameters:
                with tempfile.TemporaryDirectory() as directory:
                    test(Path(directory))
            else:
                test()
            print(f"PASS: {test.__name__}")
            passed += 1
        except Exception as exc:
            print(f"FAIL: {test.__name__}: {exc}")
            failed.append(f"{name}.{test.__name__}")

    return passed, failed


if __name__ == "__main__":
    passed = 0
    failed = []

    for test_module in TESTS:
        module_passed, module_failed = run_test_module(test_module)
        passed += module_passed
        failed.extend(module_failed)

    print("=== COMPILATION ===")
    compile_result = subprocess.run([sys.executable, "-m", "compileall", "-q", "src", "tests"])
    if compile_result.returncode == 0:
        print("PASS: compilation")
        passed += 1
    else:
        print("FAIL: compilation")
        failed.append("compilation")

    total = passed + len(failed)
    print("=== FIREWORKS TEST SUMMARY ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {len(failed)}/{total}")

    if failed:
        print("FAILED CHECKS:")
        for item in failed:
            print(f"  - {item}")
        sys.exit(1)

    print("ALL FIREWORKS CHECKS PASSED")
