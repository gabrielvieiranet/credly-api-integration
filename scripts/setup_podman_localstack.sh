#!/bin/bash

# Script to configure and start LocalStack with Podman rootless support
# Based on: https://docs.localstack.cloud/aws/capabilities/config/podman/#rootless-podman

set -e

echo "=================================================="
echo "LocalStack Podman Rootless Configuration"
echo "=================================================="

# Step 1: Check Podman installation
echo ""
echo "Step 1: Checking Podman installation..."
if ! command -v podman &> /dev/null; then
    echo "✗ Podman not found. Please install Podman first."
    exit 1
fi

PODMAN_VERSION=$(podman --version)
echo "✓ Podman installed: $PODMAN_VERSION"

# Step 2: Start Podman socket service
echo ""
echo "Step 2: Starting Podman socket service..."

# Check if systemd is available
if command -v systemctl &> /dev/null; then
    echo "Starting podman.service (user-level)..."
    systemctl --user start podman.service || echo "⚠ Could not start via systemctl, trying manual socket activation..."
    
    # Verify socket is running
    if systemctl --user is-active --quiet podman.service; then
        echo "✓ Podman socket service is running"
    else
        echo "⚠ Starting socket manually..."
        podman system service --time=0 unix:///run/user/$(id -u)/podman/podman.sock &
        sleep 2
    fi
else
    echo "systemctl not available, starting socket manually..."
    podman system service --time=0 unix:///run/user/$(id -u)/podman/podman.sock &
    sleep 2
fi

# Step 3: Verify socket exists
PODMAN_SOCK="/run/user/$(id -u)/podman/podman.sock"
echo ""
echo "Step 3: Verifying Podman socket..."
echo "Socket path: $PODMAN_SOCK"

if [ -S "$PODMAN_SOCK" ]; then
    echo "✓ Podman socket exists"
else
    echo "✗ Podman socket not found at $PODMAN_SOCK"
    echo "Trying to create it..."
    mkdir -p "$(dirname $PODMAN_SOCK)"
    podman system service --time=0 "unix://$PODMAN_SOCK" &
    sleep 3
    
    if [ ! -S "$PODMAN_SOCK" ]; then
        echo "✗ Failed to create Podman socket"
        exit 1
    fi
fi

# Step 4: Update docker-compose.yml with correct user ID
echo ""
echo "Step 4: Updating docker-compose.yml with current user ID..."
USER_ID=$(id -u)
echo "User ID: $USER_ID"

# Update docker-compose.yml to use correct user ID
sed -i.bak "s|/run/user/1000/podman/podman.sock|/run/user/$USER_ID/podman/podman.sock|g" docker-compose.yml
echo "✓ docker-compose.yml updated"

# Step 5: Start LocalStack
echo ""
echo "Step 5: Starting LocalStack with Podman..."
echo ""
echo "Starting containers..."
docker-compose up -d

# Wait for LocalStack to be ready
echo ""
echo "Waiting for LocalStack to be ready..."
READY=false
MAX_WAIT=30
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:4566/_localstack/health | grep -q "\"running\""; then
        READY=true
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    echo -n "."
done
echo ""

if [ "$READY" = true ]; then
    echo "✓ LocalStack is ready!"
    echo ""
    echo "Health check:"
    curl -s http://localhost:4566/_localstack/health | jq .
else
    echo "⚠ Timeout waiting for LocalStack"
    echo "Check logs with: docker-compose logs"
fi

echo ""
echo "=================================================="
echo "✓ LocalStack with Podman configured successfully"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Run infrastructure setup: ./scripts/setup_infra.sh"
echo "2. Test Lambda deployment with: ./scripts/test_step_function_real.sh"
