<template>
  <div class="ide-editor-container" :class="{ 'csv-container': isCsvFile }">
    <markdown-editor v-if="isMarkdown"
      :codeItem="codeItem"
      :codeItemIndex="codeItemIndex">
    </markdown-editor>
    <csv-viewer v-else-if="isCsvFile"
      :content="codeItem.content">
    </csv-viewer>
    <media-viewer v-else-if="isMediaFile"
      :codeItem="codeItem"
      :codeItemIndex="codeItemIndex">
    </media-viewer>
    <code-editor v-else
      :codeItem="codeItem"
      :consoleLimit="consoleLimit"
      @run-item="$emit('run-item')"
      :codeItemIndex="codeItemIndex">
    </code-editor>
  </div>
</template>

<script>
import CodeEditor from './editor/CodeEditor';
import MarkdownEditor from './editor/MarkdownEditor';
import MediaViewer from './editor/MediaViewer';
import CsvViewer from './CsvViewer';

export default {
  props: {
    codeItem: Object,
    codeItemIndex: Number,
    consoleLimit: Boolean,
  },
  data() {
    return {
    }
  },
  computed: {
    isMarkdown() {
      return this.codeItem.path.endsWith('.md');
    },
    isCsvFile() {
      return this.codeItem.path.toLowerCase().endsWith('.csv');
    },
    isMediaFile() {
      const mediaExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.pdf'];
      const path = this.codeItem.path.toLowerCase();
      return mediaExtensions.some(ext => path.endsWith(ext));
    },
  },
  components: {
    CodeEditor,
    MarkdownEditor,
    MediaViewer,
    CsvViewer
  }
}
</script>

<style scoped>
.ide-editor-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.ide-editor-container.csv-container {
  overflow: auto; /* Allow scrolling for CSV files */
  display: flex;
  flex-direction: column;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style>