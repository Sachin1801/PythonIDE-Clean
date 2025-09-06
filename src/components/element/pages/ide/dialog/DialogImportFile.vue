<template>
  <div>
    <div class="dialog-cover"></div>
    <div class="import-file-dialog">
      <div class="dialog-header">
        <h3>Import Files</h3>
        <div class="close-btn" @click="onCancel">
          <X :size="20" />
        </div>
      </div>
      
      <div class="dialog-body">
        <!-- Directory Navigation -->
        <div class="directory-section">
          <label>Select Destination Directory:</label>
          <div class="directory-nav">
            <div class="current-path" @click="toggleDirectoryTree">
              <FolderOpen :size="16" />
              <span>{{ formatCurrentPath(currentPath) }}</span>
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
                @click="selectDirectory(dir)"
              >
                <Home v-if="dir.isRoot" :size="14" />
                <template v-else>
                  <ChevronRight :size="14" />
                  <Folder :size="14" />
                </template>
                <span>{{ dir.displayName || dir.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- File Upload Section -->
        <div class="upload-section">
          <label>Select Files to Import:</label>
          <div class="file-drop-area" 
               :class="{ 'drag-over': dragOver }"
               @drop="handleDrop"
               @dragover.prevent="dragOver = true"
               @dragleave.prevent="dragOver = false"
               @click="triggerFileInput">
            <input 
              type="file" 
              ref="fileInput"
              @change="handleFileSelect"
              multiple
              accept=".py,.txt,.csv,.pdf"
              style="display: none;"
            />
            <div class="upload-icon">
              <Upload :size="48" />
            </div>
            <div class="upload-text">
              <div class="main-text">Click to select files or drag and drop</div>
              <div class="sub-text">Supported formats: .py, .txt, .csv, .pdf</div>
            </div>
          </div>
          <div v-if="uploadError" class="error-hint">
            {{ uploadError }}
          </div>
        </div>

        <!-- Selected Files Section -->
        <div v-if="selectedFiles.length > 0" class="selected-files-section">
          <label>Selected Files ({{ selectedFiles.length }}):</label>
          <div class="selected-files-list">
            <div 
              v-for="(file, index) in selectedFiles" 
              :key="index"
              class="file-item"
            >
              <div class="file-info">
                <img :src="getFileIcon(file.name)" alt="" class="file-icon" />
                <div class="file-details">
                  <div class="file-name">{{ file.name }}</div>
                  <div class="file-size">{{ formatFileSize(file.size) }}</div>
                </div>
              </div>
              <button class="remove-btn" @click="removeFile(index)" title="Remove">
                <X :size="16" />
              </button>
            </div>
          </div>
        </div>

        <!-- Preview Section -->
        <div v-if="selectedFiles.length > 0 && !uploadError" class="preview-section">
          <label>Files will be imported to:</label>
          <div class="import-preview">
            <div class="destination-info">
              <FolderOpen :size="20" />
              <div>
                <div class="destination-path">{{ formatCurrentPath(currentPath) }}</div>
                <div class="file-count">{{ selectedFiles.length }} file(s) selected</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn-cancel" @click="onCancel">Cancel</button>
        <button 
          class="btn-import" 
          @click="onImport"
          :disabled="selectedFiles.length === 0 || uploading"
        >
          {{ uploading ? 'Importing...' : `Import ${selectedFiles.length} file(s)` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { X, FolderOpen, Folder, ChevronRight, ChevronDown, Upload, Home } from 'lucide-vue-next';
import * as types from '../../../../../store/mutation-types';
import { ElMessage } from 'element-plus';
import { getIconForFile } from 'vscode-icons-js';

export default {
  props: {
    modelValue: Boolean
  },
  data() {
    return {
      currentPath: '/',
      currentProject: null,
      directories: [],
      selectedFiles: [],
      uploadError: '',
      uploading: false,
      showDirectoryTree: false,
      dragOver: false,
      supportedExtensions: ['.py', '.txt', '.csv', '.pdf']
    }
  },
  computed: {
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
    currentUser() {
      const sessionId = localStorage.getItem('session_id');
      const username = localStorage.getItem('username');
      const role = localStorage.getItem('role');
      const fullName = localStorage.getItem('full_name');
      if (sessionId && username) {
        return { session_id: sessionId, username: username, role: role, full_name: fullName };
      }
      return null;
    }
  },
  components: {
    X,
    FolderOpen,
    Folder,
    ChevronRight,
    ChevronDown,
    Upload,
    Home
  },
  mounted() {
    this.loadDirectoryStructure();
  },
  methods: {
    loadDirectoryStructure() {
      // Get directory structure from all projects (multi-root mode)
      if (this.ideInfo.multiRootData && this.ideInfo.multiRootData.children.length > 0) {
        // Build directory tree from all projects
        this.directories = [];
        this.ideInfo.multiRootData.children.forEach(project => {
          // Add each project and its subdirectories
          const projectDirs = this.buildDirectoryTree(project, 0, project.label);
          this.directories = this.directories.concat(projectDirs);
        });
      } else if (this.ideInfo.currProj && this.ideInfo.currProj.data) {
        // Fallback to single project mode
        this.directories = this.buildDirectoryTree(this.ideInfo.currProj.data, 0, this.ideInfo.currProj.data.label);
      }
      
      // Set current path to selected node if it's a directory
      if (this.ideInfo.nodeSelected) {
        if (this.ideInfo.nodeSelected.type === 'dir' || this.ideInfo.nodeSelected.type === 'folder') {
          this.currentPath = this.ideInfo.nodeSelected.path;
          this.currentProject = this.ideInfo.nodeSelected.projectName || this.ideInfo.currProj?.data?.name;
        } else if (this.ideInfo.nodeSelected.type === 'file') {
          // If a file is selected, use its parent directory
          const parentPath = this.ideInfo.nodeSelected.path.substring(0, this.ideInfo.nodeSelected.path.lastIndexOf('/')) || '/';
          this.currentPath = parentPath;
          this.currentProject = this.ideInfo.nodeSelected.projectName || this.ideInfo.currProj?.data?.name;
        }
      } else {
        // Default to current project root
        this.currentProject = this.ideInfo.currProj?.data?.name || this.ideInfo.currProj?.config?.name;
      }
    },
    
    buildDirectoryTree(node, level = 0, projectName = null) {
      let dirs = [];
      
      // Add the root directory
      if (level === 0) {
        dirs.push({
          name: projectName || node.label || '/',
          displayName: projectName || node.label || '/',
          path: node.path || '/',
          level: 0,
          isRoot: true,
          projectName: projectName || node.label,
          fullPath: projectName ? `${projectName}${node.path}` : node.path
        });
      }
      
      // Process children
      if (node.children) {
        node.children.forEach(child => {
          if (child.type === 'dir' || child.type === 'folder') {
            dirs.push({
              name: child.label,
              displayName: child.label,
              path: child.path,
              level: level + 1,
              isRoot: false,
              projectName: projectName || child.projectName,
              fullPath: projectName ? `${projectName}${child.path}` : child.path
            });
            // Recursively add subdirectories
            if (child.children) {
              dirs = dirs.concat(this.buildDirectoryTree(child, level + 1, projectName));
            }
          }
        });
      }
      
      return dirs;
    },
    
    selectDirectory(dir) {
      this.currentPath = dir.path;
      this.currentProject = dir.projectName;
      this.showDirectoryTree = false;
    },
    
    toggleDirectoryTree() {
      this.showDirectoryTree = !this.showDirectoryTree;
    },
    
    formatCurrentPath(path) {
      if (this.currentProject) {
        if (path === '/') {
          return this.currentProject;
        }
        // Only add project name if path doesn't already contain it
        if (!path.startsWith(this.currentProject)) {
          return this.currentProject + path;
        }
        return path;
      }
      
      // Fallback to current project if no specific project context
      if (path === '/' && this.ideInfo.currProj) {
        return this.ideInfo.currProj.data?.label || this.ideInfo.currProj.config?.name;
      }
      if (path.startsWith('/') && this.ideInfo.currProj) {
        const projName = this.ideInfo.currProj.data?.label || this.ideInfo.currProj.config?.name;
        // Check if path already includes project name
        if (!path.includes(projName)) {
          return projName + path;
        }
        return path;
      }
      return path;
    },
    
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    
    handleFileSelect(event) {
      const files = Array.from(event.target.files);
      this.processFiles(files);
    },
    
    handleDrop(event) {
      event.preventDefault();
      this.dragOver = false;
      const files = Array.from(event.dataTransfer.files);
      this.processFiles(files);
    },
    
    processFiles(files) {
      this.uploadError = '';
      const validFiles = [];
      const invalidFiles = [];
      
      files.forEach(file => {
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (this.supportedExtensions.includes(fileExtension)) {
          // Check file size (limit to 10MB)
          if (file.size <= 10 * 1024 * 1024) {
            validFiles.push(file);
          } else {
            invalidFiles.push(`${file.name} (file too large, max 10MB)`);
          }
        } else {
          invalidFiles.push(`${file.name} (unsupported format)`);
        }
      });
      
      if (invalidFiles.length > 0) {
        this.uploadError = `Invalid files: ${invalidFiles.join(', ')}`;
      }
      
      // Add valid files to selection (avoid duplicates)
      validFiles.forEach(file => {
        const exists = this.selectedFiles.some(existing => 
          existing.name === file.name && existing.size === file.size
        );
        if (!exists) {
          this.selectedFiles.push(file);
        }
      });
    },
    
    removeFile(index) {
      this.selectedFiles.splice(index, 1);
      if (this.selectedFiles.length === 0) {
        this.uploadError = '';
      }
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    getFileIcon(fileName) {
      const extension = fileName.substring(fileName.lastIndexOf('.') + 1);
      return require(`@/assets/vscode-icons/${getIconForFile(extension)}`);
    },
    
    async onImport() {
      if (this.selectedFiles.length === 0) return;
      
      this.uploading = true;
      const projectName = this.currentProject || this.ideInfo.currProj?.data?.name || this.ideInfo.currProj?.config?.name;
      
      // Fix: Ensure we send the raw path within the project, not the formatted display path
      let parentPath = this.currentPath;
      
      // If currentPath contains project name (from multi-root mode), remove it
      if (parentPath && projectName && parentPath.startsWith(projectName)) {
        parentPath = parentPath.substring(projectName.length) || '/';
      }
      
      // Ensure path starts with / for consistency
      if (parentPath && !parentPath.startsWith('/')) {
        parentPath = '/' + parentPath;
      }
      
      console.log('[DialogImportFile] Upload params:', {
        projectName,
        rawCurrentPath: this.currentPath,
        cleanedParentPath: parentPath
      });
      
      try {
        const uploadPromises = this.selectedFiles.map(async (file) => {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('projectName', projectName);
          formData.append('parentPath', parentPath);
          formData.append('filename', file.name);
          
          const response = await fetch('/api/upload-file', {
            method: 'POST',
            body: formData,
            headers: {
              'session-id': this.currentUser?.session_id
            }
          });
          
          const result = await response.json();
          if (!result.success) {
            throw new Error(`Failed to upload ${file.name}: ${result.error}`);
          }
          return result;
        });
        
        await Promise.all(uploadPromises);
        
        ElMessage.success(`Successfully imported ${this.selectedFiles.length} file(s)`);
        
        // Refresh the project tree
        this.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
          projectName: projectName,
          callback: (projectResponse) => {
            if (projectResponse.code === 0) {
              this.$store.commit('ide/handleProject', projectResponse.data);
              
              // If in multi-root mode, refresh all projects
              if (this.ideInfo.multiRootData) {
                this.$parent.loadAllDefaultProjects?.();
              }
            }
          }
        });
        
        // Emit event to notify parent
        this.$emit('files-imported', {
          count: this.selectedFiles.length,
          destination: this.currentPath,
          projectName: projectName
        });
        
        // Close dialog
        this.$emit('update:modelValue', false);
        
      } catch (error) {
        console.error('[DialogImportFile] Error importing files:', error);
        ElMessage.error('Failed to import files: ' + error.message);
      } finally {
        this.uploading = false;
      }
    },
    
    onCancel() {
      this.$emit('update:modelValue', false);
    }
  }
}
</script>

<style scoped>
.dialog-cover {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9998;
}

.import-file-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #464647);
  border-radius: 8px;
  width: 700px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  z-index: 9999;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #464647);
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary, #cccccc);
}

.close-btn {
  cursor: pointer;
  color: var(--text-secondary, #969696);
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--hover-bg, rgba(255, 255, 255, 0.1));
  color: var(--text-primary, #cccccc);
}

.dialog-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  max-height: 60vh;
}

.directory-section,
.upload-section,
.selected-files-section,
.preview-section {
  margin-bottom: 20px;
}

.directory-section label,
.upload-section label,
.selected-files-section label,
.preview-section label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #cccccc);
}

.directory-nav {
  position: relative;
}

.current-path {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--input-bg, #2d2d30);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-primary, #cccccc);
}

.current-path:hover {
  background: var(--hover-bg, #383838);
  border-color: var(--accent-color, #007acc);
}

.current-path .chevron {
  margin-left: auto;
}

.directory-tree {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: var(--dropdown-bg, #252526);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.directory-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.2s;
  color: var(--text-primary, #cccccc);
  font-size: 13px;
}

.directory-item:hover {
  background: var(--hover-bg, #094771);
}

.directory-item.selected {
  background: var(--selected-bg, #094771);
}

.directory-item.root-item {
  font-weight: 500;
  border-bottom: 1px solid var(--border-color, #464647);
}

.file-drop-area {
  border: 2px dashed var(--border-color, #464647);
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--input-bg, #2d2d30);
}

.file-drop-area:hover,
.file-drop-area.drag-over {
  border-color: var(--accent-color, #007acc);
  background: var(--hover-bg, rgba(0, 122, 204, 0.1));
}

.upload-icon {
  color: var(--text-secondary, #969696);
  margin-bottom: 16px;
}

.upload-text .main-text {
  font-size: 16px;
  color: var(--text-primary, #cccccc);
  margin-bottom: 8px;
}

.upload-text .sub-text {
  font-size: 13px;
  color: var(--text-secondary, #969696);
}

.error-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--error-color, #f44747);
}

.selected-files-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  background: var(--input-bg, #2d2d30);
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid var(--border-color, #464647);
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  width: 20px;
  height: 20px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 14px;
  color: var(--text-primary, #cccccc);
  margin-bottom: 2px;
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary, #969696);
}

.remove-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary, #969696);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: var(--hover-bg, rgba(255, 255, 255, 0.1));
  color: var(--error-color, #f44747);
}

.import-preview {
  padding: 12px;
  background: var(--preview-bg, #252526);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
}

.destination-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.destination-path {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: var(--text-primary, #cccccc);
  word-break: break-all;
}

.file-count {
  font-size: 12px;
  color: var(--text-secondary, #969696);
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, #464647);
}

.btn-cancel,
.btn-import {
  padding: 8px 20px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel {
  background: var(--button-secondary-bg, #2d2d30);
  color: var(--text-primary, #cccccc);
  border: 1px solid var(--border-color, #464647);
}

.btn-cancel:hover {
  background: var(--hover-bg, #383838);
}

.btn-import {
  background: var(--accent-color, #007acc);
  color: white;
}

.btn-import:hover:not(:disabled) {
  background: var(--accent-hover, #005a9e);
}

.btn-import:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Scrollbar styles */
.directory-tree::-webkit-scrollbar,
.dialog-body::-webkit-scrollbar,
.selected-files-list::-webkit-scrollbar {
  width: 8px;
}

.directory-tree::-webkit-scrollbar-track,
.dialog-body::-webkit-scrollbar-track,
.selected-files-list::-webkit-scrollbar-track {
  background: var(--scrollbar-track, #1e1e1e);
}

.directory-tree::-webkit-scrollbar-thumb,
.dialog-body::-webkit-scrollbar-thumb,
.selected-files-list::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb, #464647);
  border-radius: 4px;
}

.directory-tree::-webkit-scrollbar-thumb:hover,
.dialog-body::-webkit-scrollbar-thumb:hover,
.selected-files-list::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover, #5a5a5a);
}
</style>