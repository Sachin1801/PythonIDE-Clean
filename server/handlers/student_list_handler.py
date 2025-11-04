#!/usr/bin/env python3

import json
import tornado.web
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager

logger = logging.getLogger(__name__)


class StudentListHandler(tornado.web.RequestHandler):
    """Handle requests to get list of all students"""

    def initialize(self):
        self.user_manager = UserManager()

    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, session-id")

    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()

    def get(self):
        """Get all students"""
        try:
            # Get session ID from headers
            session_id = self.request.headers.get("session-id")
            if not session_id:
                self.set_status(401)
                self.write(json.dumps({"success": False, "error": "No session ID provided"}))
                return

            # Validate session and get user info
            user_info = self.user_manager.validate_session(session_id)
            if not user_info:
                self.set_status(401)
                self.write(json.dumps({"success": False, "error": "Invalid session"}))
                return

            # Check if user is admin (professors only)
            admin_accounts = ["sl7927", "sa9082", "et2434", "admin_editor", "test_admin"]
            if user_info["username"] not in admin_accounts:
                self.set_status(403)
                self.write(json.dumps({"success": False, "error": "Only admin users can access student list"}))
                return

            # Get all students from database
            students = self.user_manager.get_all_students()

            # Convert to list of dictionaries (if using RealDictCursor, already dicts)
            student_list = []
            for student in students:
                student_list.append({
                    "username": student["username"],
                    "full_name": student["full_name"],
                    "email": student.get("email", "")
                })

            logger.info(f"Retrieved {len(student_list)} students for admin: {user_info['username']}")

            self.write(json.dumps({
                "success": True,
                "students": student_list,
                "count": len(student_list)
            }))

        except Exception as e:
            logger.error(f"Error in StudentListHandler: {str(e)}")
            import traceback
            traceback.print_exc()
            self.set_status(500)
            self.write(json.dumps({"success": False, "error": f"Internal server error: {str(e)}"}))
