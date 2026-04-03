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

echo "=== Building and deploying todo-app ==="
echo "Tag: $TAG"
echo ""

# Build and push to ACR
echo "[1/2] Building image in Azure Container Registry..."
az acr build \
  --registry $ACR \
  --image $IMAGE:$TAG \
  --file Dockerfile \
  .

echo ""

# Update the container app
echo "[2/2] Updating Container App..."
az containerapp update \
  --name $APP \
  --resource-group $RG \
  --image $ACR.azurecr.io/$IMAGE:$TAG \
  --output table

echo ""
echo "=== Deploy complete ==="
echo "App URL: https://todo-app.happysmoke-64bbe2ef.eastus.azurecontainerapps.io/"
