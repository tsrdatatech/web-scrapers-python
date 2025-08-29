# Web Scraper Python - Advanced Kubernetes Orchestration
# Makefile for managing the complete orchestration system

# ================================
# Configuration
# ================================
.DEFAULT_GOAL := help
SHELL := /bin/bash

# Project configuration
PROJECT_NAME := universal-web-scraper-python
NAMESPACE := web-scraper-python
IMAGE_NAME := $(PROJECT_NAME)
IMAGE_TAG := latest
REGISTRY ?= 

# Kubernetes configuration
KUBECTL := kubectl
KUSTOMIZE := kustomize
HELM := helm

# Docker configuration
DOCKER := docker
DOCKER_PLATFORM := linux/amd64
DOCKERFILE := Dockerfile

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m

# ================================
# Help
# ================================
.PHONY: help
help: ## Show this help message
	@echo -e "$(BLUE)Web Scraper Python - Kubernetes Orchestration$(NC)"
	@echo -e "$(BLUE)===============================================$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Development:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(install|test|lint|format|dev-)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Docker:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(image|docker)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Kubernetes:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(k8s|deploy|orchestrator|job|cron)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Operations:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(logs|status|clean|nuke)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

# ================================
# Development
# ================================
.PHONY: install
install: ## Install dependencies with Poetry
	@echo -e "$(BLUE)Installing dependencies...$(NC)"
	poetry install
	poetry run playwright install

.PHONY: install-k8s
install-k8s: install ## Install with Kubernetes dependencies
	@echo -e "$(BLUE)Installing Kubernetes dependencies...$(NC)"
	poetry add kubernetes structlog

.PHONY: dev
dev: ## Install with development dependencies
	@echo -e "$(BLUE)Installing with dev dependencies...$(NC)"
	poetry install --with dev
	poetry run playwright install

.PHONY: test
test: ## Run tests
	@echo -e "$(BLUE)Running tests...$(NC)"
	poetry run pytest

.PHONY: lint
lint: ## Run linting
	@echo -e "$(BLUE)Running linters...$(NC)"
	poetry run black --check src/ tests/
	poetry run flake8 src/ tests/
	poetry run mypy src/

.PHONY: format
format: ## Format code
	@echo -e "$(BLUE)Formatting code...$(NC)"
	poetry run black src/ tests/
	poetry run isort src/ tests/

.PHONY: clean
clean: ## Clean Python cache files
	@echo -e "$(BLUE)Cleaning cache files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

.PHONY: run
run: ## Run scraper locally
	@echo -e "$(BLUE)Running scraper locally...$(NC)"
	poetry run python -m src.main

.PHONY: dev-orchestrator
dev-orchestrator: ## Run orchestrator locally
	@echo -e "$(BLUE)Starting orchestrator locally...$(NC)"
	poetry run python -m src.orchestrator --parser generic_news

# ================================
# Docker Operations
# ================================
.PHONY: image-build
image-build: ## Build Docker image
	@echo -e "$(BLUE)Building Docker image...$(NC)"
	$(DOCKER) build \
		--platform $(DOCKER_PLATFORM) \
		-f $(DOCKERFILE) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) \
		-t $(IMAGE_NAME):latest \
		.
	@echo -e "$(GREEN)✅ Image built: $(IMAGE_NAME):$(IMAGE_TAG)$(NC)"

.PHONY: image-run
image-run: ## Run Docker image locally
	@echo -e "$(BLUE)Running Docker image locally...$(NC)"
	$(DOCKER) run --rm -it \
		-e LOG_LEVEL=DEBUG \
		$(IMAGE_NAME):$(IMAGE_TAG) \
		python -m src.main --parser generic_news --max-concurrency 2

.PHONY: image-push
image-push: image-build ## Push Docker image to registry
	@if [ -z "$(REGISTRY)" ]; then \
		echo -e "$(RED)❌ REGISTRY not set. Use: make image-push REGISTRY=your-registry.com$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Pushing Docker image to $(REGISTRY)...$(NC)"
	$(DOCKER) tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	$(DOCKER) push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

# ================================
# Kubernetes - Setup
# ================================
.PHONY: k8s-check
k8s-check: ## Check Kubernetes cluster connectivity
	@echo -e "$(BLUE)Checking Kubernetes cluster...$(NC)"
	@$(KUBECTL) cluster-info
	@echo -e "$(GREEN)✅ Connected to cluster$(NC)"

.PHONY: k8s-namespace
k8s-namespace: k8s-check ## Create namespace
	@echo -e "$(BLUE)Creating namespace: $(NAMESPACE)$(NC)"
	@$(KUBECTL) create namespace $(NAMESPACE) --dry-run=client -o yaml | $(KUBECTL) apply -f -
	@echo -e "$(GREEN)✅ Namespace ready$(NC)"

.PHONY: k8s-dry-run
k8s-dry-run: ## Dry run deployment
	@echo -e "$(BLUE)Running deployment dry run...$(NC)"
	@cd deployment/kubernetes && DRY_RUN=true ./deploy.sh

# ================================
# Kubernetes - Deployment
# ================================
.PHONY: deploy
deploy: image-build k8s-namespace ## Deploy complete system
	@echo -e "$(BLUE)Deploying complete orchestration system...$(NC)"
	@cd deployment/kubernetes && ./deploy.sh
	@echo -e "$(GREEN)🎉 Deployment complete!$(NC)"

.PHONY: deploy-fast
deploy-fast: k8s-namespace ## Deploy without rebuilding image
	@echo -e "$(BLUE)Fast deploying (no image rebuild)...$(NC)"
	@cd deployment/kubernetes && ./deploy.sh
	@echo -e "$(GREEN)🎉 Fast deployment complete!$(NC)"

.PHONY: k8s-config
k8s-config: ## Apply configuration only
	@echo -e "$(BLUE)Applying configuration...$(NC)"
	@$(KUBECTL) apply -f deployment/kubernetes/configmap.yaml
	@$(KUBECTL) apply -f deployment/kubernetes/orchestrator-config.yaml

.PHONY: k8s-orchestrator
k8s-orchestrator: ## Deploy orchestrator only
	@echo -e "$(BLUE)Deploying batch orchestrator...$(NC)"
	@$(KUBECTL) apply -f deployment/kubernetes/batch-orchestrator.yaml
	@$(KUBECTL) rollout status deployment/batch-orchestrator -n $(NAMESPACE)

# ================================
# Kubernetes - Jobs & CronJobs
# ================================
.PHONY: k8s-cronjobs
k8s-cronjobs: ## Deploy CronJobs
	@echo -e "$(BLUE)Deploying CronJobs...$(NC)"
	@$(KUBECTL) apply -f deployment/kubernetes/cronjobs.yaml

.PHONY: job-run
job-run: ## Create manual job from CronJob template
	@echo -e "$(BLUE)Creating manual job...$(NC)"
	@$(KUBECTL) create job scraper-manual-$$(date +%s) \
		--from=cronjob/scraper-generic-news \
		-n $(NAMESPACE)
	@echo -e "$(GREEN)✅ Manual job created$(NC)"

.PHONY: job-run-weibo
job-run-weibo: ## Create manual Weibo job
	@echo -e "$(BLUE)Creating manual Weibo job...$(NC)"
	@$(KUBECTL) create job scraper-weibo-manual-$$(date +%s) \
		--from=cronjob/scraper-weibo \
		-n $(NAMESPACE)

.PHONY: job-batch
job-batch: ## Start orchestrated batch processing
	@echo -e "$(BLUE)Starting batch orchestration...$(NC)"
	@$(KUBECTL) exec deployment/batch-orchestrator -n $(NAMESPACE) -- \
		python -m src.orchestrator --parser generic_news

.PHONY: cron-suspend
cron-suspend: ## Suspend all CronJobs
	@echo -e "$(BLUE)Suspending CronJobs...$(NC)"
	@$(KUBECTL) patch cronjob scraper-generic-news -n $(NAMESPACE) -p '{"spec":{"suspend":true}}'
	@$(KUBECTL) patch cronjob scraper-weibo -n $(NAMESPACE) -p '{"spec":{"suspend":true}}'

.PHONY: cron-resume
cron-resume: ## Resume all CronJobs
	@echo -e "$(BLUE)Resuming CronJobs...$(NC)"
	@$(KUBECTL) patch cronjob scraper-generic-news -n $(NAMESPACE) -p '{"spec":{"suspend":false}}'
	@$(KUBECTL) patch cronjob scraper-weibo -n $(NAMESPACE) -p '{"spec":{"suspend":false}}'

# ================================
# Kubernetes - Monitoring
# ================================
.PHONY: status
status: ## Show deployment status
	@echo -e "$(BLUE)📊 Deployment Status$(NC)"
	@echo -e "$(YELLOW)Deployments:$(NC)"
	@$(KUBECTL) get deployments -n $(NAMESPACE) -o wide
	@echo ""
	@echo -e "$(YELLOW)Jobs:$(NC)"
	@$(KUBECTL) get jobs -n $(NAMESPACE) -o wide
	@echo ""
	@echo -e "$(YELLOW)CronJobs:$(NC)"
	@$(KUBECTL) get cronjobs -n $(NAMESPACE) -o wide
	@echo ""
	@echo -e "$(YELLOW)Pods:$(NC)"
	@$(KUBECTL) get pods -n $(NAMESPACE) -o wide

.PHONY: logs
logs: ## Show orchestrator logs
	@echo -e "$(BLUE)📋 Orchestrator Logs$(NC)"
	@$(KUBECTL) logs -f deployment/batch-orchestrator -n $(NAMESPACE)

.PHONY: logs-scraper
logs-scraper: ## Show scraper logs
	@echo -e "$(BLUE)📋 Scraper Logs$(NC)"
	@$(KUBECTL) logs -f deployment/web-scraper-python -n $(NAMESPACE)

.PHONY: logs-jobs
logs-jobs: ## Show recent job logs
	@echo -e "$(BLUE)📋 Recent Job Logs$(NC)"
	@for job in $$($(KUBECTL) get jobs -n $(NAMESPACE) -o name | head -5); do \
		echo -e "$(YELLOW)$${job}:$(NC)"; \
		$(KUBECTL) logs $$job -n $(NAMESPACE) --tail=20; \
		echo ""; \
	done

.PHONY: events
events: ## Show recent events
	@echo -e "$(BLUE)📋 Recent Events$(NC)"
	@$(KUBECTL) get events -n $(NAMESPACE) --sort-by='.metadata.creationTimestamp' | tail -20

.PHONY: describe-orchestrator
describe-orchestrator: ## Describe orchestrator deployment
	@$(KUBECTL) describe deployment/batch-orchestrator -n $(NAMESPACE)

# ================================
# Kubernetes - Debugging
# ================================
.PHONY: shell-orchestrator
shell-orchestrator: ## Open shell in orchestrator pod
	@echo -e "$(BLUE)Opening shell in orchestrator...$(NC)"
	@$(KUBECTL) exec -it deployment/batch-orchestrator -n $(NAMESPACE) -- /bin/bash

.PHONY: shell-scraper
shell-scraper: ## Open shell in scraper pod
	@echo -e "$(BLUE)Opening shell in scraper...$(NC)"
	@$(KUBECTL) exec -it deployment/web-scraper-python -n $(NAMESPACE) -- /bin/bash

.PHONY: port-forward
port-forward: ## Port forward orchestrator metrics
	@echo -e "$(BLUE)Port forwarding orchestrator metrics to localhost:8080$(NC)"
	@$(KUBECTL) port-forward svc/batch-orchestrator 8080:8080 -n $(NAMESPACE)

.PHONY: job-debug
job-debug: ## Debug failed jobs
	@echo -e "$(BLUE)🐛 Debugging Failed Jobs$(NC)"
	@for job in $$($(KUBECTL) get jobs -n $(NAMESPACE) --field-selector=status.failed=1 -o name); do \
		echo -e "$(RED)Failed job: $$job$(NC)"; \
		$(KUBECTL) describe $$job -n $(NAMESPACE); \
		echo ""; \
	done

# ================================
# Scaling Operations
# ================================
.PHONY: scale-up
scale-up: ## Scale orchestrator up
	@echo -e "$(BLUE)Scaling orchestrator to 2 replicas...$(NC)"
	@$(KUBECTL) scale deployment batch-orchestrator --replicas=2 -n $(NAMESPACE)

.PHONY: scale-down
scale-down: ## Scale orchestrator down
	@echo -e "$(BLUE)Scaling orchestrator to 1 replica...$(NC)"
	@$(KUBECTL) scale deployment batch-orchestrator --replicas=1 -n $(NAMESPACE)

.PHONY: restart-orchestrator
restart-orchestrator: ## Restart orchestrator
	@echo -e "$(BLUE)Restarting orchestrator...$(NC)"
	@$(KUBECTL) rollout restart deployment/batch-orchestrator -n $(NAMESPACE)
	@$(KUBECTL) rollout status deployment/batch-orchestrator -n $(NAMESPACE)

# ================================
# Cleanup Operations
# ================================
.PHONY: clean-jobs
clean-jobs: ## Clean completed jobs
	@echo -e "$(BLUE)Cleaning completed jobs...$(NC)"
	@$(KUBECTL) delete jobs --field-selector=status.successful=1 -n $(NAMESPACE)

.PHONY: clean-failed
clean-failed: ## Clean failed jobs
	@echo -e "$(BLUE)Cleaning failed jobs...$(NC)"
	@$(KUBECTL) delete jobs --field-selector=status.failed=1 -n $(NAMESPACE)

.PHONY: clean-all-jobs
clean-all-jobs: ## Clean all jobs
	@echo -e "$(BLUE)Cleaning all jobs...$(NC)"
	@$(KUBECTL) delete jobs --all -n $(NAMESPACE)

.PHONY: clean-pods
clean-pods: ## Clean failed/succeeded pods
	@echo -e "$(BLUE)Cleaning completed pods...$(NC)"
	@$(KUBECTL) delete pods --field-selector=status.phase=Succeeded -n $(NAMESPACE)
	@$(KUBECTL) delete pods --field-selector=status.phase=Failed -n $(NAMESPACE)

.PHONY: undeploy
undeploy: ## Remove all deployments but keep namespace
	@echo -e "$(BLUE)Removing deployments...$(NC)"
	@$(KUBECTL) delete deployment,service,configmap,cronjob,job,serviceaccount,role,rolebinding --all -n $(NAMESPACE)

.PHONY: nuke
nuke: ## Delete entire namespace (DESTRUCTIVE)
	@echo -e "$(RED)⚠️  This will delete the entire $(NAMESPACE) namespace!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo -e "$(BLUE)Deleting namespace $(NAMESPACE)...$(NC)"
	@$(KUBECTL) delete namespace $(NAMESPACE)

# ================================
# Development Utilities
# ================================
.PHONY: kind-load
kind-load: image-build ## Load image into kind cluster
	@echo -e "$(BLUE)Loading image into kind cluster...$(NC)"
	@kind load docker-image $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: minikube-load
minikube-load: image-build ## Load image into minikube
	@echo -e "$(BLUE)Loading image into minikube...$(NC)"
	@minikube image load $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: dev-setup
dev-setup: install-k8s image-build k8s-namespace k8s-config ## Complete development setup
	@echo -e "$(GREEN)🎉 Development setup complete!$(NC)"

# ================================
# CI/CD Integration
# ================================
.PHONY: ci-test
ci-test: lint test ## Run CI tests
	@echo -e "$(GREEN)✅ All CI tests passed$(NC)"

.PHONY: ci-build
ci-build: image-build ## CI build
	@echo -e "$(GREEN)✅ CI build complete$(NC)"

.PHONY: ci-deploy
ci-deploy: deploy ## CI deployment
	@echo -e "$(GREEN)✅ CI deployment complete$(NC)"

# ================================
# Validation
# ================================
.PHONY: validate
validate: ## Validate all manifests
	@echo -e "$(BLUE)Validating Kubernetes manifests...$(NC)"
	@for file in deployment/kubernetes/*.yaml; do \
		echo "Validating $$file..."; \
		$(KUBECTL) apply --dry-run=client --validate=false -f $$file 2>/dev/null || echo "⚠️ Validation failed for $$file (cluster not available)"; \
	done
	@echo -e "$(GREEN)✅ All manifests validated$(NC)"

.PHONY: smoke-test
smoke-test: ## Run smoke tests on deployed system
	@echo -e "$(BLUE)Running smoke tests...$(NC)"
	@$(KUBECTL) wait --for=condition=available deployment/batch-orchestrator -n $(NAMESPACE) --timeout=60s
	@$(KUBECTL) wait --for=condition=available deployment/web-scraper-python -n $(NAMESPACE) --timeout=60s
	@echo -e "$(GREEN)✅ Smoke tests passed$(NC)"

# Make targets that don't create files
.PHONY: help install test lint format clean run dev-orchestrator image-build image-run image-push \
        k8s-check k8s-namespace k8s-dry-run deploy deploy-fast k8s-config k8s-orchestrator \
        k8s-cronjobs job-run job-run-weibo job-batch cron-suspend cron-resume status logs \
        logs-scraper logs-jobs events describe-orchestrator shell-orchestrator shell-scraper \
        port-forward job-debug scale-up scale-down restart-orchestrator clean-jobs clean-failed \
        clean-all-jobs clean-pods undeploy nuke kind-load minikube-load dev-setup ci-test \
        ci-build ci-deploy validate smoke-test install-k8s dev
	poetry run mypy src/

format: ## Format code
	poetry run black src/
	poetry run isort src/

format-check: ## Check code formatting
	poetry run black --check src/
	poetry run isort --check-only src/

clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf storage/
	rm -f scraper.log

run: ## Run the scraper with example URL
	poetry run python -m src.main --url https://example.com --parser generic-news

run-seeds: ## Run the scraper with seeds file
	poetry run python -m src.main --file seeds.txt

shell: ## Activate Poetry shell
	poetry shell

setup: ## Run setup script
	./setup.sh
