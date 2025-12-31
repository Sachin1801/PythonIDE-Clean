<template>
  <AdminLayout>
    <div class="file-browser-page">
      <div class="browser-layout">
        <!-- Student Sidebar -->
        <div class="students-sidebar">
          <div class="sidebar-header">
            <h3><Users :size="18" /> Students</h3>
            <span class="student-count">{{ students.length }}</span>
          </div>

          <div class="search-box">
            <Search :size="16" />
            <input
              v-model="studentSearch"
              type="text"
              placeholder="Search students..."
            />
          </div>

          <div class="students-list" v-loading="loadingStudents">
            <div
              v-for="student in filteredStudents"
              :key="student.username"
              class="student-item"
              :class="{ active: selectedStudent === student.username }"
              @click="selectStudent(student.username)"
            >
              <User :size="16" />
              <div class="student-info">
                <span class="student-name">{{ student.username }}</span>
                <span class="file-count">{{ student.file_count }} files</span>
              </div>
            </div>

            <div v-if="filteredStudents.length === 0 && !loadingStudents" class="no-students">
              No students found
            </div>
          </div>
        </div>

        <!-- Main Content Area -->
        <div class="main-content">
          <!-- Toolbar -->
          <div class="toolbar">
            <div class="breadcrumbs">
              <span class="breadcrumb-item" @click="navigateTo('')">
                <Home :size="16" />
              </span>
              <template v-for="(crumb, index) in breadcrumbs" :key="index">
                <ChevronRight :size="14" class="separator" />
                <span
                  class="breadcrumb-item"
                  :class="{ current: index === breadcrumbs.length - 1 }"
                  @click="navigateToCrumb(index)"
                >
                  {{ crumb }}
                </span>
              </template>
            </div>

            <div class="toolbar-actions">
              <el-button size="small" @click="refreshFiles">
                <RefreshCw :size="14" />
              </el-button>
              <el-button
                size="small"
                :disabled="!currentPath"
                @click="downloadCurrent"
              >
                <Download :size="14" /> Download
              </el-button>
            </div>
          </div>

          <!-- File List -->
          <div class="file-list-container" v-loading="loadingFiles">
            <div v-if="files.length > 0" class="file-list">
              <div
                v-for="file in files"
                :key="file.path"
                class="file-item"
                :class="{ selected: selectedFile?.path === file.path }"
                @click="selectFile(file)"
                @dblclick="openFile(file)"
              >
                <component :is="getFileIcon(file)" :size="20" class="file-icon" />
                <div class="file-info">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-meta">
                    <template v-if="!file.is_directory">
                      {{ formatSize(file.size) }}
                    </template>
                    {{ formatDate(file.modified) }}
                  </span>
                </div>
              </div>
            </div>

            <div v-else-if="!loadingFiles && selectedStudent" class="empty-state">
              <FolderOpen :size="48" />
              <p>This folder is empty</p>
            </div>

            <div v-else-if="!loadingFiles && !selectedStudent" class="empty-state">
              <Users :size="48" />
              <p>Select a student to browse their files</p>
            </div>
          </div>
        </div>

        <!-- Preview Panel -->
        <div class="preview-panel" v-if="selectedFile && !selectedFile.is_directory">
          <div class="preview-header">
            <div class="preview-title">
              <component :is="getFileIcon(selectedFile)" :size="18" />
              <span>{{ selectedFile.name }}</span>
            </div>
            <div class="preview-actions">
              <el-button size="small" @click="downloadFile(selectedFile)">
                <Download :size="14" /> Download
              </el-button>
              <el-button size="small" @click="closePreview">
                <X :size="14" />
              </el-button>
            </div>
          </div>

          <div class="preview-content" v-loading="loadingPreview">
            <!-- Text/Code Preview -->
            <div v-if="previewData?.type === 'text'" class="code-preview">
              <pre><code>{{ previewData.content }}</code></pre>
            </div>

            <!-- Image Preview -->
            <div v-else-if="previewData?.type === 'image'" class="image-preview">
              <img :src="`data:${previewData.mime_type};base64,${previewData.content}`" alt="Preview" />
            </div>

            <!-- Binary File -->
            <div v-else-if="previewData?.type === 'binary'" class="binary-preview">
              <FileQuestion :size="48" />
              <p>{{ previewData.message }}</p>
              <el-button @click="downloadFile(selectedFile)">
                <Download :size="16" /> Download File
              </el-button>
            </div>

            <!-- Error -->
            <div v-else-if="previewError" class="preview-error">
              <AlertCircle :size="48" />
              <p>{{ previewError }}</p>
            </div>
          </div>

          <div class="preview-footer">
            <span>Size: {{ formatSize(selectedFile.size) }}</span>
            <span>Modified: {{ formatDate(selectedFile.modified) }}</span>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import AdminLayout from '../components/layout/AdminLayout.vue'
import filesApi from '../api/files'
import {
  Users,
  User,
  Search,
  Home,
  ChevronRight,
  RefreshCw,
  Download,
  FolderOpen,
  Folder,
  File,
  FileText,
  FileCode,
  FileJson,
  Image,
  FileQuestion,
  X,
  AlertCircle
} from 'lucide-vue-next'

export default {
  name: 'FileBrowserPage',
  components: {
    AdminLayout,
    Users,
    User,
    Search,
    Home,
    ChevronRight,
    RefreshCw,
    Download,
    FolderOpen,
    Folder,
    File,
    FileText,
    FileCode,
    FileJson,
    Image,
    FileQuestion,
    X,
    AlertCircle
  },
  setup() {
    const store = useStore()

    // State
    const students = ref([])
    const studentSearch = ref('')
    const selectedStudent = ref(null)
    const currentPath = ref('')
    const files = ref([])
    const selectedFile = ref(null)
    const previewData = ref(null)
    const previewError = ref(null)

    // Loading states
    const loadingStudents = ref(false)
    const loadingFiles = ref(false)
    const loadingPreview = ref(false)

    // Computed
    const token = computed(() => store.getters['auth/token'])

    const filteredStudents = computed(() => {
      if (!studentSearch.value) return students.value
      const search = studentSearch.value.toLowerCase()
      return students.value.filter(s => s.username.toLowerCase().includes(search))
    })

    const breadcrumbs = computed(() => {
      if (!currentPath.value) return []
      return currentPath.value.split('/').filter(Boolean)
    })

    // Methods
    const fetchStudents = async () => {
      if (!token.value) return

      loadingStudents.value = true
      try {
        const response = await filesApi.getStudents(token.value)
        if (response.success) {
          students.value = response.data
        }
      } catch (error) {
        console.error('Failed to fetch students:', error)
        window.ElMessage.error('Failed to load students')
      } finally {
        loadingStudents.value = false
      }
    }

    const selectStudent = (username) => {
      selectedStudent.value = username
      currentPath.value = username
      selectedFile.value = null
      previewData.value = null
      fetchFiles()
    }

    const fetchFiles = async () => {
      if (!token.value) return

      loadingFiles.value = true
      try {
        const response = await filesApi.browse(token.value, currentPath.value)
        if (response.success) {
          files.value = response.data.items
        }
      } catch (error) {
        console.error('Failed to fetch files:', error)
        window.ElMessage.error('Failed to load files')
      } finally {
        loadingFiles.value = false
      }
    }

    const navigateTo = (path) => {
      currentPath.value = path
      selectedFile.value = null
      previewData.value = null

      if (path) {
        const parts = path.split('/')
        selectedStudent.value = parts[0]
        fetchFiles()
      } else {
        selectedStudent.value = null
        files.value = []
      }
    }

    const navigateToCrumb = (index) => {
      const parts = breadcrumbs.value.slice(0, index + 1)
      navigateTo(parts.join('/'))
    }

    const selectFile = (file) => {
      selectedFile.value = file
      if (!file.is_directory) {
        loadPreview(file)
      }
    }

    const openFile = (file) => {
      if (file.is_directory) {
        currentPath.value = file.path
        selectedFile.value = null
        previewData.value = null
        fetchFiles()
      }
    }

    const loadPreview = async (file) => {
      loadingPreview.value = true
      previewData.value = null
      previewError.value = null

      try {
        const response = await filesApi.getContent(token.value, file.path)
        if (response.success) {
          previewData.value = response.data
        } else {
          previewError.value = response.error || 'Failed to load preview'
        }
      } catch (error) {
        console.error('Failed to load preview:', error)
        previewError.value = 'Failed to load preview'
      } finally {
        loadingPreview.value = false
      }
    }

    const downloadFile = async (file) => {
      try {
        const blob = await filesApi.download(token.value, file.path)
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = file.name + (file.is_directory ? '.zip' : '')
        a.click()
        window.URL.revokeObjectURL(url)
        window.ElMessage.success('Download started')
      } catch (error) {
        console.error('Failed to download:', error)
        window.ElMessage.error('Failed to download file')
      }
    }

    const downloadCurrent = () => {
      if (currentPath.value) {
        downloadFile({ path: currentPath.value, name: breadcrumbs.value[breadcrumbs.value.length - 1], is_directory: true })
      }
    }

    const closePreview = () => {
      selectedFile.value = null
      previewData.value = null
    }

    const refreshFiles = () => {
      fetchStudents()
      if (currentPath.value) {
        fetchFiles()
      }
    }

    const getFileIcon = (file) => {
      if (file.is_directory) return Folder

      const ext = file.extension?.toLowerCase()
      if (['.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs'].includes(ext)) return FileCode
      if (['.json', '.yaml', '.yml', '.xml'].includes(ext)) return FileJson
      if (['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'].includes(ext)) return Image
      if (['.txt', '.md', '.csv', '.log'].includes(ext)) return FileText

      return File
    }

    const formatSize = (bytes) => {
      if (!bytes) return '—'
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / 1024 / 1024).toFixed(1) + ' MB'
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString()
    }

    // Lifecycle
    onMounted(() => {
      fetchStudents()
    })

    return {
      // State
      students,
      studentSearch,
      selectedStudent,
      currentPath,
      files,
      selectedFile,
      previewData,
      previewError,
      loadingStudents,
      loadingFiles,
      loadingPreview,

      // Computed
      filteredStudents,
      breadcrumbs,

      // Methods
      selectStudent,
      navigateTo,
      navigateToCrumb,
      selectFile,
      openFile,
      downloadFile,
      downloadCurrent,
      closePreview,
      refreshFiles,
      getFileIcon,
      formatSize,
      formatDate
    }
  }
}
</script>

<style scoped>
.file-browser-page {
  height: calc(100vh - 120px);
}

.browser-layout {
  display: grid;
  grid-template-columns: 250px 1fr 350px;
  gap: 16px;
  height: 100%;
}

/* Students Sidebar */
.students-sidebar {
  background-color: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--admin-border-color);
}

.sidebar-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--admin-text-white);
}

.student-count {
  background-color: var(--admin-primary);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.students-sidebar .search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin: 8px;
  background-color: var(--admin-bg-tertiary);
  border: 1px solid var(--admin-border-color);
  border-radius: 4px;
}

.students-sidebar .search-box input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--admin-text-primary);
  font-size: 13px;
  outline: none;
}

.students-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.student-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.student-item:hover {
  background-color: var(--admin-bg-hover);
}

.student-item.active {
  background-color: var(--admin-primary);
}

.student-info {
  display: flex;
  flex-direction: column;
}

.student-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--admin-text-primary);
}

.file-count {
  font-size: 11px;
  color: var(--admin-text-muted);
}

.no-students {
  text-align: center;
  padding: 20px;
  color: var(--admin-text-muted);
}

/* Main Content */
.main-content {
  background-color: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--admin-border-color);
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--admin-text-secondary);
}

.breadcrumb-item:hover {
  background-color: var(--admin-bg-hover);
  color: var(--admin-text-primary);
}

.breadcrumb-item.current {
  color: var(--admin-text-white);
  font-weight: 500;
  cursor: default;
}

.breadcrumb-item.current:hover {
  background-color: transparent;
}

.separator {
  color: var(--admin-text-muted);
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.file-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: var(--admin-bg-hover);
}

.file-item.selected {
  background-color: rgba(0, 120, 212, 0.2);
  border: 1px solid var(--admin-primary);
}

.file-icon {
  color: var(--admin-text-secondary);
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  color: var(--admin-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 11px;
  color: var(--admin-text-muted);
  flex-shrink: 0;
  margin-left: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--admin-text-muted);
  gap: 12px;
}

/* Preview Panel */
.preview-panel {
  background-color: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--admin-border-color);
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--admin-text-white);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.preview-content {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.code-preview {
  background-color: var(--admin-bg-tertiary);
  border-radius: 4px;
  padding: 16px;
  overflow: auto;
  height: 100%;
}

.code-preview pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: var(--admin-text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.image-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.image-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.binary-preview, .preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: var(--admin-text-muted);
  text-align: center;
}

.preview-footer {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid var(--admin-border-color);
  font-size: 11px;
  color: var(--admin-text-muted);
}

/* Responsive */
@media (max-width: 1200px) {
  .browser-layout {
    grid-template-columns: 200px 1fr;
  }

  .preview-panel {
    display: none;
  }
}

@media (max-width: 768px) {
  .browser-layout {
    grid-template-columns: 1fr;
  }

  .students-sidebar {
    max-height: 200px;
  }
}
</style>
