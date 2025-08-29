#!/usr/bin/env python3
"""
Kubernetes Batch Orchestrator for Web Scraper

This orchestrator manages batch scraping jobs using Kubernetes Jobs,
similar to AWS Step Functions + Batch but using pure K8s primitives.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from kubernetes import client
    from kubernetes import config as k8s_config
    from kubernetes.client.rest import ApiException
except ImportError:
    print("Kubernetes client not installed. Install with: pip install kubernetes")
    sys.exit(1)

try:
    import structlog
except ImportError:
    print("Structlog not installed. Install with: pip install structlog")
    sys.exit(1)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class OrchestratorConfig:
    """Configuration for the batch orchestrator"""

    def __init__(self) -> None:
        self.batch_size = int(os.getenv("BATCH_SIZE", "5"))
        self.max_concurrent_jobs = int(os.getenv("MAX_CONCURRENT_JOBS", "20"))
        self.job_timeout = int(os.getenv("JOB_TIMEOUT", "600"))  # 10 minutes
        self.namespace = os.getenv("NAMESPACE", "web-scraper-python")
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "10"))  # 10 seconds
        self.default_parser = os.getenv("DEFAULT_PARSER", "generic_news")
        self.seed_file = os.getenv("SEED_FILE", "seeds.txt")
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.job_ttl = int(os.getenv("JOB_TTL", "300"))  # 5 minutes cleanup

        # Resource limits
        self.job_memory_request = os.getenv("JOB_MEMORY_REQUEST", "512Mi")
        self.job_memory_limit = os.getenv("JOB_MEMORY_LIMIT", "1Gi")
        self.job_cpu_request = os.getenv("JOB_CPU_REQUEST", "200m")
        self.job_cpu_limit = os.getenv("JOB_CPU_LIMIT", "800m")

        # Image configuration
        self.scraper_image = os.getenv(
            "SCRAPER_IMAGE", "universal-web-scraper-python:latest"
        )


class BatchJob:
    """Represents a batch scraping job"""

    def __init__(self, job_id: str, batch_id: int, urls: List[str], parser: str):
        self.job_id = job_id
        self.batch_id = batch_id
        self.urls = urls
        self.parser = parser
        self.status = "pending"
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.retry_count = 0
        self.k8s_job_name: Optional[str] = None


class BatchOrchestrator:
    """
    Kubernetes-native batch orchestrator for web scraping jobs.

    Manages the lifecycle of scraping jobs:
    1. Load URLs from seed files
    2. Batch URLs into manageable chunks
    3. Create Kubernetes Jobs for each batch
    4. Monitor job progress and handle failures
    5. Cleanup completed jobs
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.logger = logger.bind(component="orchestrator")

        # Initialize Kubernetes client
        try:
            k8s_config.load_incluster_config()
            self.logger.info("Loaded in-cluster Kubernetes config")
        except k8s_config.ConfigException:
            try:
                k8s_config.load_kube_config()
                self.logger.info("Loaded local Kubernetes config")
            except k8s_config.ConfigException as e:
                self.logger.error("Failed to load Kubernetes config", error=str(e))
                raise

        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()

        # Job tracking
        self.active_jobs: Dict[str, BatchJob] = {}
        self.url_batches: List[List[str]] = []
        self.completed_batches: List[BatchJob] = []
        self.failed_batches: List[BatchJob] = []
        self.is_running = False

    def load_and_batch_urls(self, seed_file: Optional[str] = None) -> int:
        """Load URLs from seed file and create batches"""
        seed_path = Path(seed_file or self.config.seed_file)

        if not seed_path.exists():
            # Try relative to script directory
            seed_path = Path(__file__).parent.parent / seed_path.name

        if not seed_path.exists():
            raise FileNotFoundError(f"Seed file not found: {seed_path}")

        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                urls = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.strip().startswith("#")
                ]

            self.logger.info(
                "Loaded URLs from seed file",
                seed_file=str(seed_path),
                url_count=len(urls),
                batch_size=self.config.batch_size,
            )

            # Create batches
            self.url_batches = [
                urls[i : i + self.config.batch_size]
                for i in range(0, len(urls), self.config.batch_size)
            ]

            self.logger.info(
                "Created URL batches",
                total_urls=len(urls),
                batch_count=len(self.url_batches),
                batch_size=self.config.batch_size,
            )

            return len(self.url_batches)

        except Exception as e:
            self.logger.error(
                "Failed to load seed file", error=str(e), seed_file=str(seed_path)
            )
            raise

    def create_job_manifest(self, job: BatchJob) -> Dict:
        """Create Kubernetes Job manifest for a batch"""
        job_name = f"scraper-batch-{job.batch_id}-{int(time.time())}"
        job.k8s_job_name = job_name

        # Convert URLs to comma-separated string for command line
        urls_arg = ",".join(job.urls)

        manifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": job_name,
                "namespace": self.config.namespace,
                "labels": {
                    "app": "web-scraper-python",
                    "component": "batch-job",
                    "batch-id": str(job.batch_id),
                    "orchestrator-managed": "true",
                    "parser": job.parser,
                },
                "annotations": {
                    "orchestrator.web-scraper/job-id": job.job_id,
                    "orchestrator.web-scraper/batch-id": str(job.batch_id),
                    "orchestrator.web-scraper/url-count": str(len(job.urls)),
                    "orchestrator.web-scraper/created-at": job.created_at.isoformat(),
                },
            },
            "spec": {
                "ttlSecondsAfterFinished": self.config.job_ttl,
                "activeDeadlineSeconds": self.config.job_timeout,
                "backoffLimit": self.config.max_retries,
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "web-scraper-python",
                            "component": "batch-job",
                            "batch-id": str(job.batch_id),
                            "parser": job.parser,
                        }
                    },
                    "spec": {
                        "restartPolicy": "Never",
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 1001,
                            "runAsGroup": 1001,
                            "fsGroup": 1001,
                        },
                        "containers": [
                            {
                                "name": "scraper",
                                "image": self.config.scraper_image,
                                "command": ["python", "-m", "src.main"],
                                "args": [
                                    "--parser",
                                    job.parser,
                                    "--urls",
                                    urls_arg,
                                    "--max-concurrency",
                                    "2",  # Lower per-job since we run many jobs
                                    "--batch-mode",
                                ],
                                "env": [
                                    {"name": "PYTHONUNBUFFERED", "value": "1"},
                                    {"name": "PYTHONDONTWRITEBYTECODE", "value": "1"},
                                    {
                                        "name": "LOG_LEVEL",
                                        "valueFrom": {
                                            "configMapKeyRef": {
                                                "name": "web-scraper-python-config",
                                                "key": "LOG_LEVEL",
                                            }
                                        },
                                    },
                                    {"name": "BATCH_ID", "value": str(job.batch_id)},
                                    {"name": "JOB_ID", "value": job.job_id},
                                ],
                                "resources": {
                                    "requests": {
                                        "memory": self.config.job_memory_request,
                                        "cpu": self.config.job_cpu_request,
                                    },
                                    "limits": {
                                        "memory": self.config.job_memory_limit,
                                        "cpu": self.config.job_cpu_limit,
                                    },
                                },
                                "securityContext": {
                                    "allowPrivilegeEscalation": False,
                                    "readOnlyRootFilesystem": True,
                                    "capabilities": {"drop": ["ALL"]},
                                },
                                "volumeMounts": [
                                    {"name": "tmp", "mountPath": "/tmp"},
                                    {"name": "cache", "mountPath": "/app/.cache"},
                                ],
                            }
                        ],
                        "volumes": [
                            {"name": "tmp", "emptyDir": {}},
                            {"name": "cache", "emptyDir": {}},
                        ],
                    },
                },
            },
        }

        return manifest

    async def create_batch_job(
        self, batch_id: int, urls: List[str], parser: str
    ) -> BatchJob:
        """Create and submit a batch job to Kubernetes"""
        job_id = f"batch-{batch_id}-{int(time.time())}"
        job = BatchJob(job_id, batch_id, urls, parser)

        try:
            manifest = self.create_job_manifest(job)

            # Create the job
            self.batch_v1.create_namespaced_job(
                namespace=self.config.namespace, body=manifest
            )

            job.status = "running"
            job.started_at = datetime.now()
            if job.k8s_job_name:
                self.active_jobs[job.k8s_job_name] = job

            self.logger.info(
                "Created batch job",
                job_name=job.k8s_job_name,
                job_id=job.job_id,
                batch_id=batch_id,
                url_count=len(urls),
                parser=parser,
            )

            return job

        except ApiException as e:
            self.logger.error(
                "Failed to create batch job",
                job_id=job_id,
                batch_id=batch_id,
                error=str(e),
                status_code=e.status,
            )
            job.status = "failed"
            self.failed_batches.append(job)
            raise

    async def monitor_jobs(self) -> None:
        """Monitor active jobs and update their status"""
        if not self.active_jobs:
            return

        active_job_names = list(self.active_jobs.keys())

        for job_name in active_job_names:
            try:
                job_info = self.active_jobs[job_name]

                # Get job status from Kubernetes
                k8s_job = self.batch_v1.read_namespaced_job(
                    name=job_name, namespace=self.config.namespace
                )

                conditions = k8s_job.status.conditions or []

                # Check if job completed successfully
                for condition in conditions:
                    if condition.type == "Complete" and condition.status == "True":
                        job_info.status = "completed"
                        job_info.completed_at = datetime.now()
                        self.completed_batches.append(job_info)
                        del self.active_jobs[job_name]

                        self.logger.info(
                            "Job completed successfully",
                            job_name=job_name,
                            job_id=job_info.job_id,
                            batch_id=job_info.batch_id,
                            duration_seconds=(
                                (
                                    job_info.completed_at - job_info.started_at
                                ).total_seconds()
                                if job_info.started_at
                                else 0
                            ),
                        )
                        break

                    elif condition.type == "Failed" and condition.status == "True":
                        job_info.status = "failed"
                        job_info.completed_at = datetime.now()
                        job_info.retry_count += 1

                        # Check if we should retry
                        if job_info.retry_count < self.config.max_retries:
                            self.logger.warn(
                                "Job failed, will retry",
                                job_name=job_name,
                                job_id=job_info.job_id,
                                batch_id=job_info.batch_id,
                                retry_count=job_info.retry_count,
                            )
                            # Re-queue for retry
                            # (simplified - could be more sophisticated)
                            del self.active_jobs[job_name]
                            await self.create_batch_job(
                                job_info.batch_id, job_info.urls, job_info.parser
                            )
                        else:
                            self.logger.error(
                                "Job failed permanently",
                                job_name=job_name,
                                job_id=job_info.job_id,
                                batch_id=job_info.batch_id,
                                retry_count=job_info.retry_count,
                            )
                            self.failed_batches.append(job_info)
                            del self.active_jobs[job_name]
                        break

            except ApiException as e:
                if e.status == 404:
                    # Job was deleted/cleaned up
                    self.logger.warn(
                        "Job not found, removing from tracking", job_name=job_name
                    )
                    del self.active_jobs[job_name]
                else:
                    self.logger.error(
                        "Error monitoring job", job_name=job_name, error=str(e)
                    )

    async def run_orchestration(
        self, parser: Optional[str] = None, seed_file: Optional[str] = None
    ) -> None:
        """Main orchestration loop"""
        parser = parser or self.config.default_parser

        self.logger.info(
            "Starting batch orchestration",
            parser=parser,
            seed_file=seed_file or self.config.seed_file,
            batch_size=self.config.batch_size,
            max_concurrent_jobs=self.config.max_concurrent_jobs,
        )

        # Load and batch URLs
        batch_count = self.load_and_batch_urls(seed_file)

        if batch_count == 0:
            self.logger.warn("No URL batches to process")
            return

        self.is_running = True
        batch_queue = list(enumerate(self.url_batches))

        try:
            while batch_queue or self.active_jobs:
                # Start new jobs if we have capacity and batches to process
                while (
                    len(self.active_jobs) < self.config.max_concurrent_jobs
                    and batch_queue
                ):
                    batch_id, urls = batch_queue.pop(0)
                    await self.create_batch_job(batch_id, urls, parser)

                # Monitor existing jobs
                await self.monitor_jobs()

                # Status update
                if len(self.completed_batches) + len(self.failed_batches) > 0:
                    total_processed = len(self.completed_batches) + len(
                        self.failed_batches
                    )
                    self.logger.info(
                        "Orchestration progress",
                        total_batches=len(self.url_batches),
                        completed=len(self.completed_batches),
                        failed=len(self.failed_batches),
                        active=len(self.active_jobs),
                        pending=len(batch_queue),
                        progress_percent=round(
                            (total_processed / len(self.url_batches)) * 100, 1
                        ),
                    )

                # Wait before next poll
                await asyncio.sleep(self.config.poll_interval)

        except KeyboardInterrupt:
            self.logger.info("Orchestration interrupted by user")
        except Exception as e:
            self.logger.error("Orchestration failed", error=str(e))
            raise
        finally:
            self.is_running = False

            # Final summary
            self.logger.info(
                "Orchestration completed",
                total_batches=len(self.url_batches),
                completed=len(self.completed_batches),
                failed=len(self.failed_batches),
                success_rate=(
                    round(
                        (len(self.completed_batches) / len(self.url_batches)) * 100, 1
                    )
                    if self.url_batches
                    else 0
                ),
            )

    def get_status_summary(self) -> Dict:
        """Get current orchestration status"""
        return {
            "is_running": self.is_running,
            "total_batches": len(self.url_batches),
            "active_jobs": len(self.active_jobs),
            "completed_batches": len(self.completed_batches),
            "failed_batches": len(self.failed_batches),
            "success_rate": (
                round((len(self.completed_batches) / len(self.url_batches)) * 100, 1)
                if self.url_batches
                else 0
            ),
            "active_job_details": [
                {
                    "job_id": job.job_id,
                    "batch_id": job.batch_id,
                    "url_count": len(job.urls),
                    "status": job.status,
                    "started_at": (
                        job.started_at.isoformat() if job.started_at else None
                    ),
                    "runtime_seconds": (
                        (datetime.now() - job.started_at).total_seconds()
                        if job.started_at
                        else 0
                    ),
                }
                for job in self.active_jobs.values()
            ],
        }


async def main() -> None:
    """Main entry point for the orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Kubernetes Batch Orchestrator for Web Scraper"
    )
    parser.add_argument("--parser", default=None, help="Parser to use for scraping")
    parser.add_argument("--seed-file", default=None, help="Seed file containing URLs")
    parser.add_argument(
        "--status", action="store_true", help="Show orchestration status and exit"
    )

    args = parser.parse_args()

    config = OrchestratorConfig()
    orchestrator = BatchOrchestrator(config)

    if args.status:
        status = orchestrator.get_status_summary()
        print(json.dumps(status, indent=2))
        return

    try:
        await orchestrator.run_orchestration(args.parser, args.seed_file)
    except Exception as e:
        logger.error("Orchestrator failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
