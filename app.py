#!/usr/bin/env python3
import os
import sys
import subprocess

# Ensure we're in the right directory
app_root = '/home/site/wwwroot'
if os.path.exists(app_root):
    os.chdir(app_root)

# Run the server
server_path = os.path.join(app_root, 'server', 'server.py')
if os.path.exists(server_path):
    print(f"Starting server from {server_path}")
    subprocess.run([sys.executable, server_path])
else:
    print(f"ERROR: Server not found at {server_path}")
    print("Available files:")
    for root, dirs, files in os.walk(app_root):
        for file in files:
            print(f"  {os.path.join(root, file)}")
