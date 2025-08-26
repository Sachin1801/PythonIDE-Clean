// PythonREPL.vue - Vue Component with Consistent HTML Structure
// This ensures ALL entries (first and subsequent) use the same HTML structure

export default {
  name: 'PythonREPL',
  
  data() {
    return {
      history: [],
      currentInput: '',
      multilineBuffer: [],
      isMultiline: false,
      executing: false,
      codeMirror: null,
      sessionId: null,
      entryIdCounter: 0
    };
  },
  
  computed: {
    currentPrompt() {
      return this.isMultiline ? '...' : '>>>';
    }
  },
  
  mounted() {
    this.initializeCodeMirror();
    this.initializeSession();
  },
  
  methods: {
    /**
     * Initialize CodeMirror for the input area
     */
    initializeCodeMirror() {
      const textarea = this.$refs.codeInput;
      
      this.codeMirror = CodeMirror.fromTextArea(textarea, {
        mode: 'python',
        theme: 'monokai',
        lineNumbers: false,
        lineWrapping: true,
        autoCloseBrackets: true,
        indentUnit: 4,
        indentWithTabs: false,
        extraKeys: {
          'Shift-Enter': () => this.executeCode(),
          'Tab': (cm) => {
            if (cm.somethingSelected()) {
              cm.indentSelection('add');
            } else {
              cm.replaceSelection('    ', 'end');
            }
          }
        }
      });
      
      // Focus on mount
      this.codeMirror.focus();
    },
    
    /**
     * Initialize Python session on backend
     */
    async initializeSession() {
      try {
        const response = await fetch('/api/repl/session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        this.sessionId = data.sessionId;
      } catch (error) {
        console.error('Failed to initialize session:', error);
      }
    },
    
    /**
     * CRITICAL: Create consistent entry structure
     * This method ensures ALL entries have the same HTML structure
     */
    createHistoryEntry(inputLines, output = null, error = null) {
      const entry = {
        id: ++this.entryIdCounter,
        type: 'execution',
        timestamp: new Date().toISOString(),
        
        // Input is always an array of lines
        input: Array.isArray(inputLines) ? inputLines : [inputLines],
        
        // Output and error are strings or null
        output: output,
        error: error,
        
        // Status flags
        loading: false,
        incomplete: false
      };
      
      return entry;
    },
    
    /**
     * Apply syntax highlighting to Python code
     * Uses Prism.js or custom highlighting
     */
    highlightPythonCode(code) {
      // If using Prism.js
      if (typeof Prism !== 'undefined' && Prism.languages.python) {
        return Prism.highlight(code, Prism.languages.python, 'python');
      }
      
      // Fallback: Simple regex-based highlighting
      return this.simpleHighlight(code);
    },
    
    /**
     * Simple syntax highlighting fallback
     */
    simpleHighlight(code) {
      let highlighted = this.escapeHtml(code);
      
      // Keywords
      const keywords = [
        'def', 'class', 'if', 'elif', 'else', 'try', 'except', 'finally',
        'for', 'while', 'with', 'as', 'import', 'from', 'return', 'yield',
        'lambda', 'pass', 'break', 'continue', 'raise', 'assert', 'del',
        'and', 'or', 'not', 'in', 'is', 'None', 'True', 'False'
      ];
      
      const keywordRegex = new RegExp(`\\b(${keywords.join('|')})\\b`, 'g');
      highlighted = highlighted.replace(keywordRegex, '<span class="keyword">$1</span>');
      
      // Strings (simple version)
      highlighted = highlighted.replace(/(["'])((?:\\.|(?!\1).)*?)\1/g, 
        '<span class="string">$1$2$1</span>');
      
      // Numbers
      highlighted = highlighted.replace(/\b(\d+\.?\d*)\b/g, 
        '<span class="number">$1</span>');
      
      // Comments
      highlighted = highlighted.replace(/(#.*$)/gm, 
        '<span class="comment">$1</span>');
      
      // Built-in functions
      const builtins = ['print', 'input', 'range', 'len', 'str', 'int', 
                        'float', 'list', 'dict', 'set', 'tuple', 'type'];
      const builtinRegex = new RegExp(`\\b(${builtins.join('|')})\\b`, 'g');
      highlighted = highlighted.replace(builtinRegex, '<span class="builtin">$1</span>');
      
      return highlighted;
    },
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
      const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      };
      return text.replace(/[&<>"']/g, m => map[m]);
    },
    
    /**
     * Format Python error messages
     */
    formatError(error) {
      if (!error) return '';
      
      let formatted = this.escapeHtml(error);
      
      // Highlight error types
      formatted = formatted.replace(
        /(SyntaxError|NameError|TypeError|ValueError|IndentationError|AttributeError|KeyError|IndexError|ZeroDivisionError):/g,
        '<span class="error-type">$1:</span>'
      );
      
      // Highlight line numbers
      formatted = formatted.replace(
        /line (\d+)/g,
        'line <span class="error-line-number">$1</span>'
      );
      
      // Highlight file references
      formatted = formatted.replace(
        /File "(.*?)", /g,
        'File "<span class="error-file">$1</span>", '
      );
      
      // Format the caret pointer for syntax errors
      formatted = formatted.replace(
        /^(\s*\^+\s*)$/gm,
        '<span class="error-pointer">$1</span>'
      );
      
      return formatted;
    },
    
    /**
     * Execute Python code
     */
    async executeCode() {
      if (this.executing) return;
      
      const code = this.codeMirror.getValue().trim();
      if (!code) return;
      
      // Update multiline buffer
      if (this.isMultiline) {
        this.multilineBuffer.push(code);
      } else {
        this.multilineBuffer = [code];
      }
      
      // Create and add entry with consistent structure
      const entry = this.createHistoryEntry(
        this.multilineBuffer.slice(), // Copy the array
        null,
        null
      );
      entry.loading = true;
      
      this.history.push(entry);
      this.executing = true;
      
      // Clear CodeMirror
      this.codeMirror.setValue('');
      
      // Scroll to bottom
      this.$nextTick(() => this.scrollToBottom());
      
      try {
        // Call backend API
        const response = await this.callPythonBackend(
          this.multilineBuffer.join('\n')
        );
        
        // Update entry based on response
        entry.loading = false;
        
        if (response.error) {
          entry.error = response.error;
          this.resetMultiline();
        } else if (response.incomplete) {
          entry.incomplete = true;
          this.isMultiline = true;
          // Don't clear buffer, continue adding lines
        } else {
          entry.output = response.output || '';
          this.resetMultiline();
        }
        
      } catch (error) {
        entry.loading = false;
        entry.error = `Error: ${error.message}`;
        this.resetMultiline();
      } finally {
        this.executing = false;
        this.$nextTick(() => this.scrollToBottom());
      }
    },
    
    /**
     * Call Python backend API
     */
    async callPythonBackend(code) {
      const response = await fetch('/api/repl/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: code,
          sessionId: this.sessionId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    },
    
    /**
     * Reset multiline state
     */
    resetMultiline() {
      this.isMultiline = false;
      this.multilineBuffer = [];
    },
    
    /**
     * Scroll history to bottom
     */
    scrollToBottom() {
      const container = this.$refs.historyContainer;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    },
    
    /**
     * Clear history
     */
    clearHistory() {
      this.history = [];
      this.resetMultiline();
      this.codeMirror.setValue('');
      this.codeMirror.focus();
    }
  },
  
  template: `
    <div class="repl-wrapper">
      <!-- History Display -->
      <div class="repl-history" ref="historyContainer">
        <!-- CONSISTENT STRUCTURE FOR ALL ENTRIES -->
        <div v-for="entry in history" :key="entry.id" class="repl-entry">
          
          <!-- Input Lines (Always rendered the same way) -->
          <div class="repl-input-block">
            <div v-for="(line, index) in entry.input" 
                 :key="'input-' + entry.id + '-' + index" 
                 class="repl-line">
              <span class="repl-prompt" :class="{ secondary: index > 0 }">
                {{ index === 0 ? '>>>' : '...' }}
              </span>
              <span class="repl-code" v-html="highlightPythonCode(line)"></span>
            </div>
          </div>
          
          <!-- Output (if any) -->
          <div v-if="entry.output !== null && entry.output !== ''" 
               class="repl-output">{{ entry.output }}</div>
          
          <!-- Error (if any) -->
          <div v-if="entry.error" 
               class="repl-error" 
               v-html="formatError(entry.error)"></div>
          
          <!-- Loading indicator -->
          <div v-if="entry.loading" class="repl-loading">
            Executing...
          </div>
        </div>
      </div>
      
      <!-- Input Area -->
      <div class="repl-input-area">
        <div class="input-container">
          <span class="input-prompt">{{ currentPrompt }}</span>
          <textarea ref="codeInput" class="code-input"></textarea>
        </div>
        
        <div class="repl-controls">
          <button @click="executeCode" 
                  :disabled="executing"
                  class="execute-btn">
            {{ executing ? 'Running...' : 'Run (Shift+Enter)' }}
          </button>
          
          <button @click="clearHistory" 
                  class="clear-btn">
            Clear
          </button>
        </div>
      </div>
    </div>
  `
};