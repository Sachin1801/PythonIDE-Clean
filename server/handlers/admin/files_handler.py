"""
Admin File Browser Handler
Allows professors to browse, view, and download student files.
"""

import io
import logging
import mimetypes
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.database import db_manager
from common.file_storage import file_storage
from handlers.admin.auth_handler import BaseAdminHandler
from utils.audit_logger import log_admin_action, AuditActionType

logger = logging.getLogger(__name__)

# Allowed text file extensions for preview
TEXT_EXTENSIONS = {
    '.py', '.txt', '.md', '.json', '.csv', '.xml', '.html', '.css', '.js',
    '.yaml', '.yml', '.ini', '.cfg', '.conf', '.log', '.sh', '.bat',
    '.java', '.c', '.cpp', '.h', '.hpp', '.rs', '.go', '.rb', '.php',
    '.sql', '.r', '.m', '.swift', '.kt', '.ts', '.jsx', '.tsx', '.vue'
}

# Binary file extensions that can be previewed as images
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.ico'}

# Maximum file size for preview (5MB)
MAX_PREVIEW_SIZE = 5 * 1024 * 1024


def get_local_base_path():
    """Get the base path for student directories"""
    storage_info = file_storage.get_storage_info()
    return os.path.join(storage_info['ide_base'], 'Local')


def validate_path(requested_path, base_path):
    """
    Validate that the requested path is within the allowed base path.
    Prevents directory traversal attacks.
    """
    # Resolve to absolute path
    abs_base = os.path.abspath(base_path)
    abs_requested = os.path.abspath(os.path.join(base_path, requested_path))

    # Check if requested path starts with base path
    if not abs_requested.startswith(abs_base):
        return None

    return abs_requested


def get_file_info(file_path, relative_to=None):
    """Get file/directory information"""
    try:
        stat = os.stat(file_path)
        name = os.path.basename(file_path)
        is_dir = os.path.isdir(file_path)

        info = {
            'name': name,
            'path': os.path.relpath(file_path, relative_to) if relative_to else file_path,
            'is_directory': is_dir,
            'size': stat.st_size if not is_dir else None,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

        if not is_dir:
            ext = os.path.splitext(name)[1].lower()
            info['extension'] = ext
            info['is_text'] = ext in TEXT_EXTENSIONS
            info['is_image'] = ext in IMAGE_EXTENSIONS

        return info
    except OSError as e:
        logger.error(f"Error getting file info for {file_path}: {e}")
        return None


class AdminStudentsListHandler(BaseAdminHandler):
    """Handler for listing all student directories"""

    def get(self):
        """
        GET /api/admin/files/students
        Returns list of all student directories.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            base_path = get_local_base_path()

            if not os.path.exists(base_path):
                self.write({
                    "success": True,
                    "data": []
                })
                return

            students = []
            for entry in sorted(os.listdir(base_path)):
                entry_path = os.path.join(base_path, entry)
                if os.path.isdir(entry_path):
                    # Get file count for this student
                    file_count = sum(
                        len(files) for _, _, files in os.walk(entry_path)
                    )

                    # Get last modified time
                    try:
                        stat = os.stat(entry_path)
                        modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    except OSError:
                        modified = None

                    students.append({
                        'username': entry,
                        'file_count': file_count,
                        'last_modified': modified
                    })

            self.write({
                "success": True,
                "data": students
            })

        except Exception as e:
            logger.error(f"Error listing students: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to list students"})


class AdminBrowseFilesHandler(BaseAdminHandler):
    """Handler for browsing directory contents"""

    def get(self):
        """
        GET /api/admin/files/browse?path=username/subfolder
        Returns contents of the specified directory.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            requested_path = self.get_argument("path", "")
            base_path = get_local_base_path()

            # Validate path
            if requested_path:
                full_path = validate_path(requested_path, base_path)
                if not full_path:
                    self.set_status(403)
                    self.write({"success": False, "error": "Access denied"})
                    return
            else:
                full_path = base_path

            if not os.path.exists(full_path):
                self.set_status(404)
                self.write({"success": False, "error": "Path not found"})
                return

            if not os.path.isdir(full_path):
                self.set_status(400)
                self.write({"success": False, "error": "Path is not a directory"})
                return

            # List directory contents
            items = []
            for entry in sorted(os.listdir(full_path)):
                entry_path = os.path.join(full_path, entry)
                info = get_file_info(entry_path, base_path)
                if info:
                    items.append(info)

            # Sort: directories first, then files
            items.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))

            self.write({
                "success": True,
                "data": {
                    "path": requested_path,
                    "items": items
                }
            })

        except Exception as e:
            logger.error(f"Error browsing files: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to browse files"})


class AdminFileContentHandler(BaseAdminHandler):
    """Handler for reading file content"""

    def get(self):
        """
        GET /api/admin/files/content?path=username/file.py
        Returns the content of the specified file.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            requested_path = self.get_argument("path", "")
            if not requested_path:
                self.set_status(400)
                self.write({"success": False, "error": "Path is required"})
                return

            base_path = get_local_base_path()
            full_path = validate_path(requested_path, base_path)

            if not full_path:
                self.set_status(403)
                self.write({"success": False, "error": "Access denied"})
                return

            if not os.path.exists(full_path):
                self.set_status(404)
                self.write({"success": False, "error": "File not found"})
                return

            if os.path.isdir(full_path):
                self.set_status(400)
                self.write({"success": False, "error": "Path is a directory"})
                return

            # Check file size
            file_size = os.path.getsize(full_path)
            if file_size > MAX_PREVIEW_SIZE:
                self.set_status(413)
                self.write({
                    "success": False,
                    "error": f"File too large for preview (max {MAX_PREVIEW_SIZE // 1024 // 1024}MB)"
                })
                return

            # Determine file type
            ext = os.path.splitext(full_path)[1].lower()

            if ext in IMAGE_EXTENSIONS:
                # Return image as base64
                import base64
                with open(full_path, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('utf-8')

                mime_type = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'

                self.write({
                    "success": True,
                    "data": {
                        "type": "image",
                        "mime_type": mime_type,
                        "content": content,
                        "size": file_size
                    }
                })
            elif ext in TEXT_EXTENSIONS or ext == '':
                # Read as text
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Try latin-1 as fallback
                    with open(full_path, 'r', encoding='latin-1') as f:
                        content = f.read()

                self.write({
                    "success": True,
                    "data": {
                        "type": "text",
                        "content": content,
                        "size": file_size,
                        "extension": ext
                    }
                })
            else:
                # Binary file - not previewable
                self.write({
                    "success": True,
                    "data": {
                        "type": "binary",
                        "size": file_size,
                        "extension": ext,
                        "message": "Binary file - download to view"
                    }
                })

            # Log file view
            try:
                log_admin_action(
                    admin_user_id=user.get('id'),
                    action_type=AuditActionType.VIEW_FILE,
                    target_path=requested_path,
                    ip_address=self.get_client_ip()
                )
            except Exception as log_error:
                logger.warning(f"Failed to log file view: {log_error}")

        except Exception as e:
            logger.error(f"Error reading file content: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to read file"})


class AdminFileDownloadHandler(BaseAdminHandler):
    """Handler for downloading files"""

    def get(self):
        """
        GET /api/admin/files/download?path=username/file.py
        Downloads the specified file.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            requested_path = self.get_argument("path", "")
            if not requested_path:
                self.set_status(400)
                self.write({"success": False, "error": "Path is required"})
                return

            base_path = get_local_base_path()
            full_path = validate_path(requested_path, base_path)

            if not full_path:
                self.set_status(403)
                self.write({"success": False, "error": "Access denied"})
                return

            if not os.path.exists(full_path):
                self.set_status(404)
                self.write({"success": False, "error": "File not found"})
                return

            if os.path.isdir(full_path):
                # Download directory as ZIP
                self._download_as_zip(full_path, requested_path, user)
            else:
                # Download single file
                self._download_file(full_path, requested_path, user)

        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to download file"})

    def _download_file(self, full_path, requested_path, user):
        """Download a single file"""
        filename = os.path.basename(full_path)
        mime_type = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'

        self.set_header('Content-Type', mime_type)
        self.set_header('Content-Disposition', f'attachment; filename="{filename}"')

        with open(full_path, 'rb') as f:
            self.write(f.read())

        # Log download
        try:
            log_admin_action(
                admin_user_id=user.get('id'),
                action_type=AuditActionType.DOWNLOAD_FILE,
                target_path=requested_path,
                ip_address=self.get_client_ip()
            )
        except Exception as log_error:
            logger.warning(f"Failed to log file download: {log_error}")

    def _download_as_zip(self, full_path, requested_path, user):
        """Download a directory as ZIP"""
        dirname = os.path.basename(full_path)
        zip_filename = f"{dirname}.zip"

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, full_path)
                    zf.write(file_path, os.path.join(dirname, arc_name))

        zip_buffer.seek(0)

        self.set_header('Content-Type', 'application/zip')
        self.set_header('Content-Disposition', f'attachment; filename="{zip_filename}"')
        self.write(zip_buffer.read())

        # Log download
        try:
            log_admin_action(
                admin_user_id=user.get('id'),
                action_type=AuditActionType.DOWNLOAD_FILE,
                target_path=requested_path,
                details={"type": "directory_zip"},
                ip_address=self.get_client_ip()
            )
        except Exception as log_error:
            logger.warning(f"Failed to log directory download: {log_error}")


class AdminFileSearchHandler(BaseAdminHandler):
    """Handler for searching files across student directories"""

    def get(self):
        """
        GET /api/admin/files/search?q=search_term&student=username
        Searches for files matching the query.
        """
        user = self.require_admin()
        if not user:
            return

        try:
            query = self.get_argument("q", "").strip().lower()
            student = self.get_argument("student", "").strip()

            if not query:
                self.set_status(400)
                self.write({"success": False, "error": "Search query is required"})
                return

            base_path = get_local_base_path()

            # Determine search root
            if student:
                search_root = validate_path(student, base_path)
                if not search_root or not os.path.exists(search_root):
                    self.set_status(404)
                    self.write({"success": False, "error": "Student not found"})
                    return
            else:
                search_root = base_path

            # Search for files
            results = []
            max_results = 100

            for root, dirs, files in os.walk(search_root):
                if len(results) >= max_results:
                    break

                for filename in files:
                    if query in filename.lower():
                        file_path = os.path.join(root, filename)
                        info = get_file_info(file_path, base_path)
                        if info:
                            results.append(info)

                        if len(results) >= max_results:
                            break

            self.write({
                "success": True,
                "data": {
                    "query": query,
                    "results": results,
                    "total": len(results),
                    "truncated": len(results) >= max_results
                }
            })

        except Exception as e:
            logger.error(f"Error searching files: {e}")
            self.set_status(500)
            self.write({"success": False, "error": "Failed to search files"})
