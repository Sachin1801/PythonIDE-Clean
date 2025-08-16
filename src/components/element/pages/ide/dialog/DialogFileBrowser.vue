<template>
  <el-dialog
    :title="title"
    v-model="visible"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
    class="file-browser-dialog"
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
      if (this.ideInfo.multiRootData && this.ideInfo.multiRootData.children.length > 0) {
        return this.mode === 'move' ? this.filterOutFile(this.ideInfo.multiRootData.children) : this.ideInfo.multiRootData.children;
      }
      const data = this.ideInfo.currProj.data ? [this.ideInfo.currProj.data] : [];
      return this.mode === 'move' ? this.filterOutFile(data) : data;
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
      if (this.mode === 'open' && this.selectedFile) {
        this.$emit('open-file', this.selectedFile.path);
        this.handleClose();
      } else if (this.mode === 'move' && this.selectedFolder && this.fileToMove) {
        const newPath = this.selectedFolder.path + '/' + this.getFileName(this.fileToMove.path);
        this.$emit('move-file', {
          oldPath: this.fileToMove.path,
          newPath: newPath,
          projectName: this.fileToMove.projectName || this.ideInfo.currProj?.data?.name
        });
        this.handleClose();
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

<style scoped>
.file-browser-dialog {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.file-browser-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.current-path {
  padding: 8px 12px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-label,
.selected-label {
  font-weight: 500;
  color: var(--text-secondary, #666);
}

.path-value,
.selected-value {
  color: var(--text-primary, #333);
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
}

.file-tree-container {
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 4px;
  padding: 8px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--bg-primary, #fff);
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
  color: var(--text-primary, #333);
}

.selected-file {
  padding: 8px 12px;
  background: var(--bg-accent, #e3f2fd);
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* Dark theme support */
[data-theme="dark"] .current-path,
[data-theme="dark"] .file-tree-container {
  background: #1e1e1e;
  border-color: #464647;
}

[data-theme="dark"] .path-label,
[data-theme="dark"] .selected-label {
  color: #969696;
}

[data-theme="dark"] .path-value,
[data-theme="dark"] .selected-value,
[data-theme="dark"] .node-label {
  color: #cccccc;
}

[data-theme="dark"] .selected-file {
  background: #094771;
}

/* Scrollbar styling */
.file-tree-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.file-tree-container::-webkit-scrollbar-thumb {
  background: #c0c0c0;
  border-radius: 4px;
}

.file-tree-container::-webkit-scrollbar-track {
  background: #f0f0f0;
}

[data-theme="dark"] .file-tree-container::-webkit-scrollbar-thumb {
  background: #545a5e;
}

[data-theme="dark"] .file-tree-container::-webkit-scrollbar-track {
  background: #2f2f2f;
}
</style>