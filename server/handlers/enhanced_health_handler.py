#!/usr/bin/env python3
"""
Enhanced Health Handler with Threading Support
Shows current users, memory, and threading statistics
"""

import json
import time
import psutil
import os
from tornado import web
from common.user_session_manager import session_manager


class EnhancedHealthHandler(web.RequestHandler):
    """Enhanced health endpoint for threading architecture"""

    def get(self):
        """Return enhanced health status"""
        try:
            # Get session manager stats
            session_stats = session_manager.get_system_stats()

            # Get process info
            main_process = psutil.Process(os.getpid())

            # Calculate uptime
            uptime_seconds = time.time() - main_process.create_time()

            health_data = {
                "status": "healthy",
                "timestamp": time.time(),
                "uptime_seconds": round(uptime_seconds, 1),
                "uptime_hours": round(uptime_seconds / 3600, 2),
                # System resources
                "system": {
                    "cpu_percent": session_stats["system"]["cpu_percent"],
                    "memory_percent": session_stats["system"]["memory_percent"],
                    "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                    "load_average": list(os.getloadavg()) if hasattr(os, "getloadavg") else [0, 0, 0],
                },
                # User sessions
                "users": {
                    "active_count": session_stats["active_users"],
                    "max_allowed": session_stats["limits"]["max_users"],
                    "utilization_percent": round(
                        (session_stats["active_users"] / session_stats["limits"]["max_users"]) * 100, 1
                    ),
                },
                # Threading info
                "threads": {
                    "total_active": session_stats["total_threads"],
                    "memory_usage_mb": session_stats["total_memory_mb"],
                    "memory_limit_mb": session_stats["limits"]["max_memory_mb"],
                },
                # Services
                "services": {
                    "database_connected": self._test_database(),
                    "efs_mounted": os.path.ismount("/mnt/efs"),
                    "session_manager": "active",
                },
                # Architecture info
                "architecture": {
                    "type": "thread-based-sessions",
                    "sessions_per_user": 1,
                    "threads_per_user": "1-2 active",
                    "optimized_for": "8-10 concurrent users",
                },
                # Active sessions detail (for debugging)
                "session_details": (
                    session_stats["sessions"]
                    if len(session_stats["sessions"]) <= 10
                    else f"Too many sessions to display ({len(session_stats['sessions'])})"
                ),
            }

            self.set_header("Content-Type", "application/json")
            self.write(health_data)

        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "error": str(e), "timestamp": time.time()})

    def _test_database(self) -> bool:
        """Test database connectivity"""
        try:
            from common.database import db_manager

            return db_manager.test_connection()
        except:
            return False


class SystemStatsHandler(web.RequestHandler):
    """Detailed system statistics for administrators"""

    def get(self):
        """Return detailed system statistics"""
        try:
            stats = session_manager.get_system_stats()

            # Add additional system info
            stats["detailed_system"] = {
                "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
                "platform": psutil.platform.system(),
                "cpu_count": psutil.cpu_count(),
                "disk_usage": {
                    "total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
                    "used_gb": round(psutil.disk_usage("/").used / (1024**3), 2),
                    "free_gb": round(psutil.disk_usage("/").free / (1024**3), 2),
                },
            }

            # Add recommendations based on current load
            stats["recommendations"] = self._generate_recommendations(stats)

            self.set_header("Content-Type", "application/json")
            self.write(stats)

        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})

    def _generate_recommendations(self, stats: dict) -> list:
        """Generate recommendations based on current system state"""
        recommendations = []

        # User capacity recommendations
        user_utilization = stats["active_users"] / stats["limits"]["max_users"]
        if user_utilization > 0.8:
            recommendations.append(
                {
                    "type": "capacity",
                    "severity": "warning",
                    "message": f"High user load: {stats['active_users']}/{stats['limits']['max_users']} users active",
                    "suggestion": "Consider upgrading to 2 vCPU, 6GB RAM for more capacity",
                }
            )

        # Memory recommendations
        memory_utilization = stats["total_memory_mb"] / stats["limits"]["max_memory_mb"]
        if memory_utilization > 0.8:
            recommendations.append(
                {
                    "type": "memory",
                    "severity": "warning",
                    "message": f"High memory usage: {stats['total_memory_mb']:.1f}MB/{stats['limits']['max_memory_mb']}MB",
                    "suggestion": "Consider cleaning up idle sessions or upgrading RAM",
                }
            )

        # CPU recommendations
        if stats["system"]["cpu_percent"] > 80:
            recommendations.append(
                {
                    "type": "cpu",
                    "severity": "critical",
                    "message": f"High CPU usage: {stats['system']['cpu_percent']:.1f}%",
                    "suggestion": "CPU bottleneck detected. Upgrade to 2+ vCPUs recommended",
                }
            )

        # Success message if everything looks good
        if not recommendations:
            recommendations.append(
                {
                    "type": "status",
                    "severity": "info",
                    "message": "System operating within normal parameters",
                    "suggestion": f'Current capacity supports {stats["limits"]["max_users"] - stats["active_users"]} more users',
                }
            )

        return recommendations
