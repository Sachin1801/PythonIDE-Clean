"""Health monitoring and auto-recovery service for the Python IDE server"""
import os
import sys
import time
import psutil
import logging
import signal
from tornado.ioloop import PeriodicCallback, IOLoop
from common.database import db_manager

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitor server health and perform auto-recovery when needed"""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_db_check = 0
        self.db_failures = 0
        self.max_db_failures = 3
        self.memory_threshold = 85  # Restart if memory usage exceeds 85%
        self.last_activity = time.time()
        self.idle_timeout = 3600  # 1 hour idle timeout
        
    def start(self):
        """Start health monitoring"""
        # Check health every 30 seconds
        self.health_callback = PeriodicCallback(
            self.check_health,
            30000  # 30 seconds
        )
        self.health_callback.start()
        
        # Check for idle timeout every 5 minutes
        self.idle_callback = PeriodicCallback(
            self.check_idle,
            300000  # 5 minutes
        )
        self.idle_callback.start()
        
        logger.info("Health monitoring service started")
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
    
    def check_health(self):
        """Perform comprehensive health check"""
        try:
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.memory_threshold:
                logger.warning(f"Memory usage critical: {memory.percent}%")
                self.trigger_graceful_restart("High memory usage")
                return
            
            # Check database connection
            if not self.check_database():
                self.db_failures += 1
                if self.db_failures >= self.max_db_failures:
                    logger.error("Database connection failed multiple times")
                    self.trigger_graceful_restart("Database connection lost")
                    return
            else:
                self.db_failures = 0
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 95:
                logger.critical(f"Disk space critical: {disk.percent}%")
                self.cleanup_temp_files()
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                logger.warning(f"CPU usage high: {cpu_percent}%")
                # Trigger process cleanup
                self.cleanup_zombie_processes()
            
            # Log health status
            uptime = int(time.time() - self.start_time)
            logger.debug(f"Health check OK - Uptime: {uptime}s, Memory: {memory.percent}%, CPU: {cpu_percent}%")
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    def check_database(self):
        """Check database connectivity"""
        try:
            result = db_manager.execute_query("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            # Try to reconnect
            try:
                db_manager._init_postgres()
                return True
            except:
                return False
    
    def check_idle(self):
        """Check if server has been idle too long"""
        idle_time = time.time() - self.last_activity
        if idle_time > self.idle_timeout:
            logger.info(f"Server idle for {int(idle_time)}s, performing cleanup")
            self.cleanup_resources()
    
    def cleanup_resources(self):
        """Clean up resources to free memory"""
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear any caches
            if hasattr(db_manager, 'connection_pool'):
                # Close idle connections
                db_manager.connection_pool.closeall()
                db_manager._init_postgres()
                logger.info("Database connections refreshed")
            
        except Exception as e:
            logger.error(f"Resource cleanup error: {e}")
    
    def cleanup_zombie_processes(self):
        """Clean up zombie Python processes"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    os.waitpid(proc.info['pid'], os.WNOHANG)
                    logger.info(f"Cleaned up zombie process {proc.info['pid']}")
        except Exception as e:
            logger.error(f"Zombie cleanup error: {e}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files to free disk space"""
        try:
            import tempfile
            import shutil
            
            temp_dir = tempfile.gettempdir()
            # Clean old temp files (older than 1 hour)
            current_time = time.time()
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.getmtime(file_path) < current_time - 3600:
                            os.remove(file_path)
                    except:
                        pass
            
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.error(f"Temp file cleanup error: {e}")
    
    def trigger_graceful_restart(self, reason):
        """Trigger a graceful server restart"""
        logger.warning(f"Triggering graceful restart: {reason}")
        
        # On Railway, exit with code 0 for automatic restart
        # The restart policy in railway.json will handle it
        IOLoop.current().add_callback(self.shutdown)
    
    def shutdown(self):
        """Perform graceful shutdown"""
        logger.info("Starting graceful shutdown...")
        
        # Close database connections
        if hasattr(db_manager, 'close'):
            db_manager.close()
        
        # Stop the IOLoop
        IOLoop.current().stop()
        
        # Exit with code 0 for Railway to restart
        sys.exit(0)

# Global health monitor instance
health_monitor = HealthMonitor()