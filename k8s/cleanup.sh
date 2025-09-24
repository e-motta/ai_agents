#!/bin/bash

# Simple cleanup script for CloudWalk Kubernetes manifests
set -e

echo "🧹 Cleaning up CloudWalk Application from Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if kubectl can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Kubernetes cluster connection verified"

echo "🌐 Removing Ingress..."
kubectl delete -f ingress-local.yaml --ignore-not-found=true

# Remove Frontend
echo "🌐 Removing Frontend..."
kubectl delete -f frontend/service.yaml --ignore-not-found=true
kubectl delete -f frontend/deployment.yaml --ignore-not-found=true

# Remove Backend
echo "🔧 Removing Backend..."
kubectl delete -f backend/service.yaml --ignore-not-found=true
kubectl delete -f backend/deployment.yaml --ignore-not-found=true

# Remove Redis
echo "📦 Removing Redis..."
kubectl delete -f redis/service.yaml --ignore-not-found=true
kubectl delete -f redis/statefulset.yaml --ignore-not-found=true
kubectl delete -f redis/configmap.yaml --ignore-not-found=true

# Remove ConfigMap and Secrets
echo "⚙️ Removing Configuration and Secrets..."
kubectl delete -f configmap.yaml --ignore-not-found=true
kubectl delete -f secrets.yaml --ignore-not-found=true

# Secrets are already removed above

echo "✅ Cleanup completed successfully!"
echo ""
echo "🔍 To verify cleanup:"
echo "  kubectl get pods"
echo "  kubectl get services"
echo "  kubectl get ingress"
echo "  kubectl get pvc"