# Python IDE - New UI/UX Features

## Overview
The Python IDE has been enhanced with a new layout inspired by the p5.js Web Editor, providing a more intuitive and flexible development environment.

## New Features Implemented

### 1. Console Below Editor (Fixed Layout)
- **Location**: Console is now positioned below the code editor instead of on the right
- **Collapse/Expand**: Click the header to collapse/expand with smooth animation
- **Visual Indicator**: Arrow icon (▼/►) shows collapsed/expanded state
- **Persistent State**: Console state is saved in localStorage

### 2. REPL Section (Interactive Python)
- **Location**: Below the console output area
- **Functionality**: Direct Python code execution using Pyodide
- **Features**:
  - Command history with Up/Down arrow keys
  - Immediate execution with Enter key
  - Clear command support
  - Full Python environment in browser

### 3. Right Preview Panel (Draggable)
- **Purpose**: Display output, images, PDFs, and data files
- **Features**:
  - Multiple tabs for different content types
  - Output tab for program results
  - Image preview for PNG, JPG, etc.
  - PDF viewer
  - CSV data viewer
- **Draggable**: Resize by dragging the left border

### 4. Left Sidebar Enhancements
- **Draggable**: Resize by dragging the right border
- **Context Menu**: Right-click on files/folders for:
  - Open
  - Run (Python files)
  - Rename
  - Move
  - Download
  - Delete
- **Dropdown Menu**: Click ⋮ button next to each file
- **Double-Click to Rename**: Double-click any file/folder to rename
- **Single-Click to Open**: Single-click opens files in editor

### 5. Word Wrap
- **Default**: Enabled by default
- **Toggle Button**: Located in the header toolbar
- **Icon**: Text wrap icon that changes opacity based on state
- **Persistent**: Setting saved in localStorage

### 6. Console Enhancements
- **Clear Button**: Located in console header
- **Tab System**: Removed terminal tab (integrated into REPL)
- **Output Display**: Improved formatting with type indicators

### 7. Layout Persistence
All layout preferences are saved in localStorage:
- Sidebar widths
- Console height and expanded state
- Word wrap setting
- Preview panel visibility

## UI Components

### Header Toolbar
- Back button
- File operations (New File, New Folder, Rename, Delete)
- Upload/Download buttons
- Run/Stop buttons
- Theme toggle (Dark/Light)
- **NEW**: Word wrap toggle

### File Tree
- **NEW**: Dropdown menu button (⋮) on hover
- **NEW**: Right-click context menu
- **NEW**: Double-click rename functionality
- Refresh button

### Editor Area
- Tab system for multiple files
- **NEW**: Word wrap support
- Syntax highlighting
- Auto-indentation

### Console Area
- **NEW**: Collapsible header with animation
- **NEW**: Clear button
- Tab system for multiple console instances
- **NEW**: REPL input area at bottom

### Preview Panel
- **NEW**: Draggable resizing
- **NEW**: Multiple content type support
- **NEW**: Tab system for multiple previews

## Keyboard Shortcuts
- `Ctrl/Cmd + S`: Save file
- `Ctrl/Cmd + Enter`: Run current file
- `Up/Down arrows`: Navigate command history in REPL
- `Escape`: Close context menus

## Technical Implementation

### Technologies Used
- Vue 3 with Composition API
- CodeMirror for code editing
- Pyodide for Python execution in browser
- Lucide icons for UI elements
- Element Plus for tree component

### Key Files Modified
1. `VmIde.vue`: Main layout restructuring
2. `ProjTree.vue`: File tree enhancements
3. `CodeEditor.vue`: Word wrap support
4. `TopMenu.vue`: Word wrap toggle button
5. `ide.js` (store): New mutations for console management

### CSS Improvements
- Smooth animations for console collapse/expand
- Hover effects for interactive elements
- Responsive design for different screen sizes
- Dark/Light theme support

## Testing
Run `test_new_layout.py` to test all new features:
```bash
python test_new_layout.py
```

This will demonstrate:
- Console output below editor
- Input functionality
- Plot generation for preview panel
- Word wrap with long lines
- Interactive REPL testing

## Future Enhancements
- Settings modal for preferences
- File move/drag-and-drop functionality
- Multi-select in file tree
- Search in files
- Code formatting
- Git integration