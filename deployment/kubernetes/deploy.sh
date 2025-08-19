#!/bin/bash

# Simple script to build Docker image and deploy Python web scraper to local Kubernetes
# Requires: Docker, kubectl, and a local Kubernetes cluster (minikube, kind, or Docker Desktop)

set -e

echo "🐍 Building Python Docker image..."
docker build -f deployment/docker/Dockerfile -t universal-web-scraper-python:latest .

echo "☸️  Applying Kubernetes manifests..."
kubectl apply -f k8s/

echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/web-scraper-python -n web-scraper-python

echo "✅ Python deployment complete!"
echo ""
echo "📊 Check status:"
echo "  kubectl get pods -n web-scraper-python"
echo ""
echo "📝 View logs:"
echo "  kubectl logs -f deployment/web-scraper-python -n web-scraper-python"
echo ""
echo "🌐 Port forward to test:"
echo "  kubectl port-forward svc/web-scraper-python-service 8081:80 -n web-scraper-python"
echo ""
echo "🔍 Compare with JavaScript version:"
echo "  kubectl get pods -A | grep web-scraper"
