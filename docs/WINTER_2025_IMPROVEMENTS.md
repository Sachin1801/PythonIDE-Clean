# Winter 2025 IDE Improvements

**Version:** 2.0.0
**Date:** December 28, 2025
**Branch:** `feat/winter-improvements`

---

## Overview

This update introduces several quality-of-life improvements to the Python IDE, focusing on enhanced file management, tab navigation, and performance optimizations for large CSV files.

---

## Table of Contents

1. [Tab Management Improvements](#1-tab-management-improvements)
2. [Default Right Panel for Preview Files](#2-default-right-panel-for-preview-files)
3. [Drag-and-Drop Tab Rearrangement](#3-drag-and-drop-tab-rearrangement)
4. [Keyboard Shortcuts for Tab Navigation](#4-keyboard-shortcuts-for-tab-navigation)
5. [CSV Virtual Scrolling](#5-csv-virtual-scrolling)
6. [Mac Keyboard Symbol Support](#6-mac-keyboard-symbol-support)
7. [Files Modified](#7-files-modified)

---

## 1. Tab Management Improvements

### Changes
- **Editor Tab Limit**: Increased from 5 to 6 tabs
- **Preview Panel Tab Limit**: Set to 5 tabs with automatic oldest-tab closure

### Behavior
When the tab limit is reached:
- A warning message is displayed
- The oldest tab is automatically closed to make room for the new file
- Users are notified which tab was closed

### Related Files
- `src/store/modules/ide.js` - `MAX_TABS = 6`
- `src/components/element/VmIde.vue` - `MAX_PREVIEW_TABS = 5`

---

## 2. Default Right Panel for Preview Files

### Overview
Preview files (CSV, PDF, TXT, images) now open in the right panel by default instead of the fullscreen viewer.

### Supported File Types
| Category | Extensions |
|----------|------------|
| Data Files | `.csv` |
| Documents | `.pdf`, `.txt` |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`, `.bmp` |

### Context Menu Changes
- **Before**: "Open in Right Panel" option for preview files
- **After**: "Open in Editor" option for preview files (since right panel is now default)

### User Experience
1. **Single-click** on preview file → Opens in right panel
2. **Right-click → "Open in Editor"** → Opens in fullscreen viewer

### Related Files
- `src/components/element/VmIde.vue` - `getFile()` method
- `src/components/element/pages/ide/ProjTree.vue` - Context menu

---

## 3. Drag-and-Drop Tab Rearrangement

### Features
- Drag tabs to reorder them within the same panel
- Visual feedback with animated drop indicators
- Works for both editor tabs and preview panel tabs

### Visual Feedback
- **Dragging**: Tab becomes semi-transparent (opacity 50%)
- **Drop Target**: Blue indicator line appears on left or right side
- **Animation**: Pulse animation on drop indicators

### Limitations
- Cross-panel dragging is NOT supported (cannot drag from editor to preview panel)
- Touch/mobile devices are NOT supported

### Related Files
- `src/components/element/pages/ide/CodeTabs.vue` - Editor tab drag-drop
- `src/components/element/VmIde.vue` - Preview panel drag-drop
- `src/store/modules/ide.js` - `reorderCodeItems` mutation

---

## 4. Keyboard Shortcuts for Tab Navigation

### New Shortcuts

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Previous Tab | `Alt + ←` | `Option + ←` |
| Next Tab | `Alt + →` | `Option + →` |
| Go to Tab 1-6 | `Alt + 1-6` | `Option + 1-6` |

### Focus-Aware Navigation
- Shortcuts affect the currently focused panel
- Click on editor area → shortcuts navigate editor tabs
- Click on preview panel → shortcuts navigate preview tabs

### Access Keyboard Shortcuts Help
- Press `F1` to view all keyboard shortcuts
- Or go to **Help → Keyboard Shortcuts**

### Related Files
- `src/components/element/pages/ide/TwoHeaderMenu.vue` - Shortcut handlers
- `src/components/element/VmIde.vue` - Navigation methods, focus tracking
- `src/components/element/pages/ide/KeyboardShortcutsModal.vue` - Display

---

## 5. CSV Virtual Scrolling

### Overview
Replaced pagination with virtual scrolling for improved performance with large CSV files.

### Features
- **Virtual Scrolling**: Only renders visible rows for better performance
- **Large File Warning**: Shows warning for files with >10,000 rows
- **Scroll Position Indicator**: Shows "Showing rows X - Y of Z"
- **Search**: Still available (resets scroll position)
- **Sort**: Click column headers to sort (not available in Exam mode)

### Performance
| Rows | Old (Pagination) | New (Virtual Scroll) |
|------|------------------|----------------------|
| 100 | Fast | Fast |
| 1,000 | Fast | Fast |
| 10,000 | Slow page loads | Smooth scrolling |
| 50,000+ | Very slow | Performant |

### Technical Details
- Row height: 32px (fixed for virtual calculation)
- Overscan: 5 rows above/below viewport (prevents flickering)
- Uses `ResizeObserver` for dynamic container height

### Related Files
- `src/components/element/pages/ide/CsvViewer.vue`

---

## 6. Mac Keyboard Symbol Support

### Overview
The Keyboard Shortcuts modal now displays platform-appropriate symbols.

### Symbol Mapping
| Windows/Linux | Mac Symbol |
|---------------|------------|
| Ctrl | ⌘ (Command) |
| Alt | ⌥ (Option) |
| Shift | ⇧ |

### Modal Title
- **Mac**: "Keyboard Shortcuts (Mac)"
- **Windows/Linux**: "Keyboard Shortcuts (Windows/Linux)"

### Related Files
- `src/components/element/pages/ide/KeyboardShortcutsModal.vue`

---

## 7. Files Modified

| File | Changes |
|------|---------|
| `src/store/modules/ide.js` | Tab limit (5→6), `reorderCodeItems` mutation |
| `src/components/element/VmIde.vue` | Right panel default, tab navigation, drag-drop, focus tracking |
| `src/components/element/pages/ide/CodeTabs.vue` | Drag-drop for editor tabs, tab limit display |
| `src/components/element/pages/ide/ProjTree.vue` | Context menu text change, `.txt` support |
| `src/components/element/pages/ide/TwoHeaderMenu.vue` | Tab navigation keyboard shortcuts |
| `src/components/element/pages/ide/KeyboardShortcutsModal.vue` | New shortcuts, Mac symbols |
| `src/components/element/pages/ide/CsvViewer.vue` | Virtual scrolling implementation |

---

## Testing Checklist

### Tab Management
- [ ] Can open 6 editor tabs
- [ ] 7th editor tab shows warning and closes oldest
- [ ] Can open 5 preview tabs
- [ ] 6th preview tab shows warning and closes oldest

### Right Panel Default
- [ ] CSV files open in right panel by default
- [ ] PDF files open in right panel by default
- [ ] TXT files open in right panel by default
- [ ] Image files open in right panel by default
- [ ] "Open in Editor" context menu opens in fullscreen
- [ ] Python files still open in editor (not right panel)

### Drag-and-Drop
- [ ] Can drag editor tabs to reorder
- [ ] Can drag preview tabs to reorder
- [ ] Drop indicator appears when dragging
- [ ] Dropping outside cancels the drag

### Keyboard Shortcuts
- [ ] Alt+← (Option+← on Mac) goes to previous tab
- [ ] Alt+→ (Option+→ on Mac) goes to next tab
- [ ] Alt+1-6 (Option+1-6 on Mac) jumps to specific tab
- [ ] Shortcuts work for focused panel only
- [ ] F1 shows shortcuts modal
- [ ] Ctrl+Shift+P toggles preview panel

### CSV Virtual Scroll
- [ ] Small CSV scrolls smoothly
- [ ] Large CSV (>10,000 rows) shows warning
- [ ] Scroll position indicator updates
- [ ] Search works and resets scroll
- [ ] Sort works (non-exam mode)

### Mac Support
- [ ] Shortcuts modal shows ⌘, ⌥ symbols on Mac
- [ ] Modal title shows "(Mac)" on Mac

---

## Rollback Instructions

If issues occur in production:

```bash
# Revert the commit
git revert <commit-hash>

# Push to main to trigger redeployment
git push origin main
```

---

## Related Todo Items (from winter-toDo.md)

- [x] ~~Item 3: Implement functionality to open CSV and PDF files in a side panel~~
- [x] ~~Item 5: Add support for rearranging open tabs~~

---

*Last updated: December 28, 2025*
