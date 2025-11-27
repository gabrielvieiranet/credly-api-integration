#!/bin/bash

# Script to run full historical load test (badges only, 4 pages).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=================================================="
echo "Running Full Historical Load Test (Badges Only)"
echo "=================================================="

# Step 1: Run Step Functions Simulation
echo ""
echo "Step 1: Running Step Functions Simulation..."
# Load type: badges, Mode: historical, Max pages: 4
uv run python "$SCRIPT_DIR/simulate_step_function.py" --load-type badges --mode historical --max-pages 4

# Step 2: Generate Reports
echo ""
echo "Step 2: Generating Reports..."
uv run python "$SCRIPT_DIR/generate_csv_reports.py"

echo ""
echo "=================================================="
echo "✓ Full Historical Test Complete"
echo "=================================================="
