<template>
  <div class="console-div">
    <div class="console-sidebar">
      <div class="run-icon float-right" v-if="item.run === false && !(item.name === 'Terminal' && item.path === 'Terminal')" @click="$emit('run-item')" title="Re-run the script pointed to by the current console"></div>
      <div class="stop-icon float-right" v-if="item.run === true" @click="$emit('stop-item', item.id)" title="Stop the script or command running in the current console"></div>
    </div>
    <div class="console-content">
      <!-- Console output area -->
      <div 
        :id="'console-output-'+item.id"
        class="console-output"
        ref="consoleOutput"
      >
        <pre class="console-text">{{ displayContent }}</pre>
      </div>
      
      <!-- Input area (shown when waiting for input) -->
      <div v-if="item.waitingForInput" class="console-input-area">
        <span class="input-prompt">{{ item.inputPrompt || '' }}</span>
        <input
          v-model="userInput"
          @keyup.enter="sendInput"
          @keyup.escape="cancelInput"
          ref="inputField"
          class="console-input"
          type="text"
          :placeholder="'Type input and press Enter...'"
          autofocus
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    item: Object,
  },
  data() {
    return {
      userInput: '',
    }
  },
  mounted() {
    console.log('[FRONTEND-CONSOLE-DEBUG] ConsoleItemEnhanced mounted');
    console.log('[FRONTEND-CONSOLE-DEBUG] Item:', this.item);
    console.log('[FRONTEND-CONSOLE-DEBUG] waitingForInput:', this.item.waitingForInput);
    console.log('[FRONTEND-CONSOLE-DEBUG] inputPrompt:', this.item.inputPrompt);
    this.focusInput();
  },
  computed: {
    displayContent() {
      if (this.item.run && this.item.resultList.length >= 100) {
        return this.item.resultList.slice(this.item.resultList.length - 100).join('\n');
      }
      else {
        return this.item.resultList.join('\n');
      }
    }
  },
  watch: {
    displayContent() {
      this.$nextTick(() => {
        this.scrollToBottom();
      });
    },
    'item.waitingForInput'(newVal) {
      // Input state changed
      console.log('[FRONTEND-CONSOLE-DEBUG] waitingForInput changed to:', newVal);
      console.log('[FRONTEND-CONSOLE-DEBUG] Input prompt:', this.item.inputPrompt);
      if (newVal) {
        console.log('[FRONTEND-CONSOLE-DEBUG] Showing input field...');
        // Show input field
        this.$nextTick(() => {
          console.log('[FRONTEND-CONSOLE-DEBUG] Focusing input field...');
          this.focusInput();
        });
      }
    }
  },
  methods: {
    sendInput() {
      console.log('[FRONTEND-CONSOLE-DEBUG] sendInput called with:', this.userInput);
      if (this.userInput.trim() || this.userInput === '') {
        // Send input to backend
        if (window.GlobalStore) {
          console.log('[FRONTEND-CONSOLE-DEBUG] Sending input to backend:', {
            cmd: 'send_program_input',
            data: {
              program_id: this.item.id,
              input: this.userInput
            }
          });
          window.GlobalStore.commit('websocket/sendCmd', {
            cmd: 'send_program_input',
            data: {
              program_id: this.item.id,
              input: this.userInput
            }
          });
          
          // Don't add user input to console output - backend will echo it
          
          // Clear waiting state
          console.log('[FRONTEND-CONSOLE-DEBUG] Clearing waiting state');
          window.GlobalStore.commit('ide/setConsoleWaiting', {
            id: this.item.id,
            waiting: false
          });
        }
        
        // Clear input
        this.userInput = '';
        console.log('[FRONTEND-CONSOLE-DEBUG] Input cleared');
      }
    },
    cancelInput() {
      // Send empty input to unblock program
      if (window.GlobalStore) {
        window.GlobalStore.commit('websocket/sendCmd', {
          cmd: 'send_program_input',
          data: {
            program_id: this.item.id,
            input: ''
          }
        });
        
        // Add cancellation message
        window.GlobalStore.commit('ide/addConsoleOutput', {
          id: this.item.id,
          output: '[Input cancelled]'
        });
        
        // Clear waiting state
        window.GlobalStore.commit('ide/setConsoleWaiting', {
          id: this.item.id,
          waiting: false
        });
      }
      
      this.userInput = '';
    },
    scrollToBottom() {
      const output = this.$refs.consoleOutput;
      if (output) {
        output.scrollTop = output.scrollHeight;
      }
    },
    focusInput() {
      if (this.item.waitingForInput && this.$refs.inputField) {
        this.$refs.inputField.focus();
      }
    }
  }
}
</script>

<style scoped>
.console-div {
  position: relative;
  width: 100%;
  height: calc(100% - 2px); /* Account for borders */
  display: none; /* Hide the old enhanced console - using UnifiedConsole instead */
}

.console-sidebar {
  width: 20px;
  height: 100%;
  background: #3A3D41;
  flex-shrink: 0;
}

.console-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #232323;
  overflow: hidden;
  height: 100%;
  max-height: 100%;
}

.console-output {
  flex: 1;
  overflow-x: auto;
  overflow-y: auto;
  padding: 8px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  color: white;
}

.console-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.console-input-area {
  display: flex;
  align-items: center;
  padding: 8px;
  background: #1e1e1e;
  border-top: 1px solid #3A3D41;
  flex-shrink: 0;
  min-height: 40px;
  max-height: 40px;
}

.input-prompt {
  color: #9cdcfe;
  margin-right: 8px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  white-space: nowrap;
}

.console-input {
  flex: 1;
  background: #2d2d30;
  border: 1px solid #3e3e42;
  color: white;
  padding: 4px 8px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  outline: none;
  border-radius: 2px;
}

.console-input:focus {
  border-color: #007acc;
  background: #1e1e1e;
}

.console-input::placeholder {
  color: #6e7681;
  font-style: italic;
}

.run-icon {
  margin-right: 3px;
  margin-top: 2px;
  width: 16px;
  height: 16px;
  background-image: url('./../../../../assets/img/ide/icon_running.svg');
  cursor: pointer;
}

.stop-icon {
  margin-right: 3px;
  margin-top: 2px;
  width: 16px;
  height: 16px;
  background-image: url('./../../../../assets/img/ide/icon_stop.svg');
  cursor: pointer;
}

/* Scrollbar styling */
.console-output::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

.console-output::-webkit-scrollbar-thumb {
  background: #545a5e;
  border-radius: 2px;
}

.console-output::-webkit-scrollbar-track {
  background: #2F2F2F;
}
</style>