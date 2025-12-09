<template>
  <div>
    <div class="dialog-cover"></div>
    <div class="bulk-upload-dialog">
      <div class="dialog-header">
        <h3>Bulk Upload to Students</h3>
        <div class="close-btn" @click="onCancel">
          <X :size="20" />
        </div>
      </div>

      <div class="dialog-body">
        <!-- Target Students Selection -->
        <div class="students-section">
          <label>Upload To:</label>
          <div class="target-selection">
            <button
              :class="{ active: targetMode === 'all' }"
              @click="targetMode = 'all'"
              class="target-btn"
            >
              <Users :size="16" />
              All Students ({{ totalStudents }})
            </button>
            <button
              :class="{ active: targetMode === 'specific' }"
              @click="targetMode = 'specific'"
              class="target-btn"
            >
              <UserCheck :size="16" />
              Specific Students
            </button>
          </div>

          <!-- Specific Students Selector -->
          <div v-if="targetMode === 'specific'" class="specific-students">
            <input
              type="text"
              v-model="studentSearch"
              placeholder="Search students..."
              class="search-input"
            />
            <div class="student-list">
              <div
                v-for="student in filteredStudents"
                :key="student.username"
                class="student-item"
                :class="{ selected: isStudentSelected(student.username) }"
                @click="toggleStudent(student.username)"
              >
                <input
                  type="checkbox"
                  :checked="isStudentSelected(student.username)"
                  @change.stop="toggleStudent(student.username)"
                />
                <div class="student-info">
                  <span class="username">{{ student.username }}</span>
                  <span class="fullname">{{ student.full_name }}</span>
                </div>
              </div>
            </div>
            <div class="selection-summary">
              Selected: {{ selectedStudents.length }} student(s)
            </div>
          </div>
        </div>

        <!-- Common Folder Path -->
        <div class="folder-section">
          <label>Destination Folder (optional - leave empty for root):</label>
          <div class="folder-input-group">
            <input
              type="text"
              v-model="commonFolder"
              placeholder="Leave empty for root, or e.g., Examples"
              class="folder-input"
            />
            <span class="path-separator">/</span>
            <input
              type="text"
              v-model="subPath"
              placeholder="e.g., Week1 (optional)"
              class="folder-input"
            />
          </div>
          <div class="path-preview">
            Path: <code>Local/&lt;username&gt;/{{ previewPath }}</code>
          </div>
        </div>

        <!-- Upload Mode Toggle -->
        <div class="upload-section">
          <label>Select Files or Folder:</label>

          <div class="upload-mode-toggle">
            <button
              :class="{ active: uploadMode === 'files' }"
              @click="switchUploadMode('files')"
              class="mode-btn"
            >
              Files
            </button>
            <button
              :class="{ active: uploadMode === 'folder' }"
              @click="switchUploadMode('folder')"
              class="mode-btn"
            >
              Folder
            </button>
          </div>

          <!-- File Drop Area -->
          <div class="file-drop-area"
               :class="{ 'drag-over': dragOver }"
               @drop="handleDrop"
               @dragover.prevent="dragOver = true"
               @dragleave.prevent="dragOver = false"
               @click="triggerFileInput">
            <input
              v-if="uploadMode === 'files'"
              type="file"
              ref="fileInput"
              @change="handleFileSelect"
              multiple
              accept=".py,.txt,.csv,.pdf"
              style="display: none;"
            />
            <input
              v-else
              type="file"
              ref="folderInput"
              @change="handleFolderSelect"
              webkitdirectory
              directory
              multiple
              style="display: none;"
            />
            <div class="upload-icon">
              <Upload :size="48" />
            </div>
            <div class="upload-text">
              <div class="main-text">
                {{ uploadMode === 'files' ? 'Click to select files or drag and drop' : 'Click to select folder or drag and drop' }}
              </div>
              <div class="sub-text">
                Supported formats: .py, .txt, .csv, .pdf
              </div>
            </div>
          </div>
          <div v-if="uploadError" class="error-hint">
            {{ uploadError }}
          </div>
        </div>

        <!-- Selected Files Preview -->
        <div v-if="selectedFiles.length > 0" class="preview-section">
          <label>Files to Upload ({{ selectedFiles.length }}):</label>
          <div class="files-preview">
            <div v-for="(file, index) in selectedFiles.slice(0, 5)" :key="index" class="file-preview-item">
              <img :src="getFileIcon(file.name)" alt="" class="file-icon" />
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
            </div>
            <div v-if="selectedFiles.length > 5" class="more-files">
              + {{ selectedFiles.length - 5 }} more files
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn-cancel" @click="onCancel">Cancel</button>
        <button
          class="btn-upload"
          @click="onBulkUpload"
          :disabled="!canUpload || uploading"
        >
          {{ uploading ? 'Uploading...' : `Upload to ${targetCount} Student(s)` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { X, Upload, Users, UserCheck, FolderOpen } from 'lucide-vue-next';
import { ElMessage } from 'element-plus';
import { getIconForFile } from 'vscode-icons-js';

export default {
  props: {
    modelValue: Boolean
  },
  data() {
    return {
      targetMode: 'all', // 'all' or 'specific'
      selectedStudents: [],
      studentSearch: '',
      allStudents: [],
      commonFolder: '',
      subPath: '',
      uploadMode: 'files', // 'files' or 'folder'
      selectedFiles: [],
      fileStructure: [],
      uploadError: '',
      uploading: false,
      dragOver: false,
      supportedExtensions: ['.py', '.txt', '.csv', '.pdf']
    }
  },
  computed: {
    currentUser() {
      const sessionId = localStorage.getItem('session_id');
      const username = localStorage.getItem('username');
      const role = localStorage.getItem('role');
      if (sessionId && username) {
        return { session_id: sessionId, username: username, role: role };
      }
      return null;
    },
    filteredStudents() {
      if (!this.studentSearch) return this.allStudents;
      const search = this.studentSearch.toLowerCase();
      return this.allStudents.filter(s =>
        s.username.toLowerCase().includes(search) ||
        s.full_name.toLowerCase().includes(search)
      );
    },
    totalStudents() {
      return this.allStudents.length;
    },
    targetCount() {
      return this.targetMode === 'all' ? this.totalStudents : this.selectedStudents.length;
    },
    previewPath() {
      const folder = this.commonFolder.trim();
      const sub = this.subPath.trim();
      if (folder && sub) {
        return `${folder}/${sub}/`;
      } else if (folder) {
        return `${folder}/`;
      } else if (sub) {
        return `${sub}/`;
      }
      return '(root directory)';
    },
    canUpload() {
      const hasFiles = this.selectedFiles.length > 0;
      const hasTarget = this.targetMode === 'all' || this.selectedStudents.length > 0;
      return hasFiles && hasTarget;
    }
  },
  components: {
    X,
    Upload,
    Users,
    UserCheck,
    FolderOpen
  },
  mounted() {
    this.loadAllStudents();
  },
  methods: {
    async loadAllStudents() {
      try {
        const response = await fetch('/api/get-all-students', {
          method: 'GET',
          headers: {
            'session-id': this.currentUser?.session_id
          }
        });

        const result = await response.json();

        if (result.success) {
          this.allStudents = result.students;
          console.log(`[BulkUpload] Loaded ${result.count} students`);
        } else {
          throw new Error(result.error || 'Failed to fetch students');
        }
      } catch (error) {
        console.error('[BulkUpload] Error loading students:', error);
        ElMessage.error('Failed to load student list: ' + error.message);
        // Fallback to empty list
        this.allStudents = [];
      }
    },

    isStudentSelected(username) {
      return this.selectedStudents.includes(username);
    },

    toggleStudent(username) {
      const index = this.selectedStudents.indexOf(username);
      if (index > -1) {
        this.selectedStudents.splice(index, 1);
      } else {
        this.selectedStudents.push(username);
      }
    },

    switchUploadMode(mode) {
      this.uploadMode = mode;
      this.selectedFiles = [];
      this.fileStructure = [];
      this.uploadError = '';
    },

    triggerFileInput() {
      if (this.uploadMode === 'files') {
        this.$refs.fileInput?.click();
      } else {
        this.$refs.folderInput?.click();
      }
    },

    handleFileSelect(event) {
      const files = Array.from(event.target.files);
      this.processFiles(files);
    },

    handleFolderSelect(event) {
      const files = Array.from(event.target.files);
      this.processFolderFiles(files);
    },

    handleDrop(event) {
      event.preventDefault();
      this.dragOver = false;

      const items = event.dataTransfer.items;
      if (items) {
        const files = [];
        const promises = [];

        for (let i = 0; i < items.length; i++) {
          const item = items[i].webkitGetAsEntry();
          if (item) {
            promises.push(this.traverseFileTree(item, files));
          }
        }

        Promise.all(promises).then(() => {
          if (files.length > 0) {
            const hasRelativePaths = files.some(f => f.webkitRelativePath);
            if (hasRelativePaths || this.uploadMode === 'folder') {
              this.processFolderFiles(files);
            } else {
              this.processFiles(files);
            }
          }
        });
      } else {
        const files = Array.from(event.dataTransfer.files);
        this.processFiles(files);
      }
    },

    async traverseFileTree(item, filesList, path = '') {
      if (item.isFile) {
        return new Promise((resolve) => {
          item.file((file) => {
            file.relativePath = path + file.name;
            filesList.push(file);
            resolve();
          });
        });
      } else if (item.isDirectory) {
        const dirReader = item.createReader();
        return new Promise((resolve) => {
          dirReader.readEntries(async (entries) => {
            for (const entry of entries) {
              await this.traverseFileTree(entry, filesList, path + item.name + '/');
            }
            resolve();
          });
        });
      }
    },

    processFiles(files) {
      this.uploadError = '';
      const validFiles = [];
      const invalidFiles = [];

      files.forEach(file => {
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (this.supportedExtensions.includes(fileExtension)) {
          if (file.size <= 10 * 1024 * 1024) {
            validFiles.push(file);
          } else {
            invalidFiles.push(`${file.name} (too large)`);
          }
        } else {
          invalidFiles.push(`${file.name} (unsupported)`);
        }
      });

      if (invalidFiles.length > 0) {
        this.uploadError = `Invalid files: ${invalidFiles.join(', ')}`;
      }

      this.selectedFiles = validFiles;
    },

    processFolderFiles(files) {
      this.uploadError = '';
      const validFiles = [];
      const invalidFiles = [];
      this.fileStructure = [];

      files.forEach(file => {
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        const relativePath = file.webkitRelativePath || file.relativePath || file.name;

        if (this.supportedExtensions.includes(fileExtension)) {
          if (file.size <= 10 * 1024 * 1024) {
            validFiles.push(file);
            this.fileStructure.push({
              file: file,
              relativePath: relativePath,
              name: file.name,
              size: file.size
            });
          } else {
            invalidFiles.push(`${relativePath} (too large)`);
          }
        }
      });

      if (invalidFiles.length > 0) {
        this.uploadError = `Invalid files: ${invalidFiles.join(', ')}`;
      }

      this.selectedFiles = validFiles;

      if (this.selectedFiles.length === 0 && files.length > 0) {
        this.uploadError = 'No supported files found in the selected folder';
      }
    },

    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    getFileIcon(fileName) {
      const extension = fileName.substring(fileName.lastIndexOf('.') + 1);
      return require(`@/assets/vscode-icons/${getIconForFile(extension)}`);
    },

    async onBulkUpload() {
      if (!this.canUpload) return;

      this.uploading = true;

      try {
        const targetStudents = this.targetMode === 'all' ? 'all' : JSON.stringify(this.selectedStudents);

        // Upload each file
        const uploadPromises = this.selectedFiles.map(async (file, index) => {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('targetStudents', targetStudents);
          formData.append('commonFolder', this.commonFolder);
          formData.append('subPath', this.subPath || '');
          formData.append('filename', file.name);

          // Add relative path for folder uploads
          if (this.uploadMode === 'folder' && this.fileStructure[index]) {
            const relativePath = this.fileStructure[index].relativePath;
            formData.append('relativePath', relativePath);
            formData.append('preserveStructure', 'true');
          }

          const response = await fetch('/api/bulk-upload', {
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

        const results = await Promise.all(uploadPromises);

        // Calculate success statistics
        const totalUploaded = results.reduce((sum, r) => sum + r.uploaded_to, 0);
        const avgPerFile = Math.round(totalUploaded / results.length);

        ElMessage.success(`Successfully uploaded ${this.selectedFiles.length} file(s) to ${avgPerFile} students`);

        // Close dialog
        this.$emit('update:modelValue', false);

      } catch (error) {
        console.error('[BulkUpload] Error:', error);
        ElMessage.error('Failed to upload files: ' + error.message);
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

.bulk-upload-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #464647);
  border-radius: 8px;
  width: 800px;
  max-width: 90vw;
  max-height: 90vh;
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
  max-height: 70vh;
}

.students-section,
.folder-section,
.upload-section,
.preview-section {
  margin-bottom: 24px;
}

.students-section label,
.folder-section label,
.upload-section label,
.preview-section label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #cccccc);
}

.target-selection {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.target-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  background: var(--input-bg, #2d2d30);
  color: var(--text-secondary, #969696);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.target-btn:hover {
  background: var(--hover-bg, #383838);
  border-color: var(--accent-color, #007acc);
}

.target-btn.active {
  background: var(--accent-color, #007acc);
  color: white;
  border-color: var(--accent-color, #007acc);
}

.specific-students {
  margin-top: 12px;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  background: var(--input-bg, #2d2d30);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  color: var(--text-primary, #cccccc);
  font-size: 14px;
  margin-bottom: 8px;
}

.student-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  background: var(--input-bg, #2d2d30);
}

.student-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--border-color, #464647);
}

.student-item:last-child {
  border-bottom: none;
}

.student-item:hover {
  background: var(--hover-bg, #094771);
}

.student-item.selected {
  background: var(--selected-bg, rgba(0, 122, 204, 0.2));
}

.student-info {
  display: flex;
  flex-direction: column;
}

.username {
  font-size: 14px;
  color: var(--text-primary, #cccccc);
  font-weight: 500;
}

.fullname {
  font-size: 12px;
  color: var(--text-secondary, #969696);
}

.selection-summary {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary, #969696);
}

.folder-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.folder-input {
  flex: 1;
  padding: 8px 12px;
  background: var(--input-bg, #2d2d30);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  color: var(--text-primary, #cccccc);
  font-size: 14px;
}

.path-separator {
  color: var(--text-secondary, #969696);
  font-size: 18px;
}

.path-preview {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary, #969696);
}

.path-preview code {
  background: var(--input-bg, #2d2d30);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

.upload-mode-toggle {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  padding: 4px;
  background: var(--input-bg, #2d2d30);
  width: fit-content;
}

.mode-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 3px;
  background: transparent;
  color: var(--text-secondary, #969696);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.mode-btn:hover {
  background: var(--hover-bg, rgba(255, 255, 255, 0.05));
  color: var(--text-primary, #cccccc);
}

.mode-btn.active {
  background: var(--accent-color, #007acc);
  color: white;
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

.files-preview {
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  padding: 12px;
  background: var(--input-bg, #2d2d30);
}

.file-preview-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  margin-bottom: 8px;
  background: var(--bg-secondary, #252526);
  border-radius: 4px;
}

.file-preview-item:last-child {
  margin-bottom: 0;
}

.file-icon {
  width: 20px;
  height: 20px;
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary, #cccccc);
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary, #969696);
}

.more-files {
  margin-top: 8px;
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary, #969696);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, #464647);
}

.btn-cancel,
.btn-upload {
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

.btn-upload {
  background: var(--accent-color, #007acc);
  color: white;
}

.btn-upload:hover:not(:disabled) {
  background: var(--accent-hover, #005a9e);
}

.btn-upload:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
