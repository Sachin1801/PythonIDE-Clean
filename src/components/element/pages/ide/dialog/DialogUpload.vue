<template>
  <div>
    <div class="dialog-cover"></div>
    <div class="upload-dialog">
      <div class="dialog-header">
        <h3>Import File</h3>
        <div class="close-btn" @click="onCancel">
          <X :size="20" />
        </div>
      </div>
      
      <div class="dialog-body">
        <!-- Directory Navigation -->
        <div class="directory-section">
          <label>Select Directory:</label>
          <div class="directory-nav">
            <div class="current-path" @click="toggleDirectoryTree">
              <FolderOpen :size="16" />
              <span>{{ currentPath }}</span>
              <ChevronDown v-if="showDirectoryTree" :size="16" class="chevron" />
              <ChevronRight v-else :size="16" class="chevron" />
            </div>
            <div class="directory-tree" v-if="showDirectoryTree">
              <div 
                v-for="dir in directories" 
                :key="dir.path"
                class="directory-item"
                :class="{ 
                  selected: currentPath === dir.path,
                  'root-item': dir.isRoot 
                }"
                :style="{ paddingLeft: (dir.level * 20 + 12) + 'px' }"
                @click="selectDirectory(dir.path)"
              >
                <Home v-if="dir.isRoot" :size="14" />
                <template v-else>
                  <ChevronRight :size="14" />
                  <Folder :size="14" />
                </template>
                <span>{{ dir.isRoot ? 'Root (/)' : dir.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- File Upload Section -->
        <div class="upload-section">
          <label>Select File to Upload:</label>
          <div class="file-input-wrapper">
            <input 
              type="file" 
              ref="fileInput"
              @change="onFileSelect"
              accept=".py,.csv,.pdf,.png,.jpg,.jpeg,.gif,.bmp,.svg"
              class="file-input"
            />
            <div class="file-input-display" @click="$refs.fileInput.click()">
              <Upload :size="20" />
              <span v-if="!selectedFile">Click to select file...</span>
              <span v-else>{{ selectedFile.name }}</span>
            </div>
          </div>
          <div class="file-types-hint">
            Supported: .py, .csv, .pdf, .png, .jpg, .jpeg, .gif, .bmp, .svg
          </div>
        </div>

        <!-- Preview Section -->
        <div v-if="selectedFile" class="preview-section">
          <label>File Preview:</label>
          <div class="file-preview">
            <div class="file-info">
              <FileText :size="20" />
              <div>
                <div class="file-name">{{ selectedFile.name }}</div>
                <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn-cancel" @click="onCancel">Cancel</button>
        <button 
          class="btn-upload" 
          @click="onUpload"
          :disabled="!selectedFile || uploading"
        >
          {{ uploading ? 'Uploading...' : 'Upload' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { X, Upload, FolderOpen, Folder, ChevronRight, ChevronDown, FileText, Home } from 'lucide-vue-next';
import * as types from '../../../../../store/mutation-types';

export default {
  props: {
    modelValue: Boolean
  },
  data() {
    return {
      currentPath: '/',
      directories: [],
      selectedFile: null,
      uploading: false,
      showDirectoryTree: false,
    }
  },
  computed: {
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
  },
  components: {
    X,
    Upload,
    FolderOpen,
    Folder,
    ChevronRight,
    ChevronDown,
    FileText,
    Home,
  },
  mounted() {
    this.loadDirectoryStructure();
  },
  methods: {
    loadDirectoryStructure() {
      // Get directory structure from the project tree
      if (this.ideInfo.currProj && this.ideInfo.currProj.data) {
        // Build hierarchical directory structure
        this.directories = this.buildDirectoryTree(this.ideInfo.currProj.data);
        // Set current path to selected node if it's a directory
        if (this.ideInfo.nodeSelected && this.ideInfo.nodeSelected.type === 'dir') {
          this.currentPath = this.ideInfo.nodeSelected.path;
        }
      }
    },
    buildDirectoryTree(node, level = 0) {
      let dirs = [];
      
      // Add the root directory
      if (level === 0 && node.path === '/') {
        dirs.push({
          name: '/',
          path: '/',
          level: 0,
          isRoot: true
        });
      }
      
      // Process children
      if (node.children) {
        node.children.forEach(child => {
          if (child.type === 'dir' || child.type === 'folder') {
            dirs.push({
              name: child.label,
              path: child.path,
              level: level + 1,
              isRoot: false
            });
            // Recursively add subdirectories
            if (child.children) {
              dirs = dirs.concat(this.buildDirectoryTree(child, level + 1));
            }
          }
        });
      }
      
      return dirs;
    },
    selectDirectory(path) {
      this.currentPath = path;
      this.showDirectoryTree = false;
    },
    toggleDirectoryTree() {
      this.showDirectoryTree = !this.showDirectoryTree;
    },
    onFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        this.selectedFile = file;
      }
    },
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },
    async onUpload() {
      if (!this.selectedFile) return;
      
      this.uploading = true;
      
      try {
        // Read file content
        const reader = new FileReader();
        
        const fileName = this.selectedFile.name;
        const filePath = this.currentPath === '/' 
          ? `/${fileName}` 
          : `${this.currentPath}/${fileName}`;
        
        // Check if it's a binary file
        const isBinary = /\.(png|jpg|jpeg|gif|bmp|svg|pdf)$/i.test(fileName);
        
        reader.onload = (e) => {
          const content = e.target.result;
          
          if (isBinary) {
            // For binary files, content is already base64 from readAsDataURL
            // Remove the data URL prefix to get just the base64 data
            const base64 = content.split(',')[1];
            this.uploadFile(filePath, base64, true);
          } else {
            // Text files (.py, .csv)
            this.uploadFile(filePath, content, false);
          }
        };
        
        reader.onerror = (error) => {
          console.error('File read error:', error);
          this.uploading = false;
          alert('Failed to read file. Please try again.');
        };
        
        // Read as DataURL for binary files (automatically encodes to base64), text for others
        if (isBinary) {
          reader.readAsDataURL(this.selectedFile);
        } else {
          reader.readAsText(this.selectedFile);
        }
      } catch (error) {
        console.error('Upload error:', error);
        this.uploading = false;
      }
    },
    uploadFile(filePath, content, isBinary) {
      // Use the write file API to save the uploaded file
      this.$store.dispatch(`ide/${types.IDE_WRITE_FILE}`, {
        filePath: filePath,
        fileData: content,
        isBinary: isBinary,
        callback: (dict) => {
          this.uploading = false;
          if (dict && dict.code === 0) {
            // Success - refresh the project tree
            this.$emit('refresh-tree');
            // Clear the file selection
            this.selectedFile = null;
            if (this.$refs.fileInput) {
              this.$refs.fileInput.value = '';
            }
            // Close the dialog
            this.onCancel();
            // Show success message
            if (window.ElMessage) {
              window.ElMessage({
                type: 'success',
                message: 'File uploaded successfully',
                duration: 2000
              });
            }
          } else {
            console.error('Failed to upload file:', dict);
            alert('Failed to upload file. Please try again.');
          }
        }
      });
    },
    onCancel() {
      this.selectedFile = null;
      this.uploading = false;
      this.$emit('update:modelValue', false);
      this.$emit('close');
    }
  }
}
</script>

<style scoped>
.dialog-cover {
  background: #000;
  opacity: 0.5;
  position: fixed;
  z-index: 100;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.upload-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--bg-primary, #2a2a2a);
  color: var(--text-primary, #fff);
  border: 1px solid var(--border-color, #444);
  border-radius: 8px;
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  z-index: 101;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #444);
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.close-btn {
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.dialog-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.directory-section,
.upload-section,
.preview-section {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary, #ccc);
}

.directory-nav {
  border: 1px solid var(--border-color, #444);
  border-radius: 4px;
  overflow: hidden;
}

.current-path {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid var(--border-color, #444);
  font-size: 14px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.current-path:hover {
  background: rgba(255, 255, 255, 0.08);
}

.current-path .chevron {
  margin-left: auto;
}

.directory-tree {
  max-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
  background: rgba(0, 0, 0, 0.2);
}

.directory-tree::-webkit-scrollbar {
  width: 8px;
}

.directory-tree::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.directory-tree::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.directory-tree::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.directory-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
  white-space: nowrap;
  min-height: 32px;
}

.directory-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.directory-item.selected {
  background: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

.directory-item.root-item {
  font-weight: 500;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.file-input-wrapper {
  position: relative;
}

.file-input {
  display: none;
}

.file-input-display {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 2px dashed var(--border-color, #444);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.02);
}

.file-input-display:hover {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.file-types-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary, #999);
}

.file-preview {
  border: 1px solid var(--border-color, #444);
  border-radius: 4px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary, #999);
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, #444);
}

.btn-cancel,
.btn-upload {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: transparent;
  color: var(--text-primary, #fff);
  border: 1px solid var(--border-color, #444);
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-upload {
  background: #409eff;
  color: #fff;
}

.btn-upload:hover:not(:disabled) {
  background: #66b1ff;
}

.btn-upload:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Dark mode adjustments */
[data-theme="light"] .upload-dialog {
  background: #fff;
  color: #333;
}

[data-theme="light"] .dialog-header,
[data-theme="light"] .dialog-footer {
  border-color: #e0e0e0;
}

[data-theme="light"] .directory-nav,
[data-theme="light"] .file-preview {
  border-color: #e0e0e0;
}

[data-theme="light"] .current-path {
  background: #f5f5f5;
}

[data-theme="light"] .directory-item:hover,
[data-theme="light"] .file-input-display {
  background: #f5f5f5;
}

[data-theme="light"] .file-input-display {
  border-color: #d0d0d0;
}

[data-theme="light"] label {
  color: #666;
}

[data-theme="light"] .file-types-hint,
[data-theme="light"] .file-size {
  color: #888;
}
</style>