<template>
  <div class="unified-console">
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
        
        <!-- Matplotlib figure display -->
        <div v-else-if="line.type === 'figure'" class="figure-container">
          <img :src="line.data" alt="Matplotlib Figure" class="matplotlib-figure" />
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
      
      <!-- Loading indicator when program is running -->
      <div v-if="isRunning && !waitingForInput" class="loading-indicator">
        <span class="loading-dots">●●●</span>
        <span class="loading-text">Running...</span>
      </div>
    </div>
    
    <!-- Input Area (shown when waiting for input) -->
    <div v-if="waitingForInput" class="input-area">
      <div class="input-prompt-display">
        <span class="prompt-icon">💬</span>
        <span class="prompt-label">{{ currentPrompt || 'Waiting for input...' }}</span>
      </div>
      <div class="input-container">
        <span class="input-prefix">▶</span>
        <input
          v-model="userInput"
          @keyup.enter="sendInput"
          @keyup.escape="cancelInput"
          ref="inputField"
          class="user-input-field"
          placeholder="Type your input and press Enter..."
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
      <div class="input-hint">Press Enter to submit • Escape to cancel</div>
    </div>
    
    <!-- No command input area - only program input is supported -->
    
    <!-- Status Bar -->
    <div class="console-status">
      <div class="status-left">
        <span v-if="isRunning" class="status-item running">
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
        <button v-if="isRunning" class="status-btn danger" @click="stopProgram" title="Stop program">⏹️</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'UnifiedConsole',
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
    
    // Refs
    const consoleOutput = ref(null)
    const inputField = ref(null)
    
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
    
    const sendInput = () => {
      if (!userInput.value.trim()) return
      
      const input = userInput.value
      
      // Echo user input
      addOutput(input, 'user-input')
      
      // Send to backend
      emit('send-input', {
        programId: props.item.id,
        input: input
      })
      
      // Clear and hide input
      userInput.value = ''
      waitingForInput.value = false
      currentPrompt.value = ''
    }
    
    const cancelInput = () => {
      userInput.value = ''
      waitingForInput.value = false
      currentPrompt.value = ''
      
      // Send empty input to unblock
      emit('send-input', {
        programId: props.item.id,
        input: ''
      })
    }
    

    
    const clearConsole = () => {
      outputLines.value = []
      lastExitCode.value = null
      ElMessage.success('Console cleared')
    }
    
    const stopProgram = () => {
      emit('stop-item', props.item.id)
    }
    
    const scrollToBottom = () => {
      if (consoleOutput.value) {
        consoleOutput.value.scrollTop = consoleOutput.value.scrollHeight
      }
    }
    
    const downloadFigure = (dataUrl) => {
      const link = document.createElement('a')
      link.href = dataUrl
      link.download = `figure_${Date.now()}.png`
      link.click()
    }
    
    const openFigureInNewTab = (dataUrl) => {
      window.open(dataUrl, '_blank')
    }
    
    const exportOutput = () => {
      const text = outputLines.value
        .filter(line => ['text', 'error', 'system', 'user-input'].includes(line.type))
        .map(line => line.content)
        .join('\n')
      
      const blob = new Blob([text], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `console_output_${Date.now()}.txt`
      link.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success('Console output exported')
    }
    
    // Handle WebSocket messages
    const handleMessage = (message) => {
      if (message.code === 0) {
        // Normal output
        if (message.data && message.data.stdout) {
          addOutput(message.data.stdout)
        }
      } else if (message.code === 1) {
        // Error output
        if (message.data && message.data.stderr) {
          addOutput(message.data.stderr, 'error')
        }
      } else if (message.code === 2000) {
        // Input request
        if (message.data && message.data.type === 'input_request') {
          requestInput(message.data.prompt)
        }
      } else if (message.code === 3000) {
        // Matplotlib figure
        if (message.data && message.data.type === 'matplotlib_figure') {
          addFigure(message.data.data)
        }
      } else if (message.code === 1111) {
        // Program finished
        if (message.data && message.data.stdout) {
          addOutput(message.data.stdout, 'system')
          
          // Extract exit code
          const exitMatch = message.data.stdout.match(/exit code (-?\d+)/)
          if (exitMatch) {
            lastExitCode.value = parseInt(exitMatch[1])
          }
        }
      }
    }
    
    // Watch for item changes to update output
    watch(() => props.item.resultList, (newResults) => {
      if (newResults && newResults.length > 0) {
        // Clear existing output and add all results
        outputLines.value = []
        newResults.forEach(line => {
          // Check if it looks like a completion message
          if (line.includes('[Program finished') || line.includes('[Finished in') || line.includes('exit code')) {
            addOutput(line, 'system')
            // Extract exit code
            const exitMatch = line.match(/exit code (-?\d+)/)
            if (exitMatch) {
              lastExitCode.value = parseInt(exitMatch[1])
            }
          } else if (line.includes('[Error:') || line.includes('Traceback') || line.includes('Exception')) {
            addOutput(line, 'error')
          } else {
            addOutput(line)
          }
        })
      }
    }, { immediate: true, deep: true })
    
    // Watch for running state changes
    watch(() => props.item.run, (newVal) => {
      if (newVal) {
        lastExitCode.value = null
        currentProgram.value = props.item.name || 'Program'
        // Clear output when starting new run
        if (props.item.resultList && props.item.resultList.length === 0) {
          outputLines.value = []
        }
      } else {
        waitingForInput.value = false
        currentProgram.value = ''
      }
    }, { immediate: true })
    
    // Also watch isRunning prop for compatibility
    watch(() => props.isRunning, (newVal) => {
      if (newVal) {
        lastExitCode.value = null
        currentProgram.value = props.item.name || 'Program'
      } else {
        waitingForInput.value = false
        currentProgram.value = ''
      }
    })
    
    // Watch for input requests from the store
    watch(() => props.item.waitingForInput, (isWaiting) => {
      waitingForInput.value = isWaiting
      if (isWaiting && props.item.inputPrompt) {
        currentPrompt.value = props.item.inputPrompt
        // Focus input field
        nextTick(() => {
          if (inputField.value) {
            inputField.value.focus()
          }
        })
      }
    }, { immediate: true })
    

    
    return {
      outputLines,
      waitingForInput,
      currentPrompt,
      userInput,
      lastExitCode,
      currentProgram,
      consoleOutput,
      inputField,
      addOutput,
      addFigure,
      requestInput,
      sendInput,
      cancelInput,
      clearConsole,
      stopProgram,
      downloadFigure,
      openFigureInNewTab,
      exportOutput,
      handleMessage
    }
  }
}
</script>

<style scoped>
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

/* Console Output */
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

/* Input Prompt Line */
.input-prompt-line {
  display: flex;
  align-items: center;
  margin: 8px 0;
  padding: 4px 0;
  border-left: 3px solid var(--accent-color, #007acc);
  padding-left: 8px;
}

.prompt-indicator {
  margin-right: 6px;
  font-size: 12px;
}

.prompt-text {
  color: #dcdcaa;
  font-weight: 500;
}

/* User Input Line */
.user-input-line {
  display: flex;
  align-items: center;
  margin: 2px 0;
  color: #ce9178;
}

.input-indicator {
  color: #569cd6;
  font-weight: bold;
  margin-right: 6px;
  font-size: 12px;
}

.input-text {
  margin-left: 4px;
}

/* Figure Display */
.figure-container {
  margin: 10px 0;
  padding: 10px;
  background: #2d2d30;
  border-radius: 4px;
  display: inline-block;
  max-width: 100%;
}

.matplotlib-figure {
  max-width: 100%;
  height: auto;
  display: block;
  margin-bottom: 8px;
  border: 1px solid #3e3e42;
  border-radius: 4px;
}

.figure-controls {
  display: flex;
  gap: 8px;
}

.figure-btn {
  padding: 4px 8px;
  background: var(--accent-color, #007acc);
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
}

.figure-btn:hover {
  background: #1a8cff;
}

/* Loading Indicator */
.loading-indicator {
  display: flex;
  align-items: center;
  margin: 8px 0;
  color: #858585;
}

.loading-dots {
  animation: pulse 1.5s infinite;
  margin-right: 8px;
}

.loading-text {
  font-style: italic;
}

/* Input Area */
.input-area {
  border-top: 1px solid var(--border-primary, #3c3c3c);
  padding: 10px;
  background: #252526;
}

.input-prompt-display {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: #dcdcaa;
  font-weight: 500;
}

.prompt-icon {
  margin-right: 6px;
}

.prompt-label {
  margin-left: 4px;
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
  font-size: 14px;
}

.user-input-field {
  flex: 1;
  background: #1e1e1e;
  border: 1px solid #3e3e42;
  color: #d4d4d4;
  padding: 6px 10px;
  border-radius: 4px;
  font-family: inherit;
  font-size: 13px;
  outline: none;
}

.user-input-field:focus {
  border-color: var(--accent-color, #007acc);
}

.input-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  transition: background-color 0.2s ease;
}

.input-btn.primary {
  background: var(--accent-color, #007acc);
  color: white;
}

.input-btn.primary:hover:not(:disabled) {
  background: #1a8cff;
}

.input-btn.primary:disabled {
  background: #555;
  cursor: not-allowed;
}

.input-btn.secondary {
  background: #6c757d;
  color: white;
}

.input-btn.secondary:hover {
  background: #545b62;
}

.input-hint {
  font-size: 11px;
  color: #858585;
  text-align: center;
}



/* Status Bar */
.console-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 10px;
  background: var(--accent-color, #007acc);
  color: white;
  font-size: 11px;
  border-top: 1px solid var(--border-primary, #3c3c3c);
}

.status-left {
  display: flex;
  align-items: center;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.status-item.running .status-dot {
  background: #ffaa00;
  animation: pulse 1s infinite;
}

.status-item.success .status-dot {
  background: #4ec9b0;
}

.status-item.error .status-dot {
  background: #f48771;
}

.status-item.idle .status-dot {
  background: #858585;
}

.status-right {
  display: flex;
  gap: 4px;
}

.status-btn {
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: none;
  border-radius: 2px;
  cursor: pointer;
  font-size: 10px;
  transition: background-color 0.2s ease;
}

.status-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.status-btn.danger {
  background: #dc3545;
}

.status-btn.danger:hover {
  background: #c82333;
}

/* Scrollbar Styling */
.console-output::-webkit-scrollbar {
  width: 8px;
}

.console-output::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.console-output::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 4px;
}

.console-output::-webkit-scrollbar-thumb:hover {
  background: #4e4e4e;
}

/* Animations */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Theme Adaptations */
:root[data-theme="light"] .unified-console {
  --console-bg: #ffffff;
  --console-text: #333333;
}

:root[data-theme="light"] .console-output {
  background: #f5f5f5;
}

:root[data-theme="light"] .input-area {
  background: #fafafa;
  border-top-color: #e0e0e0;
}

:root[data-theme="light"] .user-input-field {
  background: #ffffff;
  border-color: #d0d0d0;
  color: #333333;
}

:root[data-theme="light"] .figure-container {
  background: #f0f0f0;
}
</style>
