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
from handlers.auth_handler import LoginHandler, LogoutHandler, ValidateSessionHandler, ChangePasswordHandler, RenewSessionHandler, ForgotPasswordHandler, ResetPasswordHandler
from handlers.upload_handler import UploadFileHandler
from setup_route import SetupHandler, ResetDatabaseHandler
from common.database import db_manager
from health_monitor import health_monitor
from migrations.migration_manager import run_auto_migrations
from auto_init_users import init_users_if_needed

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthCheckHandler(web.RequestHandler):
    """Health check endpoint for Railway"""
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
                "status": "healthy",
                "database": "connected",
                "memory_percent": memory.percent,
                "cpu_percent": cpu,
                "uptime": int(time.time() - health_monitor.start_time) if hasattr(health_monitor, 'start_time') else 0
            }
            
            # Warn if resources are getting high
            if memory.percent > 80 or cpu > 80:
                health_status["warning"] = "High resource usage detected"
            
            self.write(health_status)
        except Exception as e:
            self.set_status(503)
            self.write({"status": "unhealthy", "error": str(e)})


class ProcessCleanupService:
    """Service to clean up abandoned Python processes"""
    
    def __init__(self):
        self.max_process_age = int(os.environ.get('MAX_PROCESS_AGE', '1800'))  # 30 minutes default
        self.max_repl_age = int(os.environ.get('MAX_REPL_AGE', '3600'))  # 60 minutes for REPL
        
    def cleanup_abandoned_processes(self):
        """Kill Python processes older than the age limit"""
        try:
            current_time = time.time()
            cleanup_count = 0
            
            for proc in psutil.process_iter(['pid', 'create_time', 'cmdline', 'name']):
                try:
                    # Check if it's a Python process
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        # Get command line arguments
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and any('.py' in str(arg) for arg in cmdline):
                            # Check process age
                            age = current_time - proc.info['create_time']
                            
                            # Determine max age based on process type
                            max_age = self.max_repl_age if 'repl' in str(cmdline).lower() else self.max_process_age
                            
                            if age > max_age:
                                # Kill the process
                                try:
                                    proc.kill()
                                    cleanup_count += 1
                                    logger.info(f"Killed abandoned process PID {proc.info['pid']} (age: {int(age)}s)")
                                except psutil.NoSuchProcess:
                                    pass
                                except Exception as e:
                                    logger.error(f"Failed to kill process {proc.info['pid']}: {e}")
                                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
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
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Log warnings if resources are high
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent}%")
                
            if memory_percent > 85:
                logger.warning(f"High memory usage: {memory_percent}%")
                
            if disk_percent > 90:
                logger.warning(f"High disk usage: {disk_percent}%")
                
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent
            }
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', type=str, default='0.0.0.0', help='server listen address')
    parser.add_argument('--port', type=int, default=None, help='server listen port')
    parser.add_argument('--num_processes', type=int, default=-1, help='fork process to support')
    args = parser.parse_args()
    
    # Railway provides PORT environment variable
    port = args.port or int(os.getenv('PORT', 10086))
    address = args.address

    # Use absolute paths that work in Docker container
    template_path = '/app/dist/templates' if os.path.exists('/app/dist/templates') else os.path.join(os.path.dirname(__file__), '..', 'dist', 'templates')
    static_path = '/app/dist/static' if os.path.exists('/app/dist/static') else os.path.join(os.path.dirname(__file__), '..', 'dist', 'static')
    settings = {
        'template_path': template_path,
        'static_path': static_path,
    }
    handlers = [
        (r'/health', HealthCheckHandler),         # Health check for Railway
        (r'/api/setup', SetupHandler),            # Setup route for initialization
        (r'/api/reset-database', ResetDatabaseHandler),  # Reset database (USE WITH CAUTION!)
        (r'/ws', AuthenticatedWebSocketHandler),  # Authenticated WebSocket
        (r'/ws-legacy', WebSocketHandler),        # Keep old handler for migration
        (r'/api/login', LoginHandler),
        (r'/api/logout', LogoutHandler),
        (r'/api/validate-session', ValidateSessionHandler),
        (r'/api/renew-session', RenewSessionHandler),
        (r'/api/change-password', ChangePasswordHandler),
        (r'/api/forgot-password', ForgotPasswordHandler),
        (r'/api/reset-password', ResetPasswordHandler),
        (r'/api/upload-file', UploadFileHandler),
        (r'^.*$', VueHandler),
    ]

    # app = web.Application(handlers, **settings, autoreload=True)
    app = web.Application(handlers, **settings)

    # Ensure project directories exist
    logger.info("Ensuring project directories exist...")
    project_base = os.path.join(os.path.dirname(__file__), 'projects', 'ide')
    directories = ['Local', 'Lecture Notes']
    for dir_name in directories:
        dir_path = os.path.join(project_base, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Directory ensured: {dir_path}")
    
    # Initialize database
    logger.info("Initializing database...")
    
    # Run automatic migrations BEFORE starting the server
    logger.info("Running database migrations...")
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        logger.info("DATABASE_URL found - running migrations")
        migration_success = run_auto_migrations(database_url)
        if not migration_success:
            logger.error("Database migrations failed! Server startup aborted.")
            sys.exit(1)
        logger.info("Database migrations completed successfully")
        
        # Auto-initialize users if needed
        logger.info("Checking if users need initialization...")
        try:
            init_users_if_needed()
        except Exception as e:
            logger.error(f"Failed to initialize users: {e}")
    else:
        logger.warning("DATABASE_URL not set - using local PostgreSQL fallback")
        logger.warning("Migrations will be skipped without DATABASE_URL")
    
    if args.num_processes >= 0:
        try:
            http_server = httpserver.HTTPServer(app)
            http_server.bind(port, address)
            http_server.start(num_processes=args.num_processes)
        except:
            app.listen(port, address=address)
    else:
        app.listen(port, address=address)
    
    logger.info('Server listening on {}:{}'.format(address, port))
    logger.info('Database type: {}'.format('PostgreSQL' if db_manager.is_postgres else 'SQLite'))
    print('Server ready at http://{}:{}'.format(address, port))
    pid = os.getpid()
    ppid = os.getppid()
    print('server process pid: {}, ppid: {}'.format(pid, ppid))

    req_processor = RequestProcessor()
    res_processor = ResponseProcessor()
    main_ioloop = ioloop.IOLoop.current()
    main_ioloop.add_timeout(1, req_processor.loop)
    main_ioloop.add_timeout(1, res_processor.loop)
    
    # Initialize process cleanup service
    cleanup_service = ProcessCleanupService()
    
    # Schedule periodic cleanup (every 5 minutes)
    cleanup_interval = int(os.environ.get('CLEANUP_INTERVAL_MS', '300000'))  # 5 minutes default
    cleanup_callback = PeriodicCallback(
        cleanup_service.cleanup_abandoned_processes,
        cleanup_interval
    )
    cleanup_callback.start()
    logger.info(f"Process cleanup service started (interval: {cleanup_interval/1000}s)")
    
    # Schedule resource monitoring (every minute)
    resource_check_callback = PeriodicCallback(
        cleanup_service.check_system_resources,
        60000  # 1 minute
    )
    resource_check_callback.start()
    logger.info("Resource monitoring service started")
    
    # Start health monitoring service
    health_monitor.start()
    
    main_ioloop.start()


if __name__ == '__main__':
    main()
