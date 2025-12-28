# Winter 2025 To-Do List

## Pending

Status: **Pending**
1. Resolve issues related to REPL (Read-Eval-Print Loop) timeouts, particularly concerning interactions with variable usage and state persistence.

Status: **Pending**
2. Address infinite loop timeout errors that occur when importing or processing CSV files alongside code execution.

Status: **Pending**
4. Provide an "undo" feature for deletion actions, allowing users to revert accidental deletions.

---

## Completed (December 28, 2025)

Status: **Completed** ✅
3. Implement functionality to open CSV and PDF files in a side panel, rather than replacing the currently displayed code editor content.
   - CSV, PDF, TXT, and image files now open in right panel by default
   - Added "Open in Editor" context menu option for fullscreen view
   - See: `docs/WINTER_2025_IMPROVEMENTS.md` for details

Status: **Completed** ✅
5. Add support for rearranging open tabs, enabling users to move tabs both backwards and forwards within the tab sequence.
   - Drag-and-drop tab rearrangement for both editor and preview panel
   - Keyboard shortcuts: Alt+Arrow (prev/next), Alt+1-6 (direct jump), Ctrl+W (close)
   - See: `docs/WINTER_2025_IMPROVEMENTS.md` for details
