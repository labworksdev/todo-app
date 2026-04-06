#!/bin/bash
# Deploy todo-app to Azure Container Apps
# Usage: ./scripts/deploy.sh [tag]
# Default tag: latest

set -e

TAG=${1:-latest}
ACR="labworksacr"
IMAGE="todo-app"
RG="rg-todo-app"
APP="todo-app"
IMAGE_NAME="labworksdev/todo-app"

echo "=== Building and deploying todo-app ==="
echo "Tag: $TAG"
echo ""

# Step 1: Build locally using task
echo "[1/4] Building image locally..."
task build

echo ""

# Step 2: Tag for ACR
echo "[2/4] Tagging image for ACR..."
docker tag "${IMAGE_NAME}:latest" "${ACR}.azurecr.io/${IMAGE}:${TAG}"

echo ""

# Step 3: Push to ACR
echo "[3/4] Pushing to ACR..."
docker push "${ACR}.azurecr.io/${IMAGE}:${TAG}"

echo ""

# Step 4: Update the container app
echo "[4/4] Updating Container App..."
az containerapp update \
  --name "$APP" \
  --resource-group "$RG" \
  --image "${ACR}.azurecr.io/${IMAGE}:${TAG}" \
  --output table

echo ""
echo "=== Deploy complete ==="
