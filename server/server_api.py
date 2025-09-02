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
from handlers.auth_handler import LoginHandler, LogoutHandler, ValidateSessionHandler, ChangePasswordHandler, RenewSessionHandler, ForgotPasswordHandler, ResetPasswordHandler
from setup_route import SetupHandler, ResetDatabaseHandler
from common.database import db_manager
from health_monitor import health_monitor
from migrations.migration_manager import run_auto_migrations

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthCheckHandler(web.RequestHandler):
    """Health check endpoint for AWS ALB"""
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
    
    def options(self):
        self.set_status(204)
        self.finish()
    
    def get(self):
        try:
            # Update activity timestamp
            health_monitor.update_activity()
            
            # Check database connection
            db_manager.execute_query("SELECT 1")
            
            # Check system resources
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            
            health_status = {
                'status': 'healthy',
                'database': 'connected',
                'memory_percent': memory.percent,
                'cpu_percent': cpu,
                'active_connections': WebSocketHandler.get_connection_count(),
                'timestamp': time.time()
            }
            
            self.set_status(200)
            self.write(health_status)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.set_status(503)
            self.write({'status': 'unhealthy', 'error': str(e)})


class CORSHandler(web.RequestHandler):
    """Base handler with CORS support"""
    def set_default_headers(self):
        origin = self.request.headers.get("Origin", "*")
        # Allow specific origins in production
        allowed_origins = [
            "http://pythonide-frontend-fall2025.s3-website.us-east-2.amazonaws.com",
            "http://localhost:8081",
            "http://localhost:3000"
        ]
        
        if origin in allowed_origins or origin == "*":
            self.set_header("Access-Control-Allow-Origin", origin)
        else:
            # For development, allow any origin
            self.set_header("Access-Control-Allow-Origin", "*")
            
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token")
        self.set_header("Access-Control-Allow-Credentials", "true")
    
    def options(self):
        self.set_status(204)
        self.finish()


# Wrap all auth handlers with CORS
class CORSLoginHandler(LoginHandler, CORSHandler):
    pass

class CORSLogoutHandler(LogoutHandler, CORSHandler):
    pass

class CORSValidateSessionHandler(ValidateSessionHandler, CORSHandler):
    pass

class CORSChangePasswordHandler(ChangePasswordHandler, CORSHandler):
    pass

class CORSRenewSessionHandler(RenewSessionHandler, CORSHandler):
    pass

class CORSForgotPasswordHandler(ForgotPasswordHandler, CORSHandler):
    pass

class CORSResetPasswordHandler(ResetPasswordHandler, CORSHandler):
    pass


def periodic_cleanup():
    """Periodic cleanup of resources"""
    try:
        # Clean up expired sessions
        from auth.session_manager import session_manager
        session_manager.cleanup_expired_sessions()
        
        # Clean up abandoned processes
        from command.process_manager import cleanup_abandoned_processes
        cleanup_abandoned_processes()
        
        # Force garbage collection
        gc.collect()
        
        logger.info("Periodic cleanup completed")
    except Exception as e:
        logger.error(f"Error in periodic cleanup: {e}")


def monitor_resources():
    """Monitor and log resource usage"""
    try:
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        if memory.percent > 90:
            logger.warning(f"High memory usage: {memory.percent}%")
        if cpu > 90:
            logger.warning(f"High CPU usage: {cpu}%")
        if disk.percent > 90:
            logger.warning(f"High disk usage: {disk.percent}%")
            
    except Exception as e:
        logger.error(f"Error monitoring resources: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8080)))
    args = parser.parse_args()

    # Initialize database and ensure directories
    logger.info("Ensuring project directories exist...")
    project_base = os.path.join(os.path.dirname(__file__), 'projects', 'ide')
    for dir_name in ['Local', 'Lecture Notes', 'Assignments', 'Tests']:
        dir_path = os.path.join(project_base, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Directory ensured: {dir_path}")

    logger.info("Initializing database...")
    
    # Run migrations
    logger.info("Running database migrations...")
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        logger.info("DATABASE_URL found - running migrations")
        run_auto_migrations(database_url)
        logger.info("Database migrations completed successfully")
    else:
        logger.info("No DATABASE_URL found - skipping migrations")

    # API-only routes (no template rendering)
    app_settings = {
        'debug': False,
        'autoreload': False,
        'compiled_template_cache': False,
        'serve_traceback': False,
        'xsrf_cookies': False,  # Disable for API
        'cookie_secret': os.environ.get('IDE_SECRET_KEY', 'your-secret-key-here')
    }

    app = web.Application([
        # Health check
        (r"/health", HealthCheckHandler),
        (r"/api/health", HealthCheckHandler),
        
        # Auth endpoints with CORS
        (r"/api/auth/login", CORSLoginHandler),
        (r"/api/auth/logout", CORSLogoutHandler),
        (r"/api/auth/status", CORSValidateSessionHandler),
        (r"/api/auth/validate", CORSValidateSessionHandler),
        (r"/api/auth/change-password", CORSChangePasswordHandler),
        (r"/api/auth/renew", CORSRenewSessionHandler),
        (r"/api/auth/forgot-password", CORSForgotPasswordHandler),
        (r"/api/auth/reset-password", CORSResetPasswordHandler),
        
        # WebSocket endpoints (CORS handled differently)
        (r"/ws", WebSocketHandler),
        (r"/ws/auth", AuthenticatedWebSocketHandler),
        
        # Setup routes (if needed)
        (r"/setup", SetupHandler),
        (r"/reset_database", ResetDatabaseHandler),
    ], **app_settings)

    http_server = httpserver.HTTPServer(app)
    http_server.listen(args.port, address='0.0.0.0')
    
    print(f"API Server ready at http://0.0.0.0:{args.port}")
    print(f"server process pid: {os.getpid()}, ppid: {os.getppid()}")
    
    logger.info(f"API Server listening on 0.0.0.0:{args.port}")
    logger.info(f"Database type: {'PostgreSQL' if 'postgresql' in db_manager.db_type else db_manager.db_type}")
    
    # Start periodic cleanup (every 5 minutes)
    cleanup_interval = float(os.environ.get('CLEANUP_INTERVAL', 300)) * 1000
    cleanup_callback = PeriodicCallback(periodic_cleanup, cleanup_interval)
    cleanup_callback.start()
    logger.info(f"Process cleanup service started (interval: {cleanup_interval/1000}s)")
    
    # Start resource monitoring (every 30 seconds)
    monitor_callback = PeriodicCallback(monitor_resources, 30000)
    monitor_callback.start()
    logger.info("Resource monitoring service started")
    
    # Start health monitoring
    health_monitor.start()
    
    # Start request/response processors
    request_processor = RequestProcessor()
    response_processor = ResponseProcessor()
    request_processor.start()
    response_processor.start()
    
    try:
        ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        cleanup_callback.stop()
        monitor_callback.stop()
        health_monitor.stop()
        http_server.stop()
        ioloop.IOLoop.current().stop()
        logger.info("Server stopped")


if __name__ == '__main__':
    main()