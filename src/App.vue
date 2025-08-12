<template>
  <router-view></router-view>
</template>

<script>

export default {
  name: 'App',
  components: {
  }
}
</script>

<style>
* {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

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
  width: calc(100vw / 1.25);
  height: calc(100vh / 1.25);
  transform: scale(1.25);
  transform-origin: top left;
  position: absolute;
  top: 0;
  left: 0;
}

/* Apply Inter font globally but exclude code editor */
body, html, input, textarea, select, button {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif !important;
  font-optical-sizing: auto;
}

/* Preserve monospace font for code editor and console */
.CodeMirror, .CodeMirror *, .cm-editor, .cm-editor *, pre, code, .console-output, .console-input {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace !important;
}
</style>
