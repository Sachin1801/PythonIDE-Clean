<template>
  <div class="python-repl">
    <!-- REPL Output Area -->
    <div class="repl-output" ref="replOutput">
      <div v-for="(line, index) in outputLines" :key="index" class="repl-line">
        <!-- Welcome message -->
        <pre v-if="line.type === 'welcome'" class="welcome-text">{{ line.content }}</pre>
        
        <!-- Regular output -->
        <pre v-else-if="line.type === 'output'" class="output-text">{{ line.content }}</pre>
        
        <!-- User input with prompt -->
        <div v-else-if="line.type === 'input'" class="input-line">
          <span class="prompt">{{ line.prompt }}</span>
          <span class="user-input">{{ line.content }}</span>
        </div>
        
        <!-- Error output -->
        <pre v-else-if="line.type === 'error'" class="error-text">{{ line.content }}</pre>
        
        <!-- System messages -->
        <pre v-else-if="line.type === 'system'" class="system-text">{{ line.content }}</pre>
      </div>
    </div>
    
    <!-- REPL Input Area -->
    <div class="repl-input-area">
      <div class="input-line-container">
        <span class="repl-prompt">{{ currentPrompt }}</span>
        <textarea
          v-model="currentInput"
          @keydown="handleKeyDown"
          ref="replInput"
          class="repl-input-field"
          :placeholder="placeholder"
          :rows="inputRows"
          autofocus
        ></textarea>
      </div>
      <div class="repl-hints">
        <span class="hint">Enter: Execute | Shift+Enter: New line | Tab: Indent | Up/Down: History</span>
      </div>
    </div>
    
    <!-- REPL Controls -->
    <div class="repl-controls">
      <button @click="startREPL" v-if="!isRunning" class="control-btn start">
        ▶ Start REPL
      </button>
      <button @click="stopREPL" v-else class="control-btn stop">
        ⬛ Stop REPL
      </button>
      <button @click="clearOutput" class="control-btn clear">
        🗑 Clear
      </button>
      <button @click="exportHistory" class="control-btn export">
        💾 Export History
      </button>
    </div>
  </div>
</template>

<script>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'PythonREPL',
  setup() {
    const store = useStore()
    
    // Reactive state
    const outputLines = ref([])
    const currentInput = ref('')
    const currentPrompt = ref('>>> ')
    const isRunning = ref(false)
    const replId = ref(null)
    const commandHistory = ref([])
    const historyIndex = ref(-1)
    const placeholder = ref('Enter Python code...')
    const inputRows = ref(1)
    
    // Refs
    const replOutput = ref(null)
    const replInput = ref(null)
    
    // WebSocket message handler
    const handleMessage = (message) => {
      if (!replId.value || message.id !== replId.value) return
      
      if (message.code === 0) {
        // Regular output
        if (message.data && message.data.stdout) {
          const lines = message.data.stdout.split('\n')
          lines.forEach(line => {
            if (line) {
              outputLines.value.push({
                type: 'output',
                content: line
              })
            }
          })
          scrollToBottom()
        }
      } else if (message.code === 2000) {
        // REPL prompt request
        if (message.data && message.data.type === 'repl_prompt') {
          currentPrompt.value = message.data.prompt
          // Focus input
          nextTick(() => {
            if (replInput.value) {
              replInput.value.focus()
            }
          })
        }
      } else if (message.code === 1111) {
        // REPL ended
        if (message.data && message.data.stdout) {
          outputLines.value.push({
            type: 'system',
            content: message.data.stdout
          })
        }
        isRunning.value = false
        replId.value = null
      }
    }
    
    // Start REPL
    const startREPL = async () => {
      replId.value = Date.now().toString()
      isRunning.value = true
      
      // Clear previous output
      outputLines.value = []
      
      // Send start REPL command
      await store.dispatch('websocket/sendMessage', {
        cmd: 'start_python_repl',
        cmd_id: replId.value,
        data: {
          projectName: store.state.ide.currentProject || 'repl'
        }
      })
      
      // Add welcome message
      outputLines.value.push({
        type: 'welcome',
        content: 'Python REPL started. You can now execute Python code interactively.'
      })
    }
    
    // Stop REPL
    const stopREPL = async () => {
      if (replId.value) {
        await store.dispatch('websocket/sendMessage', {
          cmd: 'stop_python_program',
          cmd_id: Date.now().toString(),
          data: {
            program_id: replId.value
          }
        })
      }
      isRunning.value = false
      replId.value = null
      currentPrompt.value = '>>> '
    }
    
    // Send input to REPL
    const sendInput = async () => {
      if (!currentInput.value.trim() || !replId.value) return
      
      const input = currentInput.value
      
      // Add to output with prompt
      outputLines.value.push({
        type: 'input',
        prompt: currentPrompt.value,
        content: input
      })
      
      // Add to history
      commandHistory.value.push(input)
      historyIndex.value = commandHistory.value.length
      
      // Send to backend
      await store.dispatch('websocket/sendMessage', {
        cmd: 'send_program_input',
        cmd_id: Date.now().toString(),
        data: {
          program_id: replId.value,
          input: input
        }
      })
      
      // Clear input
      currentInput.value = ''
      inputRows.value = 1
      scrollToBottom()
    }
    
    // Handle key events
    const handleKeyDown = (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        // Execute on Enter (without Shift)
        event.preventDefault()
        sendInput()
      } else if (event.key === 'Enter' && event.shiftKey) {
        // New line on Shift+Enter
        inputRows.value = Math.min(10, inputRows.value + 1)
      } else if (event.key === 'Tab') {
        // Insert 4 spaces for indentation
        event.preventDefault()
        const start = event.target.selectionStart
        const end = event.target.selectionEnd
        const value = currentInput.value
        currentInput.value = value.substring(0, start) + '    ' + value.substring(end)
        // Move cursor after inserted spaces
        nextTick(() => {
          event.target.selectionStart = event.target.selectionEnd = start + 4
        })
      } else if (event.key === 'ArrowUp' && event.target.selectionStart === 0) {
        // Navigate history up
        event.preventDefault()
        if (historyIndex.value > 0) {
          historyIndex.value--
          currentInput.value = commandHistory.value[historyIndex.value]
        }
      } else if (event.key === 'ArrowDown') {
        // Navigate history down
        event.preventDefault()
        if (historyIndex.value < commandHistory.value.length - 1) {
          historyIndex.value++
          currentInput.value = commandHistory.value[historyIndex.value]
        } else {
          historyIndex.value = commandHistory.value.length
          currentInput.value = ''
        }
      }
      
      // Auto-adjust textarea height
      nextTick(() => {
        if (replInput.value) {
          const lines = currentInput.value.split('\n').length
          inputRows.value = Math.min(10, Math.max(1, lines))
        }
      })
    }
    
    // Clear output
    const clearOutput = () => {
      outputLines.value = []
      if (isRunning.value) {
        outputLines.value.push({
          type: 'welcome',
          content: 'Output cleared. REPL is still running.'
        })
      }
    }
    
    // Export history
    const exportHistory = () => {
      const historyText = commandHistory.value.join('\n')
      const blob = new Blob([historyText], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `python_repl_history_${Date.now()}.py`
      a.click()
      URL.revokeObjectURL(url)
    }
    
    // Scroll to bottom
    const scrollToBottom = () => {
      nextTick(() => {
        if (replOutput.value) {
          replOutput.value.scrollTop = replOutput.value.scrollHeight
        }
      })
    }
    
    // Listen for WebSocket messages
    onMounted(() => {
      store.commit('websocket/setMessageHandler', handleMessage)
    })
    
    onUnmounted(() => {
      if (isRunning.value) {
        stopREPL()
      }
    })
    
    return {
      outputLines,
      currentInput,
      currentPrompt,
      isRunning,
      placeholder,
      inputRows,
      replOutput,
      replInput,
      commandHistory,
      historyIndex,
      startREPL,
      stopREPL,
      sendInput,
      handleKeyDown,
      clearOutput,
      exportHistory
    }
  }
}
</script>

<style scoped>
.python-repl {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
}

/* Output area */
.repl-output {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: #1e1e1e;
}

.repl-line {
  margin: 2px 0;
}

.welcome-text {
  color: #4ec9b0;
  font-style: italic;
  margin: 0;
}

.output-text {
  color: #d4d4d4;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.input-line {
  display: flex;
  align-items: flex-start;
}

.prompt {
  color: #569cd6;
  font-weight: bold;
  margin-right: 8px;
}

.user-input {
  color: #ce9178;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.error-text {
  color: #f48771;
  margin: 0;
  white-space: pre-wrap;
}

.system-text {
  color: #9cdcfe;
  font-style: italic;
  margin: 0;
}

/* Input area */
.repl-input-area {
  border-top: 1px solid #3e3e42;
  background: #252526;
  padding: 10px;
}

.input-line-container {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.repl-prompt {
  color: #569cd6;
  font-weight: bold;
  padding-top: 5px;
}

.repl-input-field {
  flex: 1;
  background: #1e1e1e;
  border: 1px solid #3e3e42;
  color: #d4d4d4;
  padding: 5px 8px;
  border-radius: 4px;
  font-family: inherit;
  font-size: 14px;
  outline: none;
  resize: none;
  min-height: 28px;
}

.repl-input-field:focus {
  border-color: #007acc;
}

.repl-hints {
  margin-top: 5px;
  font-size: 11px;
  color: #858585;
}

.hint {
  margin-right: 15px;
}

/* Controls */
.repl-controls {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: #2d2d30;
  border-top: 1px solid #3e3e42;
}

.control-btn {
  padding: 6px 12px;
  border: 1px solid #3e3e42;
  background: #383838;
  color: #d4d4d4;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #484848;
  border-color: #007acc;
}

.control-btn.start {
  background: #0e639c;
  border-color: #007acc;
}

.control-btn.start:hover {
  background: #1177bb;
}

.control-btn.stop {
  background: #a1260d;
  border-color: #f48771;
}

.control-btn.stop:hover {
  background: #c42b1c;
}

/* Scrollbar */
.repl-output::-webkit-scrollbar {
  width: 8px;
}

.repl-output::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.repl-output::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 4px;
}

.repl-output::-webkit-scrollbar-thumb:hover {
  background: #4e4e4e;
}
</style>