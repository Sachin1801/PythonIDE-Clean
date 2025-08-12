#!/usr/bin/env python3
import os
import sys
from tornado import queues

class GLOBAL:
    class Queue:
        req_msg_que = queues.Queue()
        res_msg_que = queues.Queue()

    class Path:
        PYTHON = sys.executable
        PROJECTS = os.path.join(os.path.abspath('.'), 'projects')


