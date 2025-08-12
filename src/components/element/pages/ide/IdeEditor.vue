<template>
  <div class="ide-editor-container">
    <markdown-editor v-if="isMarkdown"
      :codeItem="codeItem"
      :codeItemIndex="codeItemIndex">
    </markdown-editor>
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
    isMediaFile() {
      const mediaExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.pdf'];
      const path = this.codeItem.path.toLowerCase();
      return mediaExtensions.some(ext => path.endsWith(ext));
    },
  },
  components: {
    CodeEditor,
    MarkdownEditor,
    MediaViewer
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
</style>