# REPL Integration Plan for Docker Testing

## Overview
Integrate the new SimpleExecutorV2 REPL implementation into the existing WebSocket infrastructure and test it with docker-compose.exam.yml

## Current State
- ✅ `SimpleExecutorV2` (formerly simple_exec_v2.py) is now in `simple_exec.py`
- ✅ Protocol defined in `exec_protocol.py`
- ✅ SimpleConsole.vue created but not integrated
- ❌ WebSocket handler still uses old HybridREPLThread
- ❌ Frontend still uses old HybridConsole.vue

## Integration Plan

### Phase 1: Backend Integration (30 minutes)

#### 1.1 Update IDE Command Handler
**File**: `/server/command/ide_cmd.py`

**Changes**:
- Import SimpleExecutorV2 instead of HybridREPLThread
- Update run_python_program to use new executor
- Keep execution lock management
- Remove REPL registry references (not needed anymore)

**Milestones**:
- [ ] Import statement updated
- [ ] run_python_program uses SimpleExecutorV2
- [ ] Lock management preserved
- [ ] Old imports commented out

#### 1.2 Handle Input Messages
**File**: `/server/handlers/authenticated_ws_handler.py`

**Changes**:
- Route 'send_input' messages to executor
- Handle new message format
- Keep authentication checks

**Milestones**:
- [ ] Input routing works
- [ ] Message format compatible

### Phase 2: Frontend Integration (45 minutes)

#### 2.1 Replace Console Component
**File**: `/src/components/element/VmIde.vue`

**Changes**:
- Import SimpleConsole instead of HybridConsole
- Update message handling for new protocol
- Handle INPUT_REQUEST messages
- Update REPL state management

**Milestones**:
- [ ] SimpleConsole imported
- [ ] Message handlers updated
- [ ] Input requests handled
- [ ] REPL state managed

#### 2.2 Update Message Processing
**Changes**:
- Map new message types to UI updates
- Handle input_request type
- Process stdout/stderr properly
- Display figures correctly

**Milestones**:
- [ ] Message types mapped
- [ ] Output displays correctly
- [ ] Input prompts work
- [ ] Figures display

### Phase 3: Docker Testing (30 minutes)

#### 3.1 Build and Deploy
```bash
# Build the exam container
docker-compose -f docker-compose.exam.yml build pythonide-exam

# Start the services
docker-compose -f docker-compose.exam.yml up -d

# Check logs
docker-compose -f docker-compose.exam.yml logs -f pythonide-exam
```

**Milestones**:
- [ ] Container builds successfully
- [ ] Services start without errors
- [ ] Can access on port 10087
- [ ] WebSocket connects

#### 3.2 Test Cases

**Test 1: Basic Script Execution**
```python
# test_basic.py
print("Hello World")
x = 42
y = x * 2
print(f"Result: {y}")
```
- [ ] Script runs
- [ ] Output displays
- [ ] Variables persist to REPL
- [ ] Can use variables in REPL

**Test 2: Input Function**
```python
# test_input.py
name = input("Enter your name: ")
age = input("Enter your age: ")
print(f"Hello {name}, you are {age} years old")
```
- [ ] Input prompt appears
- [ ] Can enter text
- [ ] Script continues after input
- [ ] Multiple inputs work

**Test 3: REPL Mode**
```python
# Direct REPL commands
>>> x = 100
>>> print(x)
>>> def greet(name):
...     return f"Hello {name}"
>>> greet("Test")
```
- [ ] REPL commands execute
- [ ] Multi-line input works
- [ ] Functions can be defined
- [ ] input() works in REPL

**Test 4: Error Handling**
```python
# test_error.py
print("Before error")
x = 1/0
print("After error")
```
- [ ] Error displays properly
- [ ] Script stops on error
- [ ] REPL doesn't start after error

### Phase 4: Cleanup (15 minutes)

#### 4.1 Remove Old Files
After successful testing:
- [ ] Remove/rename HybridREPLThread
- [ ] Remove/rename HybridConsole.vue
- [ ] Remove REPL registry
- [ ] Remove DualModeREPL.js
- [ ] Clean debug statements

#### 4.2 Documentation
- [ ] Update README with new REPL info
- [ ] Document input() handling
- [ ] Add troubleshooting guide

## File Changes Summary

### Backend Files to Modify:
1. `/server/command/ide_cmd.py` - Change imports and execution
2. `/server/handlers/authenticated_ws_handler.py` - Route input messages

### Frontend Files to Modify:
1. `/src/components/element/VmIde.vue` - Use SimpleConsole
2. `/src/components/element/pages/ide/IDEPythonStandard.vue` - Update references

### Files to Remove (after testing):
1. `/server/command/hybrid_repl_thread.py`
2. `/server/command/repl_registry.py`
3. `/src/components/element/pages/ide/HybridConsole.vue`
4. `/src/components/element/DualModeREPL.js`

## Quick Test Commands

```bash
# Build and start
docker-compose -f docker-compose.exam.yml up -d --build pythonide-exam

# View logs
docker-compose -f docker-compose.exam.yml logs -f pythonide-exam

# Stop services
docker-compose -f docker-compose.exam.yml down

# Clean rebuild
docker-compose -f docker-compose.exam.yml down -v
docker-compose -f docker-compose.exam.yml build --no-cache pythonide-exam
docker-compose -f docker-compose.exam.yml up -d
```

## Success Criteria
1. ✅ Scripts execute with output
2. ✅ Variables persist to REPL
3. ✅ input() works in scripts
4. ✅ input() works in REPL
5. ✅ Errors handled gracefully
6. ✅ Multiple users can run simultaneously
7. ✅ Timeout enforcement works
8. ✅ WebSocket messages properly formatted

## Troubleshooting

### Common Issues:
1. **Import errors**: Check PYTHONPATH in Docker
2. **WebSocket disconnects**: Check CORS and auth
3. **Input not working**: Verify PTY setup
4. **Variables not persisting**: Check script re-execution
5. **Timeout too short**: Adjust script_timeout value

## Next Steps After Integration:
1. Test with 5+ concurrent users
2. Add matplotlib support
3. Implement file locking
4. Add execution metrics
5. Deploy to AWS ECS