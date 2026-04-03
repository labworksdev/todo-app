#!/bin/bash
# Build and run todo-app locally with Docker
# Usage: ./scripts/dev.sh

set -e

echo "=== Building todo-app container ==="
docker build -t todo-app .

echo ""
echo "=== Starting todo-app ==="
echo "Open http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

docker run --rm -p 8000:8000 todo-app
