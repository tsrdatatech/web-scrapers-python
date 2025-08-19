# Kubernetes Deployment Guide - Python Web Scraper

This directory contains Kubernetes manifests for deploying the Universal Web Scraper (Python version).

## Quick Start

1. **Apply all manifests:**

   ```bash
   kubectl apply -f k8s/
   ```

2. **Or use the convenience script:**

   ```bash
   ./k8s/deploy.sh
   ```

3. **Check deployment status:**

   ```bash
   kubectl get pods -n web-scraper-python
   kubectl logs -f deployment/web-scraper-python -n web-scraper-python
   ```

4. **Test the service:**
   ```bash
   kubectl port-forward svc/web-scraper-python-service 8081:80 -n web-scraper-python
   ```

## Files

- `namespace.yaml` - Creates isolated namespace for the Python scraper
- `configmap.yaml` - Environment configuration with Python-specific variables
- `deployment.yaml` - Main application deployment with Python runtime optimizations
- `service.yaml` - Internal service for pod communication

## Python-Specific Features

### Environment Configuration

- `PYTHONUNBUFFERED=1` - Ensures real-time log output
- `PYTHONDONTWRITEBYTECODE=1` - Prevents .pyc file creation
- `PYTHONPATH=/app` - Sets proper module resolution

### Resource Allocation

- **Memory**: 512Mi request, 1Gi limit (higher than JS version due to Python overhead)
- **CPU**: 250m request, 500m limit
- **Health checks**: Python-specific commands with longer timeouts

### Storage

- Persistent volumes for `/app/storage` and `/app/logs`
- EmptyDir volumes for single-pod deployments

## Configuration

Edit `configmap.yaml` to modify:

- Log levels and Python runtime settings
- Default parser and concurrency settings
- Playwright browser configuration

## Scaling

Scale the deployment:

```bash
kubectl scale deployment web-scraper-python --replicas=3 -n web-scraper-python
```

## Side-by-Side Deployment

Run both JavaScript and Python versions simultaneously:

```bash
# Deploy both versions
kubectl apply -f ../k8s/          # JavaScript version
kubectl apply -f k8s/             # Python version

# Check both deployments
kubectl get pods -A | grep web-scraper

# Port forward both (different ports)
kubectl port-forward svc/web-scraper-service 8080:80 -n web-scraper &
kubectl port-forward svc/web-scraper-python-service 8081:80 -n web-scraper-python &
```

## Cleanup

Remove Python resources:

```bash
kubectl delete namespace web-scraper-python
```

Remove all web-scraper resources:

```bash
kubectl delete namespace web-scraper web-scraper-python
```
