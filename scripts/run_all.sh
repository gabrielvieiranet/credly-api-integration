#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "--- Step 1: Cleaning ---"
./scripts/clean_all.sh

echo ""
echo "--- Step 2: Running Full Test Suite ---"
uv run python scripts/run_full_test_suite.py

echo ""
echo "--- Step 3: Generating Reports ---"
uv run python scripts/generate_csv_reports.py

echo ""
echo "--- All Done! ---"
