#!/bin/bash

# Setup script for deployment configurations
# This script helps set up the deployment environment after cloning the repository

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the project root
if [[ ! -f "pyproject.toml" ]]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_status "Setting up deployment configurations..."

# Create .github directory structure for GitHub to recognize
print_status "Setting up GitHub Actions..."
mkdir -p .github

# Copy CI/CD workflows to the correct location
if [[ -d "deployment/ci-cd/workflows" ]]; then
    cp -r deployment/ci-cd/workflows .github/
    print_success "GitHub Actions workflows configured"
else
    print_warning "CI/CD workflows not found in deployment/ci-cd/"
fi

# Copy GitHub templates to the correct location
if [[ -d "deployment/ci-cd/github-templates" ]]; then
    # Copy issue templates
    if [[ -d "deployment/ci-cd/github-templates/ISSUE_TEMPLATE" ]]; then
        cp -r deployment/ci-cd/github-templates/ISSUE_TEMPLATE .github/
    fi
    
    # Copy PR template
    if [[ -f "deployment/ci-cd/github-templates/pull_request_template.md" ]]; then
        cp deployment/ci-cd/github-templates/pull_request_template.md .github/
    fi
    
    print_success "GitHub templates configured"
else
    print_warning "GitHub templates not found in deployment/ci-cd/"
fi

# Make docker helper script executable
if [[ -f "deployment/docker-compose/docker-helper.sh" ]]; then
    chmod +x deployment/docker-compose/docker-helper.sh
    print_success "Docker helper script made executable"
fi

# Copy dockerignore to root for Docker builds
if [[ -f ".dockerignore" ]]; then
    print_success "Docker ignore file already configured"
fi

print_success "Deployment setup complete!"
print_status "Available commands:"
echo "  • Docker development: cd deployment/docker-compose && ./docker-helper.sh up"
echo "  • Docker production:  cd deployment/docker-compose && ./docker-helper.sh up --prod"
echo "  • Run tests in Docker: cd deployment/docker-compose && ./docker-helper.sh test"
echo "  • View container logs:  cd deployment/docker-compose && ./docker-helper.sh logs"
echo "  • Kubernetes deployment: cd deployment/kubernetes && ./deploy.sh"
