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
        theme: 'dark'
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
      const savedTheme = localStorage.getItem('theme')
      if (savedTheme) {
        this.localSettings.theme = savedTheme
      }
      // Apply the saved theme
      document.documentElement.setAttribute('data-theme', this.localSettings.theme)
    },
    updateTheme(value) {
      document.documentElement.setAttribute('data-theme', value)
      localStorage.setItem('theme', value)
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