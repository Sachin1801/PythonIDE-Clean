<template>
  <transition name="modal-fade">
    <div v-if="modelValue" class="find-replace-overlay" @click.self="close">
      <div class="find-replace-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ isReplaceMode ? 'Find and Replace' : 'Find' }}</h3>
          <button class="close-btn" @click="close" title="Close (Esc)">
            <X :size="18" />
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Find Input -->
          <div class="input-group">
            <label>Find:</label>
            <input 
              ref="findInput"
              v-model="findText" 
              type="text" 
              class="modal-input"
              placeholder="Enter text to find..."
              @keydown.enter="findNext"
              @keydown.escape="close"
            />
          </div>
          
          <!-- Replace Input (only in replace mode) -->
          <div v-if="isReplaceMode" class="input-group">
            <label>Replace with:</label>
            <input 
              v-model="replaceText" 
              type="text" 
              class="modal-input"
              placeholder="Enter replacement text..."
              @keydown.enter="replace"
              @keydown.escape="close"
            />
          </div>
          
          <!-- Options -->
          <div class="options-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="caseSensitive" />
              <span>Case sensitive</span>
            </label>
            <label class="checkbox-label">
              <input type="checkbox" v-model="wholeWord" />
              <span>Whole word</span>
            </label>
            <label class="checkbox-label">
              <input type="checkbox" v-model="useRegex" />
              <span>Regular expression</span>
            </label>
          </div>
          
          <!-- Search Info -->
          <div v-if="searchInfo" class="search-info">
            {{ searchInfo }}
          </div>
        </div>
        
        <div class="modal-footer">
          <div class="button-group">
            <!-- Find buttons -->
            <button class="action-btn" @click="findPrevious" :disabled="!findText">
              <ChevronUp :size="16" />
              Find Previous
            </button>
            <button class="action-btn primary" @click="findNext" :disabled="!findText">
              <ChevronDown :size="16" />
              Find Next
            </button>
            
            <!-- Replace buttons (only in replace mode) -->
            <template v-if="isReplaceMode">
              <button class="action-btn" @click="replace" :disabled="!findText">
                Replace
              </button>
              <button class="action-btn" @click="replaceAll" :disabled="!findText">
                Replace All
              </button>
            </template>
            
            <!-- Close button -->
            <button class="action-btn" @click="close">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { X, ChevronUp, ChevronDown } from 'lucide-vue-next';

export default {
  name: 'FindReplaceModal',
  components: {
    X,
    ChevronUp,
    ChevronDown
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    mode: {
      type: String,
      default: 'find', // 'find' or 'replace'
      validator: value => ['find', 'replace'].includes(value)
    }
  },
  data() {
    return {
      findText: '',
      replaceText: '',
      caseSensitive: false,
      wholeWord: false,
      useRegex: false,
      searchInfo: '',
      currentMatch: 0,
      totalMatches: 0,
      searchCursor: null
    };
  },
  computed: {
    isReplaceMode() {
      return this.mode === 'replace';
    },
    activeEditor() {
      // Get the active CodeMirror instance
      const activeEditorElement = document.querySelector('.editor-content .code-editor-flex .CodeMirror');
      if (activeEditorElement && activeEditorElement.CodeMirror) {
        return activeEditorElement.CodeMirror;
      }
      return null;
    }
  },
  watch: {
    modelValue(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          this.$refs.findInput?.focus();
          this.initializeSearch();
        });
      } else {
        this.clearSearch();
      }
    },
    findText() {
      if (this.findText) {
        this.updateSearchInfo();
      } else {
        this.searchInfo = '';
        this.clearSearch();
      }
    }
  },
  methods: {
    initializeSearch() {
      if (this.activeEditor) {
        // Get selected text if any
        const selection = this.activeEditor.getSelection();
        if (selection) {
          this.findText = selection;
        }
      }
    },
    clearSearch() {
      if (this.activeEditor) {
        // Clear any existing search highlights
        this.activeEditor.operation(() => {
          const marks = this.activeEditor.getAllMarks();
          marks.forEach(mark => {
            if (mark.className === 'CodeMirror-search-match') {
              mark.clear();
            }
          });
        });
      }
      this.searchCursor = null;
      this.currentMatch = 0;
      this.totalMatches = 0;
      this.searchInfo = '';
    },
    getSearchQuery() {
      let query = this.findText;
      
      if (!this.useRegex) {
        // Escape regex special characters if not using regex
        query = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      }
      
      if (this.wholeWord) {
        query = '\\b' + query + '\\b';
      }
      
      try {
        return new RegExp(query, this.caseSensitive ? 'g' : 'gi');
      } catch (e) {
        // Invalid regex, return as string
        return this.findText;
      }
    },
    findNext() {
      if (!this.findText || !this.activeEditor) return;
      
      const query = this.getSearchQuery();
      const cursor = this.activeEditor.getSearchCursor(
        query,
        this.activeEditor.getCursor(),
        !this.caseSensitive
      );
      
      if (cursor.findNext()) {
        this.activeEditor.setSelection(cursor.from(), cursor.to());
        this.activeEditor.scrollIntoView(cursor.from(), 50);
        this.highlightMatch(cursor);
      } else {
        // Wrap to beginning
        const wrapCursor = this.activeEditor.getSearchCursor(
          query,
          { line: 0, ch: 0 },
          !this.caseSensitive
        );
        if (wrapCursor.findNext()) {
          this.activeEditor.setSelection(wrapCursor.from(), wrapCursor.to());
          this.activeEditor.scrollIntoView(wrapCursor.from(), 50);
          this.highlightMatch(wrapCursor);
          this.searchInfo = 'Wrapped to beginning';
        } else {
          this.searchInfo = 'No matches found';
        }
      }
      
      this.updateSearchInfo();
    },
    findPrevious() {
      if (!this.findText || !this.activeEditor) return;
      
      const query = this.getSearchQuery();
      const cursor = this.activeEditor.getSearchCursor(
        query,
        this.activeEditor.getCursor('from'),
        !this.caseSensitive
      );
      
      if (cursor.findPrevious()) {
        this.activeEditor.setSelection(cursor.from(), cursor.to());
        this.activeEditor.scrollIntoView(cursor.from(), 50);
        this.highlightMatch(cursor);
      } else {
        // Wrap to end
        const lastLine = this.activeEditor.lastLine();
        const lastCh = this.activeEditor.getLine(lastLine).length;
        const wrapCursor = this.activeEditor.getSearchCursor(
          query,
          { line: lastLine, ch: lastCh },
          !this.caseSensitive
        );
        if (wrapCursor.findPrevious()) {
          this.activeEditor.setSelection(wrapCursor.from(), wrapCursor.to());
          this.activeEditor.scrollIntoView(wrapCursor.from(), 50);
          this.highlightMatch(wrapCursor);
          this.searchInfo = 'Wrapped to end';
        } else {
          this.searchInfo = 'No matches found';
        }
      }
      
      this.updateSearchInfo();
    },
    replace() {
      if (!this.findText || !this.activeEditor) return;
      
      const selection = this.activeEditor.getSelection();
      const query = this.getSearchQuery();
      
      // Check if current selection matches the search
      if (selection && (
        (typeof query === 'string' && selection === query) ||
        (query instanceof RegExp && query.test(selection))
      )) {
        // Replace current selection
        this.activeEditor.replaceSelection(this.replaceText);
        this.findNext();
      } else {
        // Find next and then replace
        this.findNext();
      }
    },
    replaceAll() {
      if (!this.findText || !this.activeEditor) return;
      
      const query = this.getSearchQuery();
      const cursor = this.activeEditor.getSearchCursor(
        query,
        { line: 0, ch: 0 },
        !this.caseSensitive
      );
      
      let count = 0;
      this.activeEditor.operation(() => {
        while (cursor.findNext()) {
          cursor.replace(this.replaceText);
          count++;
        }
      });
      
      this.searchInfo = `Replaced ${count} occurrence${count !== 1 ? 's' : ''}`;
    },
    highlightMatch(cursor) {
      // Optional: Add visual highlight to the current match
      // This is handled by CodeMirror's selection
    },
    updateSearchInfo() {
      if (!this.findText || !this.activeEditor) {
        this.searchInfo = '';
        return;
      }
      
      // Count total matches
      const query = this.getSearchQuery();
      const cursor = this.activeEditor.getSearchCursor(
        query,
        { line: 0, ch: 0 },
        !this.caseSensitive
      );
      
      let count = 0;
      while (cursor.findNext()) {
        count++;
      }
      
      if (count === 0) {
        this.searchInfo = 'No matches found';
      } else if (count === 1) {
        this.searchInfo = '1 match found';
      } else {
        this.searchInfo = `${count} matches found`;
      }
    },
    close() {
      this.clearSearch();
      this.$emit('update:modelValue', false);
    },
    handleKeydown(e) {
      if (e.key === 'Escape') {
        this.close();
      } else if (e.key === 'F3' || (e.ctrlKey && e.key === 'g')) {
        e.preventDefault();
        if (e.shiftKey) {
          this.findPrevious();
        } else {
          this.findNext();
        }
      }
    }
  },
  mounted() {
    document.addEventListener('keydown', this.handleKeydown);
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown);
    this.clearSearch();
  }
};
</script>

<style scoped>
.find-replace-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 100px;
  z-index: 10000;
}

.find-replace-modal {
  background: var(--bg-secondary, #2d2d30);
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  border: 1px solid var(--border-color, #464647);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #3e3e42);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
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
  padding: 20px;
}

.input-group {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-group label {
  min-width: 100px;
  font-size: 14px;
  color: var(--text-primary, #cccccc);
}

.modal-input {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  color: var(--text-primary, #cccccc);
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  outline: none;
  transition: border-color 0.2s;
}

.modal-input:focus {
  border-color: var(--accent-color, #007ACC);
}

.modal-input::placeholder {
  color: var(--text-secondary, #808080);
}

.options-group {
  display: flex;
  gap: 20px;
  margin: 20px 0;
  padding: 12px 0;
  border-top: 1px solid var(--border-color, #3e3e42);
  border-bottom: 1px solid var(--border-color, #3e3e42);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-primary, #cccccc);
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.search-info {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--bg-primary, #1e1e1e);
  border-radius: 4px;
  font-size: 13px;
  color: var(--text-secondary, #969696);
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, #3e3e42);
  background: var(--bg-tertiary, #252526);
  border-radius: 0 0 8px 8px;
}

.button-group {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.action-btn {
  padding: 6px 16px;
  background: var(--bg-secondary, #3c3c3c);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  color: var(--text-primary, #cccccc);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.action-btn:hover:not(:disabled) {
  background: var(--bg-hover, #4a4a4a);
  border-color: var(--accent-color, #007ACC);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.primary {
  background: var(--accent-color, #007ACC);
  border-color: var(--accent-color, #007ACC);
  color: white;
}

.action-btn.primary:hover:not(:disabled) {
  background: var(--accent-hover, #0062a3);
}

/* Modal transition */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .find-replace-modal,
.modal-fade-leave-active .find-replace-modal {
  transition: transform 0.2s;
}

.modal-fade-enter-from .find-replace-modal {
  transform: translateY(-20px);
}

.modal-fade-leave-to .find-replace-modal {
  transform: translateY(-20px);
}

/* Light theme */
[data-theme="light"] .find-replace-modal {
  background: #ffffff;
  border-color: #e0e0e0;
}

[data-theme="light"] .modal-header {
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .modal-header h3,
[data-theme="light"] .close-btn,
[data-theme="light"] .input-group label,
[data-theme="light"] .checkbox-label,
[data-theme="light"] .action-btn {
  color: #333333;
}

[data-theme="light"] .close-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .modal-input {
  background: #f5f5f5;
  border-color: #d0d0d0;
  color: #333333;
}

[data-theme="light"] .modal-input:focus {
  border-color: #007ACC;
}

[data-theme="light"] .options-group {
  border-color: #e0e0e0;
}

[data-theme="light"] .search-info {
  background: #f5f5f5;
  color: #666666;
}

[data-theme="light"] .modal-footer {
  background: #f8f8f8;
  border-top-color: #e0e0e0;
}

[data-theme="light"] .action-btn {
  background: #f0f0f0;
  border-color: #d0d0d0;
}

[data-theme="light"] .action-btn:hover:not(:disabled) {
  background: #e0e0e0;
  border-color: #007ACC;
}
</style>