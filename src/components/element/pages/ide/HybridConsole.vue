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
        <div v-else-if="line.type === 'repl-input'" class="repl-line">
          <span class="repl-prompt">{{ line.prompt }}</span>
          <span class="repl-text">{{ line.content }}</span>
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
      
      <!-- REPL Mode Input -->
      <div class="input-container" :class="{ 'repl-mode': isReplMode }">
        <span class="input-prefix">{{ isReplMode ? replPrompt : '▶' }}</span>
        <textarea
          v-model="userInput"
          @keydown="handleKeyDown"
          ref="inputField"
          class="user-input-field"
          :placeholder="isReplMode ? 'Enter Python code...' : 'Type your input and press Enter...'"
          :rows="inputRows"
          autofocus
        />
        <button 
          v-if="!isReplMode"
          class="input-btn primary" 
          @click="sendInput"
          :disabled="!userInput.trim()"
          title="Submit (Enter)"
        >
          ✓
        </button>
        <button 
          v-if="!isReplMode"
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

export default {
  name: 'HybridConsole',
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
      outputLines.value.push({
        type,
        prompt,
        content,
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
    
    const enterReplMode = () => {
      isReplMode.value = true
      waitingForInput.value = false
      replPrompt.value = '>>> '
      userInput.value = ''
      historyIndex.value = -1
      
      // Focus input field
      nextTick(() => {
        if (inputField.value) {
          inputField.value.focus()
        }
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
      if (!userInput.value.trim()) {
        // Empty input, just show new prompt
        addReplLine(replPrompt.value, '', 'repl-input')
        replPrompt.value = '>>> '
        return
      }
      
      const command = userInput.value
      
      // Add to history
      commandHistory.value.push(command)
      historyIndex.value = commandHistory.value.length
      
      // Echo the command
      addReplLine(replPrompt.value, command, 'repl-input')
      
      // Send to backend
      emit('send-input', {
        programId: props.item.id,
        input: command,
        isRepl: true
      })
      
      // Clear input and reset prompt
      userInput.value = ''
      replPrompt.value = '>>> '
      inputRows.value = 1
    }
    
    const navigateHistory = (direction) => {
      if (commandHistory.value.length === 0) return
      
      if (direction === 'up') {
        if (historyIndex.value > 0) {
          historyIndex.value--
          userInput.value = commandHistory.value[historyIndex.value]
        } else if (historyIndex.value === -1) {
          historyIndex.value = commandHistory.value.length - 1
          userInput.value = commandHistory.value[historyIndex.value]
        }
      } else if (direction === 'down') {
        if (historyIndex.value < commandHistory.value.length - 1) {
          historyIndex.value++
          userInput.value = commandHistory.value[historyIndex.value]
        } else {
          historyIndex.value = commandHistory.value.length
          userInput.value = ''
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
  color: #ce9178;
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
  font-weight: bold;
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
</style>