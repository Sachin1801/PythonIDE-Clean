"""WebSocket keepalive mixin for maintaining connections"""
import asyncio
import time
import json
import logging
from tornado.ioloop import PeriodicCallback

logger = logging.getLogger(__name__)

class WebSocketKeepaliveMixin:
    """Mixin to add keepalive functionality to WebSocket handlers"""
    
    def setup_keepalive(self):
        """Initialize keepalive mechanism"""
        self.last_pong_time = time.time()
        self.keepalive_ping_interval = 45  # Send ping every 45 seconds (less aggressive)
        self.keepalive_pong_timeout = 120  # Close connection if no pong in 120 seconds (more lenient)
        
        # Start periodic ping
        self.ping_callback = PeriodicCallback(
            self.send_keepalive_ping,
            self.keepalive_ping_interval * 1000  # Convert to milliseconds
        )
        self.ping_callback.start()
        
        # Start periodic pong check
        self.pong_check_callback = PeriodicCallback(
            self.check_pong_timeout,
            10000  # Check every 10 seconds
        )
        self.pong_check_callback.start()
        
        logger.debug(f"Keepalive started for {self.request.remote_ip}")
    
    def send_keepalive_ping(self):
        """Send ping to client"""
        try:
            if hasattr(self, 'ws_connection') and self.ws_connection:
                self.ping(b'keepalive')
                logger.debug(f"Ping sent to {self.request.remote_ip}")
            elif hasattr(self, 'connected') and self.connected:
                # Alternative: send a keepalive message if ping is not available
                self.write_message(json.dumps({
                    'type': 'ping',
                    'timestamp': time.time()
                }))
                logger.debug(f"Keepalive message sent to {self.request.remote_ip}")
        except Exception as e:
            logger.error(f"Error sending ping: {e}")
            if hasattr(self, 'close'):
                self.close()
    
    def on_pong(self, data):
        """Handle pong response from client"""
        self.last_pong_time = time.time()
        logger.debug(f"Pong received from {self.request.remote_ip}")
    
    def check_pong_timeout(self):
        """Check if client is still responsive"""
        elapsed_time = time.time() - self.last_pong_time
        if elapsed_time > self.keepalive_pong_timeout:
            logger.warning(f"WebSocket pong timeout for {self.request.remote_ip}: {elapsed_time:.1f}s elapsed (max {self.keepalive_pong_timeout}s), closing connection and triggering reconnection")
            if hasattr(self, 'close'):
                self.close()
    
    def cleanup_keepalive(self):
        """Stop keepalive callbacks"""
        if hasattr(self, 'ping_callback'):
            self.ping_callback.stop()
        if hasattr(self, 'pong_check_callback'):
            self.pong_check_callback.stop()