# REPL System Fix Implementation Plan

## Current Architecture Analysis

### Message Flow (Current Broken System)
1. **Script Execution Phase**:
   - User clicks Run → WebSocket sends `execute_script` command
   - `hybrid_repl_thread.py` creates wrapper script with markers:
     - `__SCRIPT_START__` - marks beginning of script execution
     - `__SCRIPT_END__` - marks successful completion
     - `__SCRIPT_ERROR__` - marks error in script
   - Wrapper injects custom input() and matplotlib handlers

2. **REPL Transition Phase**:
   - After script ends, wrapper prints `__REPL_MODE_START__`
   - Enters custom REPL loop using `code.compile_command()`
   - Maintains script variables in same process

3. **Input Handling**:
   - Custom input() prints: `__INPUT_REQUEST_START__{prompt}__INPUT_REQUEST_END__`
   - Frontend parses markers and shows input field
   - User input sent back via WebSocket

4. **Matplotlib Handling**:
   - Custom show() prints: `__MATPLOTLIB_FIGURE_START__{base64}__MATPLOTLIB_FIGURE_END__`
   - Frontend parses and displays image

### Critical Problems Identified
1. **Marker-based protocol is fragile** - If user code prints these exact strings, system breaks
2. **300+ line wrapper script** - Over-engineered, reinvents Python's REPL
3. **No proper PTY** - Falls back to pipes on Windows, no terminal features
4. **Multiple timeout variables** - Confusing: script_timeout=3, cpu_time_limit=60, repl_cpu_limit=300
5. **Complex state management** - REPLRegistry persists processes unnecessarily
6. **Frontend has too much logic** - Parses markers, manages state

## New Simplified Architecture

### Design Principles
1. **JSON-only protocol** - No text markers
2. **Use existing tools** - IPython or code.InteractiveConsole
3. **Clean separation** - Backend executes, frontend displays
4. **One process per run** - No persistence, clean state
5. **Proper PTY support** - Real terminal emulation

### Message Protocol (JSON)

#### Frontend → Backend
```json
// Execute script
{
  "cmd": "execute_script",
  "cmd_id": "uuid-123",
  "file_path": "/Local/username/script.py"
}

// Send input (for input() or REPL)
{
  "cmd": "send_input",
  "cmd_id": "uuid-123",
  "text": "user input here"
}

// Stop execution
{
  "cmd": "stop_execution",
  "cmd_id": "uuid-123"
}
```

#### Backend → Frontend
```json
// Standard output
{
  "cmd_id": "uuid-123",
  "type": "stdout",
  "data": "Hello World\n"
}

// Error output
{
  "cmd_id": "uuid-123",
  "type": "stderr",
  "data": "Traceback (most recent call last)..."
}

// Script execution complete, REPL starting
{
  "cmd_id": "uuid-123",
  "type": "repl_ready",
  "prompt": ">>> "
}

// Waiting for input()
{
  "cmd_id": "uuid-123",
  "type": "input_request",
  "prompt": "Enter your name: "
}

// Matplotlib figure
{
  "cmd_id": "uuid-123",
  "type": "figure",
  "format": "png",
  "data": "base64_encoded_image_data"
}

// Execution complete
{
  "cmd_id": "uuid-123",
  "type": "complete",
  "exit_code": 0
}
```

## Implementation Milestones

### Phase 1: Foundation (1 hour)
- [ ] 1.1 Document current flow with debug logs
- [ ] 1.2 Create backup of existing files
- [ ] 1.3 Set up test environment

### Phase 2: Backend - Simple Execution (2 hours)
- [ ] 2.1 Create `simple_exec.py` with basic subprocess
- [ ] 2.2 Implement script execution with proper PTY
- [ ] 2.3 Add JSON message protocol
- [ ] 2.4 Test script output capture

### Phase 3: Backend - REPL Integration (2 hours)
- [ ] 3.1 Add IPython subprocess after script
- [ ] 3.2 Transfer script variables to REPL
- [ ] 3.3 Handle REPL input/output
- [ ] 3.4 Test variable persistence

### Phase 4: Frontend - Simple Console (1.5 hours)
- [ ] 4.1 Create `SimpleConsole.vue`
- [ ] 4.2 Display stdout/stderr lines
- [ ] 4.3 Add input field for REPL
- [ ] 4.4 Remove marker parsing logic

### Phase 5: Integration (1 hour)
- [ ] 5.1 Update WebSocket handler routing
- [ ] 5.2 Connect new backend to frontend
- [ ] 5.3 Test end-to-end flow
- [ ] 5.4 Fix integration issues

### Phase 6: Features (2 hours)
- [ ] 6.1 Add input() support
- [ ] 6.2 Add matplotlib support
- [ ] 6.3 Add multiline REPL support
- [ ] 6.4 Add command history

### Phase 7: Cleanup (1 hour)
- [ ] 7.1 Remove old REPL files
- [ ] 7.2 Remove debug statements
- [ ] 7.3 Update documentation
- [ ] 7.4 Test with multiple users

### Phase 8: Production (30 min)
- [ ] 8.1 Test on Docker locally
- [ ] 8.2 Update docker-compose
- [ ] 8.3 Deploy to AWS
- [ ] 8.4 Monitor for issues

## Files to Create/Modify

### New Files
1. `/server/command/simple_exec.py` - Clean execution engine
2. `/src/components/SimpleConsole.vue` - Minimal console UI
3. `/server/command/exec_protocol.py` - Message protocol definitions

### Files to Modify
1. `/server/command/ide_cmd.py` - Route to new executor
2. `/server/handlers/authenticated_ws_handler.py` - Update message routing
3. `/src/components/element/pages/ide/IDEPythonStandard.vue` - Use new console

### Files to Remove (After Testing)
1. `/server/command/hybrid_repl_thread.py` - Old complex implementation
2. `/server/command/repl_registry.py` - Unnecessary persistence
3. `/src/components/element/pages/ide/HybridConsole.vue` - Old console
4. `/src/components/element/DualModeREPL.js` - Pyodide fallback

## Testing Checklist

### Basic Tests
- [ ] Simple print statement
- [ ] Variables persist to REPL
- [ ] Script with error doesn't start REPL
- [ ] input() function works
- [ ] Multiple print statements

### Advanced Tests
- [ ] Matplotlib figures display
- [ ] Multiline REPL (functions, classes)
- [ ] Import statements work
- [ ] Long-running script timeout
- [ ] Concurrent users

### Edge Cases
- [ ] Script prints marker-like strings
- [ ] Unicode output
- [ ] Very large output
- [ ] Infinite loop handling
- [ ] Memory limit enforcement

## Success Criteria
1. **Simplicity**: < 200 lines for execution engine (vs current 1400)
2. **Reliability**: No marker parsing failures
3. **Performance**: < 100ms to start REPL after script
4. **Features**: All current features work (input, matplotlib, REPL)
5. **Maintainability**: Clear separation of concerns

## Rollback Plan
If issues arise:
1. Keep old files renamed with `.backup` extension
2. Can switch back via WebSocket handler routing
3. Test both implementations side-by-side
4. Gradual migration per user if needed