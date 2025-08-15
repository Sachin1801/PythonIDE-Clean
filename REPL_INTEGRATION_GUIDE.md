# Dual-Mode REPL Integration Guide

## Overview
This guide explains how to integrate the dual-mode REPL system that automatically switches between backend WebSocket REPL and browser-based Pyodide REPL.

## Features
- **Automatic Fallback**: Starts with backend REPL if available, falls back to Pyodide if not
- **Seamless Switching**: Automatically switches to Pyodide if backend fails
- **Full Python Support**: Both modes support complete Python syntax
- **Persistent Sessions**: Maintains variable state within sessions

## Integration Steps

### 1. Import the Dual-Mode REPL Module

In your `VmIde.vue` component, add:

```javascript
import DualModeREPL from './DualModeREPL';
```

### 2. Mix in the REPL Methods

Add to your component:

```javascript
export default {
  mixins: [DualModeREPL.methods],
  // ... rest of component
}
```

### 3. Update Data Properties

Add these properties to your component's data:

```javascript
data() {
  return {
    // ... existing data
    
    // REPL mode configuration
    replMode: 'auto', // 'backend', 'pyodide', or 'auto'
    pyodideNamespace: null,
    pyodideInitialized: false,
  }
}
```

### 4. Update Method Calls

Replace existing REPL methods with dual-mode versions:

#### Starting REPL:
```javascript
// Old:
async startReplSession() { ... }

// New:
async startReplSession() {
  await this.startDualModeReplSession();
}
```

#### Executing Commands:
```javascript
// Old:
async executeReplCommand() { ... }

// New:
async executeReplCommand() {
  const command = this.replInput;
  await this.executeReplCommandDualMode(command);
}
```

#### Stopping REPL:
```javascript
// Old:
async stopReplSession() { ... }

// New:
async stopReplSession() {
  await this.stopDualModeReplSession();
}
```

### 5. Update WebSocket Message Handler

Update your WebSocket message handler to route REPL messages:

```javascript
// In setupWebSocketHandler method
this.wsInfo.rws.onmessage = (event) => {
  // ... existing code
  
  try {
    const message = JSON.parse(event.data);
    
    // Check for REPL messages
    if (message.id === this.replSessionId || 
        message.cmd_id === this.replSessionId ||
        (message.data && message.data.program_id === this.replSessionId)) {
      this.handleBackendReplResponse(message);
    }
  } catch (e) {
    // Not JSON, ignore
  }
};
```

## Usage

### Starting a REPL Session

```javascript
// Start REPL (auto-detects best mode)
this.isReplMode = true;
await this.startReplSession();
```

### Forcing a Specific Mode

```javascript
// Force backend mode
this.replMode = 'backend';
await this.startReplSession();

// Force Pyodide mode
this.replMode = 'pyodide';
await this.startReplSession();

// Auto mode (default)
this.replMode = 'auto';
await this.startReplSession();
```

### Executing Python Code

The REPL automatically handles command execution based on the active mode:

```python
# Both modes support:
>>> x = 10
>>> y = 20
>>> x + y
30

>>> def factorial(n):
...     if n <= 1:
...         return 1
...     return n * factorial(n-1)
...
>>> factorial(5)
120

>>> import math
>>> math.pi
3.141592653589793
```

## Mode Behaviors

### Backend Mode
- Connects to Python backend via WebSocket
- Full system Python with all installed packages
- Can access files and system resources
- Requires backend server running

### Pyodide Mode
- Runs Python directly in the browser
- No backend required
- Limited to browser sandbox
- Includes scientific packages (NumPy, Pandas, etc.)
- Cannot access local files directly

### Auto Mode (Default)
1. Checks if WebSocket is connected
2. Tries backend REPL first
3. Falls back to Pyodide if backend fails
4. Seamlessly switches if backend disconnects

## Error Handling

The system handles various failure scenarios:

1. **Backend Unavailable**: Automatically switches to Pyodide
2. **WebSocket Disconnection**: Switches to Pyodide mid-session
3. **Pyodide Load Failure**: Shows error and disables REPL
4. **Command Execution Errors**: Displays Python tracebacks

## Testing

### Test Backend Mode
1. Start backend server: `python server/server.py`
2. Open IDE and click REPL button
3. Should see "Backend Python REPL connected"

### Test Pyodide Mode
1. Stop backend server
2. Open IDE and click REPL button
3. Should see "Python 3.11 (Pyodide) REPL"

### Test Automatic Fallback
1. Start with backend running
2. Begin REPL session
3. Stop backend server
4. Execute another command
5. Should automatically switch to Pyodide

## Troubleshooting

### REPL Not Starting
- Check browser console for errors
- Ensure Pyodide CDN is accessible
- Verify WebSocket connection if using backend

### Commands Not Executing
- Check if correct mode is active
- Verify WebSocket messages in browser DevTools
- Look for Python errors in console output

### Switching Issues
- Clear browser cache if Pyodide won't load
- Check WebSocket reconnection logic
- Verify backend server is running on correct port

## Performance Considerations

- **Initial Load**: Pyodide takes 2-5 seconds to initialize first time
- **Memory Usage**: Pyodide uses ~50-100MB of browser memory
- **Execution Speed**: Backend is faster for heavy computations
- **Network**: Backend requires stable WebSocket connection

## Future Enhancements

Potential improvements:
- Package installation in Pyodide mode
- File system emulation for Pyodide
- Session persistence across page reloads
- Code completion for both modes
- Syntax highlighting in REPL input