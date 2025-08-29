#!/bin/bash

# Kubernetes Deployment Script for Web Scraper Python
# This script deploys the complete orchestration system including:
# - Namespace and RBAC
# - ConfigMaps and Secrets
# - Batch Orchestrator
# - Job Templates and CronJobs

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE=${NAMESPACE:-"web-scraper-python"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
DRY_RUN=${DRY_RUN:-"false"}
KUBECTL_CMD="kubectl"

if [[ "$DRY_RUN" == "true" ]]; then
    KUBECTL_CMD="kubectl --dry-run=client"
    echo -e "${YELLOW}Running in DRY RUN mode${NC}"
fi

echo -e "${BLUE}🚀 Deploying Web Scraper Python Orchestration System${NC}"
echo -e "${BLUE}Namespace: ${NAMESPACE}${NC}"
echo -e "${BLUE}Image Tag: ${IMAGE_TAG}${NC}"

# Function to check if resource exists
resource_exists() {
    local resource_type=$1
    local resource_name=$2
    local namespace=${3:-""}
    
    if [[ -n "$namespace" ]]; then
        kubectl get "$resource_type" "$resource_name" -n "$namespace" >/dev/null 2>&1
    else
        kubectl get "$resource_type" "$resource_name" >/dev/null 2>&1
    fi
}

# Function to apply manifest with error handling
apply_manifest() {
    local manifest_file=$1
    local description=$2
    
    echo -e "${YELLOW}📄 Applying $description...${NC}"
    
    if [[ ! -f "$manifest_file" ]]; then
        echo -e "${RED}❌ Manifest file not found: $manifest_file${NC}"
        return 1
    fi
    
    if $KUBECTL_CMD apply -f "$manifest_file"; then
        echo -e "${GREEN}✅ Successfully applied $description${NC}"
    else
        echo -e "${RED}❌ Failed to apply $description${NC}"
        return 1
    fi
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check cluster connectivity
echo -e "${YELLOW}🔍 Checking cluster connectivity...${NC}"
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Connected to cluster${NC}"

# Build Docker image if not in dry run mode
if [[ "$DRY_RUN" != "true" ]]; then
    echo -e "${BLUE}🐳 Building Docker image...${NC}"
    docker build -f ../../Dockerfile -t "universal-web-scraper-python:${IMAGE_TAG}" ../..
    echo -e "${GREEN}✅ Docker image built${NC}"
fi

# Create namespace if it doesn't exist
echo -e "${YELLOW}🏗️  Creating namespace...${NC}"
if ! resource_exists "namespace" "$NAMESPACE"; then
    $KUBECTL_CMD create namespace "$NAMESPACE"
    echo -e "${GREEN}✅ Created namespace: $NAMESPACE${NC}"
else
    echo -e "${BLUE}ℹ️  Namespace already exists: $NAMESPACE${NC}"
fi

# Apply manifests in order
echo -e "${BLUE}� Deploying base configuration...${NC}"

# 1. ConfigMaps and Secrets
apply_manifest "configmap.yaml" "ConfigMaps and Seed Data"
apply_manifest "orchestrator-config.yaml" "Orchestrator Configuration and RBAC"

# 2. Core deployment
apply_manifest "deployment.yaml" "Core Web Scraper Deployment"
apply_manifest "service.yaml" "Core Services"

# 3. Orchestrator
apply_manifest "batch-orchestrator.yaml" "Batch Orchestrator"

# 4. Job templates and CronJobs
apply_manifest "job-template.yaml" "Job Template"
apply_manifest "cronjobs.yaml" "Scheduled CronJobs"

echo -e "${BLUE}🔍 Checking deployment status...${NC}"

# Wait for orchestrator to be ready
echo -e "${YELLOW}⏳ Waiting for batch orchestrator to be ready...${NC}"
if $KUBECTL_CMD rollout status deployment/batch-orchestrator -n "$NAMESPACE" --timeout=300s; then
    echo -e "${GREEN}✅ Batch orchestrator is ready${NC}"
else
    echo -e "${RED}❌ Batch orchestrator failed to start${NC}"
    exit 1
fi

# Wait for core deployment to be ready
echo -e "${YELLOW}⏳ Waiting for core scraper to be ready...${NC}"
if $KUBECTL_CMD rollout status deployment/web-scraper-python -n "$NAMESPACE" --timeout=300s; then
    echo -e "${GREEN}✅ Core scraper is ready${NC}"
else
    echo -e "${RED}❌ Core scraper failed to start${NC}"
    exit 1
fi

# Show resource status
echo -e "${BLUE}📊 Deployment Summary${NC}"
echo -e "${YELLOW}Deployments:${NC}"
$KUBECTL_CMD get deployments -n "$NAMESPACE" -o wide

echo -e "${YELLOW}Services:${NC}"
$KUBECTL_CMD get services -n "$NAMESPACE" -o wide

echo -e "${YELLOW}ConfigMaps:${NC}"
$KUBECTL_CMD get configmaps -n "$NAMESPACE"

echo -e "${YELLOW}CronJobs:${NC}"
$KUBECTL_CMD get cronjobs -n "$NAMESPACE" -o wide

echo -e "${YELLOW}ServiceAccounts and RBAC:${NC}"
$KUBECTL_CMD get serviceaccounts,roles,rolebindings -n "$NAMESPACE"

# Show recent events
echo -e "${YELLOW}Recent Events:${NC}"
$KUBECTL_CMD get events -n "$NAMESPACE" --sort-by='.metadata.creationTimestamp' | tail -10

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}💡 Useful Commands:${NC}"
echo -e "  View orchestrator logs:    ${YELLOW}kubectl logs -f deployment/batch-orchestrator -n $NAMESPACE${NC}"
echo -e "  View scraper logs:         ${YELLOW}kubectl logs -f deployment/web-scraper-python -n $NAMESPACE${NC}"
echo -e "  Check job status:          ${YELLOW}kubectl get jobs -n $NAMESPACE${NC}"
echo -e "  Monitor cronjobs:          ${YELLOW}kubectl get cronjobs -n $NAMESPACE -w${NC}"
echo -e "  Port forward orchestrator: ${YELLOW}kubectl port-forward svc/batch-orchestrator 8080:8080 -n $NAMESPACE${NC}"
echo ""
echo -e "${BLUE}🔧 Management:${NC}"
echo -e "  Scale orchestrator:        ${YELLOW}kubectl scale deployment batch-orchestrator --replicas=2 -n $NAMESPACE${NC}"
echo -e "  Trigger manual job:        ${YELLOW}kubectl create job --from=cronjob/scraper-generic-news manual-run -n $NAMESPACE${NC}"
echo -e "  Delete deployment:         ${YELLOW}kubectl delete namespace $NAMESPACE${NC}"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}⚠️  This was a DRY RUN. No resources were actually created.${NC}"
    echo -e "${YELLOW}   To deploy for real, run: DRY_RUN=false ./deploy.sh${NC}"
fi

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
