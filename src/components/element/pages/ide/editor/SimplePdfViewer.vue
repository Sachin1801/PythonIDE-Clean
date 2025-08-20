<template>
  <div class="simple-pdf-viewer">
    <div class="pdf-toolbar">
      <el-button @click="downloadPdf" size="small">
        <el-icon><download /></el-icon> Download PDF
      </el-button>
    </div>
    <div class="pdf-content">
      <iframe 
        v-if="pdfUrl" 
        :src="pdfUrl" 
        class="pdf-iframe"
        @error="handleError"
      />
      <div v-else class="pdf-error">
        <el-icon size="48"><document-delete /></el-icon>
        <p>Unable to display PDF</p>
        <el-button @click="downloadPdf" type="primary" size="small">
          Download PDF Instead
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { Download, DocumentDelete } from '@element-plus/icons-vue';

export default {
  name: 'SimplePdfViewer',
  components: {
    Download,
    DocumentDelete
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
  computed: {
    pdfUrl() {
      if (!this.pdfData) return null;
      
      try {
        // If it's already a data URL, use it directly
        if (this.pdfData.startsWith('data:')) {
          return this.pdfData;
        }
        
        // Try to create a data URL from base64
        // Clean the base64 string (remove any whitespace/newlines)
        const cleanBase64 = this.pdfData.replace(/[\s\n\r]/g, '');
        
        // Add padding if needed
        const padding = (4 - (cleanBase64.length % 4)) % 4;
        const paddedBase64 = cleanBase64 + '='.repeat(padding);
        
        // Create data URL
        return `data:application/pdf;base64,${paddedBase64}`;
      } catch (err) {
        console.error('Error creating PDF URL:', err);
        return null;
      }
    }
  },
  methods: {
    handleError() {
      console.error('Failed to load PDF in iframe');
    },
    
    downloadPdf() {
      try {
        let base64Data = this.pdfData;
        
        // Extract base64 if it's a data URL
        if (this.pdfData.startsWith('data:')) {
          base64Data = this.pdfData.split(',')[1];
        }
        
        // Clean and pad the base64 string
        const cleanBase64 = base64Data.replace(/[\s\n\r]/g, '');
        const padding = (4 - (cleanBase64.length % 4)) % 4;
        const paddedBase64 = cleanBase64 + '='.repeat(padding);
        
        // Try to decode and create blob
        const binaryString = atob(paddedBase64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        
        const blob = new Blob([bytes], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        
        // Create download link
        const link = document.createElement('a');
        link.href = url;
        link.download = this.fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        setTimeout(() => window.URL.revokeObjectURL(url), 100);
      } catch (err) {
        console.error('Error downloading PDF:', err);
        // Fallback: try to download the raw data URL
        if (this.pdfUrl) {
          const link = document.createElement('a');
          link.href = this.pdfUrl;
          link.download = this.fileName;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
      }
    }
  }
};
</script>

<style scoped>
.simple-pdf-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.pdf-toolbar {
  padding: 10px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
}

.pdf-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}

.pdf-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.pdf-error p {
  margin: 20px 0;
  font-size: 16px;
}
</style>