<template>
  <div class="simple-console">
    <!-- Output Area -->
    <div class="console-output" ref="outputArea">
      <!-- Display all lines -->
      <div v-for="(line, index) in outputLines" :key="index" :class="['line', line.type]">
        <pre v-if="line.type === 'stdout' || line.type === 'stderr'">{{ line.text }}</pre>
        <div v-else-if="line.type === 'input'" class="input-echo">
          <span class="prompt">{{ line.prompt }}</span>
          <span class="user-text">{{ line.text }}</span>
        </div>
        <div v-else-if="line.type === 'system'" class="system-message">
          {{ line.text }}
        </div>
        <img v-else-if="line.type === 'figure'" :src="`data:image/png;base64,${line.data}`" class="figure" />
      </div>

      <!-- Loading indicator -->
      <div v-if="isRunning && !isWaitingForInput && !isReplActive" class="loading">
        <span class="dots">●●●</span> Running...
      </div>
    </div>

    <!-- Input Area -->
    <div v-if="isWaitingForInput || isReplActive" class="console-input">
      <span class="input-prompt">{{ currentPrompt }}</span>
      <input
        v-model="userInput"
        @keydown.enter="sendInput"
        @keydown.up="historyUp"
        @keydown.down="historyDown"
        ref="inputField"
        class="input-field"
        :placeholder="inputPlaceholder"
        autofocus
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'SimpleConsole',

  props: {
    cmdId: String,
    isConnected: Boolean
  },

  data() {
    return {
      outputLines: [],
      userInput: '',
      currentPrompt: '>>> ',
      isRunning: false,
      isWaitingForInput: false,
      isReplActive: false,
      inputHistory: [],
      historyIndex: -1,
      currentHistoryInput: ''
    }
  },

  computed: {
    inputPlaceholder() {
      if (this.isWaitingForInput) {
        return 'Enter input and press Enter...'
      }
      return 'Enter Python code...'
    }
  },

  methods: {
    // Handle incoming WebSocket messages
    handleMessage(message) {
      console.log('[SimpleConsole] Received message:', message.type, message)

      switch (message.type) {
        case 'stdout':
          this.addOutputLine('stdout', message.data.text)
          break

        case 'stderr':
          this.addOutputLine('stderr', message.data.text)
          break

        case 'repl_ready':
          this.isReplActive = true
          this.isRunning = false
          this.currentPrompt = message.data.prompt || '>>> '
          this.addOutputLine('system', '🎯 REPL mode active')
          break

        case 'input_request':
          this.isWaitingForInput = true
          this.currentPrompt = message.data.prompt || ''
          break

        case 'figure':
          this.outputLines.push({
            type: 'figure',
            data: message.data.content
          })
          break

        case 'complete':
          this.isRunning = false
          this.isReplActive = false
          this.isWaitingForInput = false
          if (message.data.exit_code !== 0) {
            this.addOutputLine('system', `Process exited with code ${message.data.exit_code}`)
          }
          break

        case 'error':
          this.addOutputLine('stderr', message.data.error)
          this.isRunning = false
          break

        case 'debug':
          if (this.$store.state.debugMode) {
            console.log('[DEBUG]', message.data.text)
          }
          break
      }

      this.scrollToBottom()
    },

    // Add a line to the output
    addOutputLine(type, text) {
      // Split text by newlines to handle multi-line output
      const lines = text.split('\n')
      lines.forEach((line, index) => {
        // Don't add empty lines unless they're in the middle
        if (line || index < lines.length - 1) {
          this.outputLines.push({ type, text: line })
        }
      })
    },

    // Send user input
    sendInput() {
      if (!this.userInput.trim()) return

      // Add to history
      this.inputHistory.push(this.userInput)
      this.historyIndex = this.inputHistory.length

      // Echo the input
      this.outputLines.push({
        type: 'input',
        prompt: this.currentPrompt,
        text: this.userInput
      })

      // Send via WebSocket
      this.$emit('send-input', {
        cmd: 'send_input',
        cmd_id: this.cmdId,
        text: this.userInput
      })

      // Clear input
      this.userInput = ''
      this.isWaitingForInput = false

      // Update prompt for REPL
      if (this.isReplActive) {
        // Prompt will be updated by next message
      }

      this.scrollToBottom()
    },

    // Navigate command history
    historyUp() {
      if (this.historyIndex > 0) {
        if (this.historyIndex === this.inputHistory.length) {
          this.currentHistoryInput = this.userInput
        }
        this.historyIndex--
        this.userInput = this.inputHistory[this.historyIndex]
      }
    },

    historyDown() {
      if (this.historyIndex < this.inputHistory.length) {
        this.historyIndex++
        if (this.historyIndex === this.inputHistory.length) {
          this.userInput = this.currentHistoryInput
        } else {
          this.userInput = this.inputHistory[this.historyIndex]
        }
      }
    },

    // Start execution
    startExecution() {
      console.log('[SimpleConsole] Starting execution')
      this.outputLines = []
      this.isRunning = true
      this.isReplActive = false
      this.isWaitingForInput = false
    },

    // Stop execution
    stopExecution() {
      console.log('[SimpleConsole] Stopping execution')
      this.$emit('stop-execution', {
        cmd: 'stop_execution',
        cmd_id: this.cmdId
      })
      this.isRunning = false
      this.isReplActive = false
      this.isWaitingForInput = false
    },

    // Clear console
    clear() {
      this.outputLines = []
      this.inputHistory = []
      this.historyIndex = -1
    },

    // Scroll to bottom
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.outputArea) {
          this.$refs.outputArea.scrollTop = this.$refs.outputArea.scrollHeight
        }
      })
    },

    // Focus input field
    focusInput() {
      this.$nextTick(() => {
        if (this.$refs.inputField) {
          this.$refs.inputField.focus()
        }
      })
    }
  },

  mounted() {
    // Focus input when mounted
    if (this.isReplActive || this.isWaitingForInput) {
      this.focusInput()
    }
  },

  watch: {
    // Focus input when it becomes visible
    isWaitingForInput(val) {
      if (val) this.focusInput()
    },
    isReplActive(val) {
      if (val) this.focusInput()
    }
  }
}
</script>

<style scoped>
.simple-console {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}

.console-output {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: #1e1e1e;
}

.line {
  margin: 2px 0;
  word-wrap: break-word;
}

.line pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.line.stdout {
  color: #d4d4d4;
}

.line.stderr {
  color: #f48771;
}

.input-echo {
  color: #3794ff;
}

.input-echo .prompt {
  color: #608b4e;
  margin-right: 5px;
}

.input-echo .user-text {
  color: #3794ff;
}

.system-message {
  color: #608b4e;
  font-style: italic;
  margin: 5px 0;
}

.figure {
  max-width: 100%;
  margin: 10px 0;
  border: 1px solid #464647;
  background: white;
}

.loading {
  color: #608b4e;
  padding: 10px;
  animation: pulse 1.5s infinite;
}

.loading .dots {
  animation: blink 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

@keyframes blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.console-input {
  display: flex;
  align-items: center;
  padding: 10px;
  background: #2d2d30;
  border-top: 1px solid #464647;
}

.input-prompt {
  color: #608b4e;
  margin-right: 10px;
  white-space: nowrap;
}

.input-field {
  flex: 1;
  background: transparent;
  border: none;
  color: #d4d4d4;
  font-family: inherit;
  font-size: inherit;
  outline: none;
}

.input-field::placeholder {
  color: #6a6a6a;
}

/* Scrollbar styling */
.console-output::-webkit-scrollbar {
  width: 10px;
}

.console-output::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.console-output::-webkit-scrollbar-thumb {
  background: #464647;
  border-radius: 5px;
}

.console-output::-webkit-scrollbar-thumb:hover {
  background: #5a5a5a;
}
</style>