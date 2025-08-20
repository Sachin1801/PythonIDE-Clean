#!/usr/bin/env python3
import os
import sys

# Add server directory to path
sys.path.insert(0, '/home/site/wwwroot/server')

# Change to server directory and run
os.chdir('/home/site/wwwroot/server')

# Import and run the server
from server import main
main()
