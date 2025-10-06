<template>
  <router-view></router-view>
</template>

<script>
import { ElMessage, ElMessageBox } from 'element-plus';

export default {
  name: 'App',
  components: {},
  mounted() {
    // SINGLE-SESSION & AUTO-LOGOUT: Listen for session termination events
    window.addEventListener('session-terminated', this.handleSessionTerminated);
  },
  beforeUnmount() {
    window.removeEventListener('session-terminated', this.handleSessionTerminated);
  },
  methods: {
    handleSessionTerminated(event) {
      const { reason, message } = event.detail;

      console.warn('[Session Terminated]', reason, message);

      // Show alert box with no grace period - instant logout
      ElMessageBox.alert(message, 'Session Terminated', {
        confirmButtonText: 'OK',
        type: 'warning',
        showClose: false,
        closeOnClickModal: false,
        closeOnPressEscape: false,
        callback: () => {
          // Redirect to login page
          this.$router.push('/login');
        }
      });

      // Also show a toast notification
      ElMessage({
        message: message,
        type: 'warning',
        duration: 5000
      });
    }
  }
};
</script>

<style>
/* Removed global * selector to prevent font conflicts */

/* Reset body and html for proper scaling */
body, html {
  margin: 0;
  padding: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin: 0;
  padding: 0;
  width: 100vw;
  height: 100vh;
}

/* Apply Inter font globally but exclude code editor */
body, html, input, textarea, select, button {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif !important;
  font-optical-sizing: auto;
}

/* Preserve monospace font for code editor and console */
/* Force Consolas first for all console and code elements */
.CodeMirror, .CodeMirror *, .cm-editor, .cm-editor *, pre, code, .console-output, .console-input,
.editor-content, .vue-codemirror, .codemirror-container, .codemirror-container *,
.console-user-input, .console-text, .token {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
}

/* Ultra-high specificity override for all console elements */
.console-output-area, .console-output-area *,
.console-user-input, .console-user-input *,
.console-text, .console-text *,
pre[class*="language-"], pre[class*="language-"] *,
code[class*="language-"], code[class*="language-"] *,
.token, .token *, [class*="token"], [class*="token"] * {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
}
</style>
