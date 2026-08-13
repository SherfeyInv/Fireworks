#!/bin/bash

set -u

# ============================================================
# FIREWORKS — SEC/XBRL Validation Pipeline
# ============================================================

FIREWORKS="$HOME/fireworks"
VENV="$FIREWORKS/venv"
PYTHON="$VENV/bin/python"
ARELLE="$FIREWORKS/venv/bin/arelleCmdLine"

FILING_DIR="$FIREWORKS/filings"
LOG_DIR="$FIREWORKS/logs"
CSV_FILE="$FIREWORKS/filings_list.csv"
CLEAN_NULLS="$FIREWORKS/clean_nulls.py"

mkdir -p "$FILING_DIR" "$LOG_DIR"

echo "=========================================="
echo " FIREWORKS — SEC FILING VALIDATION"
echo "=========================================="
echo

# ------------------------------------------------------------
# Verify environment
# ------------------------------------------------------------

if [ ! -x "$PYTHON" ]; then
    echo "[ERROR] Python virtual environment not found:"
    echo "        $PYTHON"
    exit 1
fi

if [ ! -f "$CLEAN_NULLS" ]; then
    echo "[ERROR] Missing:"
    echo "        $CLEAN_NULLS"
    exit 1
fi

# Arelle may not have installed the console wrapper, so use
# the Python module directly if necessary.
if [ -x "$ARELLE" ]; then
    ARELLE_CMD="$ARELLE"
else
    ARELLE_CMD="$PYTHON $HOME/Arelle/arelleCmdLine.py"
fi

echo "[INFO] Python: $PYTHON"
echo "[INFO] Arelle: $ARELLE_CMD"
echo

# ------------------------------------------------------------
# Download filings
# ------------------------------------------------------------

if [ ! -f "$CSV_FILE" ]; then
    echo "[ERROR] Filing list not found:"
    echo "        $CSV_FILE"
    exit 1
fi

echo "[INFO] Filing list:"
echo "       $CSV_FILE"
echo

tail -n +2 "$CSV_FILE" | while IFS=',' read -r cik accession; do

    # Remove whitespace
    cik=$(echo "$cik" | xargs)
    accession=$(echo "$accession" | xargs)

    # Skip empty lines
    [ -z "$cik" ] && continue
    [ -z "$accession" ] && continue

    acc_clean=$(echo "$accession" | tr -d '-')

    filename="${cik}-${accession}.zip"

    url="https://www.sec.gov/Archives/edgar/data/${cik}/${acc_clean}/${filename}"

    dest="$FILING_DIR/$filename"

    echo "[INFO] Downloading:"
    echo "       $url"

    if [ -s "$dest" ]; then
        echo "[INFO] Already exists:"
        echo "       $dest"
    else
        rm -f "$dest"

        if wget \
            --user-agent="Aysher Intelligence Agency research contact@example.com" \
            -q \
            -O "$dest" \
            "$url"
        then

            if [ -s "$dest" ]; then
                echo "[OK] Downloaded: $filename"
            else
                echo "[ERROR] Download produced an empty file:"
                echo "        $dest"
                rm -f "$dest"
            fi

        else
            echo "[ERROR] Download failed:"
            echo "        $url"
            rm -f "$dest"
        fi
    fi

    echo

done

# ------------------------------------------------------------
# Validate filings
# ------------------------------------------------------------

shopt -s nullglob

files=("$FILING_DIR"/*.zip)

if [ ${#files[@]} -eq 0 ]; then
    echo "[WARN] No ZIP filings found in:"
    echo "       $FILING_DIR"
    echo
    echo "[INFO] Pipeline stopped."
    exit 0
fi

echo "=========================================="
echo " VALIDATING ${#files[@]} FILING(S)"
echo "=========================================="
echo

for file in "${files[@]}"; do

    base=$(basename "$file" .zip)

    log_json="$LOG_DIR/${base}_log.json"
    cleaned_log="$LOG_DIR/${base}_log_cleaned.json"

    echo "[INFO] Validating:"
    echo "       $file"

    if "$PYTHON" "$HOME/Arelle/arelleCmdLine.py" \
        --file "$file" \
        --plugins validate/EFM \
        --validate \
        --logFile "$log_json"
    then
        echo "[OK] Arelle validation completed."
    else
        echo "[WARN] Arelle returned a validation error."
    fi

    if [ -f "$log_json" ]; then
        "$PYTHON" "$CLEAN_NULLS" \
            "$log_json" \
            "$cleaned_log"

        echo "[OK] Cleaned log:"
        echo "     $cleaned_log"
    else
        echo "[WARN] No Arelle log was produced."
    fi

    echo

done

echo "=========================================="
echo " FIREWORKS COMPLETE"
echo "=========================================="
echo
echo "[INFO] Filings:"
echo "       $FILING_DIR"
echo
echo "[INFO] Logs:"
echo "       $LOG_DIR"
echo
