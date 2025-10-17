#!/usr/bin/env python3
"""
Lockdown handler for exam mode
Prevents students from accessing main IDE during exams
"""
import os
import json
from datetime import datetime, timezone
from tornado.web import RequestHandler


class LockdownHandler(RequestHandler):
    """Handle lockdown mode during exams"""

    def initialize(self):
        """Check if lockdown is active"""
        # Check environment variable
        self.lockdown_enabled = os.environ.get("LOCKDOWN_MODE", "false").lower() == "true"

        # Optional: Check time-based lockdown
        lockdown_start = os.environ.get("LOCKDOWN_START")  # ISO format: 2024-03-15T09:00:00Z
        lockdown_end = os.environ.get("LOCKDOWN_END")      # ISO format: 2024-03-15T10:30:00Z

        if lockdown_start and lockdown_end:
            try:
                start_time = datetime.fromisoformat(lockdown_start.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(lockdown_end.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)

                if start_time <= current_time <= end_time:
                    self.lockdown_enabled = True
            except Exception as e:
                print(f"Error parsing lockdown times: {e}")

    def check_lockdown(self):
        """Check if request should be blocked"""
        if not self.lockdown_enabled:
            return False

        # Allow professor access even during lockdown
        auth_header = self.request.headers.get("Authorization", "")
        if auth_header:
            # Import here to avoid circular dependency
            from auth.user_manager_postgres import UserManager
            user_manager = UserManager()

            # Extract token
            token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header

            # Validate session
            session = user_manager.validate_session(token)
            if session and session.get("role") == "professor":
                return False  # Professors can access during lockdown

        return True

    def write_lockdown_response(self):
        """Send lockdown message"""
        self.set_status(503)  # Service Temporarily Unavailable
        self.set_header("Content-Type", "application/json")

        lockdown_message = os.environ.get(
            "LOCKDOWN_MESSAGE",
            "The main IDE is temporarily unavailable during the exam period. "
            "Please use the exam environment at /exam/"
        )

        self.write(json.dumps({
            "error": "Service Temporarily Unavailable",
            "message": lockdown_message,
            "lockdown": True,
            "exam_url": "/exam/",
            "status": 503
        }))
        self.finish()


class LockdownCheckHandler(LockdownHandler):
    """API endpoint to check lockdown status"""

    def get(self):
        """Check if system is in lockdown"""
        if self.lockdown_enabled:
            lockdown_end = os.environ.get("LOCKDOWN_END", "Unknown")
            self.write(json.dumps({
                "lockdown": True,
                "message": "System is in lockdown mode",
                "exam_url": "/exam/",
                "estimated_end": lockdown_end
            }))
        else:
            self.write(json.dumps({
                "lockdown": False,
                "message": "System is operational"
            }))


def lockdown_middleware(handler_class):
    """Decorator to add lockdown check to any handler"""
    original_prepare = handler_class.prepare

    def prepare_with_lockdown(self):
        # Create a lockdown handler instance
        lockdown = LockdownHandler()
        lockdown.initialize()
        lockdown.request = self.request

        # Check lockdown
        if lockdown.check_lockdown():
            # Check if this is an API or WebSocket request
            if (self.request.path.startswith("/api/") or
                self.request.path.startswith("/ws/")):

                lockdown.write_lockdown_response()
                self.finish()
                return

            # For web pages, redirect to lockdown page
            self.redirect("/lockdown")
            return

        # Continue with original prepare
        if original_prepare:
            original_prepare(self)

    handler_class.prepare = prepare_with_lockdown
    return handler_class