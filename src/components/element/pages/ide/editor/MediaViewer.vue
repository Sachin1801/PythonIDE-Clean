<template>
  <div class="media-viewer">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <el-icon size="32" class="loading-icon"><refresh /></el-icon>
      <p>Loading media file...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <el-icon size="64" class="error-icon"><document /></el-icon>
      <p>Failed to load media file</p>
      <el-button @click="loadFile" type="primary">
        <el-icon><refresh /></el-icon> Retry
      </el-button>
    </div>
    
    <!-- Image Display -->
    <div v-else-if="isImage" class="image-container">
      <div class="toolbar">
        <el-button-group>
          <el-button @click="zoomIn" size="small">
            <el-icon><zoom-in /></el-icon> Zoom In
          </el-button>
          <el-button @click="zoomOut" size="small">
            <el-icon><zoom-out /></el-icon> Zoom Out
          </el-button>
          <el-button @click="resetZoom" size="small">
            <el-icon><refresh /></el-icon> Reset
          </el-button>
          <el-button @click="downloadFile" size="small">
            <el-icon><download /></el-icon> Download
          </el-button>
        </el-button-group>
        <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
      </div>
      <div class="image-wrapper" @wheel="handleWheel">
        <img 
          :src="fileUrl" 
          :alt="fileName"
          :style="{ transform: `scale(${zoomLevel})` }"
          @error="handleError"
          draggable="false"
        />
      </div>
    </div>
    
    <div v-else-if="isPdf" class="pdf-container">
      <div class="toolbar pdf-toolbar">
        <span class="pdf-title">PDF Viewer</span>
        <el-button @click="downloadFile" size="small">
          <el-icon><download /></el-icon> Download
        </el-button>
      </div>
      <div class="pdf-wrapper">
        <iframe 
          :src="pdfViewerUrl" 
          class="pdf-iframe"
          frameborder="0"
        ></iframe>
      </div>
    </div>
    
    <div v-else class="unsupported-file">
      <el-icon size="64"><document /></el-icon>
      <p>Preview not available for this file type</p>
      <el-button @click="downloadFile" type="primary">
        <el-icon><download /></el-icon> Download File
      </el-button>
    </div>
  </div>
</template>

<script>
import { 
  ZoomIn, 
  ZoomOut, 
  Refresh, 
  Download, 
  Document 
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import * as types from '../../../../../store/mutation-types';

export default {
  name: 'MediaViewer',
  components: {
    ZoomIn,
    ZoomOut,
    Refresh,
    Download,
    Document
  },
  props: {
    codeItem: Object,
    codeItemIndex: Number,
  },
  data() {
    return {
      zoomLevel: 1,
      fileUrl: '',
      error: false,
      loading: false,
    };
  },
  computed: {
    fileName() {
      return this.codeItem?.name || '';
    },
    fileExtension() {
      // Handle files with multiple dots (e.g., "my.file.name.png")
      const lastDotIndex = this.fileName.lastIndexOf('.');
      if (lastDotIndex === -1) return '';
      return this.fileName.substring(lastDotIndex + 1).toLowerCase();
    },
    isImage() {
      return ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'webp'].includes(this.fileExtension);
    },
    isPdf() {
      return this.fileExtension === 'pdf';
    },
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
    pdfViewerUrl() {
      // Use browser's built-in PDF viewer
      return this.fileUrl;
    }
  },
  mounted() {
    this.loadFile();
  },
  watch: {
    codeItem: {
      deep: true,
      handler() {
        this.loadFile();
      }
    }
  },
  methods: {
    async loadFile(retryCount = 0) {
      // Reset state
      this.error = false;
      this.loading = true;
      this.fileUrl = '';
      
      // Check if content is already preloaded
      if (this.codeItem?.preloaded && this.codeItem?.content) {
        this.loading = false;
        this.fileUrl = this.codeItem.content;
        console.log('Using preloaded content for media file');
        return;
      }
      
      // Get file content from backend
      const projectName = this.codeItem?.projectName || this.ideInfo.currProj?.data?.name;
      const filePath = this.codeItem?.path;
      
      if (!projectName || !filePath) {
        this.loading = false;
        this.error = true;
        return;
      }
      
      console.log('Loading media file:', { 
        projectName, 
        filePath, 
        binary: true,
        retryCount,
        codeItem: this.codeItem,
        ideInfo: this.ideInfo
      });
      
      // Add a longer initial delay for images to ensure file is fully written
      // This accounts for the time it takes for Python to complete plt.savefig()
      if (retryCount === 0 && this.isImage) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      // Request file content as base64
      this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
        projectName: projectName,
        filePath: filePath,
        binary: true,
        callback: async (response) => {
          console.log('Media file response:', {
            code: response.code,
            hasData: !!response.data,
            dataKeys: response.data ? Object.keys(response.data) : [],
            contentLength: response.data?.content ? response.data.content.length : 0,
            retryCount,
            fullResponse: response
          });
          
          if (response.code === 0 && response.data) {
            // Handle binary data
            if (response.data.content && response.data.content.length > 0) {
              this.loading = false;
              const mimeType = this.getMimeType();
              this.fileUrl = `data:${mimeType};base64,${response.data.content}`;
              console.log('File loaded successfully:', { mimeType, fileUrl: this.fileUrl.substring(0, 50) + '...' });
            } else if (retryCount < 2) {
              // File might not be fully written yet, retry with exponential backoff
              const delay = 1000 * Math.pow(1.5, retryCount); // 1000ms, 1500ms
              console.log(`No content or empty content, retrying in ${delay}ms... (attempt ${retryCount + 1})`);
              await new Promise(resolve => setTimeout(resolve, delay));
              this.loadFile(retryCount + 1);
            } else {
              this.loading = false;
              console.error('No content in response data after retries');
              this.handleError();
            }
          } else if (response.code === -22 && retryCount < 2) {
            // File doesn't exist yet, retry with exponential backoff
            const delay = 1000 * Math.pow(1.5, retryCount); // 1000ms, 1500ms
            console.log(`File not found, retrying in ${delay}ms... (attempt ${retryCount + 1})`);
            await new Promise(resolve => setTimeout(resolve, delay));
            this.loadFile(retryCount + 1);
          } else {
            this.loading = false;
            console.error('Failed to load file:', response);
            this.handleError();
          }
        }
      });
    },
    getMimeType() {
      const mimeTypes = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'svg': 'image/svg+xml',
        'webp': 'image/webp',
        'pdf': 'application/pdf'
      };
      return mimeTypes[this.fileExtension] || 'application/octet-stream';
    },
    zoomIn() {
      this.zoomLevel = Math.min(this.zoomLevel + 0.25, 3);
    },
    zoomOut() {
      this.zoomLevel = Math.max(this.zoomLevel - 0.25, 0.25);
    },
    resetZoom() {
      this.zoomLevel = 1;
    },
    handleWheel(event) {
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault();
        if (event.deltaY < 0) {
          this.zoomIn();
        } else {
          this.zoomOut();
        }
      }
    },
    downloadFile() {
      const link = document.createElement('a');
      link.href = this.fileUrl;
      link.download = this.fileName;
      link.click();
    },
    handleError() {
      this.error = true;
      this.loading = false;
      console.error('MediaViewer error:', { fileName: this.fileName, filePath: this.codeItem?.path });
      ElMessage.error(`Failed to load file: ${this.fileName}`);
    }
  }
};
</script>

<style scoped>
.media-viewer {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--editor-bg, #1e1e1e);
  color: var(--editor-text, #d4d4d4);
  overflow: hidden;
}

/* Loading and Error States */
.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.loading-container p,
.error-container p {
  margin: 16px 0;
  font-size: 16px;
  color: var(--text-secondary, #969696);
}

.loading-icon {
  animation: spin 1s linear infinite;
  color: var(--accent-color, #007acc);
}

.error-icon {
  color: var(--error-color, #ff6b68);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.toolbar {
  padding: 10px;
  background: var(--toolbar-bg, #2d2d30);
  border-bottom: 1px solid var(--border-color, #3e3e42);
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  min-height: 48px;
  max-height: 48px;
}

.zoom-level {
  margin-left: 10px;
  font-size: 14px;
  color: var(--text-secondary, #969696);
}

.page-info {
  padding: 0 15px;
  font-size: 14px;
  display: flex;
  align-items: center;
}

/* PDF specific toolbar styles */
.pdf-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: nowrap;
}

.pdf-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #d4d4d4);
}

/* Image viewer styles */
.image-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.image-wrapper {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 20px;
  background-image: 
    linear-gradient(45deg, #2a2a2a 25%, transparent 25%),
    linear-gradient(-45deg, #2a2a2a 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #2a2a2a 75%),
    linear-gradient(-45deg, transparent 75%, #2a2a2a 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
}

.image-wrapper img {
  max-width: none;
  height: auto;
  object-fit: contain;
  transition: transform 0.2s ease;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  margin: auto;
}

/* PDF viewer styles */
.pdf-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pdf-wrapper {
  flex: 1;
  position: relative;
  overflow: auto;
  min-height: 0;
  width: 100%;
}

.pdf-iframe {
  width: 100%;
  min-height: 100%;
  height: auto;
  border: none;
  background: white;
}

/* Unsupported file styles */
.unsupported-file {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
  color: var(--text-secondary, #969696);
}

.unsupported-file p {
  font-size: 16px;
  margin: 0;
}

/* Light theme adjustments */
:root[data-theme="light"] .media-viewer {
  background: #ffffff;
  color: #333333;
}

:root[data-theme="light"] .toolbar {
  background: #f5f5f5;
  border-bottom-color: #e0e0e0;
}

:root[data-theme="light"] .image-wrapper {
  background-image: 
    linear-gradient(45deg, #f0f0f0 25%, transparent 25%),
    linear-gradient(-45deg, #f0f0f0 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #f0f0f0 75%),
    linear-gradient(-45deg, transparent 75%, #f0f0f0 75%);
}
</style>