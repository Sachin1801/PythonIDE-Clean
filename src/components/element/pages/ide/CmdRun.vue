<template>
  <div class="cmd-div" :style="{ height: cmdHeight + 'px' }">
    <textarea
      class="float-left pip-input-text"
      id="pip-install-input-id"
      v-model="inputText"
      @input="adjustHeight"
      @keydown.enter="handleEnter"
      placeholder="pip install or shell commands..."
      ref="cmdInput"
      :rows="1"
    ></textarea>
    <span>
      <div class="run-icon float-right" v-if="!consoleLimit" @click="runCmd()" title="Run command"></div>
    </span>
  </div>
</template>

<script>
import * as types from '../../../../store/mutation-types';

export default {
  data() {
    return {
      inputText: '',
      cmdHeight: 30,
      lineHeight: 20,
      maxLines: 3,
    };
  },
  mounted() {
    this.resize();
    window.addEventListener('resize', this.resize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resize);
  },
  methods: {
    resize() {
      const ele = document.getElementById('pip-install-input-id');
      if (ele !== undefined && ele !== null) {
        ele.style.width = `calc(100% - 40px)`;
      }
    },
    adjustHeight() {
      this.$nextTick(() => {
        const textarea = this.$refs.cmdInput;
        if (!textarea) return;
        
        // Reset height to auto to get the correct scrollHeight
        textarea.style.height = 'auto';
        
        // Calculate lines
        const lines = textarea.value.split('\n').length;
        const scrollLines = Math.ceil(textarea.scrollHeight / this.lineHeight);
        const actualLines = Math.max(lines, scrollLines);
        
        // Limit to max 3 lines
        const displayLines = Math.min(actualLines, this.maxLines);
        
        // Set height
        this.cmdHeight = Math.max(30, displayLines * this.lineHeight + 10);
        textarea.style.height = (this.cmdHeight - 10) + 'px';
        
        // Enable scroll if more than 3 lines
        if (actualLines > this.maxLines) {
          textarea.style.overflowY = 'auto';
        } else {
          textarea.style.overflowY = 'hidden';
        }
        
        // Emit height change to parent
        this.$emit('height-changed', this.cmdHeight);
      });
    },
    handleEnter(event) {
      // Shift+Enter for new line, Enter to run
      if (!event.shiftKey) {
        event.preventDefault();
        this.runCmd();
      }
    },
    runCmd() {
      if (this.inputText === null || this.inputText === undefined || this.inputText === '') {
        return;
      }

      let selected = false;
      if (this.ideInfo.consoleSelected.run === false && this.ideInfo.consoleSelected.name === 'Terminal' && this.ideInfo.consoleSelected.path === 'Terminal') {
        selected = true;
        this.$store.commit('ide/assignConsoleSelected', {
          stop: false,
          resultList: []
        });
      }
      else {
        for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
          if (this.ideInfo.consoleItems[i].run === false && this.ideInfo.consoleItems[i].name === 'Terminal' && this.ideInfo.consoleItems[i].path === 'Terminal') {
            this.$store.commit('ide/setConsoleSelected', this.ideInfo.consoleItems[i]);
            selected = true;
            this.$store.commit('ide/assignConsoleSelected', {
              stop: false,
              resultList: []
            });
            break;
          }
        }
      }
      if (selected === false) {
        for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
          if (this.ideInfo.consoleItems[i].run === false && this.ideInfo.consoleItems[i].name === 'Terminal' && this.ideInfo.consoleItems[i].path === 'Terminal') {
            this.$store.commit('ide/spliceConsoleItems', {start: i, count: 1});
            break;
          }
        }
        const item = {
          name: 'Terminal',
          path: 'Terminal',
          resultList: [],
          run: false,
          stop: false,
          id: this.ideInfo.consoleId,
        }
        this.$store.commit('ide/addConsoleItem', item);
        this.$store.commit('ide/setConsoleSelected', item);     
      }
      else {
        this.$store.commit('ide/assignConsoleSelected', {
          id: this.ideInfo.consoleId
        });
      }

      // Remove duplicate console item creation - this was causing multiple input fields
      this.$store.dispatch(`ide/${types.IDE_RUN_PIP_COMMAND}`, {
        msgId: this.ideInfo.consoleId,
        command: this.inputText,
        callback: {
          limits: -1,
          callback: (dict) => {
            this.$store.commit('ide/handleRunResult', dict);
          }
        }
      });
      this.$store.commit('ide/setConsoleId', this.ideInfo.consoleId + 1);
      
      // Clear input after running
      this.inputText = '';
      this.adjustHeight();
    },
  },
  watch: {
    inputText() {
      this.adjustHeight();
    }
  },
  computed: {
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
    consoleLimit() {
      let count = 0;
      for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
        if (this.ideInfo.consoleItems[i].run === true && this.ideInfo.consoleItems[i].name === 'Terminal' && this.ideInfo.consoleItems[i].path === 'Terminal') {
          count += 1;
        }
      }
      return count >= 2;
    }
  },
  components: {
  },
};
</script>

<style scoped>

.cmd-div {
  position: fixed;
  width: 100%;
  min-height: 30px;
  /* left: 200px; */
  bottom: 0px;
  background: var(--bg-tertiary, #46494B);
  border-top: 1px solid var(--border-primary, #3c3c3c);
  transition: height 0.2s ease;
  display: flex;
  align-items: flex-start;
}

.pip-input-text {
  /* width:1100px; */
  width: calc(100% - 40px);
  min-height: 20px;
  max-height: 60px;
  border: none;
  background: var(--bg-tertiary, #46494B);
  color: var(--text-primary, white);
  /* box-shadow:inset 0 0 0px 0 rgba(255,255,255,0.50); */
  /* top: -5px; */
  /* bottom: 5px; */
  padding: 5px 10px;
  outline: none;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 20px;
  resize: none;
  overflow-y: hidden;
  flex: 1;
}

.pip-input-text::placeholder {
  color: var(--text-secondary, #969696);
  opacity: 0.7;
}

.run-icon {
  /* margin-right: 1px; */
  margin-top: 0px;
  width: 30px;
  height: 30px;
  background: var(--bg-secondary, #3C3F41);
  background-image: url('~@/assets/img/ide/icon_running.svg');
  background-size: 16px 16px;
  background-repeat: no-repeat;
  background-position: center;
  cursor: pointer;
  transition: background-color 0.2s ease;
  flex-shrink: 0;
}

.run-icon:hover {
  background-color: var(--bg-hover, #45494a);
}

.stop-icon {
  /* margin-right: 1px; */
  margin-top: 0px;
  width: 30px;
  height: 30px;
  background: var(--bg-secondary, #3C3F41);
  background-image: url('~@/assets/img/ide/icon_stop.svg');
  background-size: 16px 16px;
  background-repeat: no-repeat;
  background-position: center;
  cursor: pointer;
  transition: background-color 0.2s ease;
  flex-shrink: 0;
}

.stop-icon:hover {
  background-color: var(--bg-hover, #45494a);
}

/* Scrollbar styles for textarea */
.pip-input-text::-webkit-scrollbar {
  width: 5px;
}

.pip-input-text::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb, #545a5e);
  border-radius: 3px;
}

.pip-input-text::-webkit-scrollbar-track {
  background: transparent;
}
</style>