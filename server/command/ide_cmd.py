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
default_folders = ['Local', 'Lecture Notes']
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
            'lastAccessTime': time.time()
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
        old_path = os.path.join(prj_path, convert_path(data.get('oldPath')))
        new_name = data.get('newName')
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        code, _ = rename_project_file(prj_path, old_path, new_path)
        await response(client, cmd_id, code, _)

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
                    return await response(client, cmd_id, 1111, {'stdout': 'cmd error'})
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
                    return await response(client, cmd_id, 1111, {'stdout': 'cmd error'})
            client.handler_info.set_subprogram(cmd_id, SubProgramThread(cmd, cmd_id, client, asyncio.get_event_loop()))
            await response(client, cmd_id, 0, None)
            client.handler_info.start_subprogram(cmd_id)

    async def run_python_program(self, client, cmd_id, data):
        # Config.PYTHON
        prj_name = data.get('projectName')
        prj_path = os.path.join(Config.PROJECTS, 'ide', prj_name)
        file_path = os.path.join(prj_path, convert_path(data.get('filePath')))
        # print(file_path)
        if os.path.exists(file_path) and os.path.isfile(file_path) and file_path.endswith('.py'):
            cmd = [Config.PYTHON, '-u', file_path]
            # Use the working implementation with byte-by-byte reading
            print(f"[BACKEND-DEBUG] Using WorkingSimpleThread for Python execution")
            thread = WorkingSimpleThread(cmd, cmd_id, client, asyncio.get_event_loop())
            print(f"[BACKEND-DEBUG] Thread created for cmd_id: {cmd_id} with working I/O")
            client.handler_info.set_subprogram(cmd_id, thread)
            await response(client, cmd_id, 0, None)
            client.handler_info.start_subprogram(cmd_id)
        else:
            await response(client, cmd_id, 1111, {'stdout': 'File can not run'})

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
            await response(client, cmd_id, 1, {'error': 'Program not found or does not support input'})
    
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
        """Start a Python REPL session"""
        prj_name = data.get('projectName', 'repl')
        print(f"[BACKEND-DEBUG] Starting Python REPL for project: {prj_name}")
        
        # Create REPL thread
        thread = PythonREPLThread(cmd_id, client, asyncio.get_event_loop())
        print(f"[BACKEND-DEBUG] REPL thread created for cmd_id: {cmd_id}")
        
        # Register the thread
        client.handler_info.set_subprogram(cmd_id, thread)
        await response(client, cmd_id, 0, {'type': 'repl_started'})
        client.handler_info.start_subprogram(cmd_id)


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


