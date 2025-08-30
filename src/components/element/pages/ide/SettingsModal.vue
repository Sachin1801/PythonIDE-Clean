<template>
  <div v-if="visible" class="settings-modal-overlay" @click.self="handleClose">
    <div class="settings-modal">
      <div class="settings-header">
        <h3>Settings</h3>
        <div class="close-btn" @click="handleClose">
          <X :size="20" />
        </div>
      </div>
      
      <div class="settings-body">
        <div class="setting-item">
          <label>Theme</label>
          <select v-model="localSettings.theme" @change="updateTheme(localSettings.theme)" class="setting-select">
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="contrast">High Contrast</option>
          </select>
        </div>
        
        <div class="setting-item">
          <label>Font Size</label>
          <select v-model="localSettings.fontSize" @change="updateFontSize" class="setting-select">
            <option value="12">12px</option>
            <option value="14">14px</option>
            <option value="16">16px</option>
            <option value="18">18px</option>
            <option value="26">26px</option>
          </select>
        </div>
        
        <div class="setting-item">
          <label>Show Line Numbers</label>
          <div class="switch-container" @click="toggleLineNumbers">
            <div class="switch" :class="{ 'switch-on': localSettings.showLineNumbers }">
              <div class="switch-handle"></div>
            </div>
          </div>
        </div>
        
        <div class="setting-item">
          <label>Auto-save</label>
          <div class="switch-container" @click="toggleAutoSave">
            <div class="switch" :class="{ 'switch-on': localSettings.autoSave }">
              <div class="switch-handle"></div>
            </div>
          </div>
        </div>
        
        <div class="setting-item" v-if="localSettings.autoSave">
          <label>Auto-save Interval</label>
          <select v-model="localSettings.autoSaveInterval" @change="updateAutoSaveInterval" class="setting-select">
            <option value="30">30 seconds</option>
            <option value="60">1 minute</option>
            <option value="120">2 minutes</option>
            <option value="300">5 minutes</option>
          </select>
        </div>
        
        <div class="settings-footer">
          <button class="close-button" @click="handleClose">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { X } from 'lucide-vue-next';

export default {
  name: 'SettingsModal',
  components: {
    X
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      localSettings: {
        theme: 'dark',
        fontSize: '14',
        showLineNumbers: true,
        autoSave: false,
        autoSaveInterval: '60'
      }
    }
  },
  computed: {
    visible: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    }
  },
  mounted() {
    this.loadSettings()
  },
  methods: {
    loadSettings() {
      // Load theme
      const savedTheme = localStorage.getItem('theme')
      if (savedTheme) {
        this.localSettings.theme = savedTheme
      }
      
      // Load font size
      const savedFontSize = localStorage.getItem('fontSize')
      if (savedFontSize) {
        this.localSettings.fontSize = savedFontSize
      }
      
      // Load line numbers preference
      const savedLineNumbers = localStorage.getItem('showLineNumbers')
      if (savedLineNumbers !== null) {
        this.localSettings.showLineNumbers = savedLineNumbers === 'true'
      }
      
      // Load auto-save preference
      const savedAutoSave = localStorage.getItem('autoSave')
      if (savedAutoSave !== null) {
        this.localSettings.autoSave = savedAutoSave === 'true'
      }
      
      // Load auto-save interval
      const savedAutoSaveInterval = localStorage.getItem('autoSaveInterval')
      if (savedAutoSaveInterval) {
        this.localSettings.autoSaveInterval = savedAutoSaveInterval
      }
      
      // Apply the saved theme
      document.documentElement.setAttribute('data-theme', this.localSettings.theme)
    },
    updateTheme(value) {
      document.documentElement.setAttribute('data-theme', value)
      localStorage.setItem('theme', value)
    },
    updateFontSize(value) {
      localStorage.setItem('fontSize', value)
      this.$emit('update-font-size', value)
    },
    updateLineNumbers(value) {
      localStorage.setItem('showLineNumbers', value)
      this.$emit('update-line-numbers', value)
    },
    updateAutoSave(value) {
      localStorage.setItem('autoSave', value)
      this.$emit('update-auto-save', value)
    },
    updateAutoSaveInterval(value) {
      localStorage.setItem('autoSaveInterval', value)
      this.$emit('update-auto-save-interval', value)
    },
    toggleLineNumbers() {
      this.localSettings.showLineNumbers = !this.localSettings.showLineNumbers;
      this.updateLineNumbers(this.localSettings.showLineNumbers);
    },
    toggleAutoSave() {
      this.localSettings.autoSave = !this.localSettings.autoSave;
      this.updateAutoSave(this.localSettings.autoSave);
    },
    handleClose() {
      this.visible = false
    }
  }
}
</script>

<style scoped>
.settings-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
}

.settings-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #464647);
  border-radius: 8px;
  width: 450px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  z-index: 9999;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #464647);
}

.settings-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary, #cccccc);
}

.close-btn {
  cursor: pointer;
  color: var(--text-secondary, #969696);
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: var(--hover-bg, rgba(255, 255, 255, 0.1));
  color: var(--text-primary, #cccccc);
}

.settings-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  max-height: 60vh;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 0;
  border-bottom: 1px solid var(--border-color, #464647);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-item label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #cccccc);
  flex: 1;
}

.setting-select {
  width: 150px;
  padding: 8px 12px;
  background: var(--input-bg, #2d2d30);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  color: var(--text-primary, #cccccc);
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  transition: all 0.2s;
}

.setting-select:focus {
  outline: none;
  border-color: var(--accent-color, #007acc);
  background: var(--input-focus-bg, #383838);
}

.switch-container {
  cursor: pointer;
}

.switch {
  width: 44px;
  height: 24px;
  background: var(--switch-bg-off, #404040);
  border: 1px solid var(--border-color, #464647);
  border-radius: 12px;
  position: relative;
  transition: all 0.3s;
}

.switch-on {
  background: var(--accent-color, #007acc);
  border-color: var(--accent-color, #007acc);
}

.switch-handle {
  width: 18px;
  height: 18px;
  background: var(--switch-handle, #ffffff);
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: all 0.3s;
}

.switch-on .switch-handle {
  left: 22px;
}

.settings-footer {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color, #464647);
  display: flex;
  justify-content: center;
}

.close-button {
  width: 100%;
  padding: 10px 20px;
  background: var(--accent-color, #007acc);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-sizing: border-box;
}

.close-button:hover {
  background: var(--accent-hover, #005a9e);
}

/* Light Theme Support */
[data-theme="light"] .settings-modal {
  background: #ffffff;
  border-color: #d0d0d0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

[data-theme="light"] .settings-header {
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .settings-header h3 {
  color: #333333;
}

[data-theme="light"] .close-btn {
  color: rgba(0, 0, 0, 0.6);
}

[data-theme="light"] .close-btn:hover {
  color: rgba(0, 0, 0, 0.9);
  background: rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .setting-item {
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .setting-item label {
  color: #333333;
}

[data-theme="light"] .setting-select {
  background: #f8f8f8;
  border-color: #d0d0d0;
  color: #333333;
}

[data-theme="light"] .setting-select:focus {
  background: #ffffff;
  border-color: #1890ff;
}

[data-theme="light"] .switch {
  background: #e0e0e0;
  border-color: #d0d0d0;
}

[data-theme="light"] .switch-on {
  background: #1890ff;
  border-color: #1890ff;
}

[data-theme="light"] .switch-handle {
  background: #ffffff;
}

[data-theme="light"] .settings-footer {
  border-top-color: #e0e0e0;
}

[data-theme="light"] .close-button {
  background: #1890ff;
}

[data-theme="light"] .close-button:hover {
  background: #096dd9;
}

/* High Contrast Theme Support */
[data-theme="high-contrast"] .settings-modal {
  background: #000000;
  border: 2px solid #ffffff;
  box-shadow: 0 8px 32px rgba(255, 255, 255, 0.3);
}

[data-theme="high-contrast"] .settings-header {
  border-bottom: 2px solid #ffffff;
}

[data-theme="high-contrast"] .settings-header h3 {
  color: #ffffff;
}

[data-theme="high-contrast"] .close-btn {
  color: #ffffff;
}

[data-theme="high-contrast"] .close-btn:hover {
  background: #333333;
  border: 1px solid #ffff00;
}

[data-theme="high-contrast"] .setting-item {
  border-bottom: 2px solid #ffffff;
}

[data-theme="high-contrast"] .setting-item label {
  color: #ffffff;
}

[data-theme="high-contrast"] .setting-select {
  background: #000000;
  border: 2px solid #ffffff;
  color: #ffffff;
}

[data-theme="high-contrast"] .setting-select:focus {
  border-color: #ffff00;
}

[data-theme="high-contrast"] .switch {
  background: #333333;
  border: 2px solid #ffffff;
}

[data-theme="high-contrast"] .switch-on {
  background: #00bfff;
  border-color: #00bfff;
}

[data-theme="high-contrast"] .switch-handle {
  background: #ffffff;
}

[data-theme="high-contrast"] .settings-footer {
  border-top: 2px solid #ffffff;
}

[data-theme="high-contrast"] .close-button {
  background: #00bfff;
  color: #000000;
  border: 2px solid #ffffff;
}

[data-theme="high-contrast"] .close-button:hover {
  background: #ffff00;
  border-color: #ffff00;
}
</style>