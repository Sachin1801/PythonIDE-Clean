<template>
  <el-dialog
    v-model="visible"
    title="Settings"
    width="400px"
    :before-close="handleClose"
    class="settings-dialog"
  >
    <div class="settings-content">
      <div class="setting-item">
        <label>Theme</label>
        <el-select v-model="localSettings.theme" @change="updateTheme">
          <el-option label="Light" value="light" />
          <el-option label="Dark" value="dark" />
          <el-option label="High Contrast" value="contrast" />
        </el-select>
      </div>
      
      <div class="setting-item">
        <label>Font Size</label>
        <el-select v-model="localSettings.fontSize" @change="updateFontSize">
          <el-option label="12px" value="12" />
          <el-option label="14px" value="14" />
          <el-option label="16px" value="16" />
          <el-option label="18px" value="18" />
          <el-option label="26px" value="26" />
        </el-select>
      </div>
      
      <div class="setting-item">
        <label>Show Line Numbers</label>
        <el-switch 
          v-model="localSettings.showLineNumbers" 
          @change="updateLineNumbers"
        />
      </div>
      
      <div class="setting-item">
        <label>Auto-save</label>
        <el-switch 
          v-model="localSettings.autoSave" 
          @change="updateAutoSave"
        />
      </div>
      
      <div class="setting-item" v-if="localSettings.autoSave">
        <label>Auto-save Interval</label>
        <el-select v-model="localSettings.autoSaveInterval" @change="updateAutoSaveInterval">
          <el-option label="30 seconds" value="30" />
          <el-option label="1 minute" value="60" />
          <el-option label="2 minutes" value="120" />
          <el-option label="5 minutes" value="300" />
        </el-select>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button type="primary" @click="handleClose">Close</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
export default {
  name: 'SettingsModal',
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
    handleClose() {
      this.visible = false
    }
  }
}
</script>

<style scoped>
/* CSS Variables for theme support */
.settings-dialog {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  --settings-bg: #ffffff;
  --settings-text: #303133;
  --settings-text-secondary: #606266;
  --settings-border: #e4e7ed;
  --settings-bg-secondary: #f5f7fa;
  --settings-input-bg: #ffffff;
  --settings-primary: #409eff;
  --settings-hover-bg: rgba(0, 0, 0, 0.05);
}

/* Dark theme */
body[data-theme="dark"] .settings-dialog,
body.dark-mode .settings-dialog {
  --settings-bg: #1e1e1e;
  --settings-text: #e4e4e4;
  --settings-text-secondary: #b0b0b0;
  --settings-border: #3a3a3a;
  --settings-bg-secondary: #2d2d2d;
  --settings-input-bg: #2a2a2a;
  --settings-primary: #5ca7ff;
  --settings-hover-bg: rgba(255, 255, 255, 0.1);
}

/* High contrast theme */
body[data-theme="high-contrast"] .settings-dialog,
body[data-theme="contrast"] .settings-dialog,
body.high-contrast-mode .settings-dialog {
  --settings-bg: #000000;
  --settings-text: #ffffff;
  --settings-text-secondary: #e0e0e0;
  --settings-border: #ffffff;
  --settings-bg-secondary: #1a1a1a;
  --settings-input-bg: #0a0a0a;
  --settings-primary: #00aaff;
  --settings-hover-bg: rgba(255, 255, 255, 0.2);
}

.settings-content {
  padding: 10px 0;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin: 8px 0;
  background: var(--settings-bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--settings-border);
  transition: background 0.3s;
}

.setting-item:hover {
  background: var(--settings-hover-bg);
}

.setting-item label {
  flex: 1;
  font-size: 14px;
  color: var(--settings-text);
  font-weight: 500;
}

.setting-item .el-select {
  width: 200px;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  width: 100%;
}

/* Dialog styling */
:deep(.el-dialog) {
  background: var(--settings-bg) !important;
  color: var(--settings-text) !important;
}

/* Force Element Plus dialog background for different themes */
body[data-theme="dark"] .settings-dialog :deep(.el-dialog),
body.dark-mode .settings-dialog :deep(.el-dialog) {
  background-color: #1e1e1e !important;
}

body[data-theme="high-contrast"] .settings-dialog :deep(.el-dialog),
body[data-theme="contrast"] .settings-dialog :deep(.el-dialog),
body.high-contrast-mode .settings-dialog :deep(.el-dialog) {
  background-color: #000000 !important;
  border: 2px solid #ffffff !important;
}

:deep(.el-dialog__header) {
  padding: 20px;
  border-bottom: 1px solid var(--settings-border);
  background: var(--settings-bg);
}

:deep(.el-dialog__body) {
  padding: 20px;
  background: var(--settings-bg);
}

:deep(.el-dialog__footer) {
  padding: 15px 20px;
  border-top: 1px solid var(--settings-border);
  background: var(--settings-bg);
}

:deep(.el-dialog__title) {
  color: var(--settings-text) !important;
}

/* Input and select styling */
:deep(.el-input__inner) {
  background-color: var(--settings-input-bg) !important;
  color: var(--settings-text) !important;
  border-color: var(--settings-border) !important;
}

:deep(.el-input__inner:focus) {
  border-color: var(--settings-primary) !important;
}

:deep(.el-select-dropdown) {
  background: var(--settings-bg) !important;
  border-color: var(--settings-border) !important;
}

:deep(.el-select-dropdown__item) {
  color: var(--settings-text) !important;
}

:deep(.el-select-dropdown__item:hover) {
  background: var(--settings-hover-bg) !important;
}

:deep(.el-select-dropdown__item.selected) {
  color: var(--settings-primary) !important;
}

/* Switch styling - OFF state */
:deep(.el-switch__core) {
  background-color: #dcdfe6 !important;
  border-color: #dcdfe6 !important;
}

body[data-theme="dark"] :deep(.el-switch__core),
body.dark-mode :deep(.el-switch__core) {
  background-color: #4a4a4a !important;
  border-color: #4a4a4a !important;
}

body[data-theme="high-contrast"] :deep(.el-switch__core),
body[data-theme="contrast"] :deep(.el-switch__core),
body.high-contrast-mode :deep(.el-switch__core) {
  background-color: #333333 !important;
  border: 2px solid #ffffff !important;
}

/* Switch styling - ON state */
:deep(.el-switch.is-checked .el-switch__core) {
  background-color: #409eff !important;
  border-color: #409eff !important;
}

body[data-theme="dark"] :deep(.el-switch.is-checked .el-switch__core),
body.dark-mode :deep(.el-switch.is-checked .el-switch__core) {
  background-color: #5ca7ff !important;
  border-color: #5ca7ff !important;
}

body[data-theme="high-contrast"] :deep(.el-switch.is-checked .el-switch__core),
body[data-theme="contrast"] :deep(.el-switch.is-checked .el-switch__core),
body.high-contrast-mode :deep(.el-switch.is-checked .el-switch__core) {
  background-color: #00aaff !important;
  border: 2px solid #00aaff !important;
}

/* Switch action button */
:deep(.el-switch__action) {
  background-color: #ffffff !important;
}

body[data-theme="dark"] :deep(.el-switch__action),
body.dark-mode :deep(.el-switch__action) {
  background-color: #e0e0e0 !important;
}

body[data-theme="high-contrast"] :deep(.el-switch__action),
body[data-theme="contrast"] :deep(.el-switch__action),
body.high-contrast-mode :deep(.el-switch__action) {
  background-color: #ffffff !important;
}

/* Additional high contrast styles */
body[data-theme="high-contrast"] .settings-dialog .setting-item,
body[data-theme="contrast"] .settings-dialog .setting-item,
body.high-contrast-mode .settings-dialog .setting-item {
  border-width: 2px;
}

body[data-theme="high-contrast"] .settings-dialog :deep(.el-input__inner),
body[data-theme="contrast"] .settings-dialog :deep(.el-input__inner),
body.high-contrast-mode .settings-dialog :deep(.el-input__inner) {
  border-width: 2px !important;
}

body[data-theme="high-contrast"] .settings-dialog :deep(.el-switch__core),
body[data-theme="contrast"] .settings-dialog :deep(.el-switch__core),
body.high-contrast-mode .settings-dialog :deep(.el-switch__core) {
  border: 2px solid var(--settings-border) !important;
}
</style>