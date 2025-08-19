# PythonIDE Platform Smoke Test Checklist

## 🧪 Test Setup
- Open two browser tabs (incognito/private mode recommended)
- Tab 1: Student account (sa9082 / sa90822024)
- Tab 2: Professor account (professor / ChangeMeASAP2024!)

---

## ✅ Authentication Tests

### Login
- [ ] Student login works
- [ ] Professor login works
- [ ] Invalid credentials show error
- [ ] Session persists on page refresh

### Logout
- [ ] Student logout works
- [ ] Professor logout works
- [ ] Cannot access app after logout
- [ ] Redirects to login page

---

## 📁 File Operations Tests

### Student Account (sa9082)

#### In `Local/sa9082/` directory:
- [ ] View file tree
- [ ] Create new Python file
- [ ] Edit Python file
- [ ] Save Python file (Ctrl+S)
- [ ] Delete file
- [ ] Rename file
- [ ] Create new folder
- [ ] Delete folder
- [ ] Upload file

#### In `Lecture Notes/` directory:
- [ ] View files (READ)
- [ ] Cannot edit files (should show error)
- [ ] Cannot create files (should show error)
- [ ] Cannot delete files (should show error)

#### In `Assignments/` directory:
- [ ] View assignment descriptions
- [ ] Submit assignment file
- [ ] View own submissions

### Professor Account

#### In all directories:
- [ ] Full access to everything
- [ ] Can edit `Lecture Notes/`
- [ ] Can view all student directories
- [ ] Can grade submissions
- [ ] Can upload lecture materials

---

## 🏃 Code Execution Tests

### Basic Execution
- [ ] Run simple print statement
- [ ] Run file with functions
- [ ] Run file with loops
- [ ] Stop running program
- [ ] Handle infinite loop (stop should work)

### Input/Output
- [ ] Program with input() works
- [ ] Can provide input during execution
- [ ] Output appears in console
- [ ] Errors display properly

### REPL Mode
- [ ] Start Python REPL
- [ ] Execute commands in REPL
- [ ] Variables persist in REPL session
- [ ] Stop REPL

---

## 🔄 Rapid Operations Tests

### Edit-Save-Run Cycle
- [ ] Edit file
- [ ] Save immediately (Ctrl+S)
- [ ] Run immediately - should run NEW code
- [ ] Repeat rapidly - each run uses latest saved version

### Multiple Files
- [ ] Create multiple files
- [ ] Switch between files
- [ ] Edit different files
- [ ] Run different files

---

## 🚫 Permission Tests

### Student CANNOT:
- [ ] Access other student's `Local/` directory
- [ ] Modify `Lecture Notes/`
- [ ] Delete professor's files
- [ ] Access professor's workspace

### Student CAN:
- [ ] Full control in `Local/sa9082/`
- [ ] Read `Lecture Notes/`
- [ ] Submit to `Assignments/`

---

## 🔌 WebSocket Tests

### Connection
- [ ] WebSocket connects on login
- [ ] Reconnects if disconnected
- [ ] File operations work over WebSocket
- [ ] No connection errors in console

---

## 🎨 UI/UX Tests

### Editor
- [ ] Syntax highlighting works
- [ ] Auto-indent works
- [ ] Line numbers show
- [ ] Find/Replace works (Ctrl+F)

### File Tree
- [ ] Folders expand/collapse
- [ ] Right-click context menu works
- [ ] Icons display correctly
- [ ] Refresh updates tree

### Console
- [ ] Clear button works
- [ ] Scroll works properly
- [ ] Copy/paste works
- [ ] Resizable panels

---

## 🐛 Known Issues to Verify Fixed

- [x] Login works with PostgreSQL
- [x] Files sync to database
- [x] WebSocket URL correct when deployed
- [x] Create file works
- [x] Save updates file content
- [x] Run uses latest saved version
- [x] Logout works

---

## 📊 Performance Tests

### With 60 Concurrent Users (if possible):
- [ ] System remains responsive
- [ ] No crashes
- [ ] File operations still work
- [ ] Code execution queues properly

---

## 🔴 Current Status

### Working ✅
- Authentication (login)
- File operations (most)
- Code execution
- Permissions
- Database sync

### Just Fixed 🔧
- Logout functionality
- File creation
- Save/Run synchronization

### To Test 🧪
- All items in this checklist

---

## Notes Section
Use this space to note any issues found:

1. Issue: ________________
   - Steps to reproduce: ________________
   - Expected: ________________
   - Actual: ________________

2. Issue: ________________
   - Steps to reproduce: ________________
   - Expected: ________________
   - Actual: ________________