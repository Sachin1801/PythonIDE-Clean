<template>
  <div class="two-header-container">
    <!-- First Header: File Menu + Sign In -->
    <div class="header-first">
      <!-- Left Section: All Dropdown Menus -->
      <nav class="nav-menu">
        <ul class="nav__items-left">
          <!-- File Dropdown -->
          <li class="nav__item">
            <button 
              class="nav__item-button"
              @click.stop="toggleDropdown('file')"
              aria-haspopup="menu"
              :aria-expanded="activeDropdown === 'file'"
            >
              <span class="nav__item-header">File</span>
              <svg class="nav__item-triangle" width="9" height="6" viewBox="0 0 9 6" xmlns="http://www.w3.org/2000/svg">
                <polygon points="4.5 6 9 0 0 0" fill="currentColor"/>
              </svg>
            </button>
            <ul class="nav__dropdown" v-show="activeDropdown === 'file'" @click.stop>
              <li class="nav__dropdown-item">
                <button @click="newFile()">
                  <span>New File</span>
                  <span class="nav__keyboard-shortcut">Ctrl+Alt+N</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="openFile()">
                  <span>Open File</span>
                  <span class="nav__keyboard-shortcut">Ctrl+O</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="duplicateFile()" :disabled="!hasSelectedFile">
                  <span>Duplicate (Make a copy)</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="saveFile()">
                  <span>Save</span>
                  <span class="nav__keyboard-shortcut">Ctrl+S</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="saveAsFile()" :disabled="!canSaveAsFile">
                  <span>Save As</span>
                  <span class="nav__keyboard-shortcut">Ctrl+Shift+S</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="moveFile()" :disabled="!hasSelectedFile">
                  <span>Move</span>
                  <span class="nav__keyboard-shortcut">Ctrl+Shift+M</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="downloadFile()">
                  <span>Download</span>
                  <span class="nav__keyboard-shortcut">Ctrl+D</span>
                </button>
              </li>
            </ul>
          </li>
          
          <!-- Edit Dropdown -->
          <li class="nav__item">
            <button 
              class="nav__item-button"
              @click.stop="toggleDropdown('edit')"
              aria-haspopup="menu"
              :aria-expanded="activeDropdown === 'edit'"
            >
              <span class="nav__item-header">Edit</span>
              <svg class="nav__item-triangle" width="9" height="6" viewBox="0 0 9 6" xmlns="http://www.w3.org/2000/svg">
                <polygon points="4.5 6 9 0 0 0" fill="currentColor"/>
              </svg>
            </button>
            <ul class="nav__dropdown" v-show="activeDropdown === 'edit'" @click.stop>
              <li class="nav__dropdown-item">
                <button @click="undo()">
                  <span>Undo</span>
                  <span class="nav__keyboard-shortcut">Ctrl+Z</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="redo()">
                  <span>Redo</span>
                  <span class="nav__keyboard-shortcut">Ctrl+Y</span>
                </button>
              </li>
              <li class="nav__dropdown-divider"></li>
              <li class="nav__dropdown-item">
                <button @click="cut()">
                  <span>Cut</span>
                  <span class="nav__keyboard-shortcut">Ctrl+X</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="copy()">
                  <span>Copy</span>
                  <span class="nav__keyboard-shortcut">Ctrl+C</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="paste()">
                  <span>Paste</span>
                  <span class="nav__keyboard-shortcut">Ctrl+V</span>
                </button>
              </li>
              <li class="nav__dropdown-divider"></li>
              <!-- TEMPORARILY DISABLED FOR FILE HANDLING ASSIGNMENT -->
              <!-- <li class="nav__dropdown-item">
                <button @click="find()">
                  <span>Find</span>
                  <span class="nav__keyboard-shortcut">Ctrl+F</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="replace()">
                  <span>Replace</span>
                  <span class="nav__keyboard-shortcut">Ctrl+H</span>
                </button>
              </li> -->
              <!-- <li class="nav__dropdown-divider"></li> -->
              <li class="nav__dropdown-item">
                <button @click="comment()">
                  <span>Comment</span>
                  <!-- <span class="nav__keyboard-shortcut">Ctrl+/</span> -->
                </button>
              </li>
            </ul>
          </li>
          
          <!-- Run Dropdown -->
          <li class="nav__item">
            <button 
              class="nav__item-button"
              @click.stop="toggleDropdown('run')"
              aria-haspopup="menu"
              :aria-expanded="activeDropdown === 'run'"
            >
              <span class="nav__item-header">Run</span>
              <svg class="nav__item-triangle" width="9" height="6" viewBox="0 0 9 6" xmlns="http://www.w3.org/2000/svg">
                <polygon points="4.5 6 9 0 0 0" fill="currentColor"/>
              </svg>
            </button>
            <ul class="nav__dropdown" v-show="activeDropdown === 'run'" @click.stop>
              <li class="nav__dropdown-item">
                <button @click="runScript()">
                  <span>Run Script</span>
                  <span class="nav__keyboard-shortcut">F5</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="stopScript()">
                  <span>Stop</span>
                  <span class="nav__keyboard-shortcut">Shift+F5</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="clearConsole()">
                  <span>Clear Console</span>
                </button>
              </li>
            </ul>
          </li>
          
          <!-- View Dropdown -->
          <li class="nav__item">
            <button 
              class="nav__item-button"
              @click.stop="toggleDropdown('view')"
              aria-haspopup="menu"
              :aria-expanded="activeDropdown === 'view'"
            >
              <span class="nav__item-header">View</span>
              <svg class="nav__item-triangle" width="9" height="6" viewBox="0 0 9 6" xmlns="http://www.w3.org/2000/svg">
                <polygon points="4.5 6 9 0 0 0" fill="currentColor"/>
              </svg>
            </button>
            <ul class="nav__dropdown" v-show="activeDropdown === 'view'" @click.stop>
              <li class="nav__dropdown-item">
                <button @click="toggleConsole()">
                  <span>{{ consoleVisible ? 'Hide REPL' : 'Show REPL' }}</span>
                  <span class="nav__keyboard-shortcut">Ctrl+`</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="togglePreviewPanel()">
                  <span>{{ previewPanelVisible ? 'Hide Right Panel' : 'Show Right Panel' }}</span>
                  <span class="nav__keyboard-shortcut">Ctrl+Shift+P</span>
                </button>
              </li>
              <li class="nav__dropdown-item">
                <button @click="toggleSidebar()">
                  <span>{{ sidebarVisible ? 'Hide Sidebar' : 'Show Sidebar' }}</span>
                  <span class="nav__keyboard-shortcut">Ctrl+B</span>
                </button>
              </li>
            </ul>
          </li>
          
          <!-- Help Dropdown -->
          <li class="nav__item">
            <button 
              class="nav__item-button"
              @click.stop="toggleDropdown('help')"
              aria-haspopup="menu"
              :aria-expanded="activeDropdown === 'help'"
            >
              <span class="nav__item-header">Help</span>
              <svg class="nav__item-triangle" width="9" height="6" viewBox="0 0 9 6" xmlns="http://www.w3.org/2000/svg">
                <polygon points="4.5 6 9 0 0 0" fill="currentColor"/>
              </svg>
            </button>
            <ul class="nav__dropdown" v-show="activeDropdown === 'help'" @click.stop>
              <li class="nav__dropdown-item">
                <button @click="showKeyboardShortcuts()">
                  <span>Keyboard Shortcuts</span>
                  <span class="nav__keyboard-shortcut">F1</span>
                </button>
              </li>
            </ul>
          </li>
        </ul>
      </nav>

      <!-- Right Section: Sign In / User Button -->
      <div class="header-right-section">
        <button 
          v-if="!currentUser"
          class="sign-in-btn" 
          @click="handleSignIn"
        >
          <UserCircle :size="18" />
          <span>Sign In</span>
        </button>
        
        <button 
          v-else
          class="user-btn"
          @click="showUserProfile = true"
        >
          <UserCircle :size="18" />
          <span>{{ currentUser.username }}</span>
        </button>
      </div>
    </div>

    <!-- Second Header: Icon Buttons -->
    <div class="header-second">
      <!-- Center Container with absolute positioning -->
      <div class="header-second-center-container">
        <!-- Run/Stop Button -->
        <div class="icon-btn run-btn" v-if="!hasRunProgram" @click="runScript()" title="Run (F5)">
          <Play :size="20" />
        </div>
        <div class="icon-btn stop-btn" @click="stopScript()" v-if="hasRunProgram" title="Stop (Shift+F5)">
          <Square :size="20" />
        </div>

        <!-- Save Button -->
        <div class="icon-btn save-btn" @click="saveFile()" title="Save (Ctrl+S)">
          <Save :size="20" />
        </div>


      </div>

      <!-- Right Section: Settings Icon -->
      <div class="header-second-right">
        <div class="icon-btn settings-btn" @click="openSettings()" title="Settings">
          <Settings :size="20" />
        </div>
      </div>
    </div>
    
    <!-- User Profile Modal -->
    <UserProfileModal 
      v-model="showUserProfile"
      :current-user="currentUser"
      @logout="handleLogout"
      @password-changed="handlePasswordChanged"
    />
  </div>
</template>

<script>
import { Upload, Play, Square, Settings, Trash2, UserCircle, Save } from 'lucide-vue-next';
import { ElMessageBox, ElMessage } from 'element-plus';
import UserProfileModal from '../../UserProfileModal.vue';

export default {
  props: {
    consoleLimit: Boolean,
    hasRunProgram: Boolean,
    currentUser: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      isRun: true,
      activeDropdown: null,
      consoleVisible: true,
      previewPanelVisible: false,
      sidebarVisible: true,
      showUserProfile: false,
    }
  },
  computed: {
    ideInfo() {
      return this.$store?.state?.ide?.ideInfo || {};
    },
    isPythonFile() {
      return this.ideInfo.currProj && 
             this.ideInfo.currProj.pathSelected && 
             this.ideInfo.codeItems && 
             this.ideInfo.codeItems.length > 0 && 
             this.ideInfo.currProj.pathSelected.endsWith('.py');
    },
    hasSelectedFile() {
      const result = this.ideInfo.nodeSelected && this.ideInfo.nodeSelected.type === 'file';
      console.log('🔍 [DEBUG] hasSelectedFile computed:', {
        nodeSelected: this.ideInfo.nodeSelected,
        nodeType: this.ideInfo.nodeSelected?.type,
        result: result
      });
      return result;
    },
    canDeleteFile() {
      // Check if a file is selected and it's not a protected item
      const selected = this.ideInfo.nodeSelected;
      return selected && selected.type === 'file';
    },
    deleteButtonTitle() {
      if (!this.ideInfo.nodeSelected) {
        return 'Select a file to delete';
      }
      if (this.ideInfo.nodeSelected.type !== 'file') {
        return 'Can only delete files';
      }
      return `Delete ${this.ideInfo.nodeSelected.label || this.ideInfo.nodeSelected.name}`;
    },
    canSaveAsFile() {
      // Can save if we have a file selected in tree OR a file open in editor
      const hasSelected = this.hasSelectedFile;
      const hasCodeSelected = this.ideInfo.codeSelected && this.ideInfo.codeSelected.fileName;
      const result = hasSelected || hasCodeSelected;
      
      console.log('🔍 [DEBUG] canSaveAsFile computed:', {
        hasSelectedFile: hasSelected,
        nodeSelected: this.ideInfo.nodeSelected,
        hasCodeSelected: hasCodeSelected,
        codeSelected: this.ideInfo.codeSelected,
        result: result
      });
      
      return result;
    },
  },
  components: {
    Upload,
    Play,
    Square,
    Settings,
    Trash2,
    UserCircle,
    Save,
    UserProfileModal,
  },
  mounted() {
    // Initialize theme on mount
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Add click outside listener for dropdowns
    document.addEventListener('click', this.closeDropdowns);
    
    // Add keyboard shortcuts
    console.log('🎹 TwoHeaderMenu - Adding keyboard shortcut listener');
    document.addEventListener('keydown', this.handleKeyboardShortcuts);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeDropdowns);
    document.removeEventListener('keydown', this.handleKeyboardShortcuts);
  },
  methods: {
    toggleDropdown(name) {
      this.activeDropdown = this.activeDropdown === name ? null : name;
    },
    closeDropdowns() {
      this.activeDropdown = null;
    },
    handleKeyboardShortcuts(e) {
      // File Operations
      // Ctrl+S - Save
      if (e.ctrlKey && !e.shiftKey && e.key === 's') {
        e.preventDefault();
        e.stopPropagation();
        this.saveFile();
        return;
      }
      // Ctrl+Shift+S - Save As
      if (e.ctrlKey && e.shiftKey && e.key === 'S') {
        console.log('🔍 [DEBUG] Ctrl+Shift+S keyboard shortcut triggered');
        console.log('🔍 [DEBUG] canSaveAsFile:', this.canSaveAsFile);
        e.preventDefault();
        e.stopPropagation();
        if (this.canSaveAsFile) {
          console.log('🔍 [DEBUG] Calling saveAsFile() from keyboard shortcut');
          this.saveAsFile();
        } else {
          console.log('🔍 [DEBUG] Cannot save as - no file available');
        }
        return;
      }
      // Ctrl+Alt+N - New File
      if (e.ctrlKey && e.altKey && !e.shiftKey && e.key === 'n') {
        e.preventDefault();
        e.stopPropagation();
        this.newFile();
        return;
      }
      // Ctrl+O - Open File
      if (e.ctrlKey && !e.shiftKey && e.key === 'o') {
        e.preventDefault();
        e.stopPropagation();
        this.openFile();
        return;
      }
      // Ctrl+D - Download
      if (e.ctrlKey && !e.shiftKey && e.key === 'd') {
        e.preventDefault();
        e.stopPropagation();
        this.downloadFile();
        return;
      }
      // Ctrl+Shift+M - Move
      if (e.ctrlKey && e.shiftKey && e.key === 'M') {
        e.preventDefault();
        e.stopPropagation();
        if (this.hasSelectedFile) {
          this.moveFile();
        }
        return;
      }
      
      // Edit Operations
      // Ctrl+Z - Undo
      if (e.ctrlKey && !e.shiftKey && e.key === 'z') {
        e.preventDefault();
        e.stopPropagation();
        this.undo();
        return;
      }
      // Ctrl+Y - Redo
      if (e.ctrlKey && !e.shiftKey && e.key === 'y') {
        e.preventDefault();
        e.stopPropagation();
        this.redo();
        return;
      }
      // Helper function to check if the focused element should handle copy/paste natively
      const shouldAllowNativeCopyPaste = () => {
        const activeElement = document.activeElement;
        if (!activeElement) return false;

        // Allow native behavior for all text input contexts
        return (
          // Standard input elements
          activeElement.tagName === 'INPUT' ||
          activeElement.tagName === 'TEXTAREA' ||
          // REPL input (existing logic)
          activeElement.classList.contains('repl-input') ||
          // Contenteditable elements
          activeElement.contentEditable === 'true' ||
          // Modal input fields (common classes)
          activeElement.classList.contains('filename-input') ||
          activeElement.classList.contains('el-input__inner') ||
          // Any element with input-like role
          activeElement.getAttribute('role') === 'textbox'
        );
      };

      // Helper: Check for Ctrl (Windows/Linux) or Cmd (Mac)
      const isCopyPasteModifier = e.ctrlKey || e.metaKey;

      // Ctrl+X or Cmd+X - Cut (allow native cut in all text inputs)
      if (isCopyPasteModifier && !e.shiftKey && e.key === 'x') {
        if (shouldAllowNativeCopyPaste()) {
          // Let the input handle cut naturally
          return;
        }

        e.preventDefault();
        e.stopPropagation();
        this.cut();
        return;
      }
      // Ctrl+C or Cmd+C - Copy (allow native copy in all text inputs)
      if (isCopyPasteModifier && !e.shiftKey && e.key === 'c') {
        if (shouldAllowNativeCopyPaste()) {
          // Let the input handle copy naturally
          return;
        }

        e.preventDefault();
        e.stopPropagation();
        this.copy();
        return;
      }
      // Ctrl+V, Ctrl+Shift+V, Cmd+V, or Cmd+Shift+V - Paste (allow native paste in all text inputs)
      if (isCopyPasteModifier && e.key === 'v') {
        if (shouldAllowNativeCopyPaste()) {
          // Let the input handle paste naturally
          return;
        }

        e.preventDefault();
        e.stopPropagation();
        this.paste();
        return;
      }
      // TEMPORARILY DISABLED FOR FILE HANDLING ASSIGNMENT
      // Ctrl+F or Cmd+F - Find (block both Ctrl and Meta/Cmd keys)
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key === 'f') {
        e.preventDefault();
        e.stopPropagation();
        // this.find(); // DISABLED
        return;
      }
      // Ctrl+H or Cmd+H - Replace (block both Ctrl and Meta/Cmd keys)
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key === 'h') {
        e.preventDefault();
        e.stopPropagation();
        // this.replace(); // DISABLED
        return;
      }
      // Ctrl+/ - Comment
      if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        e.stopPropagation();
        this.comment();
        return;
      }
      
      // Run Operations
      // F5 - Run
      if (e.key === 'F5' && !e.shiftKey) {
        e.preventDefault();
        e.stopPropagation();
        if (this.isPythonFile && !this.consoleLimit) {
          this.runScript();
        }
        return;
      }
      // Shift+F5 - Stop
      if (e.shiftKey && e.key === 'F5') {
        e.preventDefault();
        e.stopPropagation();
        if (this.hasRunProgram) {
          this.stopScript();
        }
        return;
      }
      
      // View Operations
      // Ctrl+` - Toggle Console
      if (e.ctrlKey && e.key === '`') {
        e.preventDefault();
        e.stopPropagation();
        this.toggleConsole();
        return;
      }
      // Ctrl+Shift+P - Toggle Preview Panel (not Ctrl+P to avoid print dialog)
      if (e.ctrlKey && e.shiftKey && e.key === 'P') {
        e.preventDefault();
        e.stopPropagation();
        this.togglePreviewPanel();
        return;
      }
      // Ctrl+B - Toggle Sidebar
      if (e.ctrlKey && !e.shiftKey && e.key === 'b') {
        e.preventDefault();
        e.stopPropagation();
        this.toggleSidebar();
        return;
      }
      
      // General Operations
      // F1 - Show Keyboard Shortcuts
      if (e.key === 'F1') {
        e.preventDefault();
        e.stopPropagation();
        this.showKeyboardShortcuts();
        return;
      }
      // Ctrl+, - Settings
      if (e.ctrlKey && e.key === ',') {
        e.preventDefault();
        e.stopPropagation();
        this.openSettings();
        return;
      }
    },
    newFile() {
      this.closeDropdowns();
      if (!this.ideInfo.nodeSelected || (this.ideInfo.nodeSelected.type !== 'dir' && this.ideInfo.nodeSelected.type !== 'folder')) {
        // Select root folder if no folder is selected
        const rootFolder = this.ideInfo.currProj?.data;
        if (rootFolder) {
          this.$store.commit('ide/setNodeSelected', rootFolder);
        }
      }
      this.$emit('set-text-dialog', {
        type: 'create-file',
        title: 'New File',
        tips: 'Enter file name:',
        text: 'untitled.py'
      });
    },
    saveFile() {
      this.closeDropdowns();
      if (this.ideInfo.codeSelected) {
        this.$store.dispatch('ide/saveFile', {
          codeItem: this.ideInfo.codeSelected,
          isAutoSave: false
        }).then(() => {
          ElMessage.success('File saved');
        }).catch((error) => {
          // Handle permission denied or other errors
          const errorMsg = error.message || 'Failed to save file';
          ElMessage.error(errorMsg);
          console.error('[SAVE-ERROR]', error);
        });
      }
    },
    downloadFile() {
      this.closeDropdowns();
      if (!this.ideInfo.nodeSelected || this.ideInfo.nodeSelected.type !== 'file') {
        if (this.ideInfo.codeSelected) {
          this.$emit('download-file', this.ideInfo.codeSelected);
        } else {
          ElMessage.warning('Please select a file to download');
        }
      } else {
        // Convert tree node selection to fileInfo format
        const selectedFile = this.ideInfo.nodeSelected;
        const fileInfo = {
          fileName: selectedFile.label || selectedFile.name,
          filePath: selectedFile.path,
          projectName: selectedFile.projectName || this.ideInfo.currProj?.data?.name
        };
        this.$emit('download-file', fileInfo);
      }
    },
    runScript() {
      this.closeDropdowns();
      this.$emit('run-item');
    },
    stopScript() {
      this.closeDropdowns();
      for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
        if (this.ideInfo.consoleItems[i].run === true) {
          this.$store.commit('ide/setConsoleItemRun', {index: i, value: false});
        }
      }
      this.$emit('stop-item', null);
    },
    clearConsole() {
      this.$emit('clear-console');
    },
    deleteSelectedFile() {
      // Check if we can delete
      if (!this.canDeleteFile) {
        ElMessage.warning('Please select a file to delete');
        return;
      }
      
      const selected = this.ideInfo.nodeSelected;
      const fileName = selected.label || selected.name;
      
      // Show confirmation dialog
      ElMessageBox.confirm(
        `Are you sure you want to delete "${fileName}"?`,
        'Confirm Delete',
        {
          confirmButtonText: 'Delete',
          cancelButtonText: 'Cancel',
          type: 'warning',
        }
      ).then(() => {
        // Emit delete event
        this.$emit('delete-selected-file', {
          path: selected.path,
          type: selected.type,
          projectName: selected.projectName || this.ideInfo.currProj?.data?.name
        });
      }).catch(() => {
        // User cancelled - do nothing
      });
    },
    openSettings() {
      this.$emit('open-settings');
    },
    handleSignIn() {
      this.$emit('sign-in');
    },
    openFile() {
      this.closeDropdowns();
      this.$emit('open-file-browser');
    },
    duplicateFile() {
      console.log('🔍 [DEBUG] duplicateFile() called from TwoHeaderMenu');
      this.closeDropdowns();
      if (!this.hasSelectedFile) {
        console.log('🔍 [DEBUG] No file selected for duplication');
        ElMessage.warning('Please select a file to duplicate');
        return;
      }
      const selectedFile = this.ideInfo.nodeSelected;
      const fileName = selectedFile.label || selectedFile.name;
      const extension = fileName.includes('.') ? fileName.substring(fileName.lastIndexOf('.')) : '';
      const baseName = fileName.includes('.') ? fileName.substring(0, fileName.lastIndexOf('.')) : fileName;
      const newName = `${baseName}_copy${extension}`;
      
      console.log('🔍 [DEBUG] Emitting duplicate-file event:', {
        originalPath: selectedFile.path,
        newName: newName,
        projectName: selectedFile.projectName || this.ideInfo.currProj?.data?.name
      });
      
      this.$emit('duplicate-file', {
        originalPath: selectedFile.path,
        newName: newName,
        projectName: selectedFile.projectName || this.ideInfo.currProj?.data?.name
      });
    },
    saveAsFile() {
      console.log('🔍 [DEBUG] saveAsFile() called');
      console.log('🔍 [DEBUG] hasSelectedFile:', this.hasSelectedFile);
      console.log('🔍 [DEBUG] nodeSelected:', this.ideInfo.nodeSelected);
      console.log('🔍 [DEBUG] codeSelected:', this.ideInfo.codeSelected);
      console.log('🔍 [DEBUG] canSaveAsFile:', this.canSaveAsFile);
      
      this.closeDropdowns();
      
      // Check if we have a file selected in the tree (like delete functionality)
      if (this.hasSelectedFile) {
        const selectedFile = this.ideInfo.nodeSelected;
        
        // Convert tree node to fileInfo format (like codeSelected)
        const fileInfo = {
          fileName: selectedFile.label || selectedFile.name,
          filePath: selectedFile.path,
          projectName: selectedFile.projectName || this.ideInfo.currProj?.data?.name
        };
        
        console.log('🔍 [DEBUG] Converted tree file to fileInfo:', fileInfo);
        console.log('🔍 [DEBUG] Original selectedFile:', selectedFile);
        this.$emit('save-as-file', fileInfo);
        return;
      }
      
      // Fallback to currently open file in editor
      if (this.ideInfo.codeSelected) {
        console.log('🔍 [DEBUG] Emitting save-as-file for editor file:', this.ideInfo.codeSelected);
        this.$emit('save-as-file', this.ideInfo.codeSelected);
        return;
      }
      
      // No file selected
      console.log('🔍 [DEBUG] No file available for save as');
      ElMessage.warning('Please select a file to save');
    },
    moveFile() {
      this.closeDropdowns();
      if (!this.hasSelectedFile) {
        ElMessage.warning('Please select a file to move');
        return;
      }
      this.$emit('open-move-dialog', this.ideInfo.nodeSelected);
    },
    deleteFile() {
      this.closeDropdowns();
      if (!this.hasSelectedFile) {
        ElMessage.warning('Please select a file to delete');
        return;
      }
      
      const selectedFile = this.ideInfo.nodeSelected;
      const fileName = selectedFile.label || selectedFile.name;
      
      ElMessageBox.confirm(
        `Are you sure you want to delete "${fileName}"?`,
        'Confirm Delete',
        {
          confirmButtonText: 'Delete',
          cancelButtonText: 'Cancel',
          type: 'warning',
        }
      ).then(() => {
        this.$emit('delete-file', {
          path: selectedFile.path,
          type: selectedFile.type,
          projectName: selectedFile.projectName || this.ideInfo.currProj?.data?.name
        });
      }).catch(() => {
        // User cancelled
      });
    },
    // Edit menu methods
    undo() {
      this.closeDropdowns();
      this.$emit('undo');
    },
    redo() {
      this.closeDropdowns();
      this.$emit('redo');
    },
    cut() {
      this.closeDropdowns();
      this.$emit('cut');
    },
    copy() {
      this.closeDropdowns();
      this.$emit('copy');
    },
    paste() {
      this.closeDropdowns();
      this.$emit('paste');
    },
    find() {
      this.closeDropdowns();
      this.$emit('find');
    },
    replace() {
      this.closeDropdowns();
      this.$emit('replace');
    },
    comment() {
      this.closeDropdowns();
      this.$emit('comment');
    },
    // View menu methods
    toggleConsole() {
      this.closeDropdowns();
      this.consoleVisible = !this.consoleVisible;
      this.$emit('toggle-console', this.consoleVisible);
    },
    togglePreviewPanel() {
      this.closeDropdowns();
      this.previewPanelVisible = !this.previewPanelVisible;
      this.$emit('toggle-preview-panel', this.previewPanelVisible);
    },
    toggleSidebar() {
      this.closeDropdowns();
      this.sidebarVisible = !this.sidebarVisible;
      this.$emit('toggle-sidebar', this.sidebarVisible);
    },
    // Help menu methods
    showKeyboardShortcuts() {
      this.closeDropdowns();
      this.$emit('show-keyboard-shortcuts');
    },
    handleLogout() {
      // Clear all session data
      localStorage.removeItem('session_id');
      localStorage.removeItem('username');
      localStorage.removeItem('role');
      localStorage.removeItem('full_name');
      
      // Emit logout event
      this.$emit('logout');
      
      // Show success message
      ElMessage.success('Logged out successfully');
      
      // Reload page to reset state
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    },
    handlePasswordChanged() {
      ElMessage.success('Password changed successfully!');
    },
  },
};
</script>

<style scoped>
.two-header-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 100;
}

/* First Header */
.header-first {
  width: 100%;
  height: 40px;
  background: var(--header-bg, #313131);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color, #252525);
  position: relative;
}

/* Second Header */
.header-second {
  width: 100%;
  height: 40px;
  background: var(--header-bg, #313131);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color, #252525);
  position: relative;
}

/* Navigation Menu */
.nav-menu {
  flex: 0 0 auto;
}

.nav__items-left {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 4px;
}

.nav__item {
  position: relative;
}

.nav__item-button {
  background: transparent;
  border: none;
  color: var(--text-primary, #B5B5B5);
  padding: 6px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  border-radius: 4px;
  transition: background 0.2s;
  height: 28px;
}

.nav__item-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav__item-header {
  font-weight: 400;
}

.nav__item-triangle {
  opacity: 0.6;
  width: 8px;
  height: 5px;
}

/* Dropdown Menu */
.nav__dropdown {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  background: var(--bg-secondary, #252526);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  min-width: 220px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  padding: 4px 0;
  list-style: none;
  margin: 0;
}

.nav__dropdown-item {
  padding: 0;
  margin: 0;
}

.nav__dropdown-item button {
  width: 100%;
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: var(--text-primary, #ccc);
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.2s;
  text-decoration: none;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.nav__keyboard-shortcut {
  font-size: 11px;
  opacity: 0.6;
  margin-left: 24px;
  font-family: monospace;
}

.nav__dropdown-divider {
  height: 1px;
  background: var(--border-color, #464647);
  margin: 4px 0;
}

.nav__dropdown-item button:hover {
  background: var(--hover-bg, #094771);
}

.nav__dropdown-item button:disabled {
  color: var(--text-tertiary, #666);
  cursor: not-allowed;
  opacity: 0.5;
}

.nav__dropdown-item button:disabled:hover {
  background: transparent;
}

.nav__dropdown-item .delete-option {
  color: #F44747;
}

.nav__dropdown-item .delete-option:hover:not(:disabled) {
  background: rgba(244, 71, 71, 0.2);
}

/* Sign In / User Button */
.header-right-section {
  display: flex;
  align-items: center;
  margin-right: 20px;
  padding-right: 8px;
}

.sign-in-btn,
.user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  margin-right: 12px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-primary, #B5B5B5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  height: 32px;
  outline: none;
}

.sign-in-btn:hover,
.user-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.sign-in-btn:focus,
.user-btn:focus {
  outline: none;
}

.user-btn {
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary-color, #409eff);
  border: 1px solid rgba(64, 158, 255, 0.3);
}

.user-btn:hover {
  background: rgba(64, 158, 255, 0.2);
  border-color: rgba(64, 158, 255, 0.5);
}

/* Second Header Sections */
.header-second-center-container {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  height: 100%;
}

.header-second-right {
  display: flex;
  align-items: center;
  margin-left: auto;
  margin-right: 20px;
  padding-right: 8px;
}

/* Icon Button Styles */
.icon-btn {
  padding: 5px;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 6px;
  color: var(--text-primary, #ccc);
}

.delete-btn.disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

.delete-btn:not(.disabled):hover {
  background: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
}

.settings-btn {
  margin-right: 12px;
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.icon-btn:active {
  transform: translateY(0);
}

/* Run and Stop button styling */
.run-btn {
  /* background: var(--accent-color, #28a745); */
  color: white;
}

.run-btn:hover {
  /* background: var(--accent-hover, #218838); */
}

.stop-btn {
  background: var(--danger-color, #6c757d);
  color: white;
}

.stop-btn:hover {
  background: var(--danger-hover, #adb5bd);
}

.save-btn {
  color: var(--text-primary, #ccc);
}

.save-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* Theme-specific adjustments */
[data-theme="light"] .header-first,
[data-theme="light"] .header-second {
  background: #f3f3f3;
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .nav__item-button,
[data-theme="light"] .icon-btn,
[data-theme="light"] .sign-in-btn {
  color: #333;
}

[data-theme="light"] .nav__item-button:hover,
[data-theme="light"] .icon-btn:hover,
[data-theme="light"] .sign-in-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .nav__dropdown {
  background: #ffffff;
  border-color: #e0e0e0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

[data-theme="light"] .nav__dropdown-item button {
  color: #333;
}

[data-theme="light"] .nav__dropdown-item button:hover {
  background: #e8e8e8;
}

/* Light mode specific run/stop button fixes */
[data-theme="light"] .run-btn {
  background: #28a745;
  color: white;
  border: 1px solid #239a3b;
}

[data-theme="light"] .run-btn:hover {
  background: #239a3b;
  box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);
}

[data-theme="light"] .stop-btn {
  background: #dc3545;
  color: white;
  border: 1px solid #c82333;
}

[data-theme="light"] .stop-btn:hover {
  background: #c82333;
  box-shadow: 0 2px 4px rgba(220, 53, 69, 0.2);
}

[data-theme="light"] .save-btn {
  color: #333;
}

[data-theme="light"] .save-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}
</style>