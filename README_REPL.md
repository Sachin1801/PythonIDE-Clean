# Python REPL Implementation

## Overview
A Python REPL (Read-Eval-Print Loop) has been added to the PythonIDE-Clean application to enable interactive Python code execution with support for multi-line statements like loops, functions, and classes.

## Problem Solved
The original implementation only supported running complete Python scripts from files. This made it impossible to:
- Execute code interactively line by line
- Test multi-line constructs like for loops
- Experiment with code snippets without creating files
- Maintain variable state between code executions

## Solution Architecture

### Backend Components

1. **`server/command/repl_thread.py`**
   - New thread class `PythonREPLThread` that manages a persistent Python interpreter subprocess
   - Runs Python with `-i` flag for interactive mode
   - Handles multi-line input detection (continuation prompts)
   - Manages input/output streaming between frontend and Python process

2. **`server/command/ide_cmd.py`**
   - Added `start_python_repl` command handler
   - Imports and initializes the REPL thread
   - Manages WebSocket communication

### Frontend Components

1. **`src/components/element/pages/ide/PythonREPL.vue`**
   - Complete Vue component for REPL interface
   - Features:
     - Multi-line input support with Shift+Enter
     - Command history navigation with Up/Down arrows
     - Tab key for indentation
     - Auto-adjusting textarea height
     - Export history functionality
     - Clear output option

2. **`src/components/element/pages/ide/TopMenu.vue`**
   - Added Terminal icon button to launch REPL
   - Emits `open-repl` event

3. **`src/components/element/VmIde.vue`**
   - Added REPL modal container
   - Methods to show/hide REPL
   - Modal styling

## How to Use

1. **Launch the REPL**
   - Click the Terminal icon in the top menu bar
   - A modal window will open with the Python REPL

2. **Execute Code**
   - Type Python code in the input area
   - Press Enter to execute single-line statements
   - Use Shift+Enter to add new lines for multi-line code
   - Empty line after indented block ends the block

3. **Multi-line Example**
   ```python
   >>> for i in range(5):
   ...     print(f"Value: {i}")
   ...     if i % 2 == 0:
   ...         print("Even")
   ... 
   Value: 0
   Even
   Value: 1
   Value: 2
   Even
   Value: 3
   Value: 4
   Even
   ```

4. **Features**
   - **History Navigation**: Use Up/Down arrows to navigate command history
   - **Tab Indentation**: Press Tab to insert 4 spaces
   - **Clear Output**: Click Clear button to clear the console
   - **Export History**: Save your session commands to a .py file
   - **Persistent State**: Variables and imports persist across commands

## Technical Details

### WebSocket Communication
The REPL uses the existing WebSocket infrastructure:
- Command: `start_python_repl` - Starts a new REPL session
- Command: `send_program_input` - Sends user input to REPL
- Command: `stop_python_program` - Stops the REPL session

### Message Codes
- `0`: Regular output from Python
- `2000`: REPL prompt request (>>> or ...)
- `2001`: Input processed confirmation
- `1111`: Session ended

### Input Detection
The backend detects when Python is waiting for more input by:
1. Monitoring stdout for prompt patterns (>>> or ...)
2. Detecting incomplete statements that require continuation
3. Handling empty lines to end multi-line blocks

## Benefits

1. **Interactive Learning**: Students can experiment with Python code immediately
2. **Quick Testing**: Test code snippets without creating files
3. **Debugging**: Inspect variables and test functions interactively
4. **Educational**: See immediate results and understand Python behavior

## Future Enhancements

1. **Syntax Highlighting**: Add code highlighting in the REPL
2. **Auto-completion**: Implement tab completion for variables and functions
3. **Magic Commands**: Add IPython-style magic commands
4. **Session Persistence**: Save and restore REPL sessions
5. **Multiple REPLs**: Support multiple concurrent REPL sessions
6. **Integrated Help**: Built-in help system for Python functions

## Testing

To test the REPL implementation:

1. Start the application
2. Click the Terminal icon in the top menu
3. Try these examples:

```python
# Simple variable assignment
x = 10
y = 20
print(x + y)

# Multi-line function
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

print(factorial(5))

# For loop with nested if
for i in range(10):
    if i % 2 == 0:
        print(f"{i} is even")
    else:
        print(f"{i} is odd")

# List comprehension
squares = [x**2 for x in range(10)]
print(squares)
```

## Troubleshooting

1. **REPL not starting**: Check server logs for Python path issues
2. **No output**: Ensure PYTHONUNBUFFERED is set in environment
3. **Multi-line not working**: Check that empty line is sent to end blocks
4. **Connection lost**: WebSocket may have disconnected, refresh page