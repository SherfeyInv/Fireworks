#!/bin/bash

# === Setup Directories ===
ROOT="$HOME/sec_validation"
FILING_DIR="$ROOT/filings"
LOG_DIR="$ROOT/logs"
CSV_FILE="$ROOT/filings_list.csv"

mkdir -p "$FILING_DIR" "$LOG_DIR"

# === Step 1: Download Filings ===
if [ -f "$CSV_FILE" ]; then
    echo "[INFO] Found $CSV_FILE. Downloading filings..."
    tail -n +2 "$CSV_FILE" | while IFS=',' read -r cik accession; do
        acc_clean=$(echo "$accession" | sed 's/-//g')
        filename="${cik}-${accession}.zip"
        url="https://www.sec.gov/Archives/edgar/data/${cik}/${acc_clean}/${filename}"
        dest="$FILING_DIR/$filename"

        if [ ! -f "$dest" ]; then
            echo "[INFO] Downloading $filename"
            wget -q -O "$dest" "$url"
        else
            echo "[INFO] Already exists: $filename"
        fi
    done
else
    echo "[INFO] No CSV file found — skipping download step."
fi

# === Step 2: Validate All Filings ===
for file in "$FILING_DIR"/*.zip; do
    [ -e "$file" ] || continue  # skip if none found

    base=$(basename "$file" .zip)
    log_json="$LOG_DIR/${base}_log.json"
    cleaned_log="$LOG_DIR/${base}_log_cleaned.json"

    echo "[INFO] Validating: $file"

    arelle-cli \
        --file "$file" \
        --plugins validate/EFM \
        --validate \
        --logFile "$log_json"  # removed --logFormat json (was causing crash)

    # === Step 3: Clean Log File (remove nulls) ===
    python3 "$ROOT/clean_nulls.py" "$log_json" "$cleaned_log"
done
