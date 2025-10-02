#!/usr/bin/env python3
"""
AWS Integration for Process Registry Monitoring
Tracks system metrics for 38 concurrent users across AWS services
"""

import json
import logging
import time
import psutil
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict

# Try importing boto3 for CloudWatch metrics (optional)
try:
    import boto3

    CLOUDWATCH_AVAILABLE = True
except ImportError:
    CLOUDWATCH_AVAILABLE = False

from common.process_registry import process_registry
from common.database import db_manager

logger = logging.getLogger(__name__)


class AWSMonitor:
    """Monitor and track system metrics across AWS services"""

    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-2")
        self.cluster_name = "pythonide-cluster"
        self.service_name = "pythonide-service"

        # Initialize CloudWatch client if available
        self.cloudwatch = None
        if CLOUDWATCH_AVAILABLE:
            try:
                self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)
                logger.info("CloudWatch integration enabled")
            except Exception as e:
                logger.warning(f"CloudWatch integration failed: {e}")

        # Monitoring intervals
        self.metric_interval = 60  # Send metrics every minute
        self.health_interval = 30  # Health checks every 30s

        # Start monitoring
        self._start_monitoring()

    def get_system_metrics(self) -> Dict:
        """Collect comprehensive system metrics"""

        # Process registry stats
        registry_stats = process_registry.get_system_stats()

        # System resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Database connection info
        db_stats = self._get_database_metrics()

        # EFS mount status
        efs_stats = self._get_efs_metrics()

        metrics = {
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / 1024 / 1024,
                "memory_available_mb": memory.available / 1024 / 1024,
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / 1024 / 1024 / 1024,
                "load_average": os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0],
            },
            "processes": registry_stats,
            "database": db_stats,
            "storage": efs_stats,
            "aws": {"region": self.region, "cluster": self.cluster_name, "service": self.service_name},
        }

        return metrics

    def _get_database_metrics(self) -> Dict:
        """Get PostgreSQL database metrics"""
        try:
            # Test database connection
            connection_healthy = db_manager.test_connection()

            # Get connection pool stats if available
            pool_stats = {}
            if hasattr(db_manager, "pool"):
                pool = db_manager.pool
                pool_stats = {
                    "total_connections": pool.maxconn if hasattr(pool, "maxconn") else "unknown",
                    "active_connections": "unknown",  # Would need pool instrumentation
                    "idle_connections": "unknown",
                }

            return {
                "connection_healthy": connection_healthy,
                "pool_stats": pool_stats,
                "host": (
                    os.getenv("DATABASE_URL", "").split("@")[1].split("/")[0]
                    if "@" in os.getenv("DATABASE_URL", "")
                    else "unknown"
                ),
            }
        except Exception as e:
            logger.error(f"Database metrics error: {e}")
            return {"connection_healthy": False, "error": str(e)}

    def _get_efs_metrics(self) -> Dict:
        """Get AWS EFS storage metrics"""
        efs_path = "/mnt/efs"

        try:
            # Check if EFS is mounted
            is_mounted = os.path.ismount(efs_path)

            stats = {}
            if is_mounted and os.path.exists(efs_path):
                # Get directory size and file count
                stats = self._get_directory_stats(efs_path)

            return {
                "mounted": is_mounted,
                "path": efs_path,
                "stats": stats,
                "filesystem_id": os.getenv("EFS_FILESYSTEM_ID", "fs-0ba3b6fecab24774a"),
            }
        except Exception as e:
            logger.error(f"EFS metrics error: {e}")
            return {"mounted": False, "error": str(e)}

    def _get_directory_stats(self, path: str) -> Dict:
        """Get directory statistics (size, file count)"""
        try:
            total_size = 0
            file_count = 0
            dir_count = 0

            for root, dirs, files in os.walk(path):
                file_count += len(files)
                dir_count += len(dirs)

                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        continue

            return {"total_size_mb": total_size / 1024 / 1024, "file_count": file_count, "directory_count": dir_count}
        except Exception as e:
            logger.error(f"Directory stats error for {path}: {e}")
            return {}

    def send_metrics_to_cloudwatch(self, metrics: Dict):
        """Send custom metrics to CloudWatch"""
        if not self.cloudwatch:
            return

        try:
            # Prepare metrics for CloudWatch
            metric_data = []

            # System metrics
            metric_data.extend(
                [
                    {
                        "MetricName": "CPUUtilization",
                        "Value": metrics["system"]["cpu_percent"],
                        "Unit": "Percent",
                        "Dimensions": [{"Name": "Service", "Value": self.service_name}],
                    },
                    {
                        "MetricName": "MemoryUtilization",
                        "Value": metrics["system"]["memory_percent"],
                        "Unit": "Percent",
                        "Dimensions": [{"Name": "Service", "Value": self.service_name}],
                    },
                    {
                        "MetricName": "ActiveUsers",
                        "Value": metrics["processes"]["active_users"],
                        "Unit": "Count",
                        "Dimensions": [{"Name": "Service", "Value": self.service_name}],
                    },
                    {
                        "MetricName": "TotalProcesses",
                        "Value": metrics["processes"]["total_processes"],
                        "Unit": "Count",
                        "Dimensions": [{"Name": "Service", "Value": self.service_name}],
                    },
                    {
                        "MetricName": "ProcessMemoryMB",
                        "Value": metrics["processes"]["total_memory_mb"],
                        "Unit": "Megabytes",
                        "Dimensions": [{"Name": "Service", "Value": self.service_name}],
                    },
                ]
            )

            # Database health
            metric_data.append(
                {
                    "MetricName": "DatabaseHealthy",
                    "Value": 1 if metrics["database"]["connection_healthy"] else 0,
                    "Unit": "Count",
                    "Dimensions": [{"Name": "Service", "Value": self.service_name}],
                }
            )

            # EFS health
            metric_data.append(
                {
                    "MetricName": "EFSMounted",
                    "Value": 1 if metrics["storage"]["mounted"] else 0,
                    "Unit": "Count",
                    "Dimensions": [{"Name": "Service", "Value": self.service_name}],
                }
            )

            # Send to CloudWatch in batches (max 20 per call)
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i : i + 20]
                self.cloudwatch.put_metric_data(Namespace="PythonIDE/Custom", MetricData=batch)

            logger.debug(f"Sent {len(metric_data)} metrics to CloudWatch")

        except Exception as e:
            logger.error(f"CloudWatch metrics error: {e}")

    def log_metrics_to_file(self, metrics: Dict):
        """Log metrics to file for analysis"""
        try:
            log_dir = "/tmp/pythonide_metrics"
            os.makedirs(log_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H")
            log_file = f"{log_dir}/metrics_{timestamp}.jsonl"

            with open(log_file, "a") as f:
                f.write(json.dumps(metrics) + "\n")

        except Exception as e:
            logger.error(f"Metrics logging error: {e}")

    def check_health_thresholds(self, metrics: Dict) -> List[Dict]:
        """Check if metrics exceed health thresholds"""
        alerts = []

        # CPU threshold
        if metrics["system"]["cpu_percent"] > 80:
            alerts.append(
                {
                    "severity": "warning",
                    "metric": "cpu_percent",
                    "value": metrics["system"]["cpu_percent"],
                    "threshold": 80,
                    "message": "High CPU usage detected",
                }
            )

        # Memory threshold
        if metrics["system"]["memory_percent"] > 85:
            alerts.append(
                {
                    "severity": "warning",
                    "metric": "memory_percent",
                    "value": metrics["system"]["memory_percent"],
                    "threshold": 85,
                    "message": "High memory usage detected",
                }
            )

        # Process count threshold
        max_processes = metrics["processes"]["resource_limits"]["max_processes"]
        current_processes = metrics["processes"]["total_processes"]
        if current_processes > max_processes * 0.9:
            alerts.append(
                {
                    "severity": "warning",
                    "metric": "total_processes",
                    "value": current_processes,
                    "threshold": max_processes * 0.9,
                    "message": "Approaching process limit",
                }
            )

        # Database health
        if not metrics["database"]["connection_healthy"]:
            alerts.append(
                {
                    "severity": "critical",
                    "metric": "database_connection",
                    "value": False,
                    "threshold": True,
                    "message": "Database connection failed",
                }
            )

        # EFS mount
        if not metrics["storage"]["mounted"]:
            alerts.append(
                {
                    "severity": "critical",
                    "metric": "efs_mount",
                    "value": False,
                    "threshold": True,
                    "message": "EFS filesystem not mounted",
                }
            )

        return alerts

    def _start_monitoring(self):
        """Start background monitoring threads"""

        def metrics_loop():
            while True:
                try:
                    time.sleep(self.metric_interval)

                    # Collect metrics
                    metrics = self.get_system_metrics()

                    # Send to CloudWatch
                    self.send_metrics_to_cloudwatch(metrics)

                    # Log to file
                    self.log_metrics_to_file(metrics)

                    # Check health thresholds
                    alerts = self.check_health_thresholds(metrics)
                    for alert in alerts:
                        logger.warning(f"Health Alert: {alert['message']} - {alert['metric']}: {alert['value']}")

                except Exception as e:
                    logger.error(f"Metrics loop error: {e}")

        def health_loop():
            while True:
                try:
                    time.sleep(self.health_interval)

                    # Quick health check
                    metrics = {
                        "system": {
                            "cpu_percent": psutil.cpu_percent(),
                            "memory_percent": psutil.virtual_memory().percent,
                        },
                        "processes": process_registry.get_system_stats(),
                        "database": self._get_database_metrics(),
                        "storage": {"mounted": os.path.ismount("/mnt/efs")},
                    }

                    # Log critical issues immediately
                    if metrics["system"]["cpu_percent"] > 95:
                        logger.critical(f"CPU critical: {metrics['system']['cpu_percent']}%")

                    if metrics["system"]["memory_percent"] > 95:
                        logger.critical(f"Memory critical: {metrics['system']['memory_percent']}%")

                except Exception as e:
                    logger.error(f"Health loop error: {e}")

        # Start daemon threads
        metrics_thread = threading.Thread(target=metrics_loop, daemon=True)
        metrics_thread.start()

        health_thread = threading.Thread(target=health_loop, daemon=True)
        health_thread.start()

        logger.info("AWS monitoring started (metrics and health checks)")


# Global monitor instance
aws_monitor = AWSMonitor()


# Health endpoint data
def get_health_data() -> Dict:
    """Get current health data for /health endpoint"""
    try:
        metrics = aws_monitor.get_system_metrics()

        return {
            "status": "healthy",
            "timestamp": metrics["timestamp"],
            "uptime_seconds": time.time() - metrics["timestamp"],  # Approximate
            "system": {
                "cpu_percent": metrics["system"]["cpu_percent"],
                "memory_percent": metrics["system"]["memory_percent"],
                "memory_used_mb": round(metrics["system"]["memory_used_mb"]),
                "disk_percent": metrics["system"]["disk_percent"],
            },
            "users": {
                "active_users": metrics["processes"]["active_users"],
                "total_processes": metrics["processes"]["total_processes"],
                "process_memory_mb": round(metrics["processes"]["total_memory_mb"]),
            },
            "services": {
                "database_connected": metrics["database"]["connection_healthy"],
                "efs_mounted": metrics["storage"]["mounted"],
            },
            "limits": metrics["processes"]["resource_limits"],
        }
    except Exception as e:
        logger.error(f"Health data error: {e}")
        return {"status": "error", "error": str(e), "timestamp": time.time()}
