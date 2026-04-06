#!/bin/bash
# Deploy todo-app to Azure Container Apps
# Usage: ./scripts/deploy.sh [tag]
# Default tag: latest

set -e

TAG=${1:-latest}

echo "=== Building and deploying todo-app ==="
echo "Tag: $TAG"
echo ""

echo "[1/3] Building image..."
task build

echo ""
echo "[2/3] Distributing image to ACR..."
IMAGE_TAG="$TAG" task distribute

echo ""
echo "[3/3] Deploying to Container Apps..."
IMAGE_TAG="$TAG" task deploy

echo ""
echo "=== Deploy complete ==="
