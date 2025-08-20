<template>
  <div class="pdf-viewer-container">
    <div class="pdf-toolbar">
      <div class="toolbar-left">
        <el-button @click="previousPage" :disabled="currentPage <= 1" size="small">
          <el-icon><arrow-left /></el-icon>
        </el-button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <el-button @click="nextPage" :disabled="currentPage >= totalPages" size="small">
          <el-icon><arrow-right /></el-icon>
        </el-button>
      </div>
      
      <div class="toolbar-center">
        <el-button-group>
          <el-button @click="zoomOut" size="small">
            <el-icon><zoom-out /></el-icon>
          </el-button>
          <el-button @click="resetZoom" size="small">
            {{ Math.round(scale * 100) }}%
          </el-button>
          <el-button @click="zoomIn" size="small">
            <el-icon><zoom-in /></el-icon>
          </el-button>
        </el-button-group>
      </div>
      
      <div class="toolbar-right">
        <el-button @click="fitToWidth" size="small">
          <el-icon><rank /></el-icon> Fit Width
        </el-button>
        <el-button @click="fitToPage" size="small">
          <el-icon><full-screen /></el-icon> Fit Page
        </el-button>
        <el-button @click="downloadPdf" size="small">
          <el-icon><download /></el-icon>
        </el-button>
      </div>
    </div>
    
    <div class="pdf-content" ref="pdfContainer" @wheel="handleWheel">
      <canvas ref="pdfCanvas" class="pdf-canvas"></canvas>
      <div v-if="loading" class="pdf-loading">
        <el-icon size="32" class="loading-spinner"><loading /></el-icon>
        <p>Loading PDF...</p>
      </div>
      <div v-if="error" class="pdf-error">
        <el-icon size="48"><document-delete /></el-icon>
        <p>{{ error }}</p>
        <el-button @click="loadPdf" type="primary" size="small">
          <el-icon><refresh /></el-icon> Retry
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { 
  ArrowLeft, 
  ArrowRight, 
  ZoomIn, 
  ZoomOut, 
  Download,
  Refresh,
  Loading,
  DocumentDelete,
  FullScreen,
  Rank
} from '@element-plus/icons-vue';
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf';
import { ElMessage } from 'element-plus';

// Configure PDF.js worker - using compatible version
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';

export default {
  name: 'PdfViewer',
  components: {
    ArrowLeft,
    ArrowRight,
    ZoomIn,
    ZoomOut,
    Download,
    Refresh,
    Loading,
    DocumentDelete,
    FullScreen,
    Rank
  },
  props: {
    pdfData: {
      type: String,
      required: true
    },
    fileName: {
      type: String,
      default: 'document.pdf'
    }
  },
  data() {
    return {
      pdfDoc: null,
      currentPage: 1,
      totalPages: 0,
      scale: 1.0,
      loading: false,
      error: null,
      renderTask: null,
      baseScale: 1.0
    };
  },
  mounted() {
    this.loadPdf();
    // Add resize listener
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    // Clean up
    window.removeEventListener('resize', this.handleResize);
    if (this.renderTask) {
      this.renderTask.cancel();
    }
  },
  watch: {
    pdfData() {
      this.loadPdf();
    },
    currentPage() {
      this.renderPage();
    },
    scale() {
      this.renderPage();
    }
  },
  methods: {
    async loadPdf() {
      if (!this.pdfData) {
        this.error = 'No PDF data provided';
        return;
      }
      
      this.loading = true;
      this.error = null;
      
      try {
        // Convert base64 to binary
        let pdfDataBinary;
        if (this.pdfData.startsWith('data:')) {
          // Extract base64 data from data URL
          const base64Data = this.pdfData.split(',')[1];
          const binaryString = atob(base64Data);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          pdfDataBinary = bytes;
        } else {
          // Assume it's already base64
          const binaryString = atob(this.pdfData);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          pdfDataBinary = bytes;
        }
        
        // Load PDF document
        const loadingTask = pdfjsLib.getDocument({ data: pdfDataBinary });
        this.pdfDoc = await loadingTask.promise;
        this.totalPages = this.pdfDoc.numPages;
        this.currentPage = 1;
        
        // Initial render
        await this.renderPage();
        
        // Calculate initial scale to fit
        this.$nextTick(() => {
          this.fitToWidth();
        });
        
      } catch (err) {
        console.error('Error loading PDF:', err);
        this.error = 'Failed to load PDF: ' + err.message;
      } finally {
        this.loading = false;
      }
    },
    
    async renderPage() {
      if (!this.pdfDoc) return;
      
      // Cancel any ongoing render
      if (this.renderTask) {
        await this.renderTask.cancel();
      }
      
      try {
        const page = await this.pdfDoc.getPage(this.currentPage);
        const viewport = page.getViewport({ scale: this.scale });
        
        const canvas = this.$refs.pdfCanvas;
        if (!canvas) return;
        
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        const renderContext = {
          canvasContext: context,
          viewport: viewport
        };
        
        this.renderTask = page.render(renderContext);
        await this.renderTask.promise;
        
      } catch (err) {
        if (err.name !== 'RenderingCancelledException') {
          console.error('Error rendering page:', err);
        }
      }
    },
    
    previousPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },
    
    zoomIn() {
      this.scale = Math.min(this.scale * 1.2, 3.0);
    },
    
    zoomOut() {
      this.scale = Math.max(this.scale * 0.8, 0.5);
    },
    
    resetZoom() {
      this.scale = 1.0;
    },
    
    fitToWidth() {
      if (!this.pdfDoc || !this.$refs.pdfContainer) return;
      
      this.pdfDoc.getPage(this.currentPage).then(page => {
        const viewport = page.getViewport({ scale: 1.0 });
        const containerWidth = this.$refs.pdfContainer.clientWidth - 40; // Padding
        this.scale = containerWidth / viewport.width;
        this.baseScale = this.scale;
      });
    },
    
    fitToPage() {
      if (!this.pdfDoc || !this.$refs.pdfContainer) return;
      
      this.pdfDoc.getPage(this.currentPage).then(page => {
        const viewport = page.getViewport({ scale: 1.0 });
        const containerWidth = this.$refs.pdfContainer.clientWidth - 40;
        const containerHeight = this.$refs.pdfContainer.clientHeight - 40;
        
        const scaleX = containerWidth / viewport.width;
        const scaleY = containerHeight / viewport.height;
        this.scale = Math.min(scaleX, scaleY);
        this.baseScale = this.scale;
      });
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
    
    handleResize() {
      // Recalculate scale on window resize
      if (this.baseScale === this.scale) {
        this.fitToWidth();
      }
    },
    
    downloadPdf() {
      try {
        // Convert base64 to blob
        let base64Data;
        if (this.pdfData.startsWith('data:')) {
          base64Data = this.pdfData.split(',')[1];
        } else {
          base64Data = this.pdfData;
        }
        
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });
        
        // Create download link
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = this.fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        ElMessage.success('PDF downloaded successfully');
      } catch (err) {
        console.error('Download error:', err);
        ElMessage.error('Failed to download PDF');
      }
    }
  }
};
</script>

<style scoped>
.pdf-viewer-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
}

.pdf-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.toolbar-left,
.toolbar-center,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-info {
  padding: 0 12px;
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.pdf-content {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 20px;
  position: relative;
}

.pdf-canvas {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: white;
  max-width: 100%;
  height: auto;
}

.pdf-loading,
.pdf-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #909399;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.pdf-error {
  color: #f56c6c;
}

.pdf-error p {
  margin: 12px 0;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .pdf-toolbar {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .toolbar-left,
  .toolbar-center,
  .toolbar-right {
    flex: 1;
    justify-content: center;
  }
}
</style>