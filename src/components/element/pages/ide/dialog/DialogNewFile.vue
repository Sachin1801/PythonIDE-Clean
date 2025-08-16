<template>
  <div>
    <div class="dialog-cover"></div>
    <div class="new-file-dialog">
      <div class="dialog-header">
        <h3>New File</h3>
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

        <!-- File Name Section -->
        <div class="filename-section">
          <label>File Name:</label>
          <div class="filename-input-wrapper">
            <input 
              type="text" 
              v-model="fileName"
              @input="validateFileName"
              placeholder="Enter file name (e.g., script.py)"
              class="filename-input"
              ref="fileNameInput"
            />
            <div v-if="fileExtension" class="file-type-icon">
              <FileText :size="20" />
            </div>
          </div>
          <div v-if="fileNameError" class="error-hint">
            {{ fileNameError }}
          </div>
          <div v-else class="file-types-hint">
            Common extensions: .py, .txt, .csv, .json, .md, .html, .css, .js
          </div>
        </div>



        <!-- Preview Section -->
        <div v-if="fileName && !fileNameError" class="preview-section">
          <label>File will be created at:</label>
          <div class="file-preview">
            <div class="file-info">
              <FileText :size="20" />
              <div>
                <div class="file-path">{{ getFullFilePath() }}</div>
                <div class="file-type">{{ getFileTypeDescription() }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn-cancel" @click="onCancel">Cancel</button>
        <button 
          class="btn-create" 
          @click="onCreate"
          :disabled="!fileName || !!fileNameError || creating"
        >
          {{ creating ? 'Creating...' : 'Create File' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { X, FolderOpen, Folder, ChevronRight, ChevronDown, FileText, Home } from 'lucide-vue-next';
import * as types from '../../../../../store/mutation-types';
import { ElMessage } from 'element-plus';

export default {
  props: {
    modelValue: Boolean
  },
  data() {
    return {
      currentPath: '/',
      currentProject: null,
      directories: [],
      fileName: '',
      fileNameError: '',
      creating: false,
      showDirectoryTree: false,

    }
  },
  computed: {
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
    fileExtension() {
      if (!this.fileName) return '';
      const lastDot = this.fileName.lastIndexOf('.');
      return lastDot > 0 ? this.fileName.substring(lastDot) : '';
    }
  },
  components: {
    X,
    FolderOpen,
    Folder,
    ChevronRight,
    ChevronDown,
    FileText,
    Home
  },
  mounted() {
    this.loadDirectoryStructure();
    // Focus on file name input
    this.$nextTick(() => {
      this.$refs.fileNameInput?.focus();
    });
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
        return this.currentProject + path;
      }
      // Fallback to current project if no specific project context
      if (path === '/' && this.ideInfo.currProj) {
        return this.ideInfo.currProj.data?.label || this.ideInfo.currProj.config?.name;
      }
      if (path.startsWith('/') && this.ideInfo.currProj) {
        return (this.ideInfo.currProj.data?.label || this.ideInfo.currProj.config?.name) + path;
      }
      return path;
    },
    validateFileName() {
      this.fileNameError = '';
      
      if (!this.fileName) {
        return;
      }
      
      // Check for invalid characters
      if (/[<>:"|?*\\]/.test(this.fileName)) {
        this.fileNameError = 'File name contains invalid characters';
        return;
      }
      
      // Check for reserved names
      const reserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                       'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                       'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'];
      const nameWithoutExt = this.fileName.split('.')[0].toUpperCase();
      if (reserved.includes(nameWithoutExt)) {
        this.fileNameError = 'This is a reserved file name';
        return;
      }
      
      // Check if file starts or ends with dot
      if (this.fileName.startsWith('.') || this.fileName.endsWith('.')) {
        this.fileNameError = 'File name cannot start or end with a dot';
        return;
      }
      
      // Warn if no extension
      if (!this.fileExtension) {
        this.fileNameError = 'Consider adding a file extension (e.g., .py, .txt)';
      }
    },

    getFullFilePath() {
      const fileName = this.fileName || 'new_file';
      const path = this.currentPath === '/' 
        ? `/${fileName}` 
        : `${this.currentPath}/${fileName}`;
      
      return this.formatCurrentPath(path);
    },
    getFileTypeDescription() {
      const ext = this.fileExtension.toLowerCase();
      const types = {
        '.py': 'Python Script',
        '.txt': 'Text File',
        '.csv': 'CSV Data File',
        '.json': 'JSON Data File',
        '.md': 'Markdown Document',
        '.html': 'HTML Document',
        '.css': 'CSS Stylesheet',
        '.js': 'JavaScript File',
        '.xml': 'XML Document',
        '.yaml': 'YAML Configuration',
        '.yml': 'YAML Configuration',
        '.ini': 'Configuration File',
        '.log': 'Log File'
      };
      return types[ext] || 'File';
    },
    async onCreate() {
      if (!this.fileName || this.fileNameError) return;
      
      this.creating = true;
      
      try {
        const fileName = this.fileName;
        const parentPath = this.currentPath;
        const projectName = this.currentProject || this.ideInfo.currProj?.data?.name || this.ideInfo.currProj?.config?.name;
        
        console.log('[DialogNewFile] Creating file:', {
          fileName,
          parentPath,
          projectName
        });
        
        // Default content based on extension
        let initialContent = '';
        const ext = this.fileExtension.toLowerCase();
        if (ext === '.py') {
          initialContent = '#!/usr/bin/env python3\n\n';
        } else if (ext === '.json') {
          initialContent = '{}';
        }
        
        // Create the file using the IDE store action
        await new Promise((resolve, reject) => {
          this.$store.dispatch(`ide/${types.IDE_CREATE_FILE}`, {
            projectName: projectName,
            parentPath: parentPath,
            fileName: fileName,
            callback: (response) => {
              console.log('[DialogNewFile] Create file response:', response);
              
              if (response.code === 0) {
                // File created successfully
                ElMessage.success(`File "${fileName}" created successfully`);
                
                // If we have initial content, write it to the file
                if (initialContent) {
                  const filePath = parentPath === '/' ? `/${fileName}` : `${parentPath}/${fileName}`;
                  this.$store.dispatch(`ide/${types.IDE_WRITE_FILE}`, {
                    projectName: projectName,
                    filePath: filePath,
                    fileData: initialContent,
                    callback: (writeResponse) => {
                      console.log('[DialogNewFile] Write file response:', writeResponse);
                      resolve();
                    }
                  });
                } else {
                  resolve();
                }
                
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
                
                // Open the newly created file
                const newFilePath = parentPath === '/' ? `/${fileName}` : `${parentPath}/${fileName}`;
                this.$emit('file-created', {
                  path: newFilePath,
                  projectName: projectName
                });
                
                // Close dialog
                this.$emit('update:modelValue', false);
              } else {
                // Error creating file
                const errorMsg = response.message || 'Failed to create file';
                ElMessage.error(errorMsg);
                reject(new Error(errorMsg));
              }
            }
          });
        });
      } catch (error) {
        console.error('[DialogNewFile] Error creating file:', error);
        ElMessage.error('Failed to create file: ' + error.message);
      } finally {
        this.creating = false;
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

.new-file-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #464647);
  border-radius: 8px;
  width: 600px;
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
.filename-section,
.preview-section {
  margin-bottom: 20px;
}

.directory-section label,
.filename-section label,
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

.filename-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filename-input {
  flex: 1;
  padding: 10px 12px;
  background: var(--input-bg, #2d2d30);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  color: var(--text-primary, #cccccc);
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  transition: all 0.2s;
}

.filename-input:focus {
  outline: none;
  border-color: var(--accent-color, #007acc);
  background: var(--input-focus-bg, #383838);
}

.filename-input::placeholder {
  color: var(--text-disabled, #6b6b6b);
}

.file-type-icon {
  color: var(--text-secondary, #969696);
}

.file-types-hint,
.error-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-secondary, #969696);
}

.error-hint {
  color: var(--error-color, #f44747);
}



.file-preview {
  padding: 12px;
  background: var(--preview-bg, #252526);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-path {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: var(--text-primary, #cccccc);
  word-break: break-all;
}

.file-type {
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
.btn-create {
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

.btn-create {
  background: var(--accent-color, #007acc);
  color: white;
}

.btn-create:hover:not(:disabled) {
  background: var(--accent-hover, #005a9e);
}

.btn-create:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Scrollbar styles */
.directory-tree::-webkit-scrollbar,
.dialog-body::-webkit-scrollbar {
  width: 8px;
}

.directory-tree::-webkit-scrollbar-track,
.dialog-body::-webkit-scrollbar-track {
  background: var(--scrollbar-track, #1e1e1e);
}

.directory-tree::-webkit-scrollbar-thumb,
.dialog-body::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb, #464647);
  border-radius: 4px;
}

.directory-tree::-webkit-scrollbar-thumb:hover,
.dialog-body::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover, #5a5a5a);
}
</style>