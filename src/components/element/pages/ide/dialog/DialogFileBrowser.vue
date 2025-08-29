<template>
  <el-dialog
    :title="title"
    v-model="visible"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
    class="file-browser-dialog custom-dialog"
  >
    <div class="file-browser-content">
      <div class="current-path">
        <span class="path-label">Current Path:</span>
        <span class="path-value">{{ currentPath || '/' }}</span>
      </div>
      
      <div class="file-tree-container">
        <el-tree
          :data="treeData"
          :props="treeProps"
          node-key="path"
          :expand-on-click-node="false"
          :default-expanded-keys="expandedKeys"
          highlight-current
          @node-click="handleNodeClick"
          @node-expand="handleNodeExpand"
          @node-collapse="handleNodeCollapse"
          ref="fileTree"
        >
          <template #default="{ node, data }">
            <span class="node-item">
              <img :src="getIconUrl(data)" alt="" class="node-icon" />
              <span class="node-label">{{ node.label }}</span>
            </span>
          </template>
        </el-tree>
      </div>
      
      <div class="selected-file" v-if="mode === 'open'">
        <span class="selected-label">Selected File:</span>
        <span class="selected-value">{{ selectedFile ? selectedFile.label : 'None' }}</span>
      </div>
      
      <div class="selected-file" v-if="mode === 'move'">
        <span class="selected-label">Move to:</span>
        <span class="selected-value">{{ selectedFolder ? selectedFolder.path : '/' }}</span>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">Cancel</el-button>
        <el-button type="primary" @click="handleConfirm" :disabled="!canConfirm">
          {{ confirmButtonText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { getIconForFile, getIconForFolder, getIconForOpenFolder } from 'vscode-icons-js';

export default {
  name: 'DialogFileBrowser',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    mode: {
      type: String,
      default: 'open', // 'open' or 'move'
      validator: (value) => ['open', 'move'].includes(value)
    },
    fileToMove: {
      type: Object,
      default: null
    },
    currentUser: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      selectedFile: null,
      selectedFolder: null,
      currentPath: '/',
      expandedKeys: [],
      treeProps: {
        label: 'label',
        children: 'children',
      }
    };
  },
  computed: {
    visible: {
      get() {
        return this.modelValue;
      },
      set(val) {
        this.$emit('update:modelValue', val);
      }
    },
    title() {
      return this.mode === 'open' ? 'Open File' : 'Move File';
    },
    confirmButtonText() {
      return this.mode === 'open' ? 'Open' : 'Move';
    },
    canConfirm() {
      if (this.mode === 'open') {
        return this.selectedFile !== null;
      } else if (this.mode === 'move') {
        return this.selectedFolder !== null && 
               this.fileToMove && 
               this.selectedFolder.path !== this.getParentPath(this.fileToMove.path);
      }
      return false;
    },
    ideInfo() {
      return this.$store?.state?.ide?.ideInfo || {};
    },
    treeData() {
      // Use multi-root data if available, otherwise fall back to single project
      let data;
      if (this.ideInfo.multiRootData && this.ideInfo.multiRootData.children.length > 0) {
        data = this.ideInfo.multiRootData.children;
      } else {
        data = this.ideInfo.currProj.data ? [this.ideInfo.currProj.data] : [];
      }
      
      // Filter data based on mode and permissions
      if (this.mode === 'move') {
        data = this.filterOutFile(data);
        data = this.filterByPermissions(data);
      }
      
      return data;
    },
    isStudent() {
      // Only return true if we have clear student role - don't assume
      return this.currentUser && this.currentUser.role === 'student';
    },
    studentDirectory() {
      if (!this.isStudent || !this.currentUser?.username) return null;
      return `Local/${this.currentUser.username}`;
    }
  },
  methods: {
    getIconUrl(data) {
      try {
        if (data.type === 'file') {
          const extension = data.path.substring(data.path.lastIndexOf('.') + 1);
          return require(`@/assets/vscode-icons/${getIconForFile(extension)}`);
        } else if (data.type === 'dir' || data.type === 'folder') {
          const isExpanded = this.expandedKeys.includes(data.path);
          const iconName = isExpanded ? getIconForOpenFolder(data.label) : getIconForFolder(data.label);
          return require(`@/assets/vscode-icons/${iconName}`);
        }
      } catch (e) {
        // Fallback to default icons
        return data.type === 'file' ? 
          require('@/assets/vscode-icons/default_file.svg') : 
          require('@/assets/vscode-icons/default_folder.svg');
      }
    },
    handleNodeClick(data) {
      if (this.mode === 'open') {
        if (data.type === 'file') {
          this.selectedFile = data;
          this.currentPath = data.path;
        } else {
          // Expand/collapse folder on click
          if (this.expandedKeys.includes(data.path)) {
            this.handleNodeCollapse(data);
          } else {
            this.handleNodeExpand(data);
          }
        }
      } else if (this.mode === 'move') {
        if (data.type === 'dir' || data.type === 'folder') {
          // Check if student can access this folder - only if we have user data
          if (this.currentUser && this.isStudent && !this.canAccessPath(data.path)) {
            this.$message.warning('You can only move files within your personal directory');
            return;
          }
          this.selectedFolder = data;
          this.currentPath = data.path;
        }
      }
    },
    handleNodeExpand(data) {
      if (!this.expandedKeys.includes(data.path)) {
        this.expandedKeys.push(data.path);
      }
    },
    handleNodeCollapse(data) {
      const index = this.expandedKeys.indexOf(data.path);
      if (index > -1) {
        this.expandedKeys.splice(index, 1);
      }
    },
    handleConfirm() {
      console.log('[DialogFileBrowser] handleConfirm called:', {
        mode: this.mode,
        selectedFile: this.selectedFile,
        selectedFolder: this.selectedFolder,
        fileToMove: this.fileToMove
      });
      
      if (this.mode === 'open' && this.selectedFile) {
        console.log('[DialogFileBrowser] Opening file:', this.selectedFile.path);
        this.$emit('open-file', this.selectedFile.path);
        this.handleClose();
      } else if (this.mode === 'move' && this.selectedFolder && this.fileToMove) {
        const fileName = this.getFileName(this.fileToMove.path);
        // Ensure path doesn't have double slashes
        const newPath = this.selectedFolder.path.endsWith('/') 
          ? this.selectedFolder.path + fileName 
          : this.selectedFolder.path + '/' + fileName;
        
        console.log('[DialogFileBrowser] Moving file - DETAILED DEBUG:', {
          mode: this.mode,
          oldPath: this.fileToMove.path,
          newPath: newPath,
          selectedFolderPath: this.selectedFolder.path,
          fileName: fileName,
          fileToMove: this.fileToMove,
          selectedFolder: this.selectedFolder,
          projectName: this.fileToMove.projectName || this.ideInfo.currProj?.data?.name
        });
        
        this.$emit('move-file', {
          oldPath: this.fileToMove.path,
          newPath: newPath,
          projectName: this.fileToMove.projectName || this.ideInfo.currProj?.data?.name
        });
        this.handleClose();
      } else {
        console.log('[DialogFileBrowser] Cannot confirm - missing requirements:', {
          mode: this.mode,
          hasSelectedFile: !!this.selectedFile,
          hasSelectedFolder: !!this.selectedFolder,
          hasFileToMove: !!this.fileToMove,
          canConfirm: this.canConfirm
        });
      }
    },
    handleClose() {
      this.selectedFile = null;
      this.selectedFolder = null;
      this.currentPath = '/';
      this.expandedKeys = [];
      this.$emit('update:modelValue', false);
    },
    getParentPath(filePath) {
      const lastSlash = filePath.lastIndexOf('/');
      return lastSlash > 0 ? filePath.substring(0, lastSlash) : '/';
    },
    getFileName(filePath) {
      const lastSlash = filePath.lastIndexOf('/');
      return lastSlash >= 0 ? filePath.substring(lastSlash + 1) : filePath;
    },
    filterOutFile(treeData) {
      // Filter out the file being moved from the tree
      if (!this.fileToMove) return treeData;
      
      return treeData.map(item => {
        if (item.path === this.fileToMove.path) {
          return null;
        }
        if (item.children && item.children.length > 0) {
          return {
            ...item,
            children: this.filterOutFile(item.children).filter(Boolean)
          };
        }
        return item;
      }).filter(Boolean);
    },
    filterByPermissions(treeData) {
      if (!this.isStudent) {
        // Professors can access all directories
        return treeData;
      }
      
      // Students can only access their Local/{username} directory
      return treeData.map(item => {
        if (this.canAccessPath(item.path)) {
          if (item.children && item.children.length > 0) {
            return {
              ...item,
              children: this.filterByPermissions(item.children)
            };
          }
          return item;
        }
        return null;
      }).filter(Boolean);
    },
    canAccessPath(path) {
      if (!this.isStudent) {
        return true; // Professors can access everything
      }
      
      if (!path || !this.studentDirectory) {
        return false;
      }
      
      // Students can only access their personal directory
      return path === this.studentDirectory || 
             path.startsWith(this.studentDirectory + '/');
    }
  },
  watch: {
    visible(val) {
      if (val) {
        // Reset state when dialog opens
        this.selectedFile = null;
        this.selectedFolder = null;
        this.currentPath = '/';
        this.expandedKeys = [];
        
        // Expand root folders by default
        this.$nextTick(() => {
          if (this.treeData && this.treeData.length > 0) {
            this.treeData.forEach(item => {
              if ((item.type === 'dir' || item.type === 'folder') && item.path) {
                this.expandedKeys.push(item.path);
              }
            });
          }
        });
      }
    }
  }
};
</script>

<style>
.file-browser-dialog {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Improved styling for Move File modal - using CSS variables that adapt to themes */
.custom-dialog .el-dialog {
  background: var(--bg-primary, #303030) !important;
  border: 1px solid var(--border-color, #464647) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

/* Override Element Plus dialog background variable to prevent conflicts */
.custom-dialog {
  --el-dialog-bg-color: unset !important;
}

.custom-dialog .el-dialog__header {
  background: var(--bg-secondary, #3F4955) !important;
  padding: 16px 24px !important;
  border-bottom: 1px solid var(--border-color, #464647) !important;
}

.custom-dialog .el-dialog__title {
  color: var(--text-primary, #FFFFFF) !important;
  font-size: 18px !important;
  font-weight: 500 !important;
}

.custom-dialog .el-dialog__headerbtn {
  color: var(--text-primary, #FFFFFF) !important;
  top: 16px !important;
  right: 20px !important;
}

.custom-dialog .el-dialog__headerbtn:hover {
  color: var(--btn-primary-bg, #4fc08d) !important;
}

.custom-dialog .el-dialog__body {
  background: var(--bg-primary, #303030) !important;
  color: var(--text-primary, #CCCCCC) !important;
  padding: 20px !important;
}

.custom-dialog .el-dialog__footer {
  background: var(--bg-primary, #303030) !important;
  border-top: 1px solid var(--border-color, #464647) !important;
  padding: 16px 20px !important;
}

/* Enhanced content styling */
.file-browser-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.current-path {
  padding: 10px 12px;
  background: var(--bg-secondary, #252526);
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border-color, #464647);
}

.path-label,
.selected-label {
  font-weight: 500;
  color: var(--text-secondary, #969696);
  font-size: 14px;
}

.path-value,
.selected-value {
  color: var(--text-primary, #cccccc);
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
}

.file-tree-container {
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  padding: 8px;
  max-height: 300px;
  overflow-y: auto;
  background: var(--bg-primary, #1e1e1e);
}

.node-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
}

.node-icon {
  width: 16px;
  height: 16px;
}

.node-label {
  font-size: 14px;
  color: var(--text-primary, #cccccc);
}

.selected-file {
  padding: 10px 12px;
  background: var(--active-bg, #094771);
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border-color, #464647);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Improved button styling */
.custom-dialog .el-button {
  background: var(--btn-secondary-bg, #484848) !important;
  border: 1px solid var(--border-color, #464647) !important;
  color: var(--text-primary, #cccccc) !important;
  font-size: 14px !important;
  padding: 8px 20px !important;
  height: auto !important;
  min-height: 36px !important;
  border-radius: 4px !important;
  font-weight: 500 !important;
}

.custom-dialog .el-button:hover {
  background: var(--hover-bg, #5a5a5a) !important;
  border-color: var(--border-color, #464647) !important;
}

.custom-dialog .el-button--primary {
  background: var(--btn-primary-bg, #007acc) !important;
  border-color: var(--btn-primary-bg, #007acc) !important;
  color: #FFFFFF !important;
}

.custom-dialog .el-button--primary:hover {
  background: var(--btn-primary-hover, #005a9e) !important;
  border-color: var(--btn-primary-hover, #005a9e) !important;
}

.custom-dialog .el-button--primary.is-disabled {
  background: var(--btn-primary-bg, #007acc) !important;
  border-color: var(--btn-primary-bg, #007acc) !important;
  opacity: 0.5 !important;
  color: #FFFFFF !important;
}

/* Tree styling improvements */
.file-browser-dialog .el-tree {
  background: transparent !important;
  color: var(--text-primary, #CCCCCC) !important;
}

.file-browser-dialog .el-tree-node__content {
  background: transparent !important;
  color: var(--text-primary, #CCCCCC) !important;
  border: none !important;
  padding: 4px 8px !important;
  border-radius: 4px !important;
  margin: 2px 0 !important;
}

.file-browser-dialog .el-tree-node__content:hover {
  background: var(--hover-bg, #2a2d2e) !important;
  color: var(--text-primary, #FFFFFF) !important;
}

.file-browser-dialog .el-tree-node.is-current > .el-tree-node__content {
  background: var(--active-bg, #094771) !important;
  color: var(--text-primary, #FFFFFF) !important;
}

.file-browser-dialog .el-tree-node__expand-icon {
  color: var(--text-secondary, #969696) !important;
}

.file-browser-dialog .el-tree-node__expand-icon.is-leaf {
  color: transparent !important;
}

/* Scrollbar styling */
.file-tree-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.file-tree-container::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb, #545a5e);
  border-radius: 4px;
}

.file-tree-container::-webkit-scrollbar-track {
  background: var(--scrollbar-track, #2f2f2f);
}


</style>