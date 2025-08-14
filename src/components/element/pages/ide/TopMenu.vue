<template>
  <div class="top-menu-container">
    <!-- Left Section: File Dropdown Only -->
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
                New
                <span class="nav__keyboard-shortcut">Ctrl+N</span>
              </button>
            </li>
            <li class="nav__dropdown-item">
              <button @click="saveFile()">
                Save
                <span class="nav__keyboard-shortcut">Ctrl+S</span>
              </button>
            </li>
            <li class="nav__dropdown-item nav__dropdown-item--disabled">
              <button disabled>Share</button>
            </li>
            <li class="nav__dropdown-item">
              <button @click="downloadFile()">Download</button>
            </li>
            <li class="nav__dropdown-item">
              <button @click="addFile()">
                Add File
              </button>
            </li>
            <li class="nav__dropdown-item">
              <button @click="addFolder()">
                Add Folder
              </button>
            </li>
          </ul>
        </li>
      </ul>
    </nav>

    <!-- Center Section: Run/Stop (Exactly Centered) -->
    <div class="header-center-absolute">
      <div class="icon-btn run-btn" v-if="!hasRunProgram" @click="runScript()" title="Run (F5)">
        <Play :size="20" />
      </div>
      <div class="icon-btn stop-btn" @click="stopScript()" v-if="hasRunProgram" title="Stop (Shift+F5)">
        <Square :size="20" />
      </div>
    </div>

    <!-- Right Section: Upload and Settings -->
    <div class="header-right">
      <div class="icon-btn" @click="openUploadDialog()" title="Import File">
        <Upload :size="20" />
      </div>
      <div class="icon-btn settings-btn" @click="openSettings()" title="Settings">
        <Settings :size="20" />
      </div>
    </div>
  </div>
</template>

<script>
import { Upload, Play, Square, Terminal, Settings } from 'lucide-vue-next';

export default {
  props: {
    consoleLimit: Boolean,
    hasRunProgram: Boolean,
  },
  data() {
    return {
      isRun: true,
      activeDropdown: null,
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
  },
  components: {
    Upload,
    Play,
    Square,
    Terminal,
    Settings,
  },
  mounted() {
    // Initialize theme on mount
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Add click outside listener for dropdowns
    document.addEventListener('click', this.closeDropdowns);
    
    // Add keyboard shortcuts
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
      // Ctrl+S - Save
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        this.saveFile();
      }
      // Ctrl+N - New File
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        this.newFile();
      }
      // F5 - Run
      if (e.key === 'F5' && !e.shiftKey && this.isPythonFile && !this.consoleLimit) {
        e.preventDefault();
        this.runScript();
      }
      // Shift+F5 - Stop
      if (e.shiftKey && e.key === 'F5' && this.hasRunProgram) {
        e.preventDefault();
        this.stopScript();
      }
    },
    newFile() {
      this.closeDropdowns();
      if (!this.ideInfo.nodeSelected || (this.ideInfo.nodeSelected.type !== 'dir' && this.ideInfo.nodeSelected.type !== 'folder')) {
        // Select root folder if no folder is selected
        const rootFolder = this.ideInfo.currProj?.fileTree?.[0];
        if (rootFolder) {
          this.$store.commit('ide/setNodeSelected', rootFolder);
        }
      }
      this.$emit('set-text-dialog', {
        type: 'file',
        title: 'New File',
        tips: 'Enter file name:',
        text: 'untitled.py'
      });
    },
    addFile() {
      this.newFile();
    },
    addFolder() {
      this.closeDropdowns();
      if (!this.ideInfo.nodeSelected || (this.ideInfo.nodeSelected.type !== 'dir' && this.ideInfo.nodeSelected.type !== 'folder')) {
        const rootFolder = this.ideInfo.currProj?.fileTree?.[0];
        if (rootFolder) {
          this.$store.commit('ide/setNodeSelected', rootFolder);
        }
      }
      this.$emit('set-text-dialog', {
        type: 'folder',
        title: 'New Folder',
        tips: 'Enter folder name:',
        text: 'new_folder'
      });
    },
    saveFile() {
      this.closeDropdowns();
      if (this.ideInfo.codeSelected) {
        this.$store.dispatch('ide/saveFile', this.ideInfo.codeSelected);
        this.$message.success('File saved');
      }
    },
    downloadFile() {
      this.closeDropdowns();
      if (!this.ideInfo.nodeSelected || this.ideInfo.nodeSelected.type !== 'file') {
        if (this.ideInfo.codeSelected) {
          this.$emit('download-file', this.ideInfo.codeSelected);
        } else {
          this.$message.warning('Please select a file to download');
        }
      } else {
        this.$emit('download-file');
      }
    },
    openUploadDialog() {
      this.closeDropdowns();
      this.$emit('open-upload-dialog');
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
    openREPL() {
      this.$emit('open-repl');
    },
    openSettings() {
      this.$emit('open-settings');
    },
  },
};
</script>

<style scoped>
.top-menu-container {
  width: 100%;
  height: 50px;
  background: var(--header-bg, #313131);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
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
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  border-radius: 4px;
  transition: background 0.2s;
}

.nav__item-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav__item-header {
  font-weight: 400;
}

.nav__item-triangle {
  opacity: 0.6;
  width: 9px;
  height: 6px;
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

.nav__dropdown-item button,
.nav__dropdown-item a {
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

.nav__dropdown-item button:hover,
.nav__dropdown-item a:hover {
  background: var(--hover-bg, #094771);
}

.nav__dropdown-item--disabled button {
  color: var(--text-tertiary, #666);
  cursor: not-allowed;
  opacity: 0.5;
}

.nav__dropdown-item--disabled button:hover {
  background: transparent;
}

.nav__keyboard-shortcut {
  font-size: 11px;
  opacity: 0.6;
  margin-left: 24px;
  font-family: monospace;
}

/* Header Sections */
.header-center-absolute {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.settings-btn {
  margin-right: 12px;
}

/* Run and Stop button styling */
.run-btn {
  background: var(--accent-color, #28a745);
  color: white;
}

.run-btn:hover {
  background: var(--accent-hover, #218838);
}

.stop-btn {
  background: var(--danger-color, #dc3545);
  color: white;
}

.stop-btn:hover {
  background: var(--danger-hover, #c82333);
}

/* Icon Button Styles */
.icon-btn {
  padding: 8px;
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 6px;
  color: var(--text-primary, #ccc);
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.icon-btn:active {
  transform: translateY(0);
}

/* Theme-specific adjustments */
[data-theme="light"] .top-menu-container {
  background: #f3f3f3;
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .nav__item-button,
[data-theme="light"] .icon-btn {
  color: #333;
}

[data-theme="light"] .nav__item-button:hover,
[data-theme="light"] .icon-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .nav__dropdown {
  background: #ffffff;
  border-color: #e0e0e0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

[data-theme="light"] .nav__dropdown-item button,
[data-theme="light"] .nav__dropdown-item a {
  color: #333;
}

[data-theme="light"] .nav__dropdown-item button:hover,
[data-theme="light"] .nav__dropdown-item a:hover {
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
  transform: translateY(-1px);
}

[data-theme="light"] .stop-btn {
  background: #dc3545;
  color: white;
  border: 1px solid #c82333;
}

[data-theme="light"] .stop-btn:hover {
  background: #c82333;
  box-shadow: 0 2px 4px rgba(220, 53, 69, 0.2);
  transform: translateY(-1px);
}
</style>