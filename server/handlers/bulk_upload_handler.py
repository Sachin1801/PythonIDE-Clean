#!/usr/bin/env python3

import json
import tornado.web
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.user_manager_postgres import UserManager
from common.file_storage import file_storage
from command.resource import write_project_file

logger = logging.getLogger(__name__)


class BulkUploadHandler(tornado.web.RequestHandler):
    """Handle bulk file upload to multiple students' folders"""

    def initialize(self):
        self.user_manager = UserManager()

    def set_default_headers(self):
        """Set CORS headers"""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, session-id")

    def options(self):
        """Handle preflight requests"""
        self.set_status(204)
        self.finish()

    def post(self):
        """Handle bulk file upload POST request"""
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
                self.write(json.dumps({"success": False, "error": "Only admin users can perform bulk uploads"}))
                return

            # Get form data
            target_students = self.get_argument("targetStudents", default="all")
            common_folder = self.get_argument("commonFolder", default="Examples")
            sub_path = self.get_argument("subPath", default="")
            filename = self.get_argument("filename", default=None)
            relative_path = self.get_argument("relativePath", default=None)
            preserve_structure = self.get_argument("preserveStructure", default="false")

            if not filename:
                self.set_status(400)
                self.write(json.dumps({"success": False, "error": "Missing required parameter: filename"}))
                return

            # Get uploaded file
            if "file" not in self.request.files:
                self.set_status(400)
                self.write(json.dumps({"success": False, "error": "No file uploaded"}))
                return

            file_info = self.request.files["file"][0]
            file_content = file_info["body"]

            # Validate file extension
            allowed_extensions = [".py", ".txt", ".csv", ".pdf"]
            file_extension = "." + filename.split(".")[-1].lower()
            if file_extension not in allowed_extensions:
                self.set_status(400)
                self.write(
                    json.dumps(
                        {
                            "success": False,
                            "error": f'File type not allowed. Supported: {", ".join(allowed_extensions)}',
                        }
                    )
                )
                return

            # Validate file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if len(file_content) > max_size:
                self.set_status(400)
                self.write(json.dumps({"success": False, "error": "File too large. Maximum size: 10MB"}))
                return

            # Get list of target students
            if target_students == "all":
                students = self.user_manager.get_all_students()
                student_usernames = [s["username"] for s in students]
            else:
                # Parse JSON array of student usernames
                try:
                    student_usernames = json.loads(target_students)
                except json.JSONDecodeError:
                    self.set_status(400)
                    self.write(json.dumps({"success": False, "error": "Invalid targetStudents format"}))
                    return

            if not student_usernames:
                self.set_status(400)
                self.write(json.dumps({"success": False, "error": "No students found"}))
                return

            # Upload file to each student's folder
            success_count = 0
            failed_students = []

            for username in student_usernames:
                try:
                    # Construct project name (Local/{username})
                    project_name = f"Local/{username}"

                    # Construct the file path within the student's folder
                    # Format: /{commonFolder}/{subPath}/{file_structure}
                    if preserve_structure == "true" and relative_path:
                        # Handle folder structure preservation
                        path_parts = relative_path.split('/')

                        if len(path_parts) == 1:
                            # Single file, no nesting
                            if sub_path:
                                file_path = f"/{common_folder}/{sub_path}/{filename}"
                            else:
                                file_path = f"/{common_folder}/{filename}"
                        else:
                            # Preserve nested structure (skip root folder name)
                            nested_path = '/'.join(path_parts[1:])
                            if sub_path:
                                file_path = f"/{common_folder}/{sub_path}/{nested_path}"
                            else:
                                file_path = f"/{common_folder}/{nested_path}"
                    else:
                        # Simple file upload
                        safe_filename = os.path.basename(filename)
                        if sub_path:
                            file_path = f"/{common_folder}/{sub_path}/{safe_filename}"
                        else:
                            file_path = f"/{common_folder}/{safe_filename}"

                    # Get project path (handles both local and EFS)
                    project_path = os.path.join(file_storage.ide_base, project_name)
                    full_file_path = os.path.join(project_path, file_path.lstrip("/"))

                    # Ensure parent directory exists
                    os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

                    # Determine if it's a binary file
                    is_binary = self._is_binary_file(file_extension)

                    if is_binary:
                        # For binary files, save raw content
                        with open(full_file_path, "wb") as f:
                            f.write(file_content)
                        code = 0
                    else:
                        # For text files, decode and use write_project_file
                        try:
                            content_str = file_content.decode("utf-8")
                        except UnicodeDecodeError:
                            try:
                                content_str = file_content.decode("latin-1")
                            except UnicodeDecodeError:
                                content_str = file_content.decode("utf-8", errors="replace")

                        code, error = write_project_file(project_path, full_file_path, content_str)

                    if code == 0:
                        success_count += 1
                        logger.info(f"Bulk upload: {filename} → {project_name}{file_path} (admin: {user_info['username']})")
                    else:
                        failed_students.append(username)
                        logger.error(f"Failed to upload to {username}: error code {code}")

                except Exception as e:
                    failed_students.append(username)
                    logger.error(f"Failed to upload to {username}: {str(e)}")

            # Return results
            response = {
                "success": True,
                "uploaded_to": success_count,
                "total_students": len(student_usernames),
                "failed_students": failed_students,
                "file_path": file_path if success_count > 0 else None
            }

            if failed_students:
                response["warning"] = f"Failed to upload to {len(failed_students)} student(s)"

            logger.info(f"Bulk upload complete: {success_count}/{len(student_usernames)} successful")
            self.write(json.dumps(response))

        except Exception as e:
            logger.error(f"Error in BulkUploadHandler: {str(e)}")
            import traceback
            traceback.print_exc()
            self.set_status(500)
            self.write(json.dumps({"success": False, "error": f"Internal server error: {str(e)}"}))

    def _is_binary_file(self, extension):
        """Determine if a file should be treated as binary based on its extension"""
        binary_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".zip", ".tar", ".gz"]
        return extension.lower() in binary_extensions
