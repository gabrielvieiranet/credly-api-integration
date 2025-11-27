#!/bin/bash

# Script to reset the environment: clean resources, recreate infra, and populate secrets.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=================================================="
echo "Resetting Environment"
echo "=================================================="

# Step 1: Clean and Recreate Infrastructure
echo ""
echo "Step 1: Recreating Infrastructure..."
"$SCRIPT_DIR/setup_infra.sh"

# Step 2: Populate Secrets
echo ""
echo "Step 2: Populating Secrets..."
"$SCRIPT_DIR/update_local_token.sh"

echo ""
echo "=================================================="
echo "✓ Environment Reset Complete"
echo "=================================================="
