<template>
  <div class="main-wrapper ide-wrapper ide-container">
    <TopMenu class="top-menu"
      :consoleLimit="consoleLimit"
      :hasRunProgram="hasRunProgram"
      @set-text-dialog="setTextDialog"
      @set-del-dialog="setDelDialog"
      @set-projs-dialog="setProjsDialog"
      v-on:run-item="runPathSelected"
      @stop-item="stop"
      @theme-changed="handleThemeChange"
      @open-upload-dialog="showUploadDialog = true"
      @download-file="downloadFile"
    ></TopMenu>
    <div id="total-frame" class="total-frame">
      <ProjTree id="left-frame" class="left-frame float-left"
        v-on:get-item="getFile"
      ></ProjTree>
      <div id="right-frame" class="right-frame">
        <!-- Editor Panel -->
        <div class="editor-panel" :style="{ width: editorWidth }">
          <div class="editor-tab-bar">
            <CodeTabs
              v-if="ideInfo.codeItems.length > 0"
              v-on:select-item="selectFile"
              v-on:close-item="closeFile">
            </CodeTabs>
          </div>
          <div class="editor-content">
            <template v-for="(item, index) in ideInfo.codeItems" :key="item.path + index">
              <IdeEditor 
                :codeItem="item"
                :codeItemIndex="index"
                :consoleLimit="consoleLimit"
                @run-item="runPathSelected"
                v-if="ideInfo.codeSelected.path === item.path" 
                v-on:update-item="updateItem"></IdeEditor>
            </template>
          </div>
        </div>

        <!-- Resizable Splitter -->
        <div class="panel-splitter" 
             @mousedown="startResize" 
             :class="{ 'resizing': isResizing }">
          <div class="splitter-handle"></div>
        </div>

        <!-- Console Toggle Button -->
        <div v-if="showConsole" class="console-toggle-btn" @click="toggleConsole" :title="consoleVisible ? 'Hide Console' : 'Show Console'">
          {{ consoleVisible ? '◀' : '▶' }}
        </div>
        
        <!-- Console Panel -->
        <div class="console-panel" 
             :style="{ width: consoleWidth }"
             v-show="!isMarkdown && showConsole && consoleVisible">
          
          <!-- New Tab System -->
          <div class="console-mode-tabs">
            <button 
              :class="['tab-button', { 'active': consoleModeTab === 'output' }]"
              @click="consoleModeTab = 'output'">
              📄 Output
              <span v-if="outputBadgeCount > 0" class="tab-badge">{{ outputBadgeCount }}</span>
            </button>
            <button 
              :class="['tab-button', { 'active': consoleModeTab === 'terminal' }]"
              @click="switchToTerminalTab">
              💻 Terminal
              <span v-if="terminalBadgeCount > 0" class="tab-badge">{{ terminalBadgeCount }}</span>
            </button>
          </div>

          <!-- Output Tab Content -->
          <div v-show="consoleModeTab === 'output'" class="tab-content output-tab">
            <div class="console-tab-bar" v-if="showConsole">
              <ConsoleTabs
                v-if="ideInfo.consoleItems.length > 0"
                v-on:select-item="selectConsole"
                v-on:close-item="closeConsoleSafe">
              </ConsoleTabs>
            </div>
            <div class="console-content">
              <template v-for="(item, index) in ideInfo.consoleItems" :key="item.path + index">
                <UnifiedConsole
                  :item="item"
                  :isRunning="item.run"
                  @run-item="runConsoleSelected"
                  @stop-item="stop"
                  @send-input="handleProgramInput"
                  v-if="ideInfo.consoleSelected.path === item.path && ideInfo.consoleSelected.id === item.id">
                </UnifiedConsole>
              </template>
            </div>
          </div>

          <!-- Terminal Tab Content -->
          <div v-show="consoleModeTab === 'terminal'" class="tab-content terminal-tab">
            <div class="terminal-header">
              <span class="terminal-title">Python Interactive Terminal (REPL)</span>
              <div class="terminal-actions">
                <button @click="restartTerminal" class="terminal-btn">Restart</button>
                <button @click="clearTerminal" class="terminal-btn">Clear</button>
              </div>
            </div>
            <div class="terminal-content" ref="terminalContent">
              <!-- Terminal Output -->
              <div class="terminal-output">
                <!-- Welcome message -->
                <div v-if="terminalOutput.length === 0" class="terminal-welcome">
                  <div v-if="pyodideLoading" class="pyodide-loading">
                    <div>🐍 Loading Python environment...</div>
                    <div>Please wait while Pyodide initializes (~10MB download)</div>
                    <div class="loading-spinner">⏳</div>
                  </div>
                  <div v-else-if="pyodideReady" class="pyodide-ready">
                    <div>🐍 Python 3.11 Interactive Shell (Powered by Pyodide)</div>
                    <div>Type Python commands and press Enter to execute.</div>
                    <div>Variables persist across commands - full Python environment!</div>
                    <div class="python-features">Available: numpy, pandas, matplotlib, and more!</div>
                  </div>
                  <div v-else class="pyodide-not-loaded" @click="initializePyodide">
                    <div>🐍 Python Interactive Terminal</div>
                    <div>Click here or type a command to initialize Python environment.</div>
                  </div>
                </div>
                
                <!-- Terminal history -->
                <div v-for="(item, index) in terminalOutput" :key="index" class="terminal-line">
                  <div v-if="item.type === 'input'" class="terminal-input-line">
                    <span class="prompt-symbol">>>> </span>
                    <span class="input-text">{{ item.content }}</span>
                  </div>
                  <div v-else-if="item.type === 'output'" class="terminal-output-line">
                    <pre>{{ item.content }}</pre>
                  </div>
                  <div v-else-if="item.type === 'error'" class="terminal-error-line">
                    <pre>{{ item.content }}</pre>
                  </div>
                </div>
              </div>
              
              <!-- Current input prompt -->
              <div class="terminal-current-prompt">
                <span class="prompt-symbol">>>> </span>
                <input 
                  type="text" 
                  class="terminal-input"
                  placeholder="Enter Python command..."
                  v-model="terminalInput"
                  @keyup.enter="executeTerminalCommand"
                  @keyup.up="navigateHistory('up')"
                  @keyup.down="navigateHistory('down')"
                  ref="terminalInputField">
              </div>
            </div>
          </div>
        </div>
      </div>
      <DialogProjs v-if="showProjsDialog"
        @on-cancel="onCloseProjsDialog" @on-select="onSelectProj" @on-delete="onDeleteProj" 
        @set-text-dialog="setTextDialog"></DialogProjs>
      <DialogText v-if="showFileDialog" :title="dialogTitle" :text="dialogText" :tips="dialogTips" @check-input="inputIsLegal"
        @on-cancel="onCloseTextDialog" @on-create="onCreate"></DialogText>
      <DialogDelete v-if="showDeleteDialog" :title="dialogTitle"
        @on-cancel="onCancelDelete" @on-delete="onDelete"></DialogDelete>
      <DialogUpload v-if="showUploadDialog" v-model="showUploadDialog" @refresh-tree="refreshProjectTree" @close="showUploadDialog = false"></DialogUpload>
    </div>
  </div>
</template>

<script>
import * as types from '../../store/mutation-types';
import { ElMessage, ElMessageBox } from 'element-plus';
import TopMenu from './pages/ide/TopMenu';
import CodeTabs from './pages/ide/CodeTabs';
import UnifiedConsole from './pages/ide/UnifiedConsole';
import ConsoleTabs from './pages/ide/ConsoleTabs';
import ProjTree from './pages/ide/ProjTree';
import IdeEditor from './pages/ide/IdeEditor';
import DialogProjs from './pages/ide/dialog/DialogProjs';
import DialogText from './pages/ide/dialog/DialogText';
import DialogDelete from './pages/ide/dialog/DialogDelete';
import DialogUpload from './pages/ide/dialog/DialogUpload';
const path = require('path');

export default {
  data() {
    return {
      showDeleteDialog: false,
      showFileDialog: false,
      showProjsDialog: false,
      showUploadDialog: false,
      showCover: true,
      
      dialogType: '',
      dialogTitle: '',
      dialogTips: '',
      dialogText: '',
      
      // Split layout properties - keep editor at full size
      consoleWidth: '0%',
      editorWidth: '100%',
      isResizing: false,
      startX: 0,
      startConsoleWidth: 0,
      minConsoleWidth: 300,
      maxConsoleWidth: 70, // percentage
      consoleVisible: true, // Control console visibility
      
      // Console tab system
      consoleModeTab: 'output', // 'output' | 'terminal'
      outputBadgeCount: 0,
      terminalBadgeCount: 0,
      terminalInput: '',
      terminalHistory: [],
      terminalHistoryIndex: -1,
      terminalOutput: [],
      terminalSessionActive: false,
      
      // Pyodide Python integration
      pyodide: null,
      pyodideLoading: false,
      pyodideReady: false
    }
  },
  components: {
    TopMenu,
    CodeTabs,
    UnifiedConsole,
    ConsoleTabs,
    ProjTree,
    IdeEditor,
    DialogProjs,
    DialogText,
    DialogDelete,
    DialogUpload,
  },
  created() {
  },
  mounted() {
    // Load saved console height from localStorage
    const savedHeight = localStorage.getItem('ide-console-height');
    if (savedHeight) {
      this.consoleHeight = Math.max(this.minConsoleHeight, Math.min(this.maxConsoleHeight, parseInt(savedHeight)));
    }
    if (!this.wsInfo.rws) {
      this.$store.dispatch('websocket/init', {});
    }
    
    // Load user layout preferences
    this.loadLayoutPreferences();
    
    const self = this;
    const t = setInterval(() => {
      if (self.wsInfo.connected) {
        this.$store.dispatch(`ide/${types.IDE_LIST_PROJECTS}`, {
          callback: (dict) => {
            clearInterval(t);
            if (dict.code == 0) {
              this.$store.commit('ide/handleProjects', dict.data);
              // Load all default projects instead of just one
              self.loadAllDefaultProjects();
            }
          }
        })
      }
    }, 1000);
    window.addEventListener('resize', this.resize);
    
    // Update max console height based on window size
    this.updateMaxConsoleHeight();
  },
  computed: {
    wsInfo() {
      return this.$store.getters['websocket/wsInfo']();
      // return this.$store.state.websocket.wsInfoMap.default;
    },
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
    isMarkdown() {
      if (this.ideInfo.codeSelected.path)
        return this.ideInfo.codeSelected.path.endsWith('.md');
      else
        return false;
    },
    isMediaFile() {
      if (this.ideInfo.codeSelected.path) {
        const mediaExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.pdf'];
        const path = this.ideInfo.codeSelected.path.toLowerCase();
        return mediaExtensions.some(ext => path.endsWith(ext));
      }
      return false;
    },
    consoleLimit() {
      let count = 0;
      for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
        if (this.ideInfo.consoleItems[i].run === true && !(this.ideInfo.consoleItems[i].name === 'Terminal' && this.ideInfo.consoleItems[i].path === 'Terminal')) {
          count += 1;
        }
      }
      return count >= 3;
    },
    hasRunProgram() {
      return this.ideInfo.consoleItems.some(item => item.run);
    },
    showConsole() {
      const show = this.ideInfo.consoleItems.length !== 0;
      return show;
    }
  },
  methods: {
    toggleConsole() {
      this.consoleVisible = !this.consoleVisible;
    },
    handleThemeChange(theme) {
      // Theme change event handler - can be used for additional logic if needed
      console.log('Theme changed to:', theme);
    },
    downloadFile(fileInfo) {
      // Check if it's a binary file
      const binaryExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.pdf', '.zip', '.tar', '.gz'];
      const isBinary = binaryExtensions.some(ext => fileInfo.fileName.toLowerCase().endsWith(ext));
      
      this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
        projectName: fileInfo.projectName,
        filePath: fileInfo.filePath,
        binary: isBinary,
        callback: (dict) => {
          if (dict.code == 0) {
            // Create download link
            const blob = isBinary 
              ? new Blob([Uint8Array.from(atob(dict.data), c => c.charCodeAt(0))], { type: 'application/octet-stream' })
              : new Blob([dict.data], { type: 'text/plain' });
            
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = fileInfo.fileName;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            ElMessage({
              type: 'success',
              message: `Downloaded ${fileInfo.fileName}`,
              duration: 2000
            });
          } else {
            ElMessage({
              type: 'error',
              message: `Failed to download ${fileInfo.fileName}`,
              duration: 3000
            });
          }
        }
      });
    },
    refreshProjectTree() {
      // Refresh the project tree by re-fetching the project data
      const self = this;
      if (this.ideInfo.currProj && this.ideInfo.currProj.data) {
        this.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
          projectName: this.ideInfo.currProj.data.name,
          callback: (dict) => {
            if (dict.code == 0) {
              self.$store.commit('ide/handleProject', dict.data);
              ElMessage({
                type: 'success',
                message: 'Project tree refreshed successfully',
                duration: 2000
              });
            }
          }
        });
      }
    },
    inputIsLegal(text, callback) {
      this.dialogText = text;
      let isLegal = this.checkStrIsLegal(this.dialogText, this.dialogType === 'create-file' || this.dialogType === 'rename-file');
      if (isLegal) {
        if (this.dialogType === 'create-project' || this.dialogType === 'rename-project') {
          isLegal = !this.isProjExist(this.dialogText);
        }
        else if (this.dialogType === 'create-file' || this.dialogType === 'rename-file' || this.dialogType === 'create-folder' || this.dialogType === 'rename-folder') {
          isLegal = !this.isFileExist(this.dialogText, this.dialogType === 'create-file' || this.dialogType === 'create-folder');
        }
      }
      callback(isLegal);
      return isLegal;
    },
    isProjExist(name) {
      const exist = this.ideInfo.projList.some(item => item.name === name);
      if (exist) {
        this.dialogTips = 'Project name already exists';
      }
      return exist;
    },
    getParentData(path) {
      if (this.ideInfo.treeRef.currentNode && this.ideInfo.treeRef.currentNode.parent) {
        return this.ideInfo.treeRef.currentNode.parent.data;
      }
      else {
        let data = this.ideInfo.currProj.data;
        let alive = true;
        while (alive) {
          alive = false;
          for (var i = 0; i < data.children.length; i++) {
            if (data.children[i].path === this.ideInfo.nodeSelected.path) {
              return data;
            }
            else if (path.indexOf(data.children[i].path) === 0) {
              data = data.children[i];
              alive = true;
              break;
            }
          }
        }
      }
    },
    isFileExist(name, isCreate) {
      let exist = false;
      if (isCreate) {
        exist = this.ideInfo.nodeSelected.children.some(item => item.name === name);
      }
      else {
        const parentData = this.getParentData(this.ideInfo.nodeSelected.path);
        if (parentData && parentData.children)
          exist = parentData.children.some(item => item.name === name);
      }
      if (exist) {
        this.dialogTips = 'File with the same name already exists';
      }
      return exist;
    },
    checkStrIsLegal(str, isFile) {
      this.dialogTips = '';
      let name = isFile ? str.lastIndexOf('.') !== -1 ? str.substring(0, str.lastIndexOf('.')) : str : str;
      if (!name) {
        this.dialogTips = 'Name cannot be empty';
        return false;
      }
      else if (name.length > 15) {
        this.dialogTips = 'Name length cannot exceed 15 characters';
        return false;
      }
      if (isFile && str.endsWith('.')) {
        this.dialogTips = 'Name can only contain letters, numbers and underscore _';
        return false;
      }
      const ret = /^[a-zA-Z0-9_]+$/.test(name);
      if (!ret) {
        this.dialogTips = 'Name can only contain letters, numbers and underscore _';
      }
      return ret;
    },
    listProjects(projectName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_LIST_PROJECTS}`, {
        callback: (dict) => {
          if (dict.code == 0) {
            self.$store.commit('ide/handleProjects', dict.data);
            if (projectName) {
              self.getProject(projectName);
            }
          }
        }
      });
    },
    loadAllDefaultProjects() {
      const self = this;
      const defaultProjects = ['Local', 'Lecture Notes', 'Python'];
      const loadedProjects = [];
      let loadCount = 0;
      
      defaultProjects.forEach(projectName => {
        // Check if project exists in the list
        const projectExists = this.ideInfo.projList.some(p => p.name === projectName);
        if (projectExists) {
          this.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
            projectName: projectName,
            callback: (dict) => {
              if (dict.code == 0) {
                loadedProjects.push(dict.data);
                loadCount++;
                
                // When all projects are loaded, combine them
                if (loadCount === defaultProjects.filter(p => 
                  self.ideInfo.projList.some(proj => proj.name === p)
                ).length) {
                  self.$store.commit('ide/handleMultipleProjects', loadedProjects);
                  // Also set the first project as current for compatibility
                  if (loadedProjects.length > 0) {
                    self.$store.commit('ide/handleProject', loadedProjects[0]);
                  }
                }
              }
            }
          });
        }
      });
    },
    getProject(name) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
        projectName: name === undefined ? this.ideInfo.currProj.config.name : name,
        callback: (dict) => {
          if (dict.code == 0) {
            self.$store.commit('ide/handleProject', dict.data);
            for (var i = 0; i < self.ideInfo.currProj.config.openList.length; i++) {
              self.getFile(self.ideInfo.currProj.config.openList[i], false);
            }
          }
        }
      });
    },
    getFile(path, save) {
      const self = this;
      // Check if it's a media file
      const mediaExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.pdf'];
      const isMediaFile = mediaExtensions.some(ext => path.toLowerCase().endsWith(ext));
      
      if (isMediaFile) {
        // For media files, don't fetch content, just add to tabs
        self.$store.commit('ide/handleGetFile', {
          filePath: path,
          data: '', // Empty content for media files
          save: save,
          isMedia: true
        });
        if (save !== false)
          self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
      } else {
        // For regular files, fetch content as before
        this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
          projectName: this.ideInfo.currProj?.data?.name, // Ensure project name is passed
          filePath: path,
          callback: (dict) => {
            if (dict.code == 0) {
              self.$store.commit('ide/handleGetFile', {
                filePath: path,
                data: dict.data,
                save: save,
                isMedia: false
              });
              if (save !== false)
                self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
            } else {
              console.error('Failed to get file:', path, dict);
            }
          }
        });
      }
    },
    setTextDialog(data) {
      this.dialogType = data.type;
      this.dialogTitle = data.title;
      this.dialogText = data.text;
      this.dialogTips = data.tips;
      this.showFileDialog = true;
      this.showProjsDialog = false;
    },
    setDelDialog(data) {
      this.dialogType = '';
      this.dialogTitle = data.title;
      this.dialogText = '';
      this.dialogTips = '';
      this.showDeleteDialog = true;
    },
    setProjsDialog(data) {
      this.dialogType = '';
      this.dialogTitle = '';
      this.dialogText = '';
      this.dialogTips = '';
      this.showProjsDialog = true;
    },
    onCloseTextDialog() {
      this.showFileDialog = false;
      if (this.ideInfo.nodeSelected) {
        this.ideInfo.treeRef.setCurrentNode(this.ideInfo.nodeSelected);
      }
      if (this.dialogType === 'create-project') {
        this.showProjsDialog = true;
      }
    },
    onCloseProjsDialog() {
      this.showProjsDialog = false;
      this.showFileDialog = false;
      this.showDeleteDialog = false;
      if (this.ideInfo.nodeSelected) {
        this.ideInfo.treeRef.setCurrentNode(this.ideInfo.nodeSelected);
      }
    },
    onCancelDelete() {
      this.showDeleteDialog = false;
      if (this.ideInfo.nodeSelected) {
        this.ideInfo.treeRef.setCurrentNode(this.ideInfo.nodeSelected);
      }
    },
    deleteProject(projectName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_DEL_PROJECT}`, {
        projectName: projectName,
        callback: (dict) => {
          if (dict.code == 0) {
            self.$store.commit('ide/handleDelProject', projectName);
          }
        }
      });
    },
    deleteFile(filePath, projectName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_DEL_FILE}`, {
        projectName: projectName === undefined ? this.ideInfo.currProj.config.name : projectName,
        filePath: filePath,
        callback: (dict) => {
          if (dict.code == 0) {
            const parentData = self.getParentData(filePath);
            self.$store.commit('ide/handleDelFile', {parentData, filePath});
          }
        }
      });
    },
    deleteFolder(folderPath, projectName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_DEL_FOLDER}`, {
        projectName: projectName === undefined ? this.ideInfo.currProj.config.name : projectName,
        folderPath: folderPath,
        callback: (dict) => {
          if (dict.code == 0) {
            const parentData = self.getParentData(folderPath);
            if (parentData)
              self.$store.commit('ide/handleDelFolder', {parentData, folderPath});
          }
        }
      });
    },
    createProject(projectName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_CREATE_PROJECT}`, {
        projectName: projectName,
        callback: (dict) => {
          if (dict.code == 0) {
            self.listProjects(projectName);
          }
        }
      });
    },
    createFile(fileName, parentPath, projectName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_CREATE_FILE}`, {
        projectName: projectName === undefined ? this.ideInfo.currProj.config.name : projectName,
        parentPath: parentPath === undefined ? this.ideInfo.nodeSelected.path : parentPath,
        fileName: fileName,
        callback: (dict) => {
          if (dict.code == 0) {
            const newPath = path.join(self.ideInfo.nodeSelected.path, fileName);
            self.$store.commit('ide/addChildrenNode', {
              name: fileName,
              path: newPath,
              type: 'file'
            });
            self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
          }
        }
      });
    },
    createFolder(folderName, parentPath, projectName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_CREATE_FOLDER}`, {
        projectName: projectName === undefined ? this.ideInfo.currProj.config.name : projectName,
        parentPath: parentPath === undefined ? this.ideInfo.nodeSelected.path : parentPath,
        folderName: folderName,
        callback: (dict) => {
          if (dict.code == 0) {
            const newPath = path.join(self.ideInfo.nodeSelected.path, folderName);
            self.$store.commit('ide/addChildrenNode', {
              name: folderName,
              path: newPath,
              type: 'dir'
            });
            self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
          }
        }
      });
    },
    renameProject(newName, oldName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_RENAME_PROJECT}`, {
        oldName: oldName === undefined ? this.ideInfo.currProj.config.name : oldName,
        newName: newName,
        callback: (dict) => {
          if (dict.code == 0) {
            self.$store.commit('ide/handleRename', newName);
            self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
          }
        }
      });
    },
    renameFile(newName, oldPath, projectName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_RENAME_FILE}`, {
        projectName: projectName === undefined ? this.ideInfo.currProj.config.name : projectName,
        oldPath: oldPath === undefined ? this.ideInfo.nodeSelected.path : oldPath,
        fileName: newName,
        callback: (dict) => {
          if (dict.code == 0) {
            self.$store.commit('ide/handleRename', newName);
            self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
          }
        }
      });
    },
    renameFolder(newName, oldPath, projectName) {
      const self = this;
      this.$store.dispatch(`ide/${types.IDE_RENAME_FOLDER}`, {
        projectName: projectName === undefined ? this.ideInfo.currProj.config.name : projectName,
        oldPath: oldPath === undefined ? this.ideInfo.nodeSelected.path : oldPath,
        folderName: newName,
        callback: (dict) => {
          if (dict.code == 0) {
            self.$store.commit('ide/handleRename', newName);
            self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
          }
        }
      });
    },
    onDelete() {
      this.showDeleteDialog = false;
      if (!this.ideInfo.nodeSelected || !this.ideInfo.nodeSelected.type) {
        // delete file
        this.deleteFile(this.ideInfo.nodeSelected.path);
      }
      else {
        // Check for both 'dir' and 'folder' types
        if (this.ideInfo.nodeSelected.type === 'dir' || this.ideInfo.nodeSelected.type === 'folder') {
          // delete folder
          this.deleteFolder(this.ideInfo.nodeSelected.path);
        }
        else {
          // delete file
          this.deleteFile(this.ideInfo.nodeSelected.path);
        }
      }
    },
    onCreate() {
      const text = this.dialogText;
      if (this.dialogType === 'create-file') {
        this.createFile(text);
      }
      else if (this.dialogType === 'rename-file') {
        this.renameFile(text);
      }
      else if (this.dialogType === 'create-folder') {
        this.createFolder(text);
      }
      else if (this.dialogType === 'rename-folder') {
        this.renameFolder(text);
      }
      else if (this.dialogType === 'create-project') {
        if (this.hasRunProgram) {
          const self = this;
          ElMessageBox.confirm(
            'Stop all running programs and create new project?',
            'Warning',
            {
              confirmButtonText: 'Stop and Create',
              cancelButtonText: 'Cancel',
              type: 'warning',
            }
          )
          .then(() => {
            self.stopAll();
            self.$store.commit('ide/setConsoleItems', []);
            self.createProject(text);
          })
          .catch(() => {
            console.log('canceled create project');
          });
        }
        else {
          this.$store.commit('ide/setConsoleItems', []);
          this.createProject(text);
        }
      }
      else if (this.dialogType === 'rename-project') {
        this.renameProject(text);
      }
      this.showProjsDialog = false;
      this.showFileDialog = false;
      this.showDeleteDialog = false;
    },
    onDeleteProj(projectName) {
      const self = this;
      ElMessageBox.confirm(
        'Delete this project?',
        'Confirm',
        {
          confirmButtonText: 'Delete',
          cancelButtonText: 'Cancel',
          type: 'warning',
        }
      )
      .then(() => {
        self.deleteProject(projectName);
        ElMessage({
          type: 'success',
          message: 'Deleted successfully',
        })
      })
      .catch(() => {
        ElMessage({
          type: 'info',
          message: 'Cancelled',
        })
      });
    },
    onSelectProj(projectName) {
      if (this.hasRunProgram) {
        ElMessageBox.confirm(
          'Stop all running programs and switch project?',
          'Warning',
          {
            confirmButtonText: 'Stop and Switch',
            cancelButtonText: 'Cancel',
            type: 'warning',
          }
        )
        .then(() => {
          this.stopAll();
          this.$store.commit('ide/setConsoleItems', []);
          this.getProject(projectName);
          this.showProjsDialog = false;
        })
        .catch(() => {
          this.showProjsDialog = false;
        });
      }
      else {
        // this.$store.commit('ide/setConsoleItems', []);
        this.getProject(projectName);
        this.showProjsDialog = false;
        this.$store.commit('ide/setConsoleItems', []);
      }
    },
    selectFile(item) {
      this.$store.commit('ide/setPathSelected', item.path);
      this.$store.commit('ide/setCodeSelected', item);
      if (this.ideInfo.currProj.pathSelected) {
        this.ideInfo.treeRef.setCurrentKey(this.ideInfo.currProj.pathSelected);
      }
      this.$store.commit('ide/setNodeSelected', this.ideInfo.treeRef.getCurrentNode());
      this.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
    },
    closeFile(item) {
      const codeItems = []
      for (let i = 0; i < this.ideInfo.codeItems.length; i++) {
        if (item.path !== this.ideInfo.codeItems[i].path) {
          codeItems.push(this.ideInfo.codeItems[i]);        
        }
        else {
          if (i > 0) {
            if (this.ideInfo.currProj.pathSelected === item.path) {
              this.$store.commit('ide/setPathSelected', this.ideInfo.codeItems[i - 1].path);
              this.$store.commit('ide/setCodeSelected', this.ideInfo.codeItems[i - 1]);
              // this.$store.commit('ide/setNodeSelected', this.ideInfo.codeItems[i - 1]);
            }
          }
          else if (i < this.ideInfo.codeItems.length - 1) {
            if (this.ideInfo.currProj.pathSelected === item.path) {
              this.$store.commit('ide/setPathSelected', this.ideInfo.codeItems[i + 1].path);
              this.$store.commit('ide/setCodeSelected', this.ideInfo.codeItems[i + 1]);
              // this.$store.commit('ide/setNodeSelected', this.ideInfo.codeItems[i + 1]);
            }
          }
        }
      }
      this.$store.commit('ide/setCodeItems', codeItems);
      if (this.ideInfo.codeItems.length === 0) {
        this.$store.commit('ide/setPathSelected', null);
        this.$store.commit('ide/setCodeSelected', {});
        // this.$store.commit('ide/setNodeSelected', null);
      }
      this.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
    },
    updateItem(path, codemirror) {
      for (let i = 0; i < this.ideInfo.codeItems.length; i++) {
        if (path === this.ideInfo.codeItems[i].path) {
          this.$store.commit('ide/setCodeItemMirror', {index: i, codemirror: codemirror});
          break;
        }
      }
    },
    selectConsole(item) {
      this.$store.commit('ide/setConsoleSelected', item);
    },
    closeConsoleSafe(item) {
      if (item.run === true) {
        ElMessageBox.confirm(
          'Stop this program and close terminal?',
          'Warning',
          {
            confirmButtonText: 'Stop and Close',
            cancelButtonText: 'Cancel',
            type: 'warning',
          }
        )
        .then(() => {
          this.stop(item.id);
          this.closeConsole(item);
        })
        .catch(() => {
          console.log('canceled close console');
        });
      }
      else {
        this.closeConsole(item);
      }
    },
    closeConsole(item) {
      const consoleItems = []
      for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
        if (item.name === 'Terminal' && item.path === 'Terminal') {
          if (item.id !== this.ideInfo.consoleItems[i].id) {
            consoleItems.push(this.ideInfo.consoleItems[i]);
          }
          else {
            if (i > 0) {
              this.$store.commit('ide/setConsoleSelected', this.ideInfo.consoleItems[i - 1]);
            }
            else if (i < this.ideInfo.consoleItems.length - 1) {
              this.$store.commit('ide/setConsoleSelected', this.ideInfo.consoleItems[i + 1]);
            }
          }
        }
        else {
          if (item.path !== this.ideInfo.consoleItems[i].path || item.id !== this.ideInfo.consoleItems[i].id) {
            consoleItems.push(this.ideInfo.consoleItems[i]);
          }
          else {
            if (i > 0) {
              this.$store.commit('ide/setConsoleSelected', this.ideInfo.consoleItems[i - 1]);
            }
            else if (i < this.ideInfo.consoleItems.length - 1) {
              this.$store.commit('ide/setConsoleSelected', this.ideInfo.consoleItems[i + 1]);
            }
          }
        }
      }
      this.$store.commit('ide/setConsoleItems', consoleItems);
      if (this.ideInfo.consoleItems.length === 0) {
        this.$store.commit('ide/setConsoleSelected', {});
      }
      this.resize();
    },
    getCurrentConsoleHeight() {
      // Method that the splitter can call to get current height
      return this.consoleHeight;
    },
    resize() {
      // No longer needed - editors now use flexbox and fill available space automatically
      // Layout is handled by CSS flexbox instead of calculated heights
    },
    runPathSelected() {
      // Auto-switch to Output tab when running programs
      this.switchToOutputTab();
      
      let selected = false;
      if (this.ideInfo.consoleSelected.run === false && this.ideInfo.consoleSelected.path === this.ideInfo.currProj.pathSelected) {
        selected = true;
        this.$store.commit('ide/assignConsoleSelected', {
          stop: false,
          resultList: []
        });
      }
      else {
        for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
          if (this.ideInfo.consoleItems[i].run === false && this.ideInfo.consoleItems[i].path === this.ideInfo.currProj.pathSelected) {
            this.$store.commit('ide/setConsoleSelected', this.ideInfo.consoleItems[i]);
            selected = true;
            this.$store.commit('ide/assignConsoleSelected', {
              stop: false,
              resultList: []
            });
            break;
          }
        }
      }
      if (selected === false) {
        // Clean up all old console items (except Terminal) to prevent duplicates
        for (let i = this.ideInfo.consoleItems.length - 1; i >= 0; i--) {
          if (this.ideInfo.consoleItems[i].run === false && !(this.ideInfo.consoleItems[i].name === 'Terminal' && this.ideInfo.consoleItems[i].path === 'Terminal')) {
            this.$store.commit('ide/spliceConsoleItems', {start: i, count: 1});
          }
        }
        const item = {
          name: path.basename(this.ideInfo.currProj.pathSelected),
          path: this.ideInfo.currProj.pathSelected,
          resultList: [],
          run: false,
          stop: false,
          id: this.ideInfo.consoleId,
          waitingForInput: false,
          inputPrompt: ''
        }
        this.$store.commit('ide/addConsoleItem', item);
        this.$store.commit('ide/setConsoleSelected', item);
      }
      else {
        this.$store.commit('ide/assignConsoleSelected', {
          id: this.ideInfo.consoleId
        });
      }

      // Remove duplicate console item creation - this was causing multiple input fields
      this.$store.dispatch(`ide/${types.IDE_RUN_PYTHON_PROGRAM}`, {
        msgId: this.ideInfo.consoleId,
        filePath: this.ideInfo.currProj.pathSelected,
        callback: {
          limits: -1,
          callback: (dict) => {
            this.$store.commit('ide/handleRunResult', dict);
          }
        }
      });
      this.$store.commit('ide/setConsoleId', this.ideInfo.consoleId + 1);
    },
    runConsoleSelected() {
      // Auto-switch to Output tab when running programs
      this.switchToOutputTab();
      
      this.$store.dispatch(`ide/${types.IDE_RUN_PYTHON_PROGRAM}`, {
        msgId: this.ideInfo.consoleSelected.id,
        filePath: this.ideInfo.consoleSelected.path,
        callback: {
          limits: -1,
          callback: (dict) => {
            this.$store.commit('ide/handleRunResult', dict);
          }
        }
      });
    },
    stop(consoleId) {
      this.$store.dispatch(`ide/${types.IDE_STOP_PYTHON_PROGRAM}`, {
        consoleId: consoleId,
        callback: {
          limits: -1,
          callback: (dict) => {
            this.$store.commit('ide/handleStopResult', {
              consoleId: consoleId,
              dict: dict
            });
          }
        }
      });
    },
    stopAll() {
      for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
        if (this.ideInfo.consoleItems[i].run === true) {
          this.stop(this.ideInfo.consoleItems[i].id);
        }
      }
      this.stop(null);
    },
    
    // Split layout resizing methods
    startResize(event) {
      this.isResizing = true;
      this.startX = event.clientX;
      
      // Get current console width in pixels
      const rightFrame = document.getElementById('right-frame');
      const consolePanel = rightFrame.querySelector('.console-panel');
      this.startConsoleWidth = consolePanel.offsetWidth;
      
      // Add event listeners
      document.addEventListener('mousemove', this.handleResize);
      document.addEventListener('mouseup', this.stopResize);
      
      // Prevent text selection during resize
      event.preventDefault();
    },
    
    handleResize(event) {
      if (!this.isResizing) return;
      
      const deltaX = this.startX - event.clientX; // Negative when moving left
      const rightFrame = document.getElementById('right-frame');
      const rightFrameWidth = rightFrame.offsetWidth;
      
      // Calculate new console width
      let newConsoleWidth = this.startConsoleWidth + deltaX;
      
      // Apply constraints
      const minWidth = this.minConsoleWidth;
      const maxWidth = (rightFrameWidth * this.maxConsoleWidth) / 100;
      
      newConsoleWidth = Math.max(minWidth, Math.min(maxWidth, newConsoleWidth));
      
      // Update widths
      const consolePercentage = (newConsoleWidth / rightFrameWidth) * 100;
      const editorPercentage = 100 - consolePercentage;
      
      this.consoleWidth = `${consolePercentage}%`;
      this.editorWidth = `${editorPercentage}%`;
    },
    
    stopResize() {
      this.isResizing = false;
      
      // Remove event listeners
      document.removeEventListener('mousemove', this.handleResize);
      document.removeEventListener('mouseup', this.stopResize);
      
      // Save user preference (could be stored in localStorage later)
      this.saveLayoutPreferences();
    },
    
    saveLayoutPreferences() {
      // Store layout preferences in localStorage
      const preferences = {
        consoleWidth: this.consoleWidth,
        editorWidth: this.editorWidth
      };
      localStorage.setItem('ide-layout-preferences', JSON.stringify(preferences));
    },
    
    loadLayoutPreferences() {
      // Load layout preferences from localStorage
      const stored = localStorage.getItem('ide-layout-preferences');
      if (stored) {
        try {
          const preferences = JSON.parse(stored);
          this.consoleWidth = preferences.consoleWidth || '0%';
          this.editorWidth = preferences.editorWidth || '100%';
        } catch (e) {
          console.warn('Failed to load layout preferences:', e);
        }
      }
    },
    
    // Handle input from UnifiedConsole for running programs
    handleProgramInput(data) {
      this.$store.dispatch(`ide/${types.IDE_SEND_PROGRAM_INPUT}`, {
        program_id: data.programId,
        input: data.input,
        callback: {
          limits: -1,
          callback: (dict) => {
            // Handle response if needed
            console.log('Input sent:', dict);
          }
        }
      });
      this.$store.commit('ide/setConsoleWaiting', {
        id: data.programId,
        waiting: false
      }); 
    },
    
    // Console tab methods
    clearTerminal() {
      this.terminalOutput = [];
      this.terminalInput = '';
      this.terminalHistory = [];
      this.terminalHistoryIndex = -1;
    },
    
    restartTerminal() {
      this.clearTerminal();
      this.terminalSessionActive = false;
      // Restart Pyodide by reinitializing it
      if (this.pyodideReady) {
        this.initializePyodide();
        this.addTerminalOutput('output', 'Python environment restarted.');
      }
    },
    
    // Pyodide Python integration methods
    async initializePyodide() {
      if (this.pyodideReady || this.pyodideLoading) return;
      
      this.pyodideLoading = true;
      this.addTerminalOutput('output', 'Initializing Python environment...');
      
      try {
        console.log('[Pyodide] Loading Python runtime...');
        
        // Check if loadPyodide is available
        if (typeof window.loadPyodide !== 'function') {
          throw new Error('Pyodide library not loaded. Please refresh the page.');
        }
        
        this.pyodide = await window.loadPyodide({
          indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
        });
        
        console.log('[Pyodide] Python runtime loaded successfully');
        this.pyodideReady = true;
        this.pyodideLoading = false;
        
        // Set up Python environment
        this.pyodide.runPython(`
import sys
print(f"Python {sys.version} on Pyodide")
print("Ready for interactive computing!")
        `);
        
        this.addTerminalOutput('output', 'Python environment ready! 🐍');
        
      } catch (error) {
        console.error('[Pyodide] Failed to load:', error);
        this.pyodideLoading = false;
        this.addTerminalOutput('error', `Failed to load Python: ${error.message}`);
      }
    },
    
    async ensurePyodideReady() {
      if (!this.pyodideReady && !this.pyodideLoading) {
        await this.initializePyodide();
      }
      
      // Wait for Pyodide to be ready
      while (this.pyodideLoading) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      return this.pyodideReady;
    },
    
    async executeTerminalCommand() {
      if (!this.terminalInput.trim()) return;
      
      const command = this.terminalInput.trim();
      
      // Add to history
      if (this.terminalHistory[this.terminalHistory.length - 1] !== command) {
        this.terminalHistory.push(command);
      }
      this.terminalHistoryIndex = -1;
      
      // Add input to display
      this.addTerminalOutput('input', command);
      
      // Handle special commands first
      if (command === 'clear' || command === 'clear()') {
        this.clearTerminal();
        this.terminalInput = '';
        return;
      }
      
      if (command === 'help' || command === 'help()') {
        this.addTerminalOutput('output', this.getHelpText());
        this.terminalInput = '';
        this.$nextTick(() => {
          this.scrollTerminalToBottom();
          this.focusTerminalInput();
        });
        return;
      }
      
      // Initialize Pyodide if not ready
      const isReady = await this.ensurePyodideReady();
      if (!isReady) {
        this.addTerminalOutput('error', 'Python environment failed to initialize');
        this.terminalInput = '';
        return;
      }
      
      // Execute Python code with Pyodide
      try {
        console.log('[Pyodide] Executing:', command);
        
        // Execute the Python code
        const result = this.pyodide.runPython(command);
        
        // Display result if it exists and is not None
        if (result !== undefined && result !== null) {
          this.addTerminalOutput('output', String(result));
        }
        
      } catch (error) {
        console.error('[Pyodide] Execution error:', error);
        // Display Python error with proper formatting
        this.addTerminalOutput('error', error.toString());
      }
      
      // Clear input and scroll to bottom
      this.terminalInput = '';
      this.$nextTick(() => {
        this.scrollTerminalToBottom();
        this.focusTerminalInput();
      });
    },
    
    addTerminalOutput(type, content) {
      this.terminalOutput.push({
        type: type,
        content: content,
        timestamp: new Date().toISOString()
      });
    },
    
    getHelpText() {
      return `🐍 Python Interactive Terminal (Powered by Pyodide)

Features:
• Full Python 3.11 environment in your browser
• All variables and imports persist across commands
• NumPy, Pandas, Matplotlib support available
• Use Up/Down arrows for command history
• Type 'clear' to clear the terminal

Try these examples:
  >>> import math
  >>> math.sqrt(16)
  >>> x = [1, 2, 3, 4, 5]
  >>> sum(x)

Advanced packages (install with micropip):
  >>> import micropip
  >>> await micropip.install("requests")`;
    },
    
    navigateHistory(direction) {
      if (this.terminalHistory.length === 0) return;
      
      if (direction === 'up') {
        if (this.terminalHistoryIndex === -1) {
          this.terminalHistoryIndex = this.terminalHistory.length - 1;
        } else if (this.terminalHistoryIndex > 0) {
          this.terminalHistoryIndex--;
        }
      } else if (direction === 'down') {
        if (this.terminalHistoryIndex === -1) return;
        if (this.terminalHistoryIndex < this.terminalHistory.length - 1) {
          this.terminalHistoryIndex++;
        } else {
          this.terminalHistoryIndex = -1;
          this.terminalInput = '';
          return;
        }
      }
      
      if (this.terminalHistoryIndex >= 0) {
        this.terminalInput = this.terminalHistory[this.terminalHistoryIndex];
      }
    },
    
    scrollTerminalToBottom() {
      if (this.$refs.terminalContent) {
        this.$refs.terminalContent.scrollTop = this.$refs.terminalContent.scrollHeight;
      }
    },
    
    focusTerminalInput() {
      if (this.$refs.terminalInputField) {
        this.$refs.terminalInputField.focus();
      }
    },
    
    // Auto-switch to output tab when running programs
    switchToOutputTab() {
      this.consoleModeTab = 'output';
    },
    
    // Switch to terminal tab and focus input
    switchToTerminalTab() {
      this.consoleModeTab = 'terminal';
      this.$nextTick(() => {
        this.focusTerminalInput();
        // Auto-initialize Pyodide when switching to terminal
        if (!this.pyodideReady && !this.pyodideLoading) {
          this.initializePyodide();
        }
      });
    },
    

  }
}
</script>
<style scoped>
/* Console Mode Tabs */
.console-mode-tabs {
  display: flex;
  background-color: var(--bg-secondary, #252526);
  border-bottom: 1px solid var(--border-color, #3E3E42);
  padding: 0;
  margin: 0;
}

.tab-button {
  background: transparent;
  border: none;
  color: var(--text-secondary, #CCCCCC);
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.tab-button:hover {
  background-color: var(--bg-hover, #2A2A2B);
  color: var(--text-primary, #FFFFFF);
}

.tab-button.active {
  color: var(--text-primary, #FFFFFF);
  border-bottom-color: var(--accent-color, #007ACC);
  background-color: var(--bg-active, #1E1E1E);
}

.tab-badge {
  background-color: var(--accent-color, #007ACC);
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 11px;
  font-weight: bold;
  min-width: 16px;
  text-align: center;
}

/* Tab Content */
.tab-content {
  height: calc(100% - 48px);
  display: flex;
  flex-direction: column;
}

.output-tab {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.output-tab .console-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.terminal-tab {
  background-color: var(--bg-primary, #1E1E1E);
}

/* Terminal Styling */
.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: var(--bg-secondary, #252526);
  border-bottom: 1px solid var(--border-color, #3E3E42);
}

.terminal-title {
  color: var(--text-secondary, #CCCCCC);
  font-size: 13px;
  font-weight: 500;
}

.terminal-actions {
  display: flex;
  gap: 8px;
}

.terminal-btn {
  background: transparent;
  border: 1px solid var(--border-color, #3E3E42);
  color: var(--text-secondary, #CCCCCC);
  padding: 4px 8px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.terminal-btn:hover {
  background-color: var(--bg-hover, #2A2A2B);
  border-color: var(--accent-color, #007ACC);
  color: var(--text-primary, #FFFFFF);
}

.terminal-content {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  overflow-x: hidden;
  font-family: 'Courier New', monospace;
  background-color: var(--bg-primary, #1E1E1E);
  width: 100%;
  box-sizing: border-box;
}

.terminal-output {
  margin-bottom: 12px;
}

.terminal-welcome {
  color: var(--text-secondary, #CCCCCC);
  margin-bottom: 16px;
  font-style: italic;
}

.terminal-welcome div {
  margin-bottom: 4px;
  font-size: 13px;
}

/* Pyodide loading states */
.pyodide-loading {
  color: var(--accent-color, #007ACC);
  text-align: center;
  padding: 20px;
}

.loading-spinner {
  font-size: 18px;
  animation: spin 1s linear infinite;
  margin-top: 8px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.pyodide-ready {
  color: var(--success-color, #4CAF50);
}

.python-features {
  color: var(--text-muted, #888888);
  font-size: 12px;
  margin-top: 8px;
}

.pyodide-not-loaded {
  color: var(--text-secondary, #CCCCCC);
  cursor: pointer;
  transition: color 0.2s ease;
}

.pyodide-not-loaded:hover {
  color: var(--accent-color, #007ACC);
}

.terminal-line {
  margin-bottom: 2px;
}

.terminal-input-line {
  display: flex;
  align-items: flex-start;
  color: var(--text-primary, #FFFFFF);
}

.terminal-output-line {
  margin-left: 20px;
  color: var(--text-secondary, #CCCCCC);
}

.terminal-output-line pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  max-width: 100%;
  box-sizing: border-box;
}

.terminal-error-line {
  margin-left: 20px;
  color: var(--error-color, #FF6B68);
}

.terminal-error-line pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  max-width: 100%;
  box-sizing: border-box;
}

.terminal-current-prompt {
  display: flex;
  align-items: center;
  margin-top: 8px;
  position: sticky;
  bottom: 0;
  background-color: var(--bg-primary, #1E1E1E);
  padding: 4px 0;
}

.prompt-symbol {
  color: var(--accent-color, #007ACC);
  font-weight: bold;
  margin-right: 8px;
  font-family: 'Courier New', monospace;
}

.input-text {
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.terminal-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary, #FFFFFF);
  font-family: 'Courier New', monospace;
  font-size: 14px;
  outline: none;
  padding: 2px 0;
}

.terminal-input::placeholder {
  color: var(--text-muted, #6A6A6A);
}

/* Existing IDE styles */
.ide-wrapper {
  text-align: left;
  background-color: var(--bg-primary, #1E1E1E);
  color: var(--text-primary, #CCCCCC);
  transition: background-color 0.3s ease, color 0.3s ease;
  width: 100%;
  height: 100vh;
  position: relative;
  overflow: hidden;
}
a {
  color: white;
}
.total-frame {
  /*background-color:gray;*/
  position: fixed;
  width: 100%;
  height: calc(100% - 50px); /* Subtract header height */
  top: 50px;
  /* top: 76px; */
  left: 0;
  z-index: 1; /* Below header */
  /* display: inline-flex; */
  /* left: 10px; */
  /* border:1px solid #96c2f1; */
  /* background:yellow; */
  /*top: 200px;
  left: 100px;*/
}
body {
  scrollbar-track-color: #3C3F41;
}
.top-menu {
  position: fixed;
  width: 100%;
  height: 50px;
  top: 0;
  /* top: 40px; */
  left: 0;
  background: #313131;
  /* background: #252526; */
  display: flex;
  align-items: center;
  z-index: 9999; /* Ensure header stays on top of everything */
}
.top-tab {
  width: 100%;
  /* background: #313335; */
  /* background-color: yellow; */
  background: var(--bg-secondary, #252526);
}
.left-frame {
  /* width:200px; */
  width: 200px;
  height: calc(100% - 31px);
  overflow-y: auto;
  overflow-x: auto;
  /* background: #2E3032; */
  /* background: #383B3D; */
  background: var(--bg-sidebar, #282828);
  color: var(--text-primary, #CCCCCC);
  /* scrollbar-track-color: #3C3F41; */
  /* SCROLLBAR-TRACK-COLOR: aquamarine; */
}
.left-frame::-webkit-scrollbar {/*scrollbar overall style*/
  width: 6px;     /*height and width correspond to horizontal and vertical scrollbar dimensions*/
  height: 6px;
}
.left-frame::-webkit-scrollbar-thumb {/*small block inside scrollbar*/
  background: #87939A;
}
.left-frame::-webkit-scrollbar-track {/*track inside scrollbar*/
  background: #2F2F2F;
}
.right-frame {
  position: absolute;
  left: 200px;
  right: 0px;
  height: 100%;
  display: flex;
  background: var(--bg-primary, #1E1E1E);
  overflow: hidden;
}

/* Editor Panel */
.editor-panel {
  display: flex;
  flex-direction: column;
  min-width: 400px;
  background: var(--bg-primary, #1E1E1E);
  border-right: 1px solid var(--border-primary, #3c3c3c);
}

.editor-tab-bar {
  height: 35px;
  background: var(--bg-secondary, #252526);
  border-bottom: 1px solid var(--border-primary, #3c3c3c);
  display: flex;
  align-items: center;
}

.editor-content {
  flex: 1;
  overflow: hidden;
  background: var(--bg-primary, #1E1E1E);
}

/* Panel Splitter */
.panel-splitter {
  width: 4px;
  background: var(--border-primary, #3c3c3c);
  cursor: col-resize;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease;
}

.panel-splitter:hover {
  background: var(--accent-color, #007acc);
}

.panel-splitter.resizing {
  background: var(--accent-color, #007acc);
}

.splitter-handle {
  width: 2px;
  height: 30px;
  background: var(--text-secondary, #858585);
  border-radius: 1px;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.panel-splitter:hover .splitter-handle,
.panel-splitter.resizing .splitter-handle {
  opacity: 1;
}

/* Console Toggle Button */
.console-toggle-btn {
  position: absolute;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  width: 20px;
  height: 60px;
  background: var(--accent-color, #007acc);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  border-radius: 4px 0 0 4px;
  z-index: 15;
  transition: background-color 0.2s ease;
}

.console-toggle-btn:hover {
  background: #1a8cff;
}

/* Console Panel */
.console-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 400px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary, #1E1E1E);
  border-left: 1px solid var(--border-primary, #3c3c3c);
  z-index: 10;
}

.console-tab-bar {
  height: 35px;
  background: var(--bg-secondary, #252526);
  border-bottom: 1px solid var(--border-primary, #3c3c3c);
  display: flex;
  align-items: center;
}

.console-content {
  flex: 1;
  overflow: hidden;
  background: var(--bg-primary, #1E1E1E);
}

/* Responsive Design */
@media (max-width: 1200px) {
  .right-frame {
    flex-direction: column;
  }
  
  .editor-panel {
    width: 100% !important;
    height: 60%;
    min-width: auto;
    border-right: none;
    border-bottom: 1px solid var(--border-primary, #3c3c3c);
  }
  
  .panel-splitter {
    width: 100%;
    height: 4px;
    cursor: row-resize;
  }
  
  .splitter-handle {
    width: 30px;
    height: 2px;
  }
  
  .console-toggle-btn {
    top: 60%;
    right: 0;
    width: 60px;
    height: 20px;
    border-radius: 4px 0 0 0;
  }
  
  .console-panel {
    position: absolute;
    top: 60%;
    left: 0;
    right: 0;
    width: 100% !important;
    height: 40%;
    min-width: auto;
    border-left: none;
    border-top: 1px solid var(--border-primary, #3c3c3c);
  }
}

/* Legacy styles for backward compatibility */
.run-icon {
  margin-right: 20px;
  margin-top: -5px;
  width: 16px;
  height: 16px;
  background-image: url('./../../assets/img/ide/icon_running.svg');
  cursor: pointer;
}

.stop-icon {
  margin-right: 20px;
  margin-top: 5px;
  width: 16px;
  height: 16px;
  background-image: url('./../../assets/img/ide/icon_stop.svg');
  cursor: pointer;
}
</style>
