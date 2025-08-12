#!/usr/bin/env python3

import os
import sys

class Config:
    PYTHON = sys.executable
    # PROJECTS = os.path.join(os.path.abspath('.'), 'projects')
    PROJECTS = os.path.join(os.path.dirname(__file__), '..', 'projects')
