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
echo "[1/5] Building image locally..."
task build

echo ""

# Step 2: Verify image exists
echo "[2/5] Verifying image was built..."
if ! docker image inspect "${IMAGE_NAME}:latest" > /dev/null 2>&1; then
  echo "ERROR: Image ${IMAGE_NAME}:latest not found after build" >&2
  exit 1
fi

echo ""

# Step 3: Tag for ACR
echo "[3/5] Tagging image for ACR..."
docker tag "${IMAGE_NAME}:latest" "${ACR}.azurecr.io/${IMAGE}:${TAG}"

echo ""

# Step 4: Push to ACR
echo "[4/5] Pushing to ACR..."
docker push "${ACR}.azurecr.io/${IMAGE}:${TAG}"

echo ""

# Step 5: Verify image in ACR
echo "[5/6] Verifying image exists in ACR..."
if ! az acr repository show-tags --name "$ACR" --repository "$IMAGE" --filter "$TAG" --output tsv | grep -q "$TAG"; then
  echo "ERROR: Image ${ACR}.azurecr.io/${IMAGE}:${TAG} not found in ACR" >&2
  exit 1
fi

echo ""

# Step 6: Update the container app
echo "[6/6] Updating Container App..."
az containerapp update \
  --name "$APP" \
  --resource-group "$RG" \
  --image "${ACR}.azurecr.io/${IMAGE}:${TAG}" \
  --output table

echo ""
echo "=== Deploy complete ==="
