# Deployment Configuration

This directory contains all deployment-related configurations organized by technology:

## 📁 Directory Structure

```
deployment/
├── docker-compose/         # Docker Compose for local development
│   ├── docker-compose.yml      # Development environment
│   ├── docker-compose.prod.yml # Production environment  
│   └── docker-helper.sh         # Development utility script
├── kubernetes/             # Kubernetes for production deployment
│   ├── namespace.yaml          # K8s namespace configuration
│   ├── deployment.yaml         # K8s deployment specification
│   ├── service.yaml            # K8s service configuration
│   ├── configmap.yaml          # K8s configuration management
│   └── deploy.sh               # K8s deployment script
├── config/                 # Shared configuration files
│   ├── nginx.conf              # Nginx reverse proxy config
│   └── init.sql                # Database initialization
├── ci-cd/                  # CI/CD pipeline configuration
│   ├── workflows/              # GitHub Actions workflows
│   └── github-templates/       # GitHub issue/PR templates
└── README.md              # This file
```

## 🐳 Docker Development

All Docker Compose files are in the `docker-compose/` subdirectory:

```bash
# Navigate to docker-compose directory
cd deployment/docker-compose

# Build and run development environment
./docker-helper.sh build
./docker-helper.sh up

# Production deployment
./docker-helper.sh up --prod
```

## ☸️ Kubernetes Production

Kubernetes manifests are in the `kubernetes/` subdirectory:

```bash
# Navigate to kubernetes directory  
cd deployment/kubernetes

# Deploy to Kubernetes cluster
./deploy.sh

# Check deployment status
kubectl get pods -n web-scraper
```

## 🚀 CI/CD Pipeline

GitHub Actions workflows and templates are in the `ci-cd/` subdirectory:

- **workflows/ci.yml**: Complete CI/CD pipeline with testing, building, and deployment
- **github-templates/**: Issue templates, PR templates for professional collaboration

## 📚 Key Features

### Docker Compose Configuration
- **Multi-stage builds**: Dockerfile optimized for production
- **Development tools**: Hot reloading, debugging support  
- **Services**: Redis, PostgreSQL, Nginx integration
- **Security**: Non-root user, health checks

### Kubernetes Configuration
- **Cloud-native**: Production-ready K8s manifests
- **Scalability**: Horizontal pod autoscaling ready
- **Configuration**: ConfigMaps and Secrets management
- **Monitoring**: Readiness and liveness probes

### CI/CD Pipeline
- **Automated testing**: Multi-Python version matrix
- **Quality gates**: Code formatting, linting, type checking
- **Security scanning**: Dependency and container vulnerability checks
- **Automated deployment**: Docker and Kubernetes deployment ready

## 🔧 Quick Setup

1. **Docker Development**:
   ```bash
   cd deployment/docker-compose
   ./docker-helper.sh up
   ```

2. **Kubernetes Production**:
   ```bash
   cd deployment/kubernetes  
   ./deploy.sh
   ```

3. **CI/CD Setup**:
   ```bash
   # Copy workflows back to .github for GitHub to recognize them
   mkdir -p .github
   cp -r deployment/ci-cd/workflows .github/
   cp -r deployment/ci-cd/github-templates .github/
   ```

This organization demonstrates professional project structure and separation of concerns in deployment configurations.
