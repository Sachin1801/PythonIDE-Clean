<template>
  <div class="test-container">
    <h2>Splitpanes Test Component</h2>
    <div style="height: 500px; border: 1px solid #ccc;">
      <splitpanes class="default-theme" horizontal>
        <pane :size="70" :min-size="30">
          <div style="background: #f0f0f0; height: 100%; padding: 20px;">
            <h3>Editor Area</h3>
            <p>This would be your code editor</p>
          </div>
        </pane>
        <pane :size="30" :min-size="10">
          <div style="background: #e0e0e0; height: 100%; padding: 20px;">
            <h3>Console Area</h3>
            <p>This would be your console</p>
          </div>
        </pane>
      </splitpanes>
    </div>
  </div>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

export default {
  name: 'TestSplitpanes',
  components: {
    Splitpanes,
    Pane
  }
}
</script>

<style scoped>
.test-container {
  padding: 20px;
}

/* Custom splitter styling */
.splitpanes.default-theme .splitpanes__splitter {
  background-color: #ccc;
  position: relative;
  transition: background-color 0.2s;
}

.splitpanes.default-theme .splitpanes__splitter:hover {
  background-color: #999;
}

.splitpanes.default-theme .splitpanes__splitter.splitpanes__splitter__active {
  background-color: #007ACC;
}

/* Horizontal splitter */
.splitpanes--horizontal > .splitpanes__splitter {
  height: 5px;
  cursor: ns-resize;
}
</style>