<template>
  <div class="fullscreen-preview" v-if="isActive">
    <div class="preview-header">
      <div class="preview-header-left">
        <span class="preview-title">{{ fileName }}</span>
      </div>
      <div class="preview-header-right">
        <button class="preview-action-btn" @click="openInRightPanel" title="Open in Right Panel">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <path d="M15 3v18"/>
          </svg>
        </button>
        <button class="preview-close-btn" @click="close" title="Close Preview">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>
    <div class="preview-content">
      <csv-viewer v-if="isCsvFile" :content="content" />
      <media-viewer v-else-if="isMediaFile" :codeItem="mediaCodeItem" :codeItemIndex="0" />
      <div v-else class="unsupported-preview">
        <p>Preview not supported for this file type</p>
      </div>
    </div>
  </div>
</template>

<script>
import CsvViewer from './CsvViewer';
import MediaViewer from './editor/MediaViewer';

export default {
  name: 'FullscreenPreview',
  components: {
    CsvViewer,
    MediaViewer
  },
  computed: {
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
    isActive() {
      return this.ideInfo.fullscreenPreview.active;
    },
    file() {
      return this.ideInfo.fullscreenPreview.file;
    },
    content() {
      return this.ideInfo.fullscreenPreview.content;
    },
    fileName() {
      return this.file?.name || '';
    },
    filePath() {
      return this.file?.path || '';
    },
    isCsvFile() {
      return this.filePath.toLowerCase().endsWith('.csv');
    },
    isMediaFile() {
      const mediaExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.pdf'];
      const path = this.filePath.toLowerCase();
      return mediaExtensions.some(ext => path.endsWith(ext));
    },
    // Create a codeItem object that MediaViewer expects with pre-loaded content
    mediaCodeItem() {
      if (!this.file) return null;
      return {
        name: this.file.name,
        path: this.file.path,
        projectName: this.file.projectName,
        content: this.content,  // Pass the already loaded content
        preloaded: true  // Flag to indicate content is already loaded
      };
    }
  },
  methods: {
    close() {
      this.$store.commit('ide/closeFullscreenPreview');
    },
    openInRightPanel() {
      // Close fullscreen preview
      this.$store.commit('ide/closeFullscreenPreview');
      
      // Open file in right panel
      if (this.file) {
        this.$emit('open-in-right-panel', this.file.path);
      }
    }
  },
  mounted() {
    // Add ESC key handler
    this.handleEsc = (e) => {
      if (e.key === 'Escape' && this.isActive) {
        this.close();
      }
    };
    document.addEventListener('keydown', this.handleEsc);
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleEsc);
  }
};
</script>

<style scoped>
.fullscreen-preview {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-primary, #1e1e1e);
  z-index: 100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  height: 40px;
  background: var(--bg-secondary, #252526);
  border-bottom: 1px solid var(--border-color, #3e3e42);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 15px;
  flex-shrink: 0;
}

.preview-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.preview-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #cccccc);
}

.preview-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-action-btn,
.preview-close-btn {
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-secondary, #969696);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.preview-action-btn:hover,
.preview-close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary, #cccccc);
}

.preview-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}


.unsupported-preview {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary, #969696);
  font-size: 16px;
}

/* Light theme */
[data-theme="light"] .fullscreen-preview {
  background: #ffffff;
}

[data-theme="light"] .preview-header {
  background: #f3f3f3;
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .preview-title {
  color: #333333;
}

[data-theme="light"] .preview-action-btn,
[data-theme="light"] .preview-close-btn {
  color: #666666;
}

[data-theme="light"] .preview-action-btn:hover,
[data-theme="light"] .preview-close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333333;
}
</style>