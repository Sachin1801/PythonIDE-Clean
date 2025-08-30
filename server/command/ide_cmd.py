#!/usr/bin/env python3
import os
import json
import jedi
import time
import asyncio
import threading
import subprocess
from tornado.ioloop import IOLoop
from jedi import __version__ as jedi_version
from packaging.version import Version
from .utils import convert_path
from .resource import *
from .response import response
from .error_handler import EducationalErrorHandler
from .interactive_thread import InteractiveSubProgramThread
from .simple_interactive_thread import SimpleInteractiveThread
from .pty_interactive_thread import PTYInteractiveThread
from .working_simple_thread import WorkingSimpleThread
from .working_input_thread import WorkingInputThread
from .repl_thread import PythonREPLThread
from .hybrid_repl_thread import HybridREPLThread
from .bug_report_handler import handle_bug_report
from common.config import Config

PROJECT_IS_EXIST = -1
PROJECT_IS_NOT_EXIST = -2

DIR_IS_EXIST = -11
DIR_IS_NOT_EXIST = -12

FILE_IS_EXIST = -21
FILE_IS_NOT_EXIST = -22

jedi_is_gt_17 = Version(jedi_version) >= Version('0.17.0')

if not os.path.exists(os.path.join(Config.PROJECTS, 'ide')):
    os.makedirs(os.path.join(Config.PROJECTS, 'ide'))

# Ensure default folders exist
default_folders = ['Local', 'Assignments', 'Lecture Notes', 'Testing']
for folder_name in default_folders:
    folder_path = os.path.join(Config.PROJECTS, 'ide', folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        # Create .config file for the folder
        config_path = os.path.join(folder_path, '.config')
        config_data = {
            'type': 'python',
            'expendKeys': [],
            'openList': [],
            'selectFilePath': '',
            'lastAccessTime': time.time(),
            'protected': folder_name in ['Assignments', 'Lecture Notes']  # Mark as protected
        }
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)


class IdeCmd(object):
    def __init__(self):
        pass

    async def ide_list_projects(self, client, cmd_id, data):
        ide_path = os.path.join(Config.PROJECTS, 'ide')
        code, projects = list_projects(ide_path)
        await response(client, cmd_id, code, projects)

    async def ide_get_project(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        code, project = get_project(prj_path)
        await response(client, cmd_id, code, project)

    async def ide_create_project(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        code, _ = create_project(prj_path, config_data={
            'type': 'python',
            'expendKeys': ['/'],
            'openList': ['/main.py'],
            'selectFilePath': '/main.py'
        })
        if code == 0:
            # Create main.py with comprehensive boilerplate code
            boilerplate_code = '''#!/usr/bin/env python3
"""
Welcome to Python Programming!

This is your first Python program. 
Let's start with the basics.
"""

# First, let's learn about printing output
print("Hello, World!")
print("Welcome to Python programming!")
print()  # This prints an empty line

# Variables and basic data types
name = "Student"  # String (text)
age = 20  # Integer (whole number)
gpa = 3.5  # Float (decimal number)
is_student = True  # Boolean (True/False)

# Printing variables
print(f"Name: {name}")
print(f"Age: {age}")
print(f"GPA: {gpa}")
print(f"Is a student: {is_student}")
print()

# Basic arithmetic operations
x = 10
y = 3

print("Basic Math Operations:")
print(f"{x} + {y} = {x + y}")  # Addition
print(f"{x} - {y} = {x - y}")  # Subtraction
print(f"{x} * {y} = {x * y}")  # Multiplication
print(f"{x} / {y} = {x / y}")  # Division
print(f"{x} // {y} = {x // y}")  # Integer division
print(f"{x} % {y} = {x % y}")  # Modulo (remainder)
print(f"{x} ** {y} = {x ** y}")  # Exponentiation
print()

# Getting user input
# Uncomment the lines below to try user input:
# user_name = input("What's your name? ")
# print(f"Nice to meet you, {user_name}!")

# Lists (arrays)
fruits = ["apple", "banana", "orange"]
print("Fruits list:", fruits)
print("First fruit:", fruits[0])
print("Number of fruits:", len(fruits))
print()

# Conditional statements
score = 85
print(f"Score: {score}")

if score >= 90:
    print("Grade: A")
elif score >= 80:
    print("Grade: B")
elif score >= 70:
    print("Grade: C")
else:
    print("Grade: F")
print()

# Loops
print("Counting from 1 to 5:")
for i in range(1, 6):
    print(f"  {i}")

print("\\nFruits in our list:")
for fruit in fruits:
    print(f"  - {fruit}")

# Functions
def greet(name):
    """A simple greeting function"""
    return f"Hello, {name}!"

def add_numbers(a, b):
    """Add two numbers and return the result"""
    return a + b

# Using our functions
print("\\nUsing functions:")
message = greet("Python Learner")
print(message)

result = add_numbers(15, 27)
print(f"15 + 27 = {result}")

# Your turn!
# Try modifying this code:
# 1. Change the values of variables
# 2. Add new items to the fruits list
# 3. Create your own function
# 4. Uncomment the input lines to make it interactive

print("\\n" + "="*50)
print("Happy coding! 🐍")
print("="*50)
'''
            write(os.path.join(prj_path, 'main.py'), boilerplate_code)
        await response(client, cmd_id, code, _)

    async def ide_delete_project(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        code, _ = delete(prj_path)
        await response(client, cmd_id, code, _)

    async def ide_rename_project(self, client, cmd_id, data):
        old_name = data.get('oldName')
        
        # Check if project is protected
        protected_projects = ['Assignments', 'Lecture Notes']
        if old_name in protected_projects:
            await response(client, cmd_id, -1, f'Cannot rename protected folder: {old_name}')
            return
            
        old_path = os.path.join(Config.PROJECTS, 'ide', old_name)
        new_name = data.get('newName')
        new_path = os.path.join(Config.PROJECTS, 'ide', new_name)
        code, _ = rename(old_path, new_path)
        await response(client, cmd_id, code, _)

    async def ide_save_project(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        code, _ = save_project(prj_path, data)
        await response(client, cmd_id, code, _)

    async def ide_create_file(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        parent_path = convert_path(data.get('parentPath'))
        file_name = data.get('fileName')
        file_path = os.path.join(prj_path, parent_path, file_name)
        code, _ = write_project_file(prj_path, file_path, '')
        await response(client, cmd_id, code, _)

    async def ide_write_file(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        file_path = os.path.join(prj_path, convert_path(data.get('filePath')))
        file_data = data.get('fileData')
        code, _ = write_project_file(prj_path, file_path, file_data)
        if data.get('complete', False):
            line = data.get('line', None)
            column = data.get('column', None)
            line = line + 1 if line is not None else line
            completions = set()
            if jedi_is_gt_17:
                script = jedi.api.Script(code=file_data, path=file_path, project=jedi.api.Project(file_path, added_sys_path=[]))
                for completion in script.complete(line=line, column=column):
                    completions.add(completion.name)
            else:
                script = jedi.api.Script(source=file_data, line=line, column=column, path=file_path)
                completions = set()
                for completion in script.completions():
                    completions.add(completion.name)
            await response(client, cmd_id, 0, list(completions))
        else:
            await response(client, cmd_id, code, _)

    async def ide_get_file(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        file_path = os.path.join(prj_path, convert_path(data.get('filePath')))
        
        # Check if binary file requested
        is_binary = data.get('binary', False)
        if is_binary:
            from .resource import get_project_file_binary
            code, file_data = get_project_file_binary(prj_path, file_path)
            if code == 0:
                await response(client, cmd_id, code, {'content': file_data, 'binary': True})
            else:
                await response(client, cmd_id, code, file_data)
        else:
            code, file_data = get_project_file(prj_path, file_path)
            await response(client, cmd_id, code, file_data)

    async def ide_delete_file(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        file_path = os.path.join(prj_path, convert_path(data.get('filePath')))
        code, _ = delete_project_file(prj_path, file_path)
        await response(client, cmd_id, code, _)

    async def ide_rename_file(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        old_path_input = data.get('oldPath')
        new_name = data.get('newName')
        
        # Debug logging
        print(f'[RENAME_FILE] Project: {prj_name}')
        print(f'[RENAME_FILE] Old path input: {old_path_input}')
        print(f'[RENAME_FILE] New name: {new_name}')
        
        old_path = os.path.join(prj_path, convert_path(old_path_input))
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        
        print(f'[RENAME_FILE] Full old path: {old_path}')
        print(f'[RENAME_FILE] Full new path: {new_path}')
        print(f'[RENAME_FILE] Old path exists: {os.path.exists(old_path)}')
        print(f'[RENAME_FILE] New path exists: {os.path.exists(new_path)}')
        
        code, error_msg = rename_project_file(prj_path, old_path, new_path)
        
        print(f'[RENAME_FILE] Result code: {code}, error: {error_msg}')
        
        if code != 0:
            # Send error message with details
            await response(client, cmd_id, code, f'Failed to rename: {error_msg or "Unknown error"}')
        else:
            await response(client, cmd_id, code, error_msg)

    async def ide_create_folder(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        parent_path = convert_path(data.get('parentPath'))
        folder_name = data.get('folderName')
        folder_path = os.path.join(prj_path, parent_path, folder_name)
        code, _ = create_project_folder(prj_path, folder_path)
        await response(client, cmd_id, code, _)

    async def ide_delete_folder(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        folder_path = os.path.join(prj_path, convert_path(data.get('folderPath')))
        code, _ = delete_project_file(prj_path, folder_path)
        await response(client, cmd_id, code, _)

    async def ide_rename_folder(self, client, cmd_id, data):
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        old_path = os.path.join(prj_path, convert_path(data.get('oldPath')))
        new_name = data.get('newName')
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        code, _ = rename_project_file(prj_path, old_path, new_path)
        await response(client, cmd_id, code, _)

    async def ide_move_file(self, client, cmd_id, data):
        """Move a file from one location to another with proper permissions"""
        try:
            # Import secure file manager for permission checking
            from command.secure_file_manager import SecureFileManager
            
            prj_name = data.get('projectName')
            old_path_input = data.get('oldPath')
            new_path_input = data.get('newPath')
            username = getattr(client, 'username', 'unknown')
            role = getattr(client, 'role', 'student')
            
            print(f'[IDE_MOVE_FILE] User: {username}, Role: {role}')
            print(f'[IDE_MOVE_FILE] Project: {prj_name}')
            print(f'[IDE_MOVE_FILE] Old path: {old_path_input}')
            print(f'[IDE_MOVE_FILE] New path: {new_path_input}')
            
            # Validate inputs
            if not old_path_input or not new_path_input:
                await response(client, cmd_id, -1, 'Missing old_path or new_path')
                return
            
            # Convert paths (handle leading slashes, backslashes)
            old_path_relative = convert_path(old_path_input)
            new_path_relative = convert_path(new_path_input)
            
            # Handle paths that might already include project context
            # If the path already starts with a project name, use it as-is
            # Otherwise, prepend the current project name
            if '/' in old_path_relative and old_path_relative.split('/')[0] in ['Local', 'Lecture Notes', 'Assignments', 'Tests']:
                old_path_full = old_path_relative  # Path already includes project context
            else:
                old_path_full = f"{prj_name}/{old_path_relative}" if old_path_relative else prj_name
                
            if '/' in new_path_relative and new_path_relative.split('/')[0] in ['Local', 'Lecture Notes', 'Assignments', 'Tests']:
                new_path_full = new_path_relative  # Path already includes project context
            else:
                new_path_full = f"{prj_name}/{new_path_relative}" if new_path_relative else prj_name
            
            print(f'[IDE_MOVE_FILE] Old path full: {old_path_full}')
            print(f'[IDE_MOVE_FILE] New path full: {new_path_full}')
            
            # Use secure file manager for permission validation
            secure_manager = SecureFileManager()
            
            # Check permissions for source path
            old_permission = secure_manager.validate_path(username, role, old_path_full)
            if not old_permission or old_permission == 'read_only':
                print(f'[IDE_MOVE_FILE] Permission denied for source: {old_path_full}')
                await response(client, cmd_id, -1, 'Permission denied for source file')
                return
            
            # Check permissions for destination path  
            new_permission = secure_manager.validate_path(username, role, new_path_full)
            if not new_permission or new_permission == 'read_only':
                print(f'[IDE_MOVE_FILE] Permission denied for destination: {new_path_full}')
                await response(client, cmd_id, -1, 'Permission denied for destination')
                return
            
            # Get full filesystem paths using the corrected paths (not relative paths)
            ide_base_path = os.path.join(Config.PROJECTS, 'ide')
            old_full_path = os.path.join(ide_base_path, old_path_full)
            new_full_path = os.path.join(ide_base_path, new_path_full)
            
            print(f'[IDE_MOVE_FILE] Full old path: {old_full_path}')
            print(f'[IDE_MOVE_FILE] Full new path: {new_full_path}')
            
            # Check if source exists
            if not os.path.exists(old_full_path):
                await response(client, cmd_id, -1, 'Source file not found')
                return
            
            # Check if destination already exists
            if os.path.exists(new_full_path):
                await response(client, cmd_id, -1, 'Destination already exists')
                return
            
            # Create destination directory if needed
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
            
            # Perform the move operation
            import shutil
            shutil.move(old_full_path, new_full_path)
            
            # Update database records
            try:
                from common.database import db_manager
                from command.file_sync import file_sync
                
                # Get user_id for database sync
                query = "SELECT id FROM users WHERE username = %s"
                users = db_manager.execute_query(query, (username,))
                user_id = users[0]['id'] if users else None
                
                if user_id:
                    # Remove old file record
                    file_sync._mark_file_deleted(user_id, old_path_full)
                    # Add new file record
                    file_sync._update_file_record(user_id, new_path_full, new_full_path)
                    print(f'[IDE_MOVE_FILE] Database updated for user_id: {user_id}')
                
            except Exception as db_error:
                print(f'[IDE_MOVE_FILE] Database update failed: {db_error}')
                # Move operation succeeded, but DB sync failed - log warning
                pass
            
            print(f'[IDE_MOVE_FILE] Successfully moved file')
            await response(client, cmd_id, 0, {'success': True, 'message': 'File moved successfully'})
            
        except Exception as e:
            print(f'[IDE_MOVE_FILE] Exception: {e}')
            import traceback
            traceback.print_exc()
            await response(client, cmd_id, -1, f'Move failed: {str(e)}')

    async def ide_move_folder(self, client, cmd_id, data):
        """Move a folder from one location to another with proper permissions"""
        try:
            # Import secure file manager for permission checking
            from command.secure_file_manager import SecureFileManager
            
            prj_name = data.get('projectName')
            old_path_input = data.get('oldPath')
            new_path_input = data.get('newPath')
            username = getattr(client, 'username', 'unknown')
            role = getattr(client, 'role', 'student')
            
            print(f'[IDE_MOVE_FOLDER] User: {username}, Role: {role}')
            print(f'[IDE_MOVE_FOLDER] Project: {prj_name}')
            print(f'[IDE_MOVE_FOLDER] Old path: {old_path_input}')
            print(f'[IDE_MOVE_FOLDER] New path: {new_path_input}')
            
            # Validate inputs
            if not old_path_input or not new_path_input:
                await response(client, cmd_id, -1, 'Missing old_path or new_path')
                return
            
            # Convert paths (handle leading slashes, backslashes)
            old_path_relative = convert_path(old_path_input)
            new_path_relative = convert_path(new_path_input)
            
            # Handle paths that might already include project context
            # If the path already starts with a project name, use it as-is
            # Otherwise, prepend the current project name
            if '/' in old_path_relative and old_path_relative.split('/')[0] in ['Local', 'Lecture Notes', 'Assignments', 'Tests']:
                old_path_full = old_path_relative  # Path already includes project context
            else:
                old_path_full = f"{prj_name}/{old_path_relative}" if old_path_relative else prj_name
                
            if '/' in new_path_relative and new_path_relative.split('/')[0] in ['Local', 'Lecture Notes', 'Assignments', 'Tests']:
                new_path_full = new_path_relative  # Path already includes project context
            else:
                new_path_full = f"{prj_name}/{new_path_relative}" if new_path_relative else prj_name
            
            print(f'[IDE_MOVE_FOLDER] Old path full: {old_path_full}')
            print(f'[IDE_MOVE_FOLDER] New path full: {new_path_full}')
            
            # Use secure file manager for permission validation
            secure_manager = SecureFileManager()
            
            # Check permissions for source path
            old_permission = secure_manager.validate_path(username, role, old_path_full)
            if not old_permission or old_permission == 'read_only':
                print(f'[IDE_MOVE_FOLDER] Permission denied for source: {old_path_full}')
                await response(client, cmd_id, -1, 'Permission denied for source folder')
                return
            
            # Check permissions for destination path  
            new_permission = secure_manager.validate_path(username, role, new_path_full)
            if not new_permission or new_permission == 'read_only':
                print(f'[IDE_MOVE_FOLDER] Permission denied for destination: {new_path_full}')
                await response(client, cmd_id, -1, 'Permission denied for destination')
                return
            
            # Get full filesystem paths using the corrected paths (not relative paths)
            ide_base_path = os.path.join(Config.PROJECTS, 'ide')
            old_full_path = os.path.join(ide_base_path, old_path_full)
            new_full_path = os.path.join(ide_base_path, new_path_full)
            
            print(f'[IDE_MOVE_FOLDER] Full old path: {old_full_path}')
            print(f'[IDE_MOVE_FOLDER] Full new path: {new_full_path}')
            
            # Check if source exists and is a directory
            if not os.path.exists(old_full_path):
                await response(client, cmd_id, -1, 'Source folder not found')
                return
                
            if not os.path.isdir(old_full_path):
                await response(client, cmd_id, -1, 'Source is not a folder')
                return
            
            # Check if destination already exists
            if os.path.exists(new_full_path):
                await response(client, cmd_id, -1, 'Destination already exists')
                return
            
            # Prevent moving folder into itself
            if new_full_path.startswith(old_full_path + os.sep):
                await response(client, cmd_id, -1, 'Cannot move folder into itself')
                return
            
            # Create parent directory if needed
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
            
            # Perform the move operation
            import shutil
            shutil.move(old_full_path, new_full_path)
            
            # Update database records for all files in the moved folder
            try:
                from common.database import db_manager
                from command.file_sync import file_sync
                
                # Get user_id for database sync
                query = "SELECT id FROM users WHERE username = %s"
                users = db_manager.execute_query(query, (username,))
                user_id = users[0]['id'] if users else None
                
                if user_id:
                    # Re-sync the user's files to update all paths
                    file_sync.sync_user_files(user_id, username)
                    print(f'[IDE_MOVE_FOLDER] Database re-synced for user_id: {user_id}')
                
            except Exception as db_error:
                print(f'[IDE_MOVE_FOLDER] Database update failed: {db_error}')
                # Move operation succeeded, but DB sync failed - log warning
                pass
            
            print(f'[IDE_MOVE_FOLDER] Successfully moved folder')
            await response(client, cmd_id, 0, {'success': True, 'message': 'Folder moved successfully'})
            
        except Exception as e:
            print(f'[IDE_MOVE_FOLDER] Exception: {e}')
            import traceback
            traceback.print_exc()
            await response(client, cmd_id, -1, f'Move failed: {str(e)}')

    async def autocomplete_python(self, client, cmd_id, data):
        source = data.get('source')
        line = data.get('line', None)
        column = data.get('column', None)
        line = line + 1 if line is not None else line
        script = jedi.api.Script(source=source, line=line, column=column)
        completions = set()
        for completion in script.completions():
            completions.add(completion.name)
        await response(client, cmd_id, 0, list(completions))

    async def run_pip_command(self, client, cmd_id, data):
        command = data.get('command')
        if not isinstance(command, str) or not command:
            return await response(client, cmd_id, 1111, {'stdout': 'pip command: {} error'.format(command)})
        else:
            options = data.get('options', [])
            if not command.startswith('pip'):
                List = command.split(' ')
                if len(List) == 1:
                    cmd = [Config.PYTHON, '-u', '-m', 'pip', List[0], ' '.join(options)]
                elif len(List) > 1:
                    cmd = [Config.PYTHON, '-u', '-m', 'pip', List[0]]
                    for op in List[1:]:
                        cmd.append(op)
                    if List[1] == 'uninstall' and '-y' not in cmd:
                        cmd.append('-y')
                    # cmd = [Config.PYTHON, '-u', '-m', 'pip', List[0], '{} {}'.format(' '.join(List[1:]), ' '.join(options))]
                else:
                    return await response(client, cmd_id, 1111, 'cmd error')
            else:
                List = command.split(' ')
                if len(List) == 2:
                    cmd = [Config.PYTHON, '-u', '-m', List[0], List[1], ' '.join(options)]
                elif len(List) > 2:
                    cmd = [Config.PYTHON, '-u', '-m', List[0], List[1]]
                    for op in List[2:]:
                        cmd.append(op)
                    if List[1] == 'uninstall' and '-y' not in cmd:
                        cmd.append('-y')
                    # cmd = [Config.PYTHON, '-u', '-m', List[0], List[1], '{} {}'.format(' '.join(List[2:]), ' '.join(options))]
                else:
                    return await response(client, cmd_id, 1111, 'cmd error')
            client.handler_info.set_subprogram(cmd_id, SubProgramThread(cmd, cmd_id, client, asyncio.get_event_loop()))
            await response(client, cmd_id, 0, None)
            client.handler_info.start_subprogram(cmd_id)

    async def run_python_program(self, client, cmd_id, data):
        # Config.PYTHON
        prj_name = data.get('projectName')
        file_path_input = data.get('filePath', '')
        use_hybrid = data.get('hybrid', True)  # Default to hybrid mode
        username = data.get('username', 'unknown')  # Get username from authenticated handler
        
        # Handle case where filePath already includes the project name
        if file_path_input.startswith(prj_name + '/'):
            # Remove the duplicate project name from the path
            file_path_input = file_path_input[len(prj_name)+1:]
        
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        file_path = os.path.join(prj_path, convert_path(file_path_input))
        
        print(f"[BACKEND-DEBUG] run_python_program: projectName={prj_name}, filePath={file_path_input}, hybrid={use_hybrid}")
        print(f"[BACKEND-DEBUG] Full path constructed: {file_path}")
        print(f"[BACKEND-DEBUG] File exists: {os.path.exists(file_path)}, Is file: {os.path.isfile(file_path) if os.path.exists(file_path) else 'N/A'}")
        
        if os.path.exists(file_path) and os.path.isfile(file_path) and file_path.endswith('.py'):
            if use_hybrid:
                # Use execution lock manager to prevent race conditions
                from .execution_lock_manager import execution_lock_manager
                
                # Try to acquire execution lock for this user+file
                lock_acquired = execution_lock_manager.acquire_execution_lock(username, file_path, cmd_id, timeout=2.0)
                if not lock_acquired:
                    print(f"[BACKEND-DEBUG] Could not acquire execution lock for user {username}, file {file_path}, cmd_id: {cmd_id}")
                    await response(client, cmd_id, -1, 'You already have this file running. Please wait for it to complete.')
                    return
                
                try:
                    # First stop any existing subprocess for this cmd_id to prevent duplicates
                    print(f"[BACKEND-DEBUG] Stopping existing subprocess for cmd_id: {cmd_id}")
                    client.handler_info.stop_subprogram(cmd_id)
                    
                    # Terminate existing REPL for this file to ensure fresh execution with updated code
                    try:
                        from .repl_registry import repl_registry
                        # Normalize path to match the format used in save handler
                        normalized_path = os.path.normpath(file_path)
                        terminated = repl_registry.terminate_repl(username, normalized_path)
                        if terminated:
                            print(f"[BACKEND-DEBUG] Terminated existing REPL for {normalized_path} before new execution")
                            # Brief delay to ensure complete process cleanup
                            import time
                            time.sleep(0.1)
                    except Exception as e:
                        print(f"[BACKEND-DEBUG] Failed to terminate REPL: {e}")
                        pass  # Continue even if termination fails
                    
                    # Always create a new HybridREPLThread (threads cannot be reused)
                    print(f"[BACKEND-DEBUG] Using HybridREPLThread for Python execution with REPL")
                    thread = HybridREPLThread(cmd_id, client, asyncio.get_event_loop(), script_path=file_path, lock_manager=execution_lock_manager, username=username)
                except Exception as e:
                    # If anything fails, release the lock
                    execution_lock_manager.release_execution_lock(username, file_path, cmd_id)
                    raise e
            else:
                # Use the working implementation with byte-by-byte reading
                cmd = [Config.PYTHON, '-u', file_path]
                print(f"[BACKEND-DEBUG] Using WorkingSimpleThread for Python execution")
                thread = WorkingSimpleThread(cmd, cmd_id, client, asyncio.get_event_loop())
            
            print(f"[BACKEND-DEBUG] Thread created for cmd_id: {cmd_id}")
            # Ensure clean state before setting new subprogram
            client.handler_info.set_subprogram(cmd_id, thread)
            await response(client, cmd_id, 0, None)
            print(f"[BACKEND-DEBUG] Starting new subprocess for cmd_id: {cmd_id}")
            client.handler_info.start_subprogram(cmd_id)
        else:
            await response(client, cmd_id, 1111, 'File can not run')

    async def stop_python_program(self, client, cmd_id, data):
        program_id = data.get('program_id', None)
        client.handler_info.stop_subprogram(program_id)
        await response(client, cmd_id, 0, None)
    
    async def send_program_input(self, client, cmd_id, data):
        """Send user input to running program"""
        program_id = data.get('program_id', None)
        user_input = data.get('input', '')
        
        # Get the running program thread
        subprogram = client.handler_info.get_subprogram(program_id)
        if subprogram and hasattr(subprogram, 'send_input'):
            success = subprogram.send_input(user_input)
            await response(client, cmd_id, 0, {'success': success})
        else:
            await response(client, cmd_id, 1, 'Program not found or does not support input')
    
    async def send_bug_report(self, client, cmd_id, data):
        """Handle bug report submission"""
        try:
            # Process the bug report
            result = handle_bug_report(data)
            
            # Send response back to client
            await response(client, cmd_id, 0, result)
        except Exception as e:
            await response(client, cmd_id, 1, {
                'success': False,
                'error': str(e),
                'message': 'Failed to submit bug report'
            })
    
    async def start_python_repl(self, client, cmd_id, data):
        """Start a Python REPL session (empty, no script)"""
        prj_name = data.get('projectName', 'repl')
        print(f"[BACKEND-DEBUG] Starting empty Python REPL for project: {prj_name}")
        
        # Create Hybrid REPL thread without script (empty REPL)
        thread = HybridREPLThread(cmd_id, client, asyncio.get_event_loop(), script_path=None)
        print(f"[BACKEND-DEBUG] Empty REPL thread created for cmd_id: {cmd_id}")
        
        # Register the thread
        client.handler_info.set_subprogram(cmd_id, thread)
        await response(client, cmd_id, 0, 'repl_started')
        client.handler_info.start_subprogram(cmd_id)
    
    async def stop_python_repl(self, client, cmd_id, data):
        """Stop a Python REPL session"""
        repl_id = data.get('repl_id', cmd_id)
        print(f"[BACKEND-DEBUG] Stopping Python REPL with id: {repl_id}")
        
        # Get the REPL thread
        subprogram = client.handler_info.get_subprogram(repl_id)
        if subprogram:
            subprogram.stop()
            client.handler_info.del_subprogram(repl_id)
            await response(client, cmd_id, 0, 'repl_stopped')
        else:
            await response(client, cmd_id, 1, 'REPL not found')


class SubProgramThread(threading.Thread):
    def __init__(self, cmd, cmd_id, client, event_loop):
        super(SubProgramThread, self).__init__()
        self.cmd = cmd
        self.cmd_id = cmd_id
        self.client = client
        self.alive = True
        self.daemon = True
        self.event_loop = event_loop
        self.p = None
        self.error_handler = EducationalErrorHandler()
        self.error_buffer = []
    
    def stop(self):
        self.alive = False
        if self.p:
            try:
                self.p.kill()
            except:
                pass
            self.p = None

    def response_to_client(self, code, stdout):
        if stdout:
            # Check if this is an error output and enhance it for educational purposes
            if any(error_indicator in stdout for error_indicator in ['Traceback', 'Error:', 'Exception']):
                self.error_buffer.append(stdout)
                # Don't send partial error messages, collect them first
                return
            elif self.error_buffer:
                # We've collected an error, process it
                full_error = '\n'.join(self.error_buffer) + '\n' + stdout if stdout else '\n'.join(self.error_buffer)
                enhanced_output = self.error_handler.process_error_output(full_error)
                self.error_buffer = []
                IOLoop.current().spawn_callback(response, self.client, self.cmd_id, code, {'stdout': enhanced_output})
            else:
                # Normal output
                IOLoop.current().spawn_callback(response, self.client, self.cmd_id, code, {'stdout': stdout})

    def run_python_program(self):
        start_time = time.time()
        p = None
        asyncio.set_event_loop(self.event_loop)
        print('[{}-Program {} is start]'.format(self.client.id, self.cmd_id))
        try:
            p = subprocess.Popen(self.cmd, shell=False, universal_newlines=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.p = p
            while self.alive and p.poll() is None:
                if not self.client.connected:
                    self.alive = False
                    p.kill()
                    self.client.handler_info.remove_subprogram(self.cmd_id)
                    print('[{}-Program {} is kill][client is disconnect]'.format(self.client.id, self.cmd_id))
                    return
                stdout = p.stdout.readline()
                stdout = stdout.strip()
                self.response_to_client(0, stdout)
                time.sleep(0.002)
            if not self.alive:
                self.response_to_client(1111, '[program is terminate]')
                p.kill()
                self.client.handler_info.remove_subprogram(self.cmd_id)
                print('[{}-Program {} is terminate]'.format(self.client.id, self.cmd_id))
                return
            try:
                stdout = p.stdout.read()
                # Process any remaining error buffer
                if self.error_buffer:
                    full_error = '\n'.join(self.error_buffer) + '\n' + stdout if stdout else '\n'.join(self.error_buffer)
                    enhanced_output = self.error_handler.process_error_output(full_error)
                    self.response_to_client(0, enhanced_output)
                    self.error_buffer = []
                else:
                    self.response_to_client(0, stdout)
            except:
                pass
            if self.client.connected:
                stdout = '[Program exit with code {code}]'.format(code=p.returncode)
            else:
                stdout = '[Finish in {second:.2f}s with exit code {code}]'.format(second=time.time() - start_time, code=p.returncode)
            self.response_to_client(1111, stdout)
            self.client.handler_info.remove_subprogram(self.cmd_id)
            if p.returncode == 0:
                print('{}-Program {} success'.format(self.client.id, self.cmd_id))
                p.kill()
                return 'ok'
            else:
                print('{}-Program {} failed'.format(self.client.id, self.cmd_id))
                p.kill()
                return 'failed'
        except Exception as e:
            print('[{}-Program {} is exception], {}'.format(self.client.id, self.cmd_id, e))
            self.response_to_client(1111, '[Program is exception], {}'.format(e))
        finally:
            try:
                p.kill()
            except:
                pass
            try:
                self.client.handler_info.remove_subprogram(self.cmd_id)
            except:
                pass

    def run(self):
        self.alive = True
        try:
            self.run_python_program()
        except Exception as e:
            print(e)
            pass
        self.alive = False


