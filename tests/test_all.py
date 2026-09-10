import subprocess
import sys

TESTS = [
    "tests.test_validate",
    "tests.test_provenance",
    "tests.test_extract",
    "tests.test_extract_baseline",
    "tests.test_filing_download",
    "tests.test_version",
    "tests.test_negative",
]


def run_test(name):
    print(f"=== {name} ===")
    result = subprocess.run([sys.executable, "-m", name])
    if result.returncode == 0:
        print(f"PASS: {name}")
        return True
    print(f"FAIL: {name}")
    return False


if __name__ == "__main__":
    passed = 0
    failed = []

    for test in TESTS:
        if run_test(test):
            passed += 1
        else:
            failed.append(test)

    print("=== COMPILATION ===")
    compile_result = subprocess.run([sys.executable, "-m", "compileall", "-q", "src", "tests"])
    if compile_result.returncode == 0:
        print("PASS: compilation")
        passed += 1
    else:
        print("FAIL: compilation")
        failed.append("compilation")

    total = len(TESTS) + 1
    print("=== FIREWORKS TEST SUMMARY ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {len(failed)}/{total}")

    if failed:
        print("FAILED CHECKS:")
        for item in failed:
            print(f"  - {item}")
        sys.exit(1)

    print("ALL FIREWORKS CHECKS PASSED")
