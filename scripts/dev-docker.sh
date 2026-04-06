#!/bin/bash
# Build and run todo-app locally with Docker
# Usage: ./scripts/dev-docker.sh

set -e

IMAGE_NAME="labworksdev/todo-app"

echo "=== Building todo-app container ==="
task build

echo ""
echo "=== Starting todo-app ==="
echo "Open http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

docker run --rm -p 8000:8000 "${IMAGE_NAME}:latest"
