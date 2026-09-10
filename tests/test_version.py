import sys

sys.path.insert(0, "src")
from fireworks.version import FIREWORKS_VERSION, PARSER_VERSION, SCHEMA_VERSION


def main():
    assert FIREWORKS_VERSION == "1.0.0"
    assert PARSER_VERSION == "1.0.0"
    assert SCHEMA_VERSION == "1.0"
    print("PASS: Fireworks version metadata test")


if __name__ == "__main__":
    main()
