<template>
  <div class="hybrid-console">
    <!-- Console Output Area -->
    <div class="console-output" ref="consoleOutput">
      <div v-for="(line, index) in outputLines" :key="index" class="output-line">
        <!-- Regular text output -->
        <pre v-if="line.type === 'text'" :class="['output-text', line.class]">{{ line.content }}</pre>
        
        <!-- Error output -->
        <pre v-else-if="line.type === 'error'" class="output-text error-output">{{ line.content }}</pre>
        
        <!-- System messages -->
        <pre v-else-if="line.type === 'system'" class="output-text system-message">{{ line.content }}</pre>
        
        <!-- Input prompt display -->
        <div v-else-if="line.type === 'input-prompt'" class="input-prompt-line">
          <span class="prompt-indicator">🔸</span>
          <span class="prompt-text">{{ line.content }}</span>
        </div>
        
        <!-- User input echo -->
        <div v-else-if="line.type === 'user-input'" class="user-input-line">
          <span class="input-indicator">▶</span>
          <span class="input-text">{{ line.content }}</span>
        </div>
        
        <!-- REPL prompt and input -->
        <div v-else-if="line.type === 'repl-input'" class="repl-line" :class="{ 'multiline': line.multiline }">
          <span class="repl-prompt">{{ line.prompt }}</span>
          <pre class="repl-input-text" :class="{ 'multiline-content': line.multiline }">{{ line.content }}</pre>
        </div>
        
        <!-- REPL output -->
        <pre v-else-if="line.type === 'repl-output'" class="repl-output">{{ line.content }}</pre>
        
        <!-- Matplotlib figure display -->
        <div v-else-if="line.type === 'figure'" class="figure-container">
          <img :src="`data:image/png;base64,${line.data}`" alt="Matplotlib Figure" class="matplotlib-figure" />
          <div class="figure-controls">
            <button class="figure-btn" @click="downloadFigure(line.data)" title="Download">
              📥
            </button>
            <button class="figure-btn" @click="openFigureInNewTab(line.data)" title="Open in new tab">
              🔍
            </button>
          </div>
        </div>
      </div>
      
      <!-- Loading indicator when program is running (not in REPL mode) -->
      <div v-if="isRunning && !waitingForInput && !isReplMode" class="loading-indicator">
        <span class="loading-dots">●●●</span>
        <span class="loading-text">Running...</span>
      </div>
    </div>
    
    <!-- Input Area (shown when waiting for input or in REPL mode) -->
    <div v-if="waitingForInput || isReplMode" class="input-area">
      <!-- Script Input Mode -->
      <div v-if="waitingForInput && !isReplMode" class="input-prompt-display">
        <span class="prompt-icon">💬</span>
        <span class="prompt-label">{{ currentPrompt || 'Waiting for input...' }}</span>
      </div>
      
      <!-- REPL Mode Input with Syntax Highlighting -->
      <div v-if="isReplMode" class="repl-input-container">
        <span class="repl-input-prefix">{{ replPrompt }}</span>
        <div class="repl-editor-wrapper">
          <Codemirror
            v-model:value="userInput"
            :options="replCodeMirrorOptions"
            @keydown="handleKeyDown"
            ref="replEditor"
            class="repl-codemirror"
            :placeholder="'Enter Python code...'"
          />
        </div>
      </div>
      
      <!-- Regular Script Input Mode -->
      <div v-else class="input-container">
        <span class="input-prefix">▶</span>
        <textarea
          v-model="userInput"
          @keydown="handleKeyDown"
          ref="inputField"
          class="user-input-field"
          placeholder="Type your input and press Enter..."
          :rows="inputRows"
          autofocus
        />
        <button 
          class="input-btn primary" 
          @click="sendInput"
          :disabled="!userInput.trim()"
          title="Submit (Enter)"
        >
          ✓
        </button>
        <button 
          class="input-btn secondary" 
          @click="cancelInput"
          title="Cancel (Escape)"
        >
          ✕
        </button>
      </div>
      
      <div class="input-hint">
        <span v-if="isReplMode">Enter: Execute | Shift+Enter: New line | Up/Down: History</span>
        <span v-else>Press Enter to submit • Escape to cancel</span>
      </div>
    </div>
    
    <!-- Status Bar -->
    <div class="console-status">
      <div class="status-left">
        <span v-if="isReplMode" class="status-item repl">
          <span class="status-dot repl"></span>
          REPL Mode
        </span>
        <span v-else-if="isRunning" class="status-item running">
          <span class="status-dot"></span>
          Running {{ currentProgram }}
        </span>
        <span v-else-if="lastExitCode === 0" class="status-item success">
          <span class="status-dot"></span>
          Ready
        </span>
        <span v-else-if="lastExitCode !== null" class="status-item error">
          <span class="status-dot"></span>
          Exit code: {{ lastExitCode }}
        </span>
        <span v-else class="status-item idle">
          <span class="status-dot"></span>
          Idle
        </span>
      </div>
      <div class="status-right">
        <button class="status-btn" @click="clearConsole" title="Clear console">🗑️</button>
        <button class="status-btn" @click="exportOutput" title="Export output">📄</button>
        <button v-if="isRunning || isReplMode" class="status-btn danger" @click="stopProgram" title="Stop">⏹️</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
// CodeMirror for REPL syntax highlighting
import Codemirror from 'codemirror-editor-vue3'
import CodeMirror from 'codemirror'
import 'codemirror/lib/codemirror.css'
import 'codemirror/theme/darcula.css'
import 'codemirror/mode/python/python'
import 'codemirror/addon/selection/active-line'
import 'codemirror/addon/edit/matchbrackets'
import 'codemirror/addon/edit/closebrackets'
import 'codemirror/addon/edit/trailingspace'
import 'codemirror/addon/comment/comment'

export default {
  name: 'HybridConsole',
  components: {
    Codemirror
  },
  props: {
    item: {
      type: Object,
      required: true
    },
    isRunning: {
      type: Boolean,
      default: false
    }
  },
  emits: ['run-item', 'stop-item', 'send-input'],
  setup(props, { emit }) {
    // Reactive data
    const outputLines = ref([])
    const waitingForInput = ref(false)
    const currentPrompt = ref('')
    const userInput = ref('')
    const lastExitCode = ref(null)
    const currentProgram = ref('')
    const isReplMode = ref(false)
    const replPrompt = ref('>>> ')
    const commandHistory = ref([])
    const historyIndex = ref(-1)
    const inputRows = ref(1)
    
    // Refs
    const consoleOutput = ref(null)
    const inputField = ref(null)
    const replEditor = ref(null)
    
    // CodeMirror options for REPL
    const replCodeMirrorOptions = ref({
      mode: {
        name: 'python',
        version: 3,
        singleLineStringErrors: false,
      },
      theme: 'repl-theme', // Custom theme
      lineNumbers: false,
      smartIndent: true,
      indentUnit: 4,
      tabSize: 4,
      indentWithTabs: false,
      matchBrackets: true,
      autoCloseBrackets: true,
      styleActiveLine: false,
      lineWrapping: true,
      showCursorWhenSelecting: true,
      viewportMargin: Infinity,
      scrollbarStyle: null,
      autofocus: true,
      extraKeys: {
        'Enter': (cm) => {
          // Custom Enter handling for REPL
          const cursor = cm.getCursor()
          const line = cm.getLine(cursor.line)
          const allCode = cm.getValue().trim()
          
          // Multi-line detection: check if line ends with : or has indentation
          const needsContinuation = (
            line.trim().endsWith(':') || 
            line.trim().endsWith('\\') ||
            /^\s+/.test(line) ||
            allCode.split('\n').some((l, i) => i < cursor.line && l.trim().endsWith(':'))
          )
          
          if (needsContinuation || cursor.line < cm.lastLine()) {
            // Continue on new line
            const indent = line.match(/^\s*/)[0]
            const extraIndent = line.trim().endsWith(':') ? '    ' : ''
            cm.replaceSelection('\n' + indent + extraIndent)
          } else if (allCode) {
            // Execute command
            executeReplCommand()
          } else {
            cm.replaceSelection('\n')
          }
        },
        'Shift-Enter': (cm) => {
          const cursor = cm.getCursor()
          const line = cm.getLine(cursor.line)
          const indent = line.match(/^\s*/)[0]
          cm.replaceSelection('\n' + indent)
        },
        'Up': (cm) => {
          if (cm.getCursor().line === 0 && !cm.getSelection()) {
            navigateHistory('up')
          } else {
            CodeMirror.commands.goLineUp(cm)
          }
        },
        'Down': (cm) => {
          if (cm.getCursor().line === cm.lastLine() && !cm.getSelection()) {
            navigateHistory('down')
          } else {
            CodeMirror.commands.goLineDown(cm)
          }
        },
        'Tab': (cm) => {
          if (cm.getSelection()) {
            cm.indentSelection('add')
          } else {
            cm.replaceSelection(Array(cm.getOption('indentUnit') + 1).join(' '))
          }
        },
        'Shift-Tab': (cm) => {
          cm.indentSelection('subtract')
        }
      }
    })
    
    // Computed
    const currentLines = computed(() => {
      if (!userInput.value) return 1
      const lines = userInput.value.split('\n').length
      return Math.min(Math.max(lines, 1), 10)
    })
    
    // Watch for input changes to adjust textarea height
    watch(userInput, () => {
      inputRows.value = currentLines.value
    })
    
    // Methods
    const addOutput = (content, type = 'text', className = '') => {
      outputLines.value.push({
        type,
        content,
        class: className,
        timestamp: Date.now()
      })
      nextTick(() => {
        scrollToBottom()
      })
    }
    
    const addReplLine = (prompt, content, type = 'repl-input') => {
      // Enhanced multiline detection for Python constructs
      const isMultiline = (
        content.includes('\n') && content.trim() !== ''
      ) || (
        // Also detect potential multiline constructs even without newlines yet
        content.trim().match(/^(def|class|if|for|while|with|try|except|finally)\s/) &&
        content.trim().endsWith(':')
      )
      
      outputLines.value.push({
        type,
        prompt,
        content: content,
        timestamp: Date.now(),
        multiline: isMultiline // Flag for multiline content
      })
      nextTick(() => {
        scrollToBottom()
      })
    }
    
    const addFigure = (data) => {
      outputLines.value.push({
        type: 'figure',
        data,
        timestamp: Date.now()
      })
      nextTick(() => {
        scrollToBottom()
      })
    }
    
    const requestInput = (prompt) => {
      // Handle empty prompts from silent input() calls
      const displayPrompt = prompt || 'Program waiting for input:'
      currentPrompt.value = displayPrompt
      waitingForInput.value = true
      
      // Add prompt to output (only if not empty)
      if (prompt) {
        addOutput(prompt, 'input-prompt')
      } else {
        addOutput('Program waiting for input:', 'input-prompt')
      }
      
      // Focus input field
      nextTick(() => {
        if (inputField.value) {
          inputField.value.focus()
        }
      })
    }
    
    const enterReplMode = () => {
      isReplMode.value = true
      waitingForInput.value = false
      replPrompt.value = '>>> '
      userInput.value = ''
      historyIndex.value = -1
      
      // Focus REPL editor with delay for proper initialization
      nextTick(() => {
        setTimeout(() => {
          if (replEditor.value?.cminstance) {
            replEditor.value.cminstance.refresh()
            replEditor.value.cminstance.focus()
          } else if (inputField.value) {
            inputField.value.focus()
          }
        }, 100)
      })
    }
    
    const exitReplMode = () => {
      isReplMode.value = false
      replPrompt.value = '>>> '
      userInput.value = ''
      commandHistory.value = []
      historyIndex.value = -1
    }
    
    const handleKeyDown = (event) => {
      if (isReplMode.value) {
        // REPL mode key handling
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault()
          executeReplCommand()
        } else if (event.key === 'Enter' && event.shiftKey) {
          // Allow new line in REPL
          replPrompt.value = '... '
        } else if (event.key === 'ArrowUp') {
          event.preventDefault()
          navigateHistory('up')
        } else if (event.key === 'ArrowDown') {
          event.preventDefault()
          navigateHistory('down')
        }
      } else {
        // Regular input mode
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault()
          sendInput()
        } else if (event.key === 'Escape') {
          event.preventDefault()
          cancelInput()
        }
      }
    }
    
    const executeReplCommand = () => {
      const command = isReplMode.value ? 
        (replEditor.value?.cminstance?.getValue() || userInput.value) : 
        userInput.value
      
      if (!command.trim()) {
        // Empty input, just show new prompt
        addReplLine(replPrompt.value, '', 'repl-input')
        replPrompt.value = '>>> '
        return
      }
      
      // Add to history (only non-empty commands)
      if (command.trim()) {
        commandHistory.value.push(command)
        historyIndex.value = commandHistory.value.length
      }
      
      // Echo the command with proper formatting
      addReplLine(replPrompt.value, command, 'repl-input')
      
      // Send to backend
      emit('send-input', {
        programId: props.item.id,
        input: command,
        isRepl: true
      })
      
      // Clear input and reset prompt
      if (isReplMode.value && replEditor.value?.cminstance) {
        replEditor.value.cminstance.setValue('')
        // Refresh CodeMirror to ensure proper rendering
        nextTick(() => {
          replEditor.value.cminstance.refresh()
          replEditor.value.cminstance.focus()
        })
      }
      userInput.value = ''
      replPrompt.value = '>>> '
      inputRows.value = 1
    }
    
    const navigateHistory = (direction) => {
      if (commandHistory.value.length === 0) return
      
      if (direction === 'up') {
        if (historyIndex.value > 0) {
          historyIndex.value--
        } else if (historyIndex.value === -1 || historyIndex.value === commandHistory.value.length) {
          historyIndex.value = commandHistory.value.length - 1
        }
        
        const historyCommand = commandHistory.value[historyIndex.value] || ''
        if (isReplMode.value && replEditor.value?.cminstance) {
          replEditor.value.cminstance.setValue(historyCommand)
          // Move cursor to end
          const doc = replEditor.value.cminstance.getDoc()
          const lastLine = doc.lastLine()
          const lastLineLength = doc.getLine(lastLine).length
          doc.setCursor(lastLine, lastLineLength)
        } else {
          userInput.value = historyCommand
        }
      } else if (direction === 'down') {
        if (historyIndex.value < commandHistory.value.length - 1) {
          historyIndex.value++
          const historyCommand = commandHistory.value[historyIndex.value] || ''
          if (isReplMode.value && replEditor.value?.cminstance) {
            replEditor.value.cminstance.setValue(historyCommand)
            // Move cursor to end
            const doc = replEditor.value.cminstance.getDoc()
            const lastLine = doc.lastLine()
            const lastLineLength = doc.getLine(lastLine).length
            doc.setCursor(lastLine, lastLineLength)
          } else {
            userInput.value = historyCommand
          }
        } else {
          historyIndex.value = commandHistory.value.length
          if (isReplMode.value && replEditor.value?.cminstance) {
            replEditor.value.cminstance.setValue('')
          } else {
            userInput.value = ''
          }
        }
      }
    }
    
    const sendInput = () => {
      if (!userInput.value.trim() && !waitingForInput.value) return
      
      const input = userInput.value
      
      // Echo user input
      addOutput(input, 'user-input')
      
      // Clear local state immediately for responsive UI
      userInput.value = ''
      waitingForInput.value = false
      currentPrompt.value = ''
      inputRows.value = 1
      
      // Send to backend (parent will handle store state update)
      emit('send-input', {
        programId: props.item.id,
        input: input,
        isRepl: false
      })
    }
    
    const cancelInput = () => {
      userInput.value = ''
      waitingForInput.value = false
      currentPrompt.value = ''
      inputRows.value = 1
      
      // Send empty input to unblock
      emit('send-input', {
        programId: props.item.id,
        input: '',
        isRepl: false
      })
    }
    
    const clearConsole = () => {
      outputLines.value = []
      lastExitCode.value = null
      if (!isReplMode.value) {
        commandHistory.value = []
        historyIndex.value = -1
      }
      ElMessage.success('Console cleared')
    }
    
    const stopProgram = () => {
      if (isReplMode.value) {
        exitReplMode()
      }
      emit('stop-item', props.item.id)
    }
    
    const scrollToBottom = () => {
      if (consoleOutput.value) {
        consoleOutput.value.scrollTop = consoleOutput.value.scrollHeight
      }
    }
    
    const downloadFigure = (dataBase64) => {
      const link = document.createElement('a')
      link.href = `data:image/png;base64,${dataBase64}`
      link.download = `figure_${Date.now()}.png`
      link.click()
    }
    
    const openFigureInNewTab = (dataBase64) => {
      const dataUrl = `data:image/png;base64,${dataBase64}`
      window.open(dataUrl, '_blank')
    }
    
    const exportOutput = () => {
      const text = outputLines.value
        .map(line => {
          if (line.type === 'text' || line.type === 'error' || line.type === 'system') {
            return line.content
          } else if (line.type === 'input-prompt') {
            return `Prompt: ${line.content}`
          } else if (line.type === 'user-input') {
            return `> ${line.content}`
          } else if (line.type === 'repl-input') {
            return `${line.prompt}${line.content}`
          } else if (line.type === 'repl-output') {
            return line.content
          }
          return ''
        })
        .join('\n')
      
      const blob = new Blob([text], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `console_output_${Date.now()}.txt`
      link.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success('Output exported')
    }
    
    // Process messages from WebSocket
    const processMessage = (message) => {
      if (message.code === 0) {
        // Regular output
        if (message.data && message.data.stdout !== undefined) {
          addOutput(message.data.stdout, 'text')
        }
      } else if (message.code === 1) {
        // Error output
        if (message.data && message.data.stdout) {
          addOutput(message.data.stdout, 'error')
        }
      } else if (message.code === 2000) {
        // Input request
        if (message.data && message.data.prompt !== undefined) {
          requestInput(message.data.prompt)
        }
      } else if (message.code === 3000) {
        // Matplotlib figure
        if (message.data && message.data.figure) {
          addFigure(message.data.figure)
        }
      } else if (message.code === 4000) {
        // Script error - don't enter REPL
        if (message.data && message.data.error) {
          lastExitCode.value = 1
        }
      } else if (message.code === 5000) {
        // REPL mode starting
        if (message.data && message.data.mode === 'repl') {
          enterReplMode()
        }
      }
    }
    
    // Watch for item changes to process messages
    watch(() => props.item.resultList, (newList) => {
      // Process only new messages
      // This is a simplified approach - you may want to track processed messages
      if (newList && newList.length > 0) {
        const lastMessage = newList[newList.length - 1]
        processMessage(lastMessage)
      }
    }, { deep: true })
    
    // Watch for program start/stop
    watch(() => props.item.run, (running) => {
      if (running) {
        currentProgram.value = props.item.name || 'program'
        lastExitCode.value = null
      } else {
        if (isReplMode.value) {
          // Program stopped, exit REPL mode
          exitReplMode()
        }
      }
    })
    
    return {
      // Data
      outputLines,
      waitingForInput,
      currentPrompt,
      userInput,
      lastExitCode,
      currentProgram,
      isReplMode,
      replPrompt,
      inputRows,
      
      // Refs
      consoleOutput,
      inputField,
      replEditor,
      replCodeMirrorOptions,
      executeReplCommand,
      
      // Methods
      handleKeyDown,
      sendInput,
      cancelInput,
      clearConsole,
      stopProgram,
      exportOutput,
      downloadFigure,
      openFigureInNewTab
    }
  }
}
</script>

<style scoped>
/* Hybrid Console styles - combines UnifiedConsole and REPL functionality */

.unified-console {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--console-bg, #1e1e1e);
  color: var(--console-text, #d4d4d4);
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  overflow: hidden;
}

.console-output {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px;
  min-height: 0;
  background: var(--console-bg, #1e1e1e);
  width: 100%;
  box-sizing: border-box;
}

.output-line {
  margin: 1px 0;
  line-height: 1.4;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.output-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: break-word;
  font-family: inherit;
  font-size: inherit;
  max-width: 100%;
  box-sizing: border-box;
}

.error-output {
  color: #f48771;
}

.system-message {
  color: #9cdcfe;
  font-style: italic;
}

.input-prompt-line {
  display: flex;
  align-items: center;
  margin: 8px 0;
  padding: 4px 0;
  border-left: 3px solid var(--accent-color, #007acc);
  padding-left: 8px;
}

.user-input-line {
  display: flex;
  align-items: center;
  margin: 2px 0;
  color: #d4d4d4; /* Changed to match console output for consistency */
}

.input-indicator {
  color: #569cd6;
  font-weight: bold;
  margin-right: 6px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.input-text {
  margin-left: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}

.input-area {
  border-top: 1px solid var(--border-primary, #3c3c3c);
  padding: 10px;
  background: #252526;
}

.input-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.input-prefix {
  color: #569cd6;
  font-weight: bold;
  font-size: 13px; /* Fixed to match console */
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.user-input-field {
  flex: 1;
  background: #1e1e1e;
  border: 1px solid #3e3e42;
  color: #d4d4d4;
  padding: 6px 10px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace; /* Fixed font */
  font-size: 13px;
  outline: none;
}

.console-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 10px;
  background: #2d2d30;
  border-top: 1px solid #3e3e42;
  font-size: 12px;
  min-height: 24px;
}

.status-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #858585;
}

.status-item.running .status-dot {
  background: #4ec9b0;
  animation: pulse 1.5s infinite;
}

.status-item.success .status-dot {
  background: #608b4e;
}

.status-item.error .status-dot {
  background: #f48771;
}

/* REPL specific styles */
.repl-line {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  display: flex;
  align-items: baseline;
  margin: 2px 0;
}

.repl-prompt {
  color: #4a9eff;
  font-weight: 500;
  margin-right: 8px;
  white-space: pre;
}

.repl-text {
  flex: 1;
  color: #e4e4e4;
  white-space: pre-wrap;
  word-break: break-all;
}

.repl-output {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  color: #cccccc;
  margin: 2px 0;
  padding-left: 20px;
  white-space: pre-wrap;
  word-break: break-all;
}

.input-container.repl-mode {
  background: #1a1a1a;
  border: 1px solid #4a9eff;
}

.input-container.repl-mode .user-input-field {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  min-height: 24px;
  resize: none;
}

.status-item.repl .status-dot {
  background: #4a9eff;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Custom CodeMirror theme for REPL */
.cm-s-repl-theme.CodeMirror {
  background: transparent !important;
  color: #d4d4d4 !important;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 1.4 !important;
}

.cm-s-repl-theme .CodeMirror-cursor {
  border-left: 1px solid #d4d4d4 !important;
}

.cm-s-repl-theme .CodeMirror-selected {
  background: rgba(68, 68, 68, 0.99) !important;
}

.cm-s-repl-theme .CodeMirror-focused .CodeMirror-selected {
  background: rgba(38, 79, 120, 0.99) !important;
}

/* Python syntax highlighting for custom theme */
.cm-s-repl-theme .cm-keyword {
  color: #569cd6 !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-string {
  color: #ce9178 !important;
}

.cm-s-repl-theme .cm-string-2 {
  color: #ce9178 !important;
}

.cm-s-repl-theme .cm-number {
  color: #b5cea8 !important;
}

.cm-s-repl-theme .cm-comment {
  color: #6a9955 !important;
  font-style: italic !important;
}

.cm-s-repl-theme .cm-def {
  color: #dcdcaa !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-builtin {
  color: #4fc1ff !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-operator {
  color: #d4d4d4 !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-variable {
  color: #9cdcfe !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-variable-2 {
  color: #9cdcfe !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-variable-3 {
  color: #4fc1ff !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-property {
  color: #9cdcfe !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-bracket {
  color: #ffd700 !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-tag {
  color: #569cd6 !important;
  font-weight: 400 !important;
}

.cm-s-repl-theme .cm-attribute {
  color: #9cdcfe !important;
  font-weight: 400 !important;
}

/* CodeMirror wrapper styles for REPL */
.repl-codemirror {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
  font-size: 13px !important;
  width: 100% !important;
  border: none !important;
}

.repl-codemirror .CodeMirror {
  background: transparent !important;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
  font-size: 13px !important;
  color: #d4d4d4 !important;
  height: auto !important;
  min-height: 20px !important;
  max-height: 200px !important;
  border: none !important;
  line-height: 1.4 !important;
}

.repl-codemirror .CodeMirror-scroll {
  min-height: 20px !important;
  max-height: 200px !important;
  overflow: auto !important;
}

.repl-codemirror .CodeMirror-lines {
  padding: 2px 0 !important;
}

.repl-codemirror .CodeMirror-line {
  line-height: 1.4 !important;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
  font-size: 13px !important;
}

.repl-codemirror .CodeMirror-gutters {
  display: none !important;
}

.repl-codemirror .CodeMirror-sizer {
  margin-left: 0 !important;
}

/* Ensure consistent font rendering for all CodeMirror content */
.repl-codemirror *,
.repl-codemirror .CodeMirror *,
.repl-codemirror .CodeMirror-line *,
.repl-codemirror span {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 1.4 !important;
}

/* Force consistent fonts and fix existing styles */
.repl-line,
.repl-prompt,
.repl-input-text,
.repl-text,
.repl-output,
.output-text {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 1.4 !important;
}

/* Multiline REPL content */
.repl-line.multiline {
  align-items: flex-start !important;
  flex-direction: column;
}

.repl-line.multiline .repl-prompt {
  align-self: flex-start;
  margin-bottom: 0;
}

.repl-line.multiline .repl-input-text {
  margin-left: 0;
  padding-left: 24px; /* Indent to match prompt */
}

.repl-line .multiline-content,
.repl-line.multiline .repl-input-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
  font-size: 13px !important;
  line-height: 1.4 !important;
  display: block;
  width: 100%;
}

/* For proper indentation preservation in multiline code */
.repl-input-text.multiline-content {
  padding-left: 0; /* Remove extra padding for multiline that's already indented */
}

/* Fix color consistency */
.repl-input-text,
.repl-text,
.repl-output {
  color: #d4d4d4 !important;
}

.repl-prompt {
  color: #4a9eff !important;
  font-weight: 400 !important;
}
</style>