<template>
  <div>
    <div class="dialog-cover"></div>
    <div class="new-folder-dialog">
      <div class="dialog-header">
        <h3>New Folder</h3>
        <div class="close-btn" @click="onCancel">
          <X :size="20" />
        </div>
      </div>
      
      <div class="dialog-body">
        <!-- Directory Navigation -->
        <div class="directory-section">
          <label>Select Parent Directory:</label>
          <div class="directory-nav">
            <div class="current-path" @click="toggleDirectoryTree">
              <FolderOpen :size="16" />
              <span>{{ formatCurrentPath(currentPath) }}</span>
              <ChevronDown v-if="showDirectoryTree" :size="16" class="chevron" />
              <ChevronRight v-else :size="16" class="chevron" />
            </div>
            <div class="directory-tree" v-if="showDirectoryTree">
              <div
                v-for="dir in visibleDirectories"
                :key="dir.path"
                class="directory-item"
                :class="{
                  selected: currentPath === dir.path,
                  'root-item': dir.isRoot,
                  'collapsible': dir.hasChildren,
                  'collapsed': isCollapsed(dir.path)
                }"
                :style="{ paddingLeft: (dir.level * 20 + 12) + 'px' }"
                @click="selectDirectory(dir)"
              >
                <!-- Chevron for all folders with children -->
                <template v-if="dir.hasChildren">
                  <ChevronDown
                    v-if="!isCollapsed(dir.path)"
                    :size="14"
                    class="folder-chevron"
                    @click.stop="toggleCollapse(dir)"
                  />
                  <ChevronRight
                    v-else
                    :size="14"
                    class="folder-chevron"
                    @click.stop="toggleCollapse(dir)"
                  />
                </template>
                <template v-else>
                  <span class="folder-spacer"></span>
                </template>

                <!-- Icons for different folder types -->
                <Home v-if="dir.isRoot && !dir.isRootCreation" :size="14" />
                <FolderPlus v-else-if="dir.isRootCreation" :size="14" />
                <Folder v-else :size="14" />

                <span>{{ dir.displayName || dir.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Folder Name Section -->
        <div class="foldername-section">
          <label>Folder Name:</label>
          <div class="foldername-input-wrapper">
            <input 
              type="text" 
              v-model="folderName"
              @input="validateFolderName"
              placeholder="Enter folder name"
              class="foldername-input"
              ref="folderNameInput"
            />
            <div class="folder-type-icon">
              <Folder :size="20" />
            </div>
          </div>
          <div v-if="folderNameError" class="error-hint">
            {{ folderNameError }}
          </div>
          <div v-else class="folder-hint">
            Folder names should not contain special characters
          </div>
        </div>

        <!-- Preview Section -->
        <div v-if="folderName && !folderNameError" class="preview-section">
          <label>Folder will be created at:</label>
          <div class="folder-preview">
            <div class="folder-info">
              <Folder :size="20" />
              <div>
                <div class="folder-path">{{ getFullFolderPath() }}</div>
                <div class="folder-type">Directory</div>
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
          :disabled="!folderName || !!folderNameError || creating"
        >
          {{ creating ? 'Creating...' : 'Create Folder' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { X, FolderOpen, Folder, ChevronRight, ChevronDown, Home, FolderPlus } from 'lucide-vue-next';
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
      folderName: '',
      folderNameError: '',
      creating: false,
      showDirectoryTree: false,
      collapsedFolders: new Set(), // Track which folders are collapsed
    }
  },
  components: {
    X,
    FolderOpen,
    Folder,
    ChevronRight,
    ChevronDown,
    Home,
    FolderPlus
  },
  mounted() {
    this.loadDirectoryStructure();
    // Focus on folder name input
    this.$nextTick(() => {
      this.$refs.folderNameInput?.focus();
    });
  },
  methods: {
    isDirectoryVisibleToStudent(path) {
      if (!this.currentUser || this.currentUser.role !== 'student') {
        return true; // Show all directories to professors and when not logged in
      }

      // For students, since they have their own isolated project (Local/username),
      // all directories within their project should be visible to them.
      // The project-level filtering already ensures they only see their own project.
      return true;
    },
    
    loadDirectoryStructure() {
      // Get directory structure from all projects (multi-root mode)
      if (this.ideInfo.multiRootData && this.ideInfo.multiRootData.children.length > 0) {
        // Build directory tree from all projects
        this.directories = [];
        this.ideInfo.multiRootData.children.forEach(project => {
          // For students, only show projects that start with "Local" (student's own directory)
          if (this.currentUser && this.currentUser.role === 'student') {
            // For students, the project is named "Local/username" not just "Local"
            const expectedProjectPrefix = `Local/${this.currentUser.username}`;
            if (!project.label.startsWith('Local/') || project.label !== expectedProjectPrefix) {
              return; // Skip projects that aren't the student's own Local directory
            }
          }

          // Add each project and its subdirectories
          const projectDirs = this.buildDirectoryTree(project, 0, project.label);
          this.directories = this.directories.concat(projectDirs);
        });
      } else if (this.ideInfo.currProj && this.ideInfo.currProj.data) {
        // Fallback to single project mode
        const projectLabel = this.ideInfo.currProj.data.label || this.ideInfo.currProj.data.name;

        // For students, only process if it's their own Local project
        if (this.currentUser && this.currentUser.role === 'student') {
          const expectedProjectName = `Local/${this.currentUser.username}`;
          if (projectLabel !== expectedProjectName) {
            this.directories = []; // Don't show any directories for non-student projects
            return;
          }
        }

        this.directories = this.buildDirectoryTree(this.ideInfo.currProj.data, 0, projectLabel);
      }

      // For professors, add the "../" option to create folders at root level (same level as Local/ and Lecture Notes/)
      if (this.currentUser && this.currentUser.role === 'professor') {
        this.directories.unshift({
          name: '../',
          displayName: '../ (Root Level)',
          path: 'ROOT_LEVEL',
          level: -1,
          isRoot: true,
          hasChildren: false,
          parentPath: '',
          projectName: '',
          fullPath: 'ROOT_LEVEL',
          isRootCreation: true
        });
      }
      
      // For students, always force default to their Local project and directory
      if (this.currentUser && this.currentUser.role === 'student') {
        // Always default students to their Local/username project
        this.currentProject = `Local/${this.currentUser.username}`;

        // Always default to their user directory root (which is the project root for them)
        this.currentPath = '/';
      } else {
        // For professors, set current path to selected node if it's a directory
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
      }
    },
    buildDirectoryTree(node, level = 0, projectName = null, parentPath = '') {
      let dirs = [];

      // Add the root directory
      if (level === 0) {
        const hasChildren = node.children && node.children.some(child =>
          (child.type === 'dir' || child.type === 'folder') &&
          this.isDirectoryVisibleToStudent(child.path)
        );

        dirs.push({
          name: projectName || node.label || '/',
          displayName: projectName || node.label || '/',
          path: node.path || '/',
          level: 0,
          isRoot: true,
          hasChildren: hasChildren,
          parentPath: '',
          projectName: projectName || node.label,
          fullPath: projectName ? `${projectName}${node.path}` : node.path
        });
      }

      // Process children
      if (node.children) {
        node.children.forEach(child => {
          if (child.type === 'dir' || child.type === 'folder') {
            // Check if this directory should be visible to the current user
            if (this.isDirectoryVisibleToStudent(child.path)) {
              // Check if this directory has children
              const hasChildren = child.children && child.children.some(grandchild =>
                (grandchild.type === 'dir' || grandchild.type === 'folder') &&
                this.isDirectoryVisibleToStudent(grandchild.path)
              );

              const currentParentPath = level === 0 ? (node.path || '/') : parentPath;

              dirs.push({
                name: child.label,
                displayName: child.label,
                path: child.path,
                level: level + 1,
                isRoot: false,
                hasChildren: hasChildren,
                parentPath: currentParentPath,
                projectName: projectName || child.projectName,
                fullPath: projectName ? `${projectName}${child.path}` : child.path
              });

              // Recursively add subdirectories
              if (child.children) {
                dirs = dirs.concat(this.buildDirectoryTree(child, level + 1, projectName, child.path));
              }
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
    toggleCollapse(dir) {
      if (!dir.hasChildren) return;

      if (this.collapsedFolders.has(dir.path)) {
        this.collapsedFolders.delete(dir.path);
      } else {
        this.collapsedFolders.add(dir.path);
      }

      // Force reactivity
      this.$forceUpdate();
    },
    isCollapsed(path) {
      return this.collapsedFolders.has(path);
    },
    isDirectoryVisible(dir) {
      // Always show root level directories
      if (dir.level === 0 || dir.isRoot) return true;

      // Check if any parent is collapsed
      let parentPath = dir.parentPath;
      while (parentPath && parentPath !== '/') {
        if (this.collapsedFolders.has(parentPath)) {
          return false;
        }
        // Find the parent directory to get its parentPath
        const parentDir = this.directories.find(d => d.path === parentPath);
        parentPath = parentDir ? parentDir.parentPath : null;
      }

      return true;
    },
    formatCurrentPath(path) {
      // Handle root-level creation display
      if (this.currentPath === 'ROOT_LEVEL') {
        return '../ (Root Level)';
      }

      // If path already contains the project name, return as is
      if (path && path !== '/') {
        // Check if path already starts with a known project name
        const knownProjects = ['Local', 'Lecture Notes'];
        for (let proj of knownProjects) {
          if (path.startsWith(proj)) {
            return path;
          }
        }
      }

      if (this.currentProject) {
        if (path === '/') {
          // Special case for students: when they're in Local project root, show their username
          if (this.currentUser && this.currentUser.role === 'student' && this.currentProject === 'Local') {
            return `Local/${this.currentUser.username}`;
          }
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
    validateFolderName() {
      this.folderNameError = '';
      
      if (!this.folderName) {
        return;
      }
      
      // Check for invalid characters
      if (/[<>:"|?*\\\/]/.test(this.folderName)) {
        this.folderNameError = 'Folder name contains invalid characters';
        return;
      }
      
      // Check for reserved names
      const reserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                       'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                       'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'];
      const nameUpper = this.folderName.toUpperCase();
      if (reserved.includes(nameUpper)) {
        this.folderNameError = 'This is a reserved folder name';
        return;
      }
      
      // Check if folder starts or ends with dot
      if (this.folderName.startsWith('.') || this.folderName.endsWith('.')) {
        this.folderNameError = 'Folder name cannot start or end with a dot';
        return;
      }
      
      // Check if folder name is too long
      if (this.folderName.length > 255) {
        this.folderNameError = 'Folder name is too long';
        return;
      }
    },
    getFullFolderPath() {
      const folderName = this.folderName || 'new_folder';

      // Handle root-level creation
      if (this.currentPath === 'ROOT_LEVEL') {
        return `${folderName} (at root level)`;
      }

      const path = this.currentPath === '/'
        ? `/${folderName}`
        : `${this.currentPath}/${folderName}`;

      return this.formatCurrentPath(path);
    },
    async onCreate() {
      if (!this.folderName || this.folderNameError) return;

      this.creating = true;

      try {
        const folderName = this.folderName;
        let parentPath = this.currentPath;
        let projectName = this.currentProject || this.ideInfo.currProj?.data?.name || this.ideInfo.currProj?.config?.name;

        // Handle root-level folder creation for professors
        const isRootCreation = parentPath === 'ROOT_LEVEL';

        if (!isRootCreation) {
          // Special handling for students: translate Local project paths to actual student directory
          if (this.currentUser && this.currentUser.role === 'student' && projectName === 'Local') {
            // For students, when they're in the "Local" project, we need to send the actual student path
            if (parentPath === '/' || parentPath === `Local/${this.currentUser.username}`) {
              // Student is at their root directory, send the actual path
              parentPath = `Local/${this.currentUser.username}`;
              projectName = '';  // Clear project name since we're sending the full path
            } else if (parentPath.startsWith(`Local/${this.currentUser.username}/`)) {
              // Student is in a subdirectory, path is already correct
              projectName = '';  // Clear project name since we're sending the full path
            } else {
              // Fallback: ensure student path is correct
              parentPath = `Local/${this.currentUser.username}${parentPath === '/' ? '' : parentPath}`;
              projectName = '';  // Clear project name since we're sending the full path
            }
          }
        }

        const actualParentPath = isRootCreation ? '' : parentPath;
        const actualProjectName = isRootCreation ? '' : projectName;

        console.log('[DialogNewFolder] ========== FOLDER CREATION DEBUG ==========');
        console.log('[DialogNewFolder] Input values:', {
          folderName,
          parentPath,
          projectName,
          'this.currentPath': this.currentPath,
          'this.currentProject': this.currentProject
        });
        console.log('[DialogNewFolder] Computed values:', {
          actualParentPath,
          actualProjectName,
          isRootCreation
        });
        console.log('[DialogNewFolder] Will send to server:', {
          projectName: actualProjectName,
          parentPath: actualParentPath,
          folderName: folderName,
          isRootCreation: isRootCreation
        });

        // Create the folder using the IDE store action
        await new Promise((resolve, reject) => {
          this.$store.dispatch(`ide/${types.IDE_CREATE_FOLDER}`, {
            projectName: actualProjectName,
            parentPath: actualParentPath,
            folderName: folderName,
            isRootCreation: isRootCreation,
            callback: (response) => {
              console.log('[DialogNewFolder] Create folder response:', response);
              
              if (response.code === 0) {
                // Folder created successfully
                ElMessage.success(`Folder "${folderName}" created successfully`);
                
                // Refresh the project tree
                if (isRootCreation) {
                  // For root-level creation, first refresh the project list, then load all projects
                  this.$store.dispatch(`ide/${types.IDE_LIST_PROJECTS}`, {
                    callback: (listResponse) => {
                      console.log('[DialogNewFolder] Project list refresh response:', listResponse);
                      if (listResponse.code === 0) {
                        // Update the project list in store
                        this.$store.commit('ide/handleProjects', listResponse.data);

                        // Now load all default projects with the updated list
                        if (this.ideInfo.multiRootData) {
                          this.$parent.loadAllDefaultProjects?.();
                        }
                      }
                    }
                  });
                } else {
                  // For regular folder creation, refresh the specific project
                  this.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
                    projectName: actualProjectName,
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
                }

                // Emit folder created event
                const newFolderPath = isRootCreation ? `/${folderName}` :
                  (actualParentPath === '/' ? `/${folderName}` : `${actualParentPath}/${folderName}`);
                this.$emit('folder-created', {
                  path: newFolderPath,
                  projectName: actualProjectName,
                  isRootCreation: isRootCreation
                });
                
                // Close dialog
                this.$emit('update:modelValue', false);
                resolve();
              } else {
                // Error creating folder
                const errorMsg = response.message || response.msg || 'Failed to create folder';
                ElMessage.error(errorMsg);
                reject(new Error(errorMsg));
              }
            }
          });
        });
      } catch (error) {
        console.error('[DialogNewFolder] Error creating folder:', error);
        ElMessage.error('Failed to create folder: ' + error.message);
      } finally {
        this.creating = false;
      }
    },
    onCancel() {
      this.$emit('update:modelValue', false);
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
    },
    visibleDirectories() {
      return this.directories.filter(dir => {
        // Apply both collapse filtering and student visibility filtering
        const isVisible = this.isDirectoryVisible(dir);
        const isStudentVisible = this.isDirectoryVisibleToStudent(dir.path);
        return isVisible && isStudentVisible;
      });
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

.new-folder-dialog {
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
.foldername-section,
.preview-section {
  margin-bottom: 20px;
}

.directory-section label,
.foldername-section label,
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

.directory-item.collapsible {
  cursor: pointer;
}

.directory-item:hover {
  background: var(--hover-bg, #094771);
}

.folder-chevron {
  cursor: pointer;
  transition: transform 0.2s ease;
  padding: 2px;
  border-radius: 2px;
  margin-right: 4px;
}

.folder-chevron:hover {
  background: rgba(255, 255, 255, 0.1);
}

.folder-spacer {
  width: 14px;
  height: 14px;
  display: inline-block;
  margin-right: 4px;
}

.foldername-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.foldername-input {
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

.foldername-input:focus {
  outline: none;
  border-color: var(--accent-color, #007acc);
  background: var(--input-focus-bg, #383838);
}

.foldername-input::placeholder {
  color: var(--text-disabled, #6b6b6b);
}

.folder-type-icon {
  color: var(--text-secondary, #969696);
}

.folder-hint,
.error-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-secondary, #969696);
}

.error-hint {
  color: var(--error-color, #f44747);
}

.folder-preview {
  padding: 12px;
  background: var(--preview-bg, #252526);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
}

.folder-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.folder-path {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: var(--text-primary, #cccccc);
  word-break: break-all;
}

.folder-type {
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

/* Light Theme Support */
[data-theme="light"] .dialog-overlay {
  background: rgba(0, 0, 0, 0.3);
}

[data-theme="light"] .dialog-content {
  background: #ffffff;
  border-color: #d0d0d0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

[data-theme="light"] .dialog-header {
  background: #ffffff;
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .dialog-header h3 {
  color: #333333;
}

[data-theme="light"] .close-btn {
  color: rgba(0, 0, 0, 0.6);
}

[data-theme="light"] .close-btn:hover {
  color: rgba(0, 0, 0, 0.9);
  background: rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .current-path {
  background: #f8f8f8;
  border-color: #d0d0d0;
  color: #333333;
}

[data-theme="light"] .current-path:hover {
  background: #f0f0f0;
  border-color: #1890ff;
}

[data-theme="light"] .directory-dropdown {
  background: #ffffff;
  border-color: #d0d0d0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

[data-theme="light"] .directory-item {
  color: #333333;
}

[data-theme="light"] .directory-item:hover {
  background: #fafafa;
}

[data-theme="light"] .directory-item.selected {
  background: #f0f8ff;
}

[data-theme="light"] .foldername-input {
  background: #ffffff;
  border-color: #d0d0d0;
  color: #333333;
}

[data-theme="light"] .foldername-input:focus {
  border-color: #1890ff;
  background: #ffffff;
}

[data-theme="light"] .foldername-input::placeholder {
  color: #999999;
}

[data-theme="light"] .btn-cancel {
  background: #f8f8f8;
  color: #333333;
  border-color: #d0d0d0;
}

[data-theme="light"] .btn-cancel:hover {
  background: #e8e8e8;
}

[data-theme="light"] .btn-create {
  background: #1890ff;
}

[data-theme="light"] .btn-create:hover:not(:disabled) {
  background: #096dd9;
}

[data-theme="light"] .directory-tree::-webkit-scrollbar-track,
[data-theme="light"] .dialog-body::-webkit-scrollbar-track {
  background: #f1f1f1;
}

[data-theme="light"] .directory-tree::-webkit-scrollbar-thumb,
[data-theme="light"] .dialog-body::-webkit-scrollbar-thumb {
  background: #c0c0c0;
}

[data-theme="light"] .directory-tree::-webkit-scrollbar-thumb:hover,
[data-theme="light"] .dialog-body::-webkit-scrollbar-thumb:hover {
  background: #a0a0a0;
}
</style>