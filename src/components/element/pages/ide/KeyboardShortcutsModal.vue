<template>
  <transition name="modal-fade">
    <div v-if="modelValue" class="modal-overlay" @click.self="close">
      <div class="modal-container">
        <div class="modal-header">
          <h2>Keyboard Shortcuts {{ isMac ? '(Mac)' : '(Windows/Linux)' }}</h2>
          <button class="close-btn" @click="close">
            <X :size="20" />
          </button>
        </div>
        
        <div class="modal-body">
          <!-- File Operations -->
          <div class="shortcut-section">
            <h3>File Operations</h3>
            <div class="shortcut-list">
              <div class="shortcut-item">
                <span class="shortcut-action">New File</span>
                <span class="shortcut-keys">Ctrl+Alt+N</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Open File</span>
                <span class="shortcut-keys">Ctrl+O</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Save</span>
                <span class="shortcut-keys">Ctrl+S</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Save As</span>
                <span class="shortcut-keys">Ctrl+Shift+S</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Move</span>
                <span class="shortcut-keys">Ctrl+Shift+M</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Download</span>
                <span class="shortcut-keys">Ctrl+D</span>
              </div>
            </div>
          </div>

          <!-- Edit Operations -->
          <div class="shortcut-section">
            <h3>Edit Operations</h3>
            <div class="shortcut-list">
              <div class="shortcut-item">
                <span class="shortcut-action">Undo</span>
                <span class="shortcut-keys">Ctrl+Z</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Redo</span>
                <span class="shortcut-keys">Ctrl+Y</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Cut</span>
                <span class="shortcut-keys">Ctrl+X</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Copy</span>
                <span class="shortcut-keys">Ctrl+C</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Paste</span>
                <span class="shortcut-keys">Ctrl+V</span>
              </div>
              <!-- TEMPORARILY DISABLED FOR FILE HANDLING ASSIGNMENT -->
              <!-- <div class="shortcut-item">
                <span class="shortcut-action">Find</span>
                <span class="shortcut-keys">Ctrl+F</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Replace</span>
                <span class="shortcut-keys">Ctrl+H</span>
              </div> -->
              <!-- <div class="shortcut-item">
                <span class="shortcut-action">Comment/Uncomment</span>
                <span class="shortcut-keys">Ctrl+/</span>
              </div> -->
              <div class="shortcut-item">
                <span class="shortcut-action">Select All</span>
                <span class="shortcut-keys">Ctrl+A</span>
              </div>
            </div>
          </div>

          <!-- Run Operations -->
          <div class="shortcut-section">
            <h3>Run Operations</h3>
            <div class="shortcut-list">
              <div class="shortcut-item">
                <span class="shortcut-action">Run Script</span>
                <span class="shortcut-keys">F5</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Stop Script</span>
                <span class="shortcut-keys">Shift+F5</span>
              </div>
            </div>
          </div>

          <!-- View Operations -->
          <div class="shortcut-section">
            <h3>View Operations</h3>
            <div class="shortcut-list">
              <div class="shortcut-item">
                <span class="shortcut-action">Toggle Console</span>
                <span class="shortcut-keys">Ctrl+`</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Toggle Preview Panel</span>
                <span class="shortcut-keys">Ctrl+Shift+P</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Toggle Sidebar</span>
                <span class="shortcut-keys">Ctrl+B</span>
              </div>
            </div>
          </div>

          <!-- Tab Navigation -->
          <div class="shortcut-section">
            <h3>Tab Navigation</h3>
            <div class="shortcut-list">
              <div class="shortcut-item">
                <span class="shortcut-action">Previous Tab</span>
                <span class="shortcut-keys">{{ formatKey('Alt') }}+←</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Next Tab</span>
                <span class="shortcut-keys">{{ formatKey('Alt') }}+→</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Go to Tab 1-6</span>
                <span class="shortcut-keys">{{ formatKey('Alt') }}+1-6</span>
              </div>
            </div>
          </div>

          <!-- General -->
          <div class="shortcut-section">
            <h3>General</h3>
            <div class="shortcut-list">
              <div class="shortcut-item">
                <span class="shortcut-action">Show Keyboard Shortcuts</span>
                <span class="shortcut-keys">F1</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Settings</span>
                <span class="shortcut-keys">Ctrl+,</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { X } from 'lucide-vue-next';

export default {
  name: 'KeyboardShortcutsModal',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  components: {
    X
  },
  computed: {
    isMac() {
      return navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    }
  },
  methods: {
    close() {
      this.$emit('update:modelValue', false);
    },
    formatKey(key) {
      if (this.isMac) {
        // Convert to Mac symbols
        return key
          .replace('Ctrl', '⌘')
          .replace('Alt', '⌥')
          .replace('Shift', '⇧');
      }
      return key;
    }
  },
  mounted() {
    // Add escape key handler
    this.handleEsc = (e) => {
      if (e.key === 'Escape' && this.modelValue) {
        this.close();
      }
    };
    document.addEventListener('keydown', this.handleEsc);
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleEsc);
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.modal-container {
  background: var(--bg-secondary, #2d2d30);
  border-radius: 8px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color, #3e3e42);
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary, #cccccc);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-primary, #cccccc);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.shortcut-section {
  margin-bottom: 30px;
}

.shortcut-section h3 {
  font-size: 14px;
  color: var(--text-primary, #cccccc);
  margin-bottom: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcut-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  background: var(--bg-primary, #1e1e1e);
}

.shortcut-action {
  color: var(--text-primary, #cccccc);
  font-size: 13px;
}

.shortcut-keys {
  color: var(--text-secondary, #969696);
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: var(--bg-tertiary, #383838);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-color, #464647);
}

/* Scrollbar styling */
.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: var(--bg-primary, #1e1e1e);
}

.modal-body::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb, #4a4a4a);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover, #5a5a5a);
}

/* Modal transition */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* Light theme adjustments */
[data-theme="light"] .modal-container {
  background: #ffffff;
}

[data-theme="light"] .modal-header {
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .modal-header h2,
[data-theme="light"] .close-btn,
[data-theme="light"] .shortcut-section h3,
[data-theme="light"] .shortcut-action {
  color: #333333;
}

[data-theme="light"] .close-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .shortcut-item {
  background: #f5f5f5;
}

[data-theme="light"] .shortcut-keys {
  color: #666666;
  background: #e8e8e8;
  border-color: #d0d0d0;
}

[data-theme="light"] .modal-body::-webkit-scrollbar-track {
  background: #f5f5f5;
}

[data-theme="light"] .modal-body::-webkit-scrollbar-thumb {
  background: #c0c0c0;
}

[data-theme="light"] .modal-body::-webkit-scrollbar-thumb:hover {
  background: #a0a0a0;
}
</style>