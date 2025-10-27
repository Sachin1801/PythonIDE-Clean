#!/usr/bin/env python3
"""
Execution Protocol Definitions
Defines the JSON message format for communication between frontend and backend
"""

from enum import Enum
from typing import Dict, Any, Optional

class MessageType(Enum):
    """Message types for backend->frontend communication"""
    STDOUT = "stdout"           # Standard output from script/REPL
    STDERR = "stderr"           # Error output
    REPL_READY = "repl_ready"   # REPL mode activated
    INPUT_REQUEST = "input_request"  # Waiting for input()
    FIGURE = "figure"           # Matplotlib figure
    COMPLETE = "complete"       # Execution finished
    ERROR = "error"             # System error (not Python exception)
    DEBUG = "debug"             # Debug messages (only in dev mode)

class ExecutionState(Enum):
    """Execution states for tracking"""
    IDLE = "idle"
    SCRIPT_RUNNING = "script_running"
    SCRIPT_COMPLETE = "script_complete"
    REPL_ACTIVE = "repl_active"
    WAITING_INPUT = "waiting_input"
    TERMINATED = "terminated"

def create_message(cmd_id: str, msg_type: MessageType, data: Any) -> Dict[str, Any]:
    """
    Create a standardized message for WebSocket transmission

    Args:
        cmd_id: Command identifier for this execution session
        msg_type: Type of message (from MessageType enum)
        data: Message payload (varies by type)

    Returns:
        Dictionary ready for JSON serialization
    """
    message = {
        "cmd_id": cmd_id,
        "type": msg_type.value,
        "timestamp": None  # Will be added by WebSocket handler
    }

    # Structure data based on message type
    if msg_type == MessageType.STDOUT:
        message["data"] = {"text": str(data)}
    elif msg_type == MessageType.STDERR:
        message["data"] = {"text": str(data)}
    elif msg_type == MessageType.REPL_READY:
        message["data"] = {"prompt": data.get("prompt", ">>> ")}
    elif msg_type == MessageType.INPUT_REQUEST:
        message["data"] = {"prompt": str(data)}
    elif msg_type == MessageType.FIGURE:
        message["data"] = {
            "format": data.get("format", "png"),
            "content": data.get("content"),  # base64 encoded
            "width": data.get("width"),
            "height": data.get("height")
        }
    elif msg_type == MessageType.COMPLETE:
        message["data"] = {
            "exit_code": data.get("exit_code", 0),
            "duration": data.get("duration"),  # execution time in seconds
        }
    elif msg_type == MessageType.ERROR:
        message["data"] = {
            "error": str(data.get("error", "Unknown error")),
            "traceback": data.get("traceback")
        }
    elif msg_type == MessageType.DEBUG:
        message["data"] = {"text": str(data)}
    else:
        message["data"] = data

    return message

def parse_frontend_message(message: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """
    Parse incoming message from frontend

    Args:
        message: JSON message from frontend

    Returns:
        Tuple of (command_type, parameters)
    """
    cmd = message.get("cmd", "")

    if cmd == "execute_script":
        return cmd, {
            "cmd_id": message.get("cmd_id"),
            "file_path": message.get("file_path"),
            "username": message.get("username"),  # Added from auth
        }
    elif cmd == "send_input":
        return cmd, {
            "cmd_id": message.get("cmd_id"),
            "text": message.get("text", "")
        }
    elif cmd == "stop_execution":
        return cmd, {
            "cmd_id": message.get("cmd_id")
        }
    else:
        return cmd, message

def format_traceback(tb_text: str) -> str:
    """
    Format Python traceback for better display
    Removes unnecessary wrapper script references
    """
    lines = tb_text.split('\n')
    filtered_lines = []
    skip_next = False

    for line in lines:
        # Skip our wrapper script references
        if '/tmp/pythonide_wrapper_' in line:
            skip_next = True
            continue
        if skip_next and line.strip().startswith('^'):
            skip_next = False
            continue
        filtered_lines.append(line)

    return '\n'.join(filtered_lines)

# Debug mode flag (set from environment or config)
DEBUG_MODE = False

def set_debug_mode(enabled: bool):
    """Enable/disable debug messages"""
    global DEBUG_MODE
    DEBUG_MODE = enabled

def debug_log(cmd_id: str, message: str) -> Optional[Dict[str, Any]]:
    """Create debug message only if debug mode is enabled"""
    if DEBUG_MODE:
        return create_message(cmd_id, MessageType.DEBUG, f"[DEBUG] {message}")
    return None