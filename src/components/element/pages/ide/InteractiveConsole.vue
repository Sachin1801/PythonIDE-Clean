<template>
  <div class="interactive-console">
    <!-- Main console output area -->
    <div class="console-output" ref="consoleOutput">
      <div v-for="(line, index) in outputLines" :key="index" class="output-line">
        <!-- Regular text output -->
        <pre v-if="line.type === 'text'" :class="line.class">{{ line.content }}</pre>
        
        <!-- Matplotlib figure display -->
        <div v-else-if="line.type === 'figure'" class="figure-container">
          <img :src="line.data" alt="Matplotlib Figure" class="matplotlib-figure" />
          <div class="figure-controls">
            <el-button size="small" @click="downloadFigure(line.data)">
              <el-icon><download /></el-icon> Download
            </el-button>
            <el-button size="small" @click="openFigureInNewTab(line.data)">
              <el-icon><full-screen /></el-icon> Full Screen
            </el-button>
          </div>
        </div>
        
        <!-- Input prompt -->
        <div v-else-if="line.type === 'input-prompt'" class="input-prompt">
          <span class="prompt-text">{{ line.prompt }}</span>
        </div>
        
        <!-- User input echo -->
        <div v-else-if="line.type === 'user-input'" class="user-input-echo">
          <span class="input-indicator">›</span> {{ line.content }}
        </div>
      </div>
    </div>
    
    <!-- Input area (shown when waiting for input) -->
    <transition name="slide-up">
      <div v-if="waitingForInput" class="input-area">
        <div class="input-prompt-display">{{ currentPrompt }}</div>
        <div class="input-container">
          <span class="input-prefix">›</span>
          <input
            v-model="userInput"
            @keyup.enter="sendInput"
            @keyup.escape="cancelInput"
            ref="inputField"
            class="user-input-field"
            :placeholder="inputPlaceholder"
            autofocus
          />
          <el-button 
            type="primary" 
            size="small" 
            @click="sendInput"
            :disabled="!userInput.trim()"
          >
            <el-icon><check /></el-icon> Submit
          </el-button>
          <el-button 
            size="small" 
            @click="cancelInput"
          >
            <el-icon><close /></el-icon> Cancel
          </el-button>
        </div>
        <div class="input-hint">Press Enter to submit, Escape to cancel</div>
      </div>
    </transition>
    
    <!-- Control buttons -->
    <div class="console-controls">
      <el-button 
        v-if="!isRunning" 
        type="success" 
        size="small" 
        @click="$emit('run')"
      >
        <el-icon><video-play /></el-icon> Run
      </el-button>
      <el-button 
        v-else 
        type="danger" 
        size="small" 
        @click="$emit('stop')"
      >
        <el-icon><video-pause /></el-icon> Stop
      </el-button>
      <el-button 
        size="small" 
        @click="clearConsole"
      >
        <el-icon><delete /></el-icon> Clear
      </el-button>
      <el-button 
        size="small" 
        @click="exportOutput"
      >
        <el-icon><document /></el-icon> Export
      </el-button>
    </div>
    
    <!-- Status bar -->
    <div class="console-status">
      <span v-if="isRunning" class="status-running">
        <span class="status-indicator running"></span> Running...
      </span>
      <span v-else-if="lastExitCode === 0" class="status-success">
        <span class="status-indicator success"></span> Ready
      </span>
      <span v-else-if="lastExitCode !== null" class="status-error">
        <span class="status-indicator error"></span> Exit code: {{ lastExitCode }}
      </span>
      <span v-else class="status-idle">
        <span class="status-indicator idle"></span> Idle
      </span>
    </div>
  </div>
</template>

<script>
import { ref, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  VideoPlay, 
  VideoPause, 
  Delete, 
  Document, 
  Download, 
  FullScreen,
  Check,
  Close 
} from '@element-plus/icons-vue'

export default {
  name: 'InteractiveConsole',
  components: {
    VideoPlay,
    VideoPause,
    Delete,
    Document,
    Download,
    FullScreen,
    Check,
    Close
  },
  props: {
    isRunning: {
      type: Boolean,
      default: false
    },
    programId: {
      type: String,
      default: null
    }
  },
  emits: ['run', 'stop', 'send-input'],
  setup(props, { emit }) {
    // Reactive data
    const outputLines = ref([])
    const waitingForInput = ref(false)
    const currentPrompt = ref('')
    const userInput = ref('')
    const inputPlaceholder = ref('Type your input here...')
    const lastExitCode = ref(null)
    
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
      currentPrompt.value = prompt
      waitingForInput.value = true
      
      // Add prompt to output
      addOutput(prompt, 'input-prompt')
      
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
      
      // Echo user input to simulate terminal behavior
      addOutput(input, 'user-input')
      
      // Send to backend
      emit('send-input', {
        programId: props.programId,
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
      
      // Send empty input to unblock the program
      emit('send-input', {
        programId: props.programId,
        input: ''
      })
    }
    
    const clearConsole = () => {
      outputLines.value = []
      lastExitCode.value = null
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
        .filter(line => line.type === 'text' || line.type === 'user-input')
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
          addOutput(message.data.stderr, 'text', 'error-output')
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
          addOutput(message.data.stdout, 'text', 'system-message')
          
          // Extract exit code
          const exitMatch = message.data.stdout.match(/exit code (-?\d+)/)
          if (exitMatch) {
            lastExitCode.value = parseInt(exitMatch[1])
          }
        }
      }
    }
    
    // Watch for running state changes
    watch(() => props.isRunning, (newVal) => {
      if (newVal) {
        lastExitCode.value = null
      }
    })
    
    // Public API
    return {
      outputLines,
      waitingForInput,
      currentPrompt,
      userInput,
      inputPlaceholder,
      lastExitCode,
      consoleOutput,
      inputField,
      addOutput,
      addFigure,
      requestInput,
      sendInput,
      cancelInput,
      clearConsole,
      downloadFigure,
      openFigureInNewTab,
      exportOutput,
      handleMessage
    }
  }
}
</script>

<style scoped>
.interactive-console {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--console-bg, #1e1e1e);
  color: var(--console-text, #d4d4d4);
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}

.console-output {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  min-height: 150px;
}

.output-line {
  margin: 2px 0;
}

.output-line pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.error-output {
  color: #f48771;
}

.system-message {
  color: #9cdcfe;
  font-style: italic;
}

.input-prompt {
  color: #dcdcaa;
  font-weight: bold;
  margin-top: 5px;
}

.user-input-echo {
  color: #ce9178;
  margin-left: 10px;
}

.input-indicator {
  color: #569cd6;
  font-weight: bold;
}

/* Matplotlib figure display */
.figure-container {
  margin: 10px 0;
  padding: 10px;
  background: #2d2d30;
  border-radius: 4px;
  display: inline-block;
}

.matplotlib-figure {
  max-width: 100%;
  height: auto;
  display: block;
  margin-bottom: 10px;
  border: 1px solid #3e3e42;
  border-radius: 4px;
}

.figure-controls {
  display: flex;
  gap: 10px;
}

/* Input area */
.input-area {
  border-top: 1px solid #3e3e42;
  padding: 10px;
  background: #252526;
}

.input-prompt-display {
  color: #dcdcaa;
  margin-bottom: 8px;
  font-weight: 500;
}

.input-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-prefix {
  color: #569cd6;
  font-weight: bold;
  font-size: 16px;
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
  border-color: #007acc;
}

.input-hint {
  margin-top: 5px;
  font-size: 11px;
  color: #858585;
}

/* Console controls */
.console-controls {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-top: 1px solid #3e3e42;
  background: #2d2d30;
}

/* Status bar */
.console-status {
  padding: 5px 10px;
  background: #007acc;
  color: white;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-indicator.running {
  background: #ffaa00;
  animation: pulse 1s infinite;
}

.status-indicator.success {
  background: #4ec9b0;
}

.status-indicator.error {
  background: #f48771;
}

.status-indicator.idle {
  background: #858585;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Transitions */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(20px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

/* Scrollbar styling */
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

/* Theme adaptations */
:root[data-theme="light"] .interactive-console {
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