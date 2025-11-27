#!/bin/bash

# Script to run daily ingestion test simulation and validate results.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=================================================="
echo "Running Daily Ingestion Test"
echo "=================================================="

# Step 1: Run Step Functions Simulation
echo ""
echo "Step 1: Running Step Functions Simulation..."
uv run python "$SCRIPT_DIR/simulate_step_function.py"

# Step 2: Generate Reports
echo ""
echo "Step 2: Generating Reports..."
uv run python "$SCRIPT_DIR/generate_csv_reports.py"

echo ""
echo "=================================================="
echo "✓ Daily Test Complete"
echo "=================================================="
