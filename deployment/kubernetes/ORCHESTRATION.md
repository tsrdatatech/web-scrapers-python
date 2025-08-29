# Advanced Kubernetes Orchestration

This document describes the advanced Kubernetes orchestration system for batch web scraping, implementing enterprise-grade patterns similar to AWS Step Functions + Batch but using pure Kubernetes primitives.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Orchestration                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │ Batch           │    │ CronJob          │    │ Manual      │ │
│  │ Orchestrator    │───▶│ Schedulers       │    │ Jobs        │ │
│  │                 │    │                  │    │             │ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
│           │                       │                      │       │
│           ▼                       ▼                      ▼       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Job Queue Manager                       │ │
│  │    • URL Batching        • Resource Management            │ │
│  │    • Job Lifecycle       • Failure Recovery               │ │
│  │    • Monitoring          • Auto-scaling                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                   │                               │
│                                   ▼                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Kubernetes Job Execution Layer                │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │ │
│  │ │ Scraper     │ │ Scraper     │ │ Scraper     │ │   ...   │ │ │
│  │ │ Job Pod 1   │ │ Job Pod 2   │ │ Job Pod 3   │ │         │ │ │
│  │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

Deploy the complete orchestration system:

```bash
# Build and deploy everything
make deploy

# Check status
make status

# Monitor logs
make logs
```

## 📦 Key Components

### Batch Orchestrator (`src/orchestrator.py`)
Advanced Python orchestrator managing the complete job lifecycle:

**Features:**
- URL batching and job creation
- Real-time job monitoring
- Automatic failure recovery and retries
- Resource management and scaling
- Structured logging and metrics

**Configuration:**
```yaml
BATCH_SIZE: "5"              # URLs per batch
MAX_CONCURRENT_JOBS: "20"    # Parallel job limit
JOB_TIMEOUT: "600"          # 10 minute timeout
POLL_INTERVAL: "10"         # Status check interval
```

### Job Templates (`job-template.yaml`)
Secure, optimized templates for batch execution:

**Security:**
- Non-root execution (user 1001)
- Read-only root filesystem
- Dropped Linux capabilities
- Resource limits and requests

**Performance:**
- Optimized resource allocation
- Cache volume mounts
- Anti-affinity for distribution
- Tolerations for dedicated nodes

### CronJobs (`cronjobs.yaml`)
Scheduled orchestration for different parsers:

**Schedules:**
- Generic News: Every hour (`0 * * * *`)
- Weibo: Every 2 hours (`30 */2 * * *`)

**Features:**
- Concurrency control
- History limits
- Resource optimization
- Parser-specific configurations

## 🔧 Management Commands

### Core Operations
```bash
# Deployment
make deploy              # Full deployment with image build
make deploy-fast         # Deploy without image rebuild
make k8s-dry-run        # Validate manifests

# Monitoring
make status             # Show all resource status
make logs               # Orchestrator logs
make events             # Recent cluster events

# Job Management
make job-run            # Create manual job
make job-batch          # Start batch processing
make cron-suspend       # Pause scheduled jobs
make cron-resume        # Resume scheduled jobs
```

### Advanced Operations
```bash
# Scaling
make scale-up           # Scale orchestrator replicas
make restart-orchestrator # Rolling restart

# Debugging
make shell-orchestrator # Shell access
make job-debug          # Debug failed jobs
make port-forward       # Access metrics

# Cleanup
make clean-jobs         # Remove completed jobs
make clean-failed       # Remove failed jobs
make nuke              # Delete entire namespace
```

## 🎛️ Configuration

### Orchestrator Configuration (`orchestrator-config.yaml`)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orchestrator-config
data:
  # Batch processing
  BATCH_SIZE: "5"
  MAX_CONCURRENT_JOBS: "20"
  JOB_TIMEOUT: "600"
  POLL_INTERVAL: "10"
  
  # Resource allocation
  JOB_MEMORY_REQUEST: "512Mi"
  JOB_MEMORY_LIMIT: "1Gi"
  JOB_CPU_REQUEST: "200m"
  JOB_CPU_LIMIT: "800m"
```

### RBAC Security (`orchestrator-config.yaml`)
```yaml
# Minimal permissions for job management
rules:
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
```

## 📊 Monitoring & Observability

### Built-in Features
- **Structured Logging**: JSON logs with correlation IDs
- **Metrics Endpoint**: Prometheus-compatible on port 8080
- **Health Checks**: Liveness and readiness probes
- **Event Tracking**: Kubernetes events for job lifecycle

### Accessing Metrics
```bash
# Port forward metrics
make port-forward

# View metrics
curl http://localhost:8080/metrics
```

### Log Analysis
```bash
# Stream logs
kubectl logs -f deployment/batch-orchestrator -n web-scraper-python

# Search for errors
kubectl logs deployment/batch-orchestrator -n web-scraper-python | grep ERROR

# Job-specific logs
kubectl logs job/scraper-batch-1-1234567890 -n web-scraper-python
```

## 🛡️ Security & Best Practices

### Pod Security Standards
- **Non-root execution**: All containers run as user 1001
- **Read-only filesystem**: Prevents container escapes
- **Capability dropping**: Minimal Linux capabilities
- **Security contexts**: Comprehensive security settings

### Resource Management
- **Resource limits**: Prevent resource exhaustion
- **Quality of Service**: Guaranteed QoS for critical components
- **Node affinity**: Optimal placement strategies
- **Horizontal scaling**: Auto-scaling based on load

### Network Security
- **Service mesh ready**: Compatible with Istio/Linkerd
- **Network policies**: Configurable network isolation
- **TLS support**: Ready for mTLS implementation

## 🔄 Workflow Examples

### Batch Processing Flow
1. **URL Loading**: Orchestrator reads from ConfigMap seed files
2. **Batch Creation**: URLs split into configurable chunk sizes
3. **Job Submission**: Kubernetes Jobs created with proper manifests
4. **Progress Monitoring**: Real-time tracking of job states
5. **Failure Handling**: Automatic retries with exponential backoff
6. **Resource Cleanup**: TTL-based cleanup of completed jobs

### Scheduled Processing Flow
1. **CronJob Trigger**: Kubernetes scheduler activates job
2. **Resource Allocation**: Pod scheduled with resource constraints
3. **Parsing Execution**: Parser runs against configured URLs
4. **Result Processing**: Data validation and storage
5. **Automatic Cleanup**: Pod termination and resource reclamation

## 🔧 Customization & Extension

### Adding New Parsers
1. Implement parser in `src/parsers/new_parser.py`
2. Register in `src/core/parser_registry.py`
3. Add CronJob configuration in `cronjobs.yaml`
4. Update ConfigMap with parser-specific seeds

### Resource Tuning
```yaml
# High-throughput configuration
resources:
  requests:
    cpu: "1"
    memory: "2Gi"
  limits:
    cpu: "4"
    memory: "8Gi"

# Memory-optimized configuration
resources:
  requests:
    cpu: "200m"
    memory: "4Gi"
  limits:
    cpu: "1"
    memory: "16Gi"
```

### Multi-Environment Support
```bash
# Deploy to different environments
NAMESPACE=web-scraper-staging make deploy
NAMESPACE=web-scraper-production make deploy

# Environment-specific configurations
kubectl apply -f overlays/staging/
kubectl apply -f overlays/production/
```

## 🚨 Troubleshooting

### Common Issues

#### Jobs Not Starting
```bash
# Check RBAC permissions
kubectl auth can-i create jobs --as=system:serviceaccount:web-scraper-python:scraper-orchestrator

# Verify resource quotas
kubectl describe resourcequota -n web-scraper-python

# Check node capacity
kubectl describe nodes
```

#### Performance Issues
```bash
# Monitor resource usage
kubectl top pods -n web-scraper-python
kubectl top nodes

# Check job completion times
kubectl get jobs -n web-scraper-python -o wide

# Analyze failed jobs
make job-debug
```

#### Orchestrator Problems
```bash
# Check orchestrator health
kubectl get pods -l app=batch-orchestrator -n web-scraper-python

# Review logs for errors
make logs | grep ERROR

# Restart if needed
make restart-orchestrator
```

## 🔮 Advanced Features

### Integration Capabilities
- **Message Queues**: RabbitMQ/Kafka integration
- **Databases**: PostgreSQL/MongoDB result storage
- **Monitoring Stack**: Prometheus/Grafana integration
- **Alerting**: AlertManager configuration
- **Service Mesh**: Istio/Linkerd compatibility

### Scaling Strategies
- **Horizontal Pod Autoscaling**: Based on CPU/memory metrics
- **Vertical Pod Autoscaling**: Automatic resource optimization
- **Cluster Autoscaling**: Node provisioning based on demand
- **Multi-cluster**: Cross-cluster job distribution

### Operational Excellence
- **GitOps**: ArgoCD/Flux deployment patterns
- **Observability**: Distributed tracing with Jaeger
- **Chaos Engineering**: Chaos Monkey integration
- **Disaster Recovery**: Multi-zone deployment strategies

This orchestration system transforms your web scraper into an enterprise-grade batch processing platform, providing the scalability, reliability, and operational excellence required for production workloads.
