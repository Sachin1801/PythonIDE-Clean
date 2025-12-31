#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import time
import gc
import psutil
from tornado import ioloop
from tornado import web
from tornado import httpserver
from tornado.ioloop import PeriodicCallback
from dotenv import load_dotenv
from command.processor import RequestProcessor, ResponseProcessor
from handlers.ws_handler import WebSocketHandler
from handlers.authenticated_ws_handler import AuthenticatedWebSocketHandler
from handlers.vue_handler import VueHandler
from handlers.auth_handler import (
    LoginHandler,
    LogoutHandler,
    ValidateSessionHandler,
    ChangePasswordHandler,
    RenewSessionHandler,
    ForgotPasswordHandler,
    ResetPasswordHandler,
)
from handlers.admin_handler import get_admin_handlers as get_legacy_admin_handlers
from handlers.admin import get_admin_handlers as get_new_admin_handlers
from handlers.migration_handler import get_migration_handler  # TEMPORARY - REMOVE AFTER MIGRATION
from handlers.upload_handler import UploadFileHandler
from handlers.bulk_upload_handler import BulkUploadHandler
from handlers.student_list_handler import StudentListHandler
from setup_route import SetupHandler, ResetDatabaseHandler
from common.database import db_manager
from health_monitor import health_monitor
from migrations.migration_manager import run_auto_migrations
from auto_init_users import init_users_if_needed
from tornado.web import StaticFileHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class HealthCheckHandler(web.RequestHandler):
    """Health check endpoint for ECS - Must be resilient to temporary DB issues"""

    def get(self):
        try:
            # Update activity timestamp
            health_monitor.update_activity()

            # Check system resources (always works, even if DB fails)
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)

            health_status = {
                "status": "healthy",
                "memory_percent": memory.percent,
                "cpu_percent": cpu,
                "uptime": int(time.time() - health_monitor.start_time) if hasattr(health_monitor, "start_time") else 0,
            }

            # Try database connection with SHORT timeout - don't kill container if DB slow
            db_status = "unknown"
            db_pool_stats = {"available": "unknown", "total": "unknown"}

            try:
                # Use a very short timeout to prevent health check hanging
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError("Database check timed out")

                # Set 2-second timeout for DB check
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(2)

                try:
                    # Test with a fresh query (not from pool) to avoid stale connections
                    db_manager.execute_query("SELECT 1")
                    db_status = "connected"

                    # Get connection pool stats for monitoring
                    if hasattr(db_manager, 'connection_pool') and db_manager.connection_pool:
                        # ThreadedConnectionPool doesn't expose stats easily, but we can log config
                        db_pool_stats = {
                            "min_conn": db_manager.connection_pool.minconn,
                            "max_conn": db_manager.connection_pool.maxconn,
                        }

                finally:
                    signal.alarm(0)  # Cancel alarm

            except Exception as db_error:
                # Log the error but DON'T fail health check
                # Container can still serve requests even if DB temporarily unavailable
                logger.warning(f"Database health check failed (non-fatal): {db_error}")
                db_status = f"degraded: {str(db_error)[:100]}"

            health_status["database"] = db_status
            health_status["db_pool"] = db_pool_stats

            # Warn if resources are getting high
            if memory.percent > 80 or cpu > 80:
                health_status["warning"] = "High resource usage detected"

            # CRITICAL: Always return 200 OK unless the APPLICATION PROCESS is broken
            # Temporary DB issues, high memory, or slow queries should NOT kill the container
            # ECS should only restart if the web server itself is unresponsive
            self.write(health_status)

        except Exception as e:
            # Even on critical errors, try to return 200 with error details
            # Only return 503 if we absolutely cannot respond (which is rare)
            logger.error(f"Health check error (attempting graceful handling): {e}")

            # Try to respond gracefully even with errors
            try:
                self.write({
                    "status": "degraded",
                    "error": str(e),
                    "message": "Application experiencing issues but still operational"
                })
            except:
                # Last resort: return 503 only if we can't even write a response
                self.set_status(503)
                self.write({"status": "unhealthy", "error": str(e)})


class ProcessCleanupService:
    """Service to clean up abandoned Python processes"""

    def __init__(self):
        # Optimized for 1 vCPU, 4GB RAM - support 8-10 users
        self.max_process_age = int(os.environ.get("MAX_PROCESS_AGE", "3600"))  # 1 hour default (increased)
        self.max_repl_age = int(os.environ.get("MAX_REPL_AGE", "7200"))  # 2 hours for REPL (increased)
        self.max_concurrent_processes = 20  # Limit total user processes for current hardware

    def cleanup_abandoned_processes(self):
        """Kill Python processes older than the age limit or exceeding limits"""
        try:
            current_time = time.time()
            cleanup_count = 0
            user_processes = []  # Track user processes for limit enforcement

            for proc in psutil.process_iter(["pid", "create_time", "cmdline", "name"]):
                try:
                    # Check if it's a Python process
                    if proc.info["name"] and "python" in proc.info["name"].lower():
                        # Skip the main server process to prevent 30-minute crashes
                        if proc.info["pid"] == os.getpid():
                            continue

                        # Get command line arguments
                        cmdline = proc.info.get("cmdline", [])
                        if cmdline and any(".py" in str(arg) for arg in cmdline):
                            # Track user processes for resource limits
                            user_processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "age": current_time - proc.info["create_time"],
                                    "cmdline": str(cmdline),
                                    "proc": proc,
                                }
                            )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by age (oldest first) and enforce limits
            user_processes.sort(key=lambda p: p["age"], reverse=True)

            # Clean up processes that exceed limits
            for i, proc_info in enumerate(user_processes):
                should_kill = False
                reason = ""

                # Check age limits
                max_age = self.max_repl_age if "repl" in proc_info["cmdline"].lower() else self.max_process_age
                if proc_info["age"] > max_age:
                    should_kill = True
                    reason = f"age limit ({int(proc_info['age'])}s > {max_age}s)"

                # Check total process count limit (kill oldest processes first)
                elif i >= self.max_concurrent_processes:
                    should_kill = True
                    reason = f"process limit exceeded (keeping newest {self.max_concurrent_processes})"

                if should_kill:
                    try:
                        proc_info["proc"].kill()
                        cleanup_count += 1
                        logger.info(f"Killed process PID {proc_info['pid']}: {reason}")
                    except psutil.NoSuchProcess:
                        pass
                    except Exception as e:
                        logger.error(f"Failed to kill process {proc_info['pid']}: {e}")

            if cleanup_count > 0:
                logger.info(f"Process cleanup: killed {cleanup_count} abandoned processes")

            # Force garbage collection to free memory
            gc.collect()

        except Exception as e:
            logger.error(f"Error in process cleanup: {e}")

    def check_system_resources(self):
        """Monitor system resource usage"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Check memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Check disk usage
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent

            # Log warnings if resources are high
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent}%")

            if memory_percent > 85:
                logger.warning(f"High memory usage: {memory_percent}%")

            if disk_percent > 90:
                logger.warning(f"High disk usage: {disk_percent}%")

            return {"cpu_percent": cpu_percent, "memory_percent": memory_percent, "disk_percent": disk_percent}

        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", type=str, default="0.0.0.0", help="server listen address")
    parser.add_argument("--port", type=int, default=None, help="server listen port")
    parser.add_argument("--num_processes", type=int, default=-1, help="fork process to support")
    args = parser.parse_args()

    # Railway provides PORT environment variable
    port = args.port or int(os.getenv("PORT", 10086))
    address = args.address

    # Use absolute paths that work in Docker container
    template_path = (
        "/app/dist/templates"
        if os.path.exists("/app/dist/templates")
        else os.path.join(os.path.dirname(__file__), "..", "dist", "templates")
    )
    static_path = (
        "/app/dist/static"
        if os.path.exists("/app/dist/static")
        else os.path.join(os.path.dirname(__file__), "..", "dist", "static")
    )
    settings = {
        "template_path": template_path,
        "static_path": static_path,
    }
    handlers = [
        (r"/health", HealthCheckHandler),  # Health check for Railway
        (r"/api/setup", SetupHandler),  # Setup route for initialization
        (r"/api/reset-database", ResetDatabaseHandler),  # Reset database (USE WITH CAUTION!)
        (r"/ws", AuthenticatedWebSocketHandler),  # Authenticated WebSocket
        (r"/ws-legacy", WebSocketHandler),  # Keep old handler for migration
        (r"/api/login", LoginHandler),
        (r"/api/logout", LogoutHandler),
        (r"/api/validate-session", ValidateSessionHandler),
        (r"/api/renew-session", RenewSessionHandler),
        (r"/api/change-password", ChangePasswordHandler),
        (r"/api/forgot-password", ForgotPasswordHandler),
        (r"/api/reset-password", ResetPasswordHandler),
        (r"/api/upload-file", UploadFileHandler),
        (r"/api/bulk-upload", BulkUploadHandler),
        (r"/api/get-all-students", StudentListHandler),
        (r"/static/(.*)", StaticFileHandler, {"path": static_path}),  # Serve static files (CSS, JS, etc)
        *get_new_admin_handlers(),  # New admin panel endpoints (for admin.pythonide-classroom.tech)
        *get_legacy_admin_handlers(),  # Legacy admin password management endpoints (IDE-side)
        get_migration_handler(),  # TEMPORARY migration endpoint - REMOVE AFTER USE
        (r"^.*$", VueHandler),
    ]

    # app = web.Application(handlers, **settings, autoreload=True)
    app = web.Application(handlers, **settings)

    # Ensure project directories exist using file storage system
    logger.info("Ensuring project directories exist...")
    from common.file_storage import file_storage

    file_storage._ensure_base_directories()
    logger.info(f"Directory ensured: {file_storage.ide_base}/Local")

    # Initialize database
    logger.info("Initializing database...")

    # Run automatic migrations BEFORE starting the server
    logger.info("Running database migrations...")
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        logger.info("DATABASE_URL found - running migrations")
        migration_success = run_auto_migrations(database_url)
        if not migration_success:
            logger.error("Database migrations failed! Server startup aborted.")
            sys.exit(1)
        logger.info("Database migrations completed successfully")

        # Auto-initialize users if needed (skip for exam environment)
        is_exam_mode = os.environ.get("IS_EXAM_MODE", "false").lower() == "true"
        if not is_exam_mode:
            logger.info("Checking if users need initialization...")
            try:
                init_users_if_needed()
            except Exception as e:
                logger.error(f"Failed to initialize users: {e}")
        else:
            logger.info("Exam mode detected - skipping auto_init_users (exam uses init_exam_users.py)")
    else:
        logger.warning("DATABASE_URL not set - using local PostgreSQL fallback")
        logger.warning("Migrations will be skipped without DATABASE_URL")

    # Check for environment variable to override num_processes
    tornado_processes = int(os.getenv('TORNADO_PROCESSES', '-1'))
    if tornado_processes > 0:
        # Use environment variable if set
        num_processes = tornado_processes
        logger.info(f"Using TORNADO_PROCESSES from environment: {num_processes}")
    else:
        # Use command line argument
        num_processes = args.num_processes

    if num_processes >= 0:
        try:
            http_server = httpserver.HTTPServer(app)
            http_server.bind(port, address)
            http_server.start(num_processes=num_processes)
            if num_processes == 0:
                logger.info(f"Started Tornado with auto-detected CPU count")
            else:
                logger.info(f"Started Tornado with {num_processes} process(es)")
        except Exception as e:
            logger.warning(f"Failed to start multi-process mode: {e}. Falling back to single process.")
            app.listen(port, address=address)
    else:
        app.listen(port, address=address)
        logger.info("Started Tornado in single-process mode")

    logger.info("Server listening on {}:{}".format(address, port))
    logger.info("Database type: {}".format("PostgreSQL" if db_manager.is_postgres else "SQLite"))
    print("Server ready at http://{}:{}".format(address, port))
    pid = os.getpid()
    ppid = os.getppid()
    print("server process pid: {}, ppid: {}".format(pid, ppid))

    req_processor = RequestProcessor()
    res_processor = ResponseProcessor()
    main_ioloop = ioloop.IOLoop.current()
    main_ioloop.add_timeout(1, req_processor.loop)
    main_ioloop.add_timeout(1, res_processor.loop)

    # Initialize process cleanup service
    cleanup_service = ProcessCleanupService()

    # Schedule periodic cleanup (every 5 minutes)
    cleanup_interval = int(os.environ.get("CLEANUP_INTERVAL_MS", "300000"))  # 5 minutes default
    cleanup_callback = PeriodicCallback(cleanup_service.cleanup_abandoned_processes, cleanup_interval)
    cleanup_callback.start()
    logger.info(f"Process cleanup service started (interval: {cleanup_interval/1000}s)")

    # Schedule resource monitoring (every minute)
    resource_check_callback = PeriodicCallback(cleanup_service.check_system_resources, 60000)  # 1 minute
    resource_check_callback.start()
    logger.info("Resource monitoring service started")

    # Start health monitoring service
    health_monitor.start()

    # Start idle session cleanup job (auto-logout after 1 hour inactivity)
    from auth.user_manager_postgres import UserManager, IdleSessionCleanupJob

    user_manager = UserManager()
    idle_cleanup = IdleSessionCleanupJob(user_manager)
    idle_cleanup.start()
    logger.info("Idle session cleanup job started (1-hour inactivity timeout)")

    # Add database connection pool refresh (every 10 minutes)
    # This prevents connections from becoming stale and causing health check failures
    def refresh_database_connections():
        """Refresh database connection pool to prevent stale connections"""
        try:
            logger.info("Starting database connection pool refresh...")

            # Strategy: Test multiple connections to detect stale ones
            # We test a sample of connections to avoid blocking all of them
            test_count = min(5, db_manager.connection_pool.maxconn // 10)  # Test 10% of pool, max 5
            successful_tests = 0
            failed_tests = 0

            for i in range(test_count):
                conn = None
                try:
                    # Get connection from pool
                    conn = db_manager.connection_pool.getconn()

                    # Test if connection is still valid
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")

                    # Connection is good, return to pool
                    db_manager.connection_pool.putconn(conn)
                    successful_tests += 1

                except Exception as conn_error:
                    logger.warning(f"Found stale connection during refresh (test {i+1}): {conn_error}")
                    failed_tests += 1

                    # Close the bad connection and let pool create a new one
                    if conn:
                        try:
                            db_manager.connection_pool.putconn(conn, close=True)
                        except:
                            pass

            logger.info(f"Connection pool refresh complete: {successful_tests} healthy, {failed_tests} replaced")

            # If more than 50% of tested connections failed, recreate entire pool
            if failed_tests > test_count / 2:
                logger.error(f"High failure rate detected ({failed_tests}/{test_count}), recreating pool...")
                try:
                    db_manager.connection_pool.closeall()
                    db_manager._init_postgres()
                    logger.info("Database connection pool successfully recreated")
                except Exception as reinit_error:
                    logger.critical(f"Failed to recreate connection pool: {reinit_error}")

        except Exception as e:
            logger.error(f"Database connection pool refresh failed: {e}")
            # Try to recreate the connection pool as last resort
            try:
                logger.warning("Attempting emergency connection pool recreation...")
                if hasattr(db_manager, 'connection_pool') and db_manager.connection_pool:
                    db_manager.connection_pool.closeall()
                db_manager._init_postgres()
                logger.info("Emergency connection pool recreation successful")
            except Exception as reinit_error:
                logger.critical(f"Emergency pool recreation failed: {reinit_error}")

    # Run every 10 minutes (600000 ms) to keep connections fresh
    # Reduced from 15 minutes to detect stale connections faster
    db_refresh_interval = int(os.environ.get("DB_REFRESH_INTERVAL_MS", "600000"))
    db_refresh_callback = PeriodicCallback(refresh_database_connections, db_refresh_interval)
    db_refresh_callback.start()
    logger.info(f"Database connection pool refresh started (interval: {db_refresh_interval/1000}s, testing ~{min(5, 5)}% of pool)")

    main_ioloop.start()


if __name__ == "__main__":
    main()
