import json
import sys

def remove_nulls(data):
    if isinstance(data, dict):
        return {k: remove_nulls(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [remove_nulls(i) for i in data if i is not None]
    else:
        return data

if __name__ == "__main__":
    infile = sys.argv[1]
    outfile = sys.argv[2]

    with open(infile, "r") as f:
        data = json.load(f)

    cleaned = remove_nulls(data)

    with open(outfile, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"Cleaned log written to {outfile}")
