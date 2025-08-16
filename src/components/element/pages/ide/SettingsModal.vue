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
          <el-option label="Small (12px)" value="12" />
          <el-option label="Medium (14px)" value="14" />
          <el-option label="Large (16px)" value="16" />
          <el-option label="Extra Large (18px)" value="18" />
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
.settings-dialog {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}

.settings-content {
  padding: 10px 0;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.setting-item label {
  flex: 1;
  font-size: 14px;
  color: #606266;
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

:deep(.el-dialog__header) {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  padding: 15px 20px;
  border-top: 1px solid #e4e7ed;
}

/* Dark theme support for dialog */
[data-theme="dark"] :deep(.el-dialog) {
  background: var(--bg-secondary, #252526);
  color: var(--text-primary, #cccccc);
}

[data-theme="dark"] :deep(.el-dialog__header) {
  border-bottom-color: var(--border-color, #464647);
}

[data-theme="dark"] :deep(.el-dialog__footer) {
  border-top-color: var(--border-color, #464647);
}

[data-theme="dark"] :deep(.el-dialog__title) {
  color: var(--text-primary, #cccccc);
}

[data-theme="dark"] .setting-item label {
  color: var(--text-primary, #cccccc);
}
</style>