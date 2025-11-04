<template>
  <div class="proj-tree-container">
    <div class="tree-header">
      <!-- <span class="tree-title">File Management</span> -->
      <div class="tree-header-actions ">
        <button class="action-btn new-folder-btn" @click="handleNewFolder" title="New Folder">
          <FolderPlus :size="16" />
        </button>
        <button class="action-btn new-file-btn" @click="handleNewFile" title="New File">
          <FilePlus :size="16" />
        </button>
        <button v-if="isAdmin" class="action-btn import-btn" @click="handleImportFile" title="Import Files">
          <Upload :size="16" />
        </button>
        <button v-if="isAdmin" class="action-btn bulk-upload-btn" @click="handleBulkUpload" title="Bulk Upload to Students">
          <Users :size="16" />
        </button>
        <button class="action-btn refresh-btn" @click="refreshTree" title="Refresh">
          <RefreshCw :size="16" />
        </button>
      </div>
    </div>
    <el-tree
      id="tree-root"
      class="ide-project-list noselected"
      :props="treeProps"
      :data="treeData"
      node-key="uuid"
      ref="tree"
      highlight-current
      :expand-on-click-node="false"
      :indent=12
      :default-expanded-keys="defaultExpandedKeys"
      @node-expand="nodeExpand"
      @node-collapse="nodeCollapse"
      @node-click="handleNodeClick"
      @node-contextmenu="handleContextMenu"
      >
      <template #default="{ node, data }">
        <span class="node-wrapper" @dblclick.stop="handleDoubleClick(data)">
          <img :src="getIconUrl(data)" alt="" class="node-icon" />
          <span class="node-label">{{ node.label }}</span>
          <span class="node-actions" v-if="data.type === 'file' || data.type === 'dir' || data.type === 'folder'">
            <button class="dropdown-btn" @click.stop="showDropdown($event, data)" title="Actions">
              <MoreVertical :size="14" />
            </button>
          </span>
        </span>
      </template>
    </el-tree>
    
    <!-- Context Menu -->
    <div v-if="contextMenu.visible" 
         class="context-menu" 
         :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }">
      <div class="menu-item" @click="handleMenuAction('openInRightPanel', contextMenu.data)" v-if="contextMenu.data.type === 'file' && isPreviewFile(contextMenu.data)">
        <span>Open in Right Panel</span>
      </div>
      <div class="menu-divider" v-if="contextMenu.data.type === 'file' && isPreviewFile(contextMenu.data)"></div>
      <div class="menu-item" 
           :class="{ disabled: !canRenameOrDelete(contextMenu.data) }"
           @click="canRenameOrDelete(contextMenu.data) && handleMenuAction('rename', contextMenu.data)"
           v-if="!isProtectedFolder(contextMenu.data)">
        <span>Rename</span>
      </div>
      <div class="menu-divider" v-if="!isProtectedFolder(contextMenu.data)"></div>
      <div class="menu-item" @click="handleMenuAction('download', contextMenu.data)" v-if="contextMenu.data.type === 'file'">
        <span>Download</span>
      </div>
      <div class="menu-item danger" 
           :class="{ disabled: !canRenameOrDelete(contextMenu.data) }"
           @click="canRenameOrDelete(contextMenu.data) && handleMenuAction('delete', contextMenu.data)"
           v-if="!isProtectedFolder(contextMenu.data)">
        <span>Delete</span>
      </div>
    </div>
    
    <!-- Dropdown Menu -->
    <div v-if="dropdown.visible" 
         class="dropdown-menu" 
         :style="{ left: dropdown.x + 'px', top: dropdown.y + 'px' }">
      <div class="menu-item" @click="handleMenuAction('openInRightPanel', dropdown.data)" v-if="dropdown.data.type === 'file' && isPreviewFile(dropdown.data)">
        <span>Open in Right Panel</span>
      </div>
      <div class="menu-divider" v-if="dropdown.data.type === 'file' && isPreviewFile(dropdown.data)"></div>
      <div class="menu-item" 
           :class="{ disabled: !canRenameOrDelete(dropdown.data) }"
           @click="canRenameOrDelete(dropdown.data) && handleMenuAction('rename', dropdown.data)"
           v-if="!isProtectedFolder(dropdown.data)">
        <span>Rename</span>
      </div>
      <div class="menu-divider" v-if="!isProtectedFolder(dropdown.data)"></div>
      <div class="menu-item" @click="handleMenuAction('download', dropdown.data)" v-if="dropdown.data.type === 'file'">
        <span>Download</span>
      </div>
      <div class="menu-item danger" 
           :class="{ disabled: !canRenameOrDelete(dropdown.data) }"
           @click="canRenameOrDelete(dropdown.data) && handleMenuAction('delete', dropdown.data)"
           v-if="!isProtectedFolder(dropdown.data)">
        <span>Delete</span>
      </div>
    </div>
  </div>
</template>

<script>
import * as types from '../../../../store/mutation-types';
import { getIconForFile, getIconForFolder, getIconForOpenFolder } from 'vscode-icons-js';
import { RefreshCw, MoreVertical, FilePlus, FolderPlus, Upload, Users } from 'lucide-vue-next';
import { ElMessage, ElMessageBox } from 'element-plus';

export default {
  components: {
    RefreshCw,
    MoreVertical,
    FilePlus,
    FolderPlus,
    Upload,
    Users,
  },
  props: {
    currentUser: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      getFile: true,
      treeProps: {
        uuid: 'uuid',
        label: 'label',
        children: 'children',
      },
      contextMenu: {
        visible: false,
        x: 0,
        y: 0,
        data: null
      },
      dropdown: {
        visible: false,
        x: 0,
        y: 0,
        data: null
      },
      renameMode: false,
      renameData: null
    }
  },
  methods: {
    isPreviewFile(data) {
      if (!data || data.type !== 'file') return false;
      const path = data.path || '';
      const previewExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.pdf', '.csv'];
      return previewExtensions.some(ext => path.toLowerCase().endsWith(ext));
    },
    handleNewFile() {
      // Check if a folder is selected, if not select the root folder
      const nodeSelected = this.ideInfo.nodeSelected;
      if (!nodeSelected || (nodeSelected.type !== 'dir' && nodeSelected.type !== 'folder')) {
        // Select the root folder
        const rootFolder = this.ideInfo.currProj?.data;
        if (rootFolder) {
          this.$store.commit('ide/setNodeSelected', rootFolder);
        }
      }
      
      // Emit event to open new file dialog
      this.$emit('new-file');
    },
    handleNewFolder() {
      // Check if a folder is selected, if not select the root folder
      const nodeSelected = this.ideInfo.nodeSelected;
      if (!nodeSelected || (nodeSelected.type !== 'dir' && nodeSelected.type !== 'folder')) {
        // Select the root folder
        const rootFolder = this.ideInfo.currProj?.data;
        if (rootFolder) {
          this.$store.commit('ide/setNodeSelected', rootFolder);
        }
      }
      
      // Emit event to open new folder dialog
      this.$emit('new-folder');
    },
    handleImportFile() {
      // Check if a folder is selected, if not select the root folder
      const nodeSelected = this.ideInfo.nodeSelected;
      if (!nodeSelected || (nodeSelected.type !== 'dir' && nodeSelected.type !== 'folder')) {
        // Select the root folder
        const rootFolder = this.ideInfo.currProj?.data;
        if (rootFolder) {
          this.$store.commit('ide/setNodeSelected', rootFolder);
        }
      }
      
      // Emit event to open import file dialog
      this.$emit('import-file');
    },
    handleBulkUpload() {
      // Emit event to open bulk upload dialog (admin only)
      this.$emit('bulk-upload');
    },
    refreshTree() {
      // Refresh all projects if in multi-root mode
      const self = this;
      
      if (this.ideInfo.allProjects && this.ideInfo.allProjects.length > 0) {
        // Multi-root mode - refresh all projects
        const projectsToRefresh = this.ideInfo.allProjects.map(p => p.name);
        const refreshedProjects = [];
        let refreshCount = 0;
        
        projectsToRefresh.forEach(projectName => {
          this.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
            projectName: projectName,
            callback: (dict) => {
              if (dict.code == 0) {
                refreshedProjects.push(dict.data);
                refreshCount++;
                
                // When all projects are refreshed, update the multi-root view
                if (refreshCount === projectsToRefresh.length) {
                  self.$store.commit('ide/handleMultipleProjects', refreshedProjects);
                  // Update current project if it was refreshed (use refreshProject to preserve state)
                  const currentProjData = refreshedProjects.find(p => p.name === self.ideInfo.currProj.data.name);
                  if (currentProjData) {
                    self.$store.commit('ide/refreshProject', currentProjData);
                  }
                  ElMessage({
                    type: 'success',
                    message: 'All project trees refreshed',
                    duration: 2000
                  });
                }
              }
            }
          });
        });
      } else if (this.ideInfo.currProj && this.ideInfo.currProj.data) {
        // Single project mode - refresh current project
        this.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
          projectName: this.ideInfo.currProj.data.name,
          callback: (dict) => {
            if (dict.code == 0) {
              self.$store.commit('ide/refreshProject', dict.data);
              ElMessage({
                type: 'success',
                message: 'Project tree refreshed',
                duration: 2000
              });
            }
          }
        });
      }
    },
    getIconUrl(data) {
      if (data.type === 'file') {
        return require(`@/assets/vscode-icons/${getIconForFile(data.path.substring(data.path.lastIndexOf('.') + 1))}`);
      }
      else if (data.type === 'dir' || data.type === 'folder') {
        if (this.expandedKeys.includes(data.path)) {
          return require(`@/assets/vscode-icons/${getIconForOpenFolder(data.label)}`);
        }
        else {
          return require(`@/assets/vscode-icons/${getIconForFolder(data.label)}`);
        }
      }
    },
    nodeExpand(data) {
      this.getFile = false;
      this.$store.commit('ide/addExpandNodeKey', data.uuid);
      this.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
    },
    nodeCollapse(data) {
      this.getFile = false;
      this.$store.commit('ide/delExpandNodeKey', data.uuid);
      this.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
    },
    handleNodeClick(data) {
      // Close any open menus
      this.closeAllMenus();
      
      console.log('[ProjTree] handleNodeClick:', {
        path: data.path,
        name: data.name,
        type: data.type,
        projectName: data.projectName,
        fullData: data
      });
      
      this.$store.commit('ide/setNodeSelected', data);
      
      // In multi-root mode, we need to set the correct project as current
      if (this.ideInfo.multiRootData && data.projectName) {
        // Find and set the project that contains this file
        const project = this.ideInfo.allProjects.find(p => p.name === data.projectName);
        if (project) {
          console.log('[ProjTree] Setting project as current:', project.name);
          this.$store.commit('ide/handleProject', project);
        }
      }
      
      // Single click opens file
      if (data.type === 'file') {
        console.log('[ProjTree] Emitting get-item with:', data.path, false, data.projectName);
        this.$emit('get-item', data.path, false, data.projectName); // path, save, projectName
      }
    },
    
    handleDoubleClick(data) {
      // Double click to open file (no longer triggers rename)
      if (data.type === 'file') {
        this.$emit('get-item', data.path, false, data.projectName); // path, save, projectName
      }
    },
    
    handleContextMenu(event, data, node) {
      event.preventDefault();
      // Show context menu for both files and folders
      if (data.type === 'file' || data.type === 'dir' || data.type === 'folder') {
        this.showContextMenu(event, data);
      }
    },
    
    showContextMenu(event, data) {
      this.closeAllMenus();
      
      // Calculate position to prevent overflow
      const menuWidth = 150; // Approximate menu width
      const menuHeight = 200; // Approximate max menu height
      let x = event.clientX;
      let y = event.clientY;
      
      // Adjust if menu would overflow right edge
      if (x + menuWidth > window.innerWidth) {
        x = window.innerWidth - menuWidth - 10;
      }
      
      // Adjust if menu would overflow bottom edge
      if (y + menuHeight > window.innerHeight) {
        y = window.innerHeight - menuHeight - 10;
      }
      
      // Ensure menu doesn't go beyond left edge
      if (x < 10) {
        x = 10;
      }
      
      this.contextMenu = {
        visible: true,
        x: x,
        y: y,
        data: data
      };
      
      // Add event listener to close menu when clicking outside
      document.addEventListener('click', this.closeAllMenus);
    },
    
    showDropdown(event, data) {
      event.preventDefault();
      event.stopPropagation();
      
      this.closeAllMenus();
      
      const rect = event.target.getBoundingClientRect();
      this.dropdown = {
        visible: true,
        x: rect.left,
        y: rect.bottom,
        data: data
      };
      
      // Add event listener to close menu when clicking outside
      document.addEventListener('click', this.closeAllMenus);
    },
    
    closeAllMenus() {
      this.contextMenu.visible = false;
      this.dropdown.visible = false;
      document.removeEventListener('click', this.closeAllMenus);
    },
    
    isProtectedFolder(data) {
      // Check if this is a protected project folder (root level)
      const name = data.label || data.name;

      // For students: all root-level folders except Local are protected
      if (this.currentUser && this.currentUser.role === 'student') {
        return data.path === '/' && name !== 'Local';
      }

      // For professors: only specific system folders are protected (currently none)
      const protectedFolders = [];
      return data.path === '/' && protectedFolders.includes(name);
    },
    
    canRenameOrDelete(data) {
      // If user is not available, deny access
      if (!this.currentUser) return false;
      
      // Professors can do everything except protected folders
      if (this.currentUser.role === 'professor') {
        return !this.isProtectedFolder(data);
      }
      
      // Students can only modify items in their own Local/{username} folder
      if (this.currentUser.role === 'student') {
        const userPath = `Local/${this.currentUser.username}`;
        const itemPath = data.path || '';
        
        // Allow if the item is inside the user's Local folder
        // but not the user's Local/{username} folder itself
        return itemPath.startsWith(userPath + '/') && !this.isProtectedFolder(data);
      }
      
      return false;
    },
    
    startRename(data) {
      // Check permissions first
      if (!this.canRenameOrDelete(data)) {
        ElMessage.warning('You do not have permission to rename this item.');
        return;
      }
      
      const fullName = data.label || data.name;
      let nameToShow = fullName;
      let extension = '';
      
      // For files, extract extension and show only filename for renaming
      if (data.type === 'file') {
        const lastDotIndex = fullName.lastIndexOf('.');
        if (lastDotIndex > 0) { // Ensure there's a filename before the extension
          nameToShow = fullName.substring(0, lastDotIndex);
          extension = fullName.substring(lastDotIndex);
        }
      }
      
      // Different patterns for files vs folders
      const isFile = data.type === 'file';
      const inputPattern = isFile 
        ? /^[a-zA-Z0-9_.-]+$/ // Files: no spaces allowed (safer for code files)
        : /^[a-zA-Z0-9_. -]+$/; // Folders: allow spaces
      const errorMessage = isFile 
        ? 'Invalid filename format (no spaces allowed)'
        : 'Invalid folder name format';

      ElMessageBox.prompt('Enter new name:', 'Rename', {
        confirmButtonText: 'OK',
        cancelButtonText: 'Cancel',
        inputValue: nameToShow,
        inputPattern: inputPattern,
        inputErrorMessage: errorMessage
      }).then(({ value }) => {
        // Add extension back for files
        const finalName = (data.type === 'file' && extension) ? value + extension : value;
        this.doRename(data, finalName);
      }).catch(() => {
        // User cancelled
      });
    },
    
    doRename(data, newName) {
      // Emit rename event to parent with the correct project name
      console.log('[ProjTree] doRename - data:', data);
      console.log('[ProjTree] doRename - projectName from data:', data.projectName);
      
      this.$emit('rename-item', {
        oldPath: data.path,
        newName: newName,
        type: data.type,
        projectName: data.projectName || this.ideInfo.currProj?.data?.name
      });
    },
    
    handleMenuAction(action, data) {
      this.closeAllMenus();
      
      switch(action) {
        case 'open':
          if (data.type === 'file') {
            this.$emit('get-item', data.path, false, data.projectName); // path, save, projectName
          }
          break;
        case 'openInRightPanel':
          if (data.type === 'file') {
            this.$emit('get-item-right-panel', data.path, data.projectName); // Special event for right panel
          }
          break;
        case 'rename':
          this.startRename(data);
          break;
        case 'delete':
          // Check if it's a protected folder
          if (this.isProtectedFolder(data)) {
            ElMessage.warning(`The "${data.label}" folder cannot be deleted as it is protected.`);
            return;
          }
          
          if (data.type === 'directory') {
            // Count folder contents
            const counts = this.countFolderContents(data);
            let message = `Are you sure you want to delete "${data.label}"?`;
            
            if (counts.totalFiles > 0 || counts.totalFolders > 0) {
              const fileText = counts.totalFiles === 1 ? 'file' : 'files';
              const folderText = counts.totalFolders === 1 ? 'folder' : 'folders';
              
              if (counts.totalFiles > 0 && counts.totalFolders > 0) {
                message = `This folder contains ${counts.totalFiles} ${fileText} and ${counts.totalFolders} ${folderText}. Are you sure you want to delete "${data.label}" and all its contents?`;
              } else if (counts.totalFiles > 0) {
                message = `This folder contains ${counts.totalFiles} ${fileText}. Are you sure you want to delete "${data.label}" and all its contents?`;
              } else {
                message = `This folder contains ${counts.totalFolders} ${folderText}. Are you sure you want to delete "${data.label}" and all its contents?`;
              }
            }
            
            ElMessageBox.confirm(
              message,
              'Confirm Delete',
              {
                confirmButtonText: 'Delete',
                cancelButtonText: 'Cancel',
                type: 'warning',
              }
            ).then(() => {
              console.log('[ProjTree] Emitting delete for:', data);
              this.$emit('delete-item', {
                path: data.path,
                type: data.type,
                projectName: data.projectName || this.ideInfo.currProj?.data?.name
              });
            }).catch(() => {
              // User cancelled
            });
          } else {
            // Original file delete logic
            ElMessageBox.confirm(
              `Are you sure you want to delete "${data.label}"?`,
              'Confirm Delete',
              {
                confirmButtonText: 'Delete',
                cancelButtonText: 'Cancel',
                type: 'warning',
              }
            ).then(() => {
              console.log('[ProjTree] Emitting delete for:', data);
              this.$emit('delete-item', {
                path: data.path,
                type: data.type,
                projectName: data.projectName || this.ideInfo.currProj?.data?.name
              });
            }).catch(() => {
              // User cancelled
            });
          }
          break;
        case 'download':
          if (data.type === 'file') {
            this.$emit('download-item', data);
          }
          break;
      }
    },
    
    countFolderContents(folderNode) {
      let totalFiles = 0;
      let totalFolders = 0;
      
      const countRecursive = (node) => {
        if (!node.children) return;
        
        for (const child of node.children) {
          if (child.type === 'file') {
            totalFiles++;
          } else if (child.type === 'directory') {
            totalFolders++;
            countRecursive(child);
          }
        }
      };
      
      countRecursive(folderNode);
      
      return { totalFiles, totalFolders };
    },
  },
  mounted() {
    this.$store.commit('ide/setTreeRef', this.$refs.tree);
    const self = this;
    setTimeout(() => {
      if (!self.ideInfo.treeRef) return;
      self.ideInfo.treeRef.setCurrentKey('/');
      if (self.ideInfo.treeRef.getCurrentNode() !== null) {
        self.$store.commit('ide/setNodeSelected', self.ideInfo.treeRef.getCurrentNode());
      }
      setTimeout(() => {
        if (self.ideInfo.currProj.pathSelected !== null) {
          self.ideInfo.treeRef.setCurrentKey(self.ideInfo.currProj.pathSelected);
          if (self.ideInfo.treeRef.getCurrentNode() !== null) {
            self.$store.commit('ide/setNodeSelected', self.ideInfo.treeRef.getCurrentNode());
          }
        }
      }, 200);
    }, 300);
  },
  watch: {
    'ideInfo.currProj.pathSelected': {
      handler(cur, old) {
        const self = this;
        setTimeout(() => {
          if (self.ideInfo.currProj.pathSelected) {
            self.ideInfo.treeRef.setCurrentKey(self.ideInfo.currProj.pathSelected);
            // self.$store.commit('ide/setNodeSelected', self.ideInfo.currProj.pathSelected);
          }
        }, 100);
      }
    },
  },
  computed: {
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
    isAdmin() {
      // Check if current user is one of the admin accounts
      const adminAccounts = ['sl7927', 'sa9082', 'et2434'];
      return this.currentUser && adminAccounts.includes(this.currentUser.username);
    },
    treeData() {
      // Use multi-root data if available, otherwise fall back to single project
      if (this.ideInfo.multiRootData && this.ideInfo.multiRootData.children.length > 0) {
        console.log('[ProjTree] Using multiRootData with projects:', 
          this.ideInfo.multiRootData.children.map(p => p.name));
        return this.ideInfo.multiRootData.children;
      }
      console.log('[ProjTree] Using single project mode:', this.ideInfo.currProj?.data?.name);
      return this.ideInfo.currProj.data ? [this.ideInfo.currProj.data] : [];
    },
    expandedKeys() {
      return this.ideInfo ? this.ideInfo.currProj.expandedKeys : [];
    },
    defaultExpandedKeys() {
      const expandedKeys = [];
      
      // Only process existing expanded keys - don't auto-expand all root folders
      if (this.expandedKeys !== undefined && Array.isArray(this.expandedKeys)) {
        for (let i = 0; i < this.expandedKeys.length; i++) {
          // Skip null or undefined values
          if (!this.expandedKeys[i]) continue;
          
          let prefix = '';
          const tmp = String(this.expandedKeys[i]).split('/');
          let flag = true;
          for (let j = 0; j < tmp.length; j++) {
            if (tmp[j]) {
              prefix += '/' + tmp[j]
              if (this.expandedKeys.indexOf(prefix) < 0) {
                flag = false;
                break;
              }
            }
            else {
              if (this.expandedKeys.indexOf('/') < 0) {
                flag = false;
                break;
              }
            }
          }
          if (flag) {
            if (expandedKeys.indexOf(this.expandedKeys[i]) < 0) {
              expandedKeys.push(this.expandedKeys[i]);
            }
          }
        }
      }
      
      return [...new Set(expandedKeys)]; // Remove duplicates
    }
  }
}
</script>
<style>
.tree {
  overflow-y: auto;
  overflow-x: auto;
}
.el-tree {
  /* min-width: 100%; */
  display: inline-block !important;
  min-width: 200px;
}

.tree::-webkit-scrollbar {/*scrollbar overall style*/
  width: 5px;     /*height and width correspond to horizontal and vertical scrollbar dimensions*/
  height: 5px;
}
.tree::-webkit-scrollbar-thumb {/*small block inside scrollbar*/
  /* background: #87939A; */
  background: #545a5e;
}
.tree::-webkit-scrollbar-track {/*track inside scrollbar*/
  background: #2F2F2F;
}
.ide-project-list .el-tree-node__content {
  /* height: 56px; */
  color: white;
}
.ide-project-list .el-tree-node.is-expanded>.el-tree-node__children {
  color: white;
}
.ide-project-list .el-tree-node.is-current>.el-tree-node__content {
  /* style for selected nodes without children */
  background-color: #094771 !important;
}
.ide-project-list .el-tree-node__content:hover {
  /* style when mouse hovers over node */
  background-color: #2a2d2e !important;
}
.ide-project-list .el-tree-node:focus>.el-tree-node__content {
  /* style for selected nodes with children */
  background: #094771 !important;
}
.ide-project-list .el-tree-node.is-current>.el-tree-node__content .display-none {
  display: inline-block;
}
</style>

<style scoped>
.proj-tree-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.tree-title {
  font-size: 14px;
  font-weight: 500;
  color: #CCCCCC;
}

.tree-header-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.action-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.1);
}

.action-btn:active {
  transform: scale(0.95);
}

.new-file-btn:hover {
  color: #67c23a;
}

.import-btn:hover {
  color: #e6a23c;
}

.bulk-upload-btn {
  /* Ensure visibility with slightly brighter default */
  color: rgba(255, 255, 255, 0.7) !important;
}

.bulk-upload-btn:hover {
  color: #9c27b0 !important; /* Purple color for bulk upload */
}

.refresh-btn:hover {
  color: #409eff;
}



.ide-project-list {
  background: #282828;
  color: #CCCCCC;
  flex: 1;
  overflow-y: auto;
  /* padding-left: 10px; */
  /* padding-right: 10px; */
}
.node-icon {
  width: 15px;
  height:15px;
}
.node-label {
  color:#A6A6A6;
  letter-spacing: -0.8px;
  font-family: 'Gotham-Book';
  padding-left: 2px;
  flex: 1;
}

.node-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  position: relative;
}

.node-actions {
  display: none;
  margin-left: auto;
  padding-right: 8px;
}

.el-tree-node__content:hover .node-actions {
  display: flex;
}

.dropdown-btn {
  background: transparent;
  border: none;
  color: #969696;
  padding: 2px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  transition: all 0.2s;
}

.dropdown-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #CCCCCC;
}

/* Context Menu & Dropdown Menu Styles */
.context-menu,
.dropdown-menu {
  position: fixed;
  background: var(--bg-secondary, #252526);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  padding: 4px 0;
  min-width: 150px;
  max-width: 250px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 99999;
  overflow: hidden;
}

.menu-item {
  padding: 8px 16px;
  cursor: pointer;
  color: #CCCCCC;
  font-size: 13px;
  transition: background-color 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-item:hover {
  background: #094771;
}

.menu-item.danger {
  color: #F44747;
}

.menu-item.danger:hover {
  background: rgba(244, 71, 71, 0.2);
}

.menu-divider {
  height: 1px;
  background: #464647;
  margin: 4px 0;
}

/* Theme Support for Context Menu */
[data-theme="light"] .context-menu {
  background: #ffffff;
  border-color: #d0d0d0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

[data-theme="light"] .menu-item {
  color: #333333;
}

[data-theme="light"] .menu-item:hover {
  background: #e8e8e8;
}

[data-theme="light"] .menu-item.danger {
  color: #d63384;
}

[data-theme="light"] .menu-item.danger:hover {
  background: rgba(214, 51, 132, 0.1);
}

[data-theme="light"] .menu-divider {
  background: #e0e0e0;
}

/* High Contrast Theme */
[data-theme="high-contrast"] .context-menu {
  background: #000000;
  border: 2px solid #ffffff;
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3);
}

[data-theme="high-contrast"] .menu-item {
  color: #ffffff;
}

[data-theme="high-contrast"] .menu-item:hover {
  background: #333333;
  border: 1px solid #ffff00;
}

[data-theme="high-contrast"] .menu-item.danger {
  color: #ff6b6b;
}

[data-theme="high-contrast"] .menu-item.danger:hover {
  background: rgba(255, 107, 107, 0.2);
  border-color: #ff6b6b;
}

[data-theme="high-contrast"] .menu-divider {
  background: #ffffff;
}

/* Theme Support for Project Tree File Selection */

/* Light Theme - Project Tree */
[data-theme="light"] .tree-header {
  background: rgba(0, 0, 0, 0.03);
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .tree-title {
  color: #333333;
}

[data-theme="light"] .action-btn {
  color: rgba(0, 0, 0, 0.6);
}

[data-theme="light"] .action-btn:hover {
  color: rgba(0, 0, 0, 0.9);
  background: rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .new-file-btn:hover {
  color: #52c41a;
}

[data-theme="light"] .import-btn:hover {
  color: #d48806;
}

[data-theme="light"] .bulk-upload-btn {
  color: rgba(0, 0, 0, 0.7) !important;
}

[data-theme="light"] .bulk-upload-btn:hover {
  color: #7b1fa2 !important;
}

:root[data-theme="light"] .refresh-btn:hover {
  color: #1890ff;
}

:root[data-theme="light"] .ide-project-list {
  background: #f8f8f8;
  color: #333333;
}

:root[data-theme="light"] .node-label {
  color: #000000 !important;
}

:root[data-theme="light"] .ide-project-list .el-tree-node__content {
  color: #000000 !important;
}

/* Light theme overrides with higher specificity */
:root[data-theme="light"] .ide-project-list .el-tree-node.is-current > .el-tree-node__content {
  background-color: #f8fbff !important;
}

:root[data-theme="light"] .ide-project-list .el-tree-node__content:hover {
  background-color: #fafafa !important;
}

:root[data-theme="light"] .ide-project-list .el-tree-node:focus > .el-tree-node__content {
  background: #f8fbff !important;
}

:root[data-theme="light"] .tree::-webkit-scrollbar-thumb {
  background: #c0c0c0;
}

:root[data-theme="light"] .tree::-webkit-scrollbar-track {
  background: #f0f0f0;
}

/* High Contrast Theme - Project Tree */
[data-theme="high-contrast"] .ide-project-list {
  background: #000000;
  color: #ffffff;
}

[data-theme="high-contrast"] .ide-project-list .el-tree-node.is-current > .el-tree-node__content {
  background-color: #ffff00 !important;
  color: #000000 !important;
}

[data-theme="high-contrast"] .ide-project-list .el-tree-node__content:hover {
  background-color: #333333 !important;
  border: 1px solid #ffff00 !important;
}

[data-theme="high-contrast"] .ide-project-list .el-tree-node:focus > .el-tree-node__content {
  background: #ffff00 !important;
  color: #000000 !important;
}

[data-theme="high-contrast"] .tree::-webkit-scrollbar-thumb {
  background: #ffffff;
}

[data-theme="high-contrast"] .tree::-webkit-scrollbar-track {
  background: #333333;
}

[data-theme="high-contrast"] .action-btn {
  color: #ffffff;
}

[data-theme="high-contrast"] .action-btn:hover {
  background: #333333;
  border: 1px solid #ffff00;
}

[data-theme="high-contrast"] .bulk-upload-btn:hover {
  color: #ff00ff; /* Bright magenta for high contrast */
}

/* Disabled menu items */
.menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  color: var(--text-disabled, #6b6b6b) !important;
}

.menu-item.disabled:hover {
  background: transparent !important;
}

[data-theme="light"] .menu-item.disabled {
  color: #cccccc !important;
}

[data-theme="high-contrast"] .menu-item.disabled {
  color: #666666 !important;
  opacity: 0.7;
}
</style>


