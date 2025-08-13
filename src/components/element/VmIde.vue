<template>
  <div class="main-wrapper ide-wrapper ide-container">
    <TopMenu class="top-menu"
      :consoleLimit="consoleLimit"
      :hasRunProgram="hasRunProgram"
      :wordWrap="wordWrap"
      @set-text-dialog="setTextDialog"
      @set-del-dialog="setDelDialog"
      @set-projs-dialog="setProjsDialog"
      v-on:run-item="runPathSelected"
      @stop-item="stop"
      @theme-changed="handleThemeChange"
      @toggle-word-wrap="toggleWordWrap"
      @open-upload-dialog="showUploadDialog = true"
      @download-file="downloadFile"
    ></TopMenu>
    <div id="total-frame" class="total-frame">
      <!-- Left Sidebar with File Tree (Draggable) -->
      <div id="left-sidebar" class="left-sidebar" :style="{ width: leftSidebarWidth + 'px' }">
        <ProjTree 
          v-on:get-item="getFile"
          @context-menu="showContextMenu"
        ></ProjTree>
      </div>
      
      <!-- Left Sidebar Resizer -->
      <div class="sidebar-resizer left" 
           @mousedown="startResizeLeft" 
           :class="{ 'resizing': isResizingLeft, 'at-limit': resizeWarning && isResizingLeft }"
           :style="{ left: leftSidebarWidth + 'px' }">
        <div class="resizer-handle"></div>
      </div>
      
      <!-- Center Content Area -->
      <div id="center-frame" class="center-frame" :style="{ left: leftSidebarWidth + 5 + 'px', right: (rightSidebarVisible && previewTabs.length > 0) ? rightSidebarWidth + 5 + 'px' : '0' }">
        <!-- Editor Section -->
        <div class="editor-section" :style="{ height: editorHeight }">
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
                :wordWrap="wordWrap"
                @run-item="runPathSelected"
                v-if="ideInfo.codeSelected.path === item.path" 
                v-on:update-item="updateItem"></IdeEditor>
            </template>
          </div>
        </div>

        <!-- Console Section Below Editor -->
        <div class="console-section" :class="{ 'collapsed': !consoleExpanded }" :style="{ height: consoleExpanded ? consoleHeight + 'px' : '35px' }">
          <!-- Console Resize Handle -->
          <div class="console-resizer" 
               @mousedown="startResizeConsole"
               :class="{ 'resizing': isResizingConsole }">
            <div class="resizer-handle horizontal"></div>
          </div>
          
          <!-- Console Header with Collapse/Expand Button -->
          <div class="console-header" @click="toggleConsoleExpand">
            <div class="console-header-left">
              <span class="collapse-icon" :class="{ 'collapsed': !consoleExpanded }">▼</span>
              <span class="console-title">Console</span>
              <span v-if="ideInfo.consoleItems.length > 0" class="console-count">({{ ideInfo.consoleItems.length }})</span>
            </div>
            <div class="console-header-right" v-if="consoleExpanded">
              <button class="console-action-btn" @click.stop="clearConsole" title="Clear Console">
                <span>Clear</span>
              </button>
            </div>
          </div>
          
          <!-- Console Content (Only visible when expanded) -->
          <div v-show="consoleExpanded" class="console-body">
            <!-- Console Output Area -->
            <div class="console-output-area" ref="consoleOutputArea">
              <template v-if="ideInfo.consoleSelected && ideInfo.consoleSelected.resultList">
                <div v-for="(result, index) in ideInfo.consoleSelected.resultList" :key="index" class="console-line">
                  <!-- Regular output -->
                  <pre v-if="result.type === 'output' || result.type === 'text'" class="console-text">{{ result.text || result.content || result }}</pre>
                  
                  <!-- Error output -->
                  <pre v-else-if="result.type === 'error'" class="console-error">{{ result.text || result.content || result }}</pre>
                  
                  <!-- Input prompt -->
                  <div v-else-if="result.type === 'input' || result.type === 'input-prompt'" class="console-input-prompt">
                    <span class="prompt-arrow">▶</span>
                    <span>{{ result.text || result.content || result }}</span>
                  </div>
                  
                  <!-- System message -->
                  <pre v-else-if="result.type === 'system'" class="console-system">{{ result.text || result.content || result }}</pre>
                  
                  <!-- Default fallback -->
                  <pre v-else class="console-text">{{ typeof result === 'object' ? (result.text || result.content || JSON.stringify(result)) : result }}</pre>
                </div>
              </template>
              
              <!-- Input field when waiting for input -->
              <div v-if="ideInfo.consoleSelected && ideInfo.consoleSelected.waitingForInput" class="console-input-area">
                <div class="input-prompt">
                  <span class="prompt-icon">💬</span>
                  <span>{{ ideInfo.consoleSelected.inputPrompt || 'Enter input:' }}</span>
                </div>
                <div class="input-field-container">
                  <input
                    v-model="programInput"
                    @keyup.enter="sendProgramInput"
                    ref="programInputField"
                    class="program-input-field"
                    placeholder="Type your input and press Enter..."
                    autofocus
                  />
                  <button @click="sendProgramInput" class="input-submit-btn">Send</button>
                </div>
              </div>
            </div>
            
            <!-- REPL Input Area (like p5.js) -->
            <div class="repl-section">
              <div class="repl-prompt">
                <span class="prompt-symbol">>>> </span>
                <input 
                  type="text" 
                  class="repl-input"
                  placeholder="Enter Python code..."
                  v-model="replInput"
                  @keyup.enter="executeReplCommand"
                  @keyup.up="navigateReplHistory('up')"
                  @keyup.down="navigateReplHistory('down')"
                  ref="replInputField">
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Show Preview Button (when hidden but has content) -->
      <div v-if="!rightSidebarVisible && previewTabs.length > 0" 
           class="show-preview-btn" 
           @click="rightSidebarVisible = true"
           title="Show Preview Panel">
        <span class="tab-count">{{ previewTabs.length }}</span>
        <span>◀</span>
      </div>
      
      <!-- Right Sidebar Resizer -->
      <div v-if="rightSidebarVisible && previewTabs.length > 0" 
           class="sidebar-resizer right" 
           @mousedown="startResizeRight" 
           :class="{ 'resizing': isResizingRight, 'at-limit': resizeWarning && isResizingRight }"
           :style="{ right: rightSidebarWidth + 'px' }">
        <div class="resizer-handle"></div>
      </div>
      
      <!-- Right Sidebar for Preview/Output (Draggable) -->
      <div v-if="rightSidebarVisible && previewTabs.length > 0" 
           id="right-sidebar" 
           class="right-sidebar" 
           :style="{ width: rightSidebarWidth + 'px' }">
        
        <!-- Preview/Output Tabs -->
        <div class="preview-tabs">
          <div class="preview-tab-list">
            <button 
              v-for="tab in previewTabs" 
              :key="tab.id"
              :class="['preview-tab', { 'active': selectedPreviewTab === tab.id }]"
              @click="selectPreviewTab(tab.id)">
              <span class="tab-icon">{{ getTabIcon(tab.type) }}</span>
              <span class="tab-title">{{ tab.title }}</span>
              <span class="tab-close" @click.stop="closePreviewTab(tab.id)">×</span>
            </button>
          </div>
          <button class="preview-tab-add" @click="toggleRightSidebar" title="Hide Preview Panel">
            ×
          </button>
        </div>
        
        <!-- Preview Content Area -->
        <div class="preview-content">
          <template v-for="tab in previewTabs" :key="tab.id">
            <div v-show="selectedPreviewTab === tab.id" class="preview-panel">
              <!-- Output Panel -->
              <div v-if="tab.type === 'output'" class="output-panel">
                <div class="output-content">
                  <div v-for="(line, idx) in tab.content" :key="idx" 
                       :class="['output-line', line.type]">
                    <pre>{{ line.text }}</pre>
                  </div>
                </div>
              </div>
              
              <!-- Image Preview Panel -->
              <div v-else-if="tab.type === 'image'" class="image-preview-panel">
                <img :src="tab.content" :alt="tab.title" />
              </div>
              
              <!-- PDF Preview Panel -->
              <div v-else-if="tab.type === 'pdf'" class="pdf-preview-panel">
                <iframe :src="tab.content" frameborder="0"></iframe>
              </div>
              
              <!-- CSV/Data Preview Panel -->
              <div v-else-if="tab.type === 'data'" class="data-preview-panel">
                <CsvViewer :content="tab.content" />
              </div>
            </div>
          </template>
        </div>
      </div>
      
      <!-- Dialogs moved outside of total-frame -->
    </div>
    <!-- Dialogs -->
    <DialogProjs v-if="showProjsDialog"
      @on-cancel="onCloseProjsDialog" @on-select="onSelectProj" @on-delete="onDeleteProj" 
      @set-text-dialog="setTextDialog"></DialogProjs>
    <DialogText v-if="showFileDialog" :title="dialogTitle" :text="dialogText" :tips="dialogTips" @check-input="inputIsLegal"
      @on-cancel="onCloseTextDialog" @on-create="onCreate"></DialogText>
    <DialogDelete v-if="showDeleteDialog" :title="dialogTitle"
      @on-cancel="onCancelDelete" @on-delete="onDelete"></DialogDelete>
    <DialogUpload v-if="showUploadDialog" v-model="showUploadDialog" @refresh-tree="refreshProjectTree" @close="showUploadDialog = false"></DialogUpload>
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
import CsvViewer from './pages/ide/CsvViewer';
const path = require('path');

export default {
  data() {
    return {
      showDeleteDialog: false,
      showFileDialog: false,
      showProjsDialog: false,
      showUploadDialog: false,
      showCover: true,
      showContextMenu: false,
      contextMenuPosition: { x: 0, y: 0 },
      contextMenuTarget: null,
      
      dialogType: '',
      dialogTitle: '',
      dialogTips: '',
      dialogText: '',
      
      // Layout properties
      leftSidebarWidth: 250,
      rightSidebarWidth: 400,
      rightSidebarVisible: false, // Hidden by default until needed
      consoleHeight: 200,
      consoleExpanded: true,
      editorHeight: 'calc(100% - 235px)', // Adjust based on console height
      minEditorWidth: 500, // Minimum width for the code editor area
      
      // Resize states
      isResizingLeft: false,
      isResizingRight: false,
      isResizingConsole: false,
      startX: 0,
      startY: 0,
      startWidth: 0,
      startHeight: 0,
      resizeWarning: false, // Show warning when approaching limits
      
      // Program input
      programInput: '',
      
      // Word wrap
      wordWrap: true, // Enabled by default
      
      // Console/REPL
      replInput: '',
      replHistory: [],
      replHistoryIndex: -1,
      
      // Preview tabs
      previewTabs: [], // Start with no tabs
      selectedPreviewTab: null,
      previewTabCounter: 0,
      
      // Terminal (moved to REPL)
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
    CsvViewer,
  },
  created() {
  },
  mounted() {
    if (!this.wsInfo.rws) {
      this.$store.dispatch('websocket/init', {});
    }
    
    // Load user layout preferences
    this.loadLayoutPreferences();
    
    // Add window resize listener to validate layout
    window.addEventListener('resize', this.validateLayout);
    
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
  },
  
  beforeUnmount() {
    window.removeEventListener('resize', this.validateLayout);
    window.removeEventListener('resize', this.resize);
    
    // Clean up blob URLs when component is destroyed
    this.previewTabs.forEach(tab => {
      if (tab.type === 'pdf' && tab.content && tab.content.startsWith('blob:')) {
        URL.revokeObjectURL(tab.content);
      }
    });
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
  watch: {
    'ideInfo.consoleSelected.waitingForInput': function(newVal) {
      if (newVal) {
        // Focus on input field when waiting for input
        this.$nextTick(() => {
          if (this.$refs.programInputField) {
            this.$refs.programInputField.focus();
          }
        });
      }
    },
    consoleExpanded(newVal) {
      if (newVal) {
        // Scroll to bottom when console is expanded
        this.$nextTick(() => {
          if (this.$refs.consoleOutputArea) {
            this.$refs.consoleOutputArea.scrollTop = this.$refs.consoleOutputArea.scrollHeight;
          }
        });
      }
    }
  },
  methods: {
    toggleConsoleExpand() {
      this.consoleExpanded = !this.consoleExpanded;
      // Update editor height when console is toggled
      this.updateEditorHeight();
      
      // Save preference
      localStorage.setItem('console-expanded', this.consoleExpanded);
    },
    
    updateEditorHeight() {
      if (this.consoleExpanded) {
        // Ensure console doesn't take too much space
        const maxConsoleHeight = window.innerHeight - 300; // Min editor height
        const actualConsoleHeight = Math.min(this.consoleHeight, maxConsoleHeight);
        this.editorHeight = `calc(100% - ${actualConsoleHeight + 35}px)`;
      } else {
        this.editorHeight = 'calc(100% - 35px)';
      }
    },
    
    clearConsole() {
      // Clear current console output
      const currentConsole = this.ideInfo.consoleSelected;
      if (currentConsole && currentConsole.resultList) {
        this.$store.commit('ide/clearConsoleOutput', currentConsole.id);
      }
      
      // Also clear program input
      this.programInput = '';
    },
    
    toggleWordWrap() {
      this.wordWrap = !this.wordWrap;
      localStorage.setItem('word-wrap', this.wordWrap);
      // The change will be picked up by the CodeEditor component
    },
    
    toggleRightSidebar() {
      // Only allow toggling if there are tabs to show
      if (this.previewTabs.length > 0 || this.rightSidebarVisible) {
        this.rightSidebarVisible = !this.rightSidebarVisible;
        localStorage.setItem('right-sidebar-visible', this.rightSidebarVisible);
      }
    },
    
    selectPreviewTab(tabId) {
      this.selectedPreviewTab = tabId;
    },
    
    closePreviewTab(tabId) {
      const index = this.previewTabs.findIndex(t => t.id === tabId);
      if (index > -1) {
        const tab = this.previewTabs[index];
        
        // Clean up blob URL if it's a PDF
        if (tab.type === 'pdf' && tab.content && tab.content.startsWith('blob:')) {
          URL.revokeObjectURL(tab.content);
        }
        
        this.previewTabs.splice(index, 1);
        
        // If this was the selected tab, select another one or null
        if (this.selectedPreviewTab === tabId) {
          this.selectedPreviewTab = this.previewTabs.length > 0 ? this.previewTabs[0].id : null;
        }
        
        // Hide sidebar if no tabs left
        if (this.previewTabs.length === 0) {
          this.rightSidebarVisible = false;
        }
      }
    },
    
    addPreviewTab(type, title, content, filePath) {
      // Check if tab already exists for this file
      const existingTab = this.previewTabs.find(tab => tab.filePath === filePath);
      
      if (existingTab) {
        // Tab already exists, just switch to it
        this.selectedPreviewTab = existingTab.id;
        
        // Update content if it has changed
        if (existingTab.content !== content) {
          // Clean up old blob URL if it exists
          if (existingTab.type === 'pdf' && existingTab.content.startsWith('blob:')) {
            URL.revokeObjectURL(existingTab.content);
          }
          existingTab.content = content;
        }
      } else {
        // Create new tab
        const id = `${type}-${++this.previewTabCounter}`;
        this.previewTabs.push({ id, type, title, content, filePath });
        this.selectedPreviewTab = id;
      }
      
      // Make sure right sidebar is visible
      if (!this.rightSidebarVisible) {
        this.rightSidebarVisible = true;
      }
    },
    
    getTabIcon(type) {
      const icons = {
        'output': '📄',
        'image': '🖼️',
        'pdf': '📑',
        'data': '📊'
      };
      return icons[type] || '📄';
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
        // For media files, fetch binary content and display in preview panel
        const fileName = path.split('/').pop();
        const fileExt = path.toLowerCase().split('.').pop();
        
        // Use the same approach as the working MediaViewer component
        this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
          projectName: this.ideInfo.currProj?.data?.name,
          filePath: path,
          binary: true,
          callback: (response) => {
            console.log('Media file response:', {
              code: response.code,
              hasData: !!response.data,
              dataContent: response.data?.content ? 'present' : 'missing',
              contentLength: response.data?.content ? response.data.content.length : 0
            });
            
            if (response.code === 0 && response.data) {
              // Handle binary data - following MediaViewer's approach
              let base64Content = response.data.content || response.data;
              
              // Check if we have content
              if (base64Content && base64Content.length > 0) {
                let previewContent;
                let previewType;
                
                // Get MIME type
                const mimeTypes = {
                  'png': 'image/png',
                  'jpg': 'image/jpeg',
                  'jpeg': 'image/jpeg',
                  'gif': 'image/gif',
                  'bmp': 'image/bmp',
                  'svg': 'image/svg+xml',
                  'webp': 'image/webp',
                  'pdf': 'application/pdf'
                };
                const mimeType = mimeTypes[fileExt] || 'application/octet-stream';
                
                // Create data URL directly (like MediaViewer does)
                previewContent = `data:${mimeType};base64,${base64Content}`;
                previewType = fileExt === 'pdf' ? 'pdf' : 'image';
                
                // Add to preview tabs with file path for duplicate detection
                self.addPreviewTab(previewType, fileName, previewContent, path);
                
                // Make sure right sidebar is visible
                if (!self.rightSidebarVisible) {
                  self.rightSidebarVisible = true;
                }
                
                // Still update the file tree selection
                if (save !== false) {
                  self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
                }
              } else {
                // No content received
                console.error('No content in response data');
                ElMessage({
                  type: 'error',
                  message: `Failed to load ${fileName}: No content received`,
                  duration: 3000
                });
              }
            } else {
              console.error('Failed to get media file:', path, response);
              ElMessage({
                type: 'error',
                message: `Failed to load ${fileName}`,
                duration: 3000
              });
            }
          }
        });
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
                isMedia: false,
                projectName: self.ideInfo.currProj?.data?.name
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
      // Return a default value since consoleHeight is no longer used
      return 400;
    },
    resize() {
      // No longer needed - editors now use flexbox and fill available space automatically
      // Layout is handled by CSS flexbox instead of calculated heights
    },
    runPathSelected() {
      // Ensure console is expanded when running
      if (!this.consoleExpanded) {
        this.consoleExpanded = true;
        this.updateEditorHeight();
      }
      
      // Don't create output tab in right panel anymore - console is sufficient
      
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
        // Clean up all old console items to prevent duplicates
        for (let i = this.ideInfo.consoleItems.length - 1; i >= 0; i--) {
          if (this.ideInfo.consoleItems[i].run === false) {
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
    
    // Sidebar resizing methods
    startResizeLeft(event) {
      this.isResizingLeft = true;
      this.startX = event.clientX;
      this.startWidth = this.leftSidebarWidth;
      
      document.addEventListener('mousemove', this.handleResizeLeft);
      document.addEventListener('mouseup', this.stopResizeLeft);
      event.preventDefault();
    },
    
    handleResizeLeft(event) {
      if (!this.isResizingLeft) return;
      
      const deltaX = event.clientX - this.startX;
      const windowWidth = window.innerWidth;
      const rightPanelWidth = this.rightSidebarVisible ? this.rightSidebarWidth : 0;
      const maxLeftWidth = windowWidth - rightPanelWidth - this.minEditorWidth - 10; // 10px for resizers
      
      // Calculate new width
      let newWidth = this.startWidth + deltaX;
      
      // Check if approaching limits
      this.resizeWarning = newWidth < 160 || newWidth > maxLeftWidth - 10;
      
      // Constrain left sidebar width
      newWidth = Math.max(150, Math.min(Math.min(500, maxLeftWidth), newWidth));
      this.leftSidebarWidth = newWidth;
    },
    
    stopResizeLeft() {
      this.isResizingLeft = false;
      this.resizeWarning = false;
      document.removeEventListener('mousemove', this.handleResizeLeft);
      document.removeEventListener('mouseup', this.stopResizeLeft);
      this.validateLayout();
      this.saveLayoutPreferences();
    },
    
    startResizeRight(event) {
      this.isResizingRight = true;
      this.startX = event.clientX;
      this.startWidth = this.rightSidebarWidth;
      
      document.addEventListener('mousemove', this.handleResizeRight);
      document.addEventListener('mouseup', this.stopResizeRight);
      event.preventDefault();
    },
    
    handleResizeRight(event) {
      if (!this.isResizingRight) return;
      
      const deltaX = this.startX - event.clientX; // Inverted for right sidebar
      const windowWidth = window.innerWidth;
      const maxRightWidth = windowWidth - this.leftSidebarWidth - this.minEditorWidth - 10; // 10px for resizers
      
      // Calculate new width
      let newWidth = this.startWidth + deltaX;
      
      // Check if approaching limits
      this.resizeWarning = newWidth < 310 || newWidth > maxRightWidth - 10;
      
      // Constrain right sidebar width (removed 600px hard limit for better PDF viewing)
      newWidth = Math.max(300, Math.min(maxRightWidth, newWidth));
      this.rightSidebarWidth = newWidth;
    },
    
    stopResizeRight() {
      this.isResizingRight = false;
      this.resizeWarning = false;
      document.removeEventListener('mousemove', this.handleResizeRight);
      document.removeEventListener('mouseup', this.stopResizeRight);
      this.validateLayout();
      this.saveLayoutPreferences();
    },
    
    // Console resizing methods
    startResizeConsole(event) {
      this.isResizingConsole = true;
      this.startY = event.clientY;
      this.startHeight = this.consoleHeight;
      
      document.addEventListener('mousemove', this.handleResizeConsole);
      document.addEventListener('mouseup', this.stopResizeConsole);
      event.preventDefault();
    },
    
    handleResizeConsole(event) {
      if (!this.isResizingConsole) return;
      
      const deltaY = this.startY - event.clientY; // Negative when dragging down
      const windowHeight = window.innerHeight;
      const maxConsoleHeight = windowHeight - 200; // Leave space for editor
      
      // Calculate new height
      let newHeight = this.startHeight + deltaY;
      
      // Constrain console height
      newHeight = Math.max(100, Math.min(maxConsoleHeight, newHeight));
      this.consoleHeight = newHeight;
      
      // Update editor height
      this.updateEditorHeight();
    },
    
    stopResizeConsole() {
      this.isResizingConsole = false;
      
      // Remove event listeners using stored handlers
      if (this._consoleMoveHandler) {
        document.removeEventListener('mousemove', this._consoleMoveHandler);
        this._consoleMoveHandler = null;
      }
      if (this._consoleUpHandler) {
        document.removeEventListener('mouseup', this._consoleUpHandler);
        this._consoleUpHandler = null;
      }
      
      // Final update to ensure proper height
      this.updateEditorHeight();
      this.saveLayoutPreferences();
    },
    
    saveLayoutPreferences() {
      // Store layout preferences in localStorage
      const preferences = {
        leftSidebarWidth: this.leftSidebarWidth,
        rightSidebarWidth: this.rightSidebarWidth,
        rightSidebarVisible: this.rightSidebarVisible,
        consoleHeight: this.consoleHeight,
        consoleExpanded: this.consoleExpanded,
        wordWrap: this.wordWrap
      };
      localStorage.setItem('ide-layout-preferences', JSON.stringify(preferences));
    },
    
    loadLayoutPreferences() {
      // Load layout preferences from localStorage
      const stored = localStorage.getItem('ide-layout-preferences');
      if (stored) {
        try {
          const preferences = JSON.parse(stored);
          this.leftSidebarWidth = preferences.leftSidebarWidth || 250;
          this.rightSidebarWidth = preferences.rightSidebarWidth || 400;
          this.rightSidebarVisible = preferences.rightSidebarVisible === true;
          this.consoleHeight = preferences.consoleHeight || 200;
          this.consoleExpanded = preferences.consoleExpanded !== false;
          this.wordWrap = preferences.wordWrap !== false;
        } catch (e) {
          console.warn('Failed to load layout preferences:', e);
        }
      }
      this.validateLayout();
      this.updateEditorHeight();
    },
    
    validateLayout() {
      // Ensure layout doesn't violate minimum editor width
      const windowWidth = window.innerWidth;
      
      // Don't validate on very small screens
      if (windowWidth < 900) {
        return;
      }
      
      const totalSidebars = this.leftSidebarWidth + (this.rightSidebarVisible ? this.rightSidebarWidth : 0);
      const availableForEditor = windowWidth - totalSidebars - 10; // 10px for resizers
      
      if (availableForEditor < this.minEditorWidth) {
        // Adjust sidebars proportionally to maintain minimum editor width
        const excess = this.minEditorWidth - availableForEditor;
        
        if (this.rightSidebarVisible) {
          // Distribute excess between both sidebars
          const leftRatio = this.leftSidebarWidth / (this.leftSidebarWidth + this.rightSidebarWidth);
          const rightRatio = 1 - leftRatio;
          
          const leftReduction = Math.min(this.leftSidebarWidth - 150, excess * leftRatio);
          const rightReduction = Math.min(this.rightSidebarWidth - 300, excess * rightRatio);
          
          // Apply reductions
          this.leftSidebarWidth = Math.max(150, this.leftSidebarWidth - leftReduction);
          this.rightSidebarWidth = Math.max(300, this.rightSidebarWidth - rightReduction);
          
          // If still not enough space, hide right sidebar
          const newTotal = this.leftSidebarWidth + this.rightSidebarWidth;
          if (windowWidth - newTotal - 10 < this.minEditorWidth) {
            this.rightSidebarVisible = false;
          }
        } else {
          // Only adjust left sidebar
          this.leftSidebarWidth = Math.max(150, Math.min(this.leftSidebarWidth, windowWidth - this.minEditorWidth - 10));
        }
      }
    },
    
    // Send input for running programs
    sendProgramInput() {
      if (!this.programInput.trim()) return;
      
      const input = this.programInput;
      const programId = this.ideInfo.consoleSelected.id;
      
      // Add input to console output
      this.$store.commit('ide/addConsoleOutput', {
        id: programId,
        type: 'input',
        text: `▶ ${input}`
      });
      
      // Clear input field
      this.programInput = '';
      
      // Clear waiting state
      this.$store.commit('ide/setConsoleWaiting', {
        id: programId,
        waiting: false,
        prompt: ''
      });
      
      // Send to backend
      this.$store.dispatch(`ide/${types.IDE_SEND_PROGRAM_INPUT}`, {
        program_id: programId,
        input: input,
        callback: {
          limits: -1,
          callback: (dict) => {
            console.log('Input sent:', dict);
          }
        }
      });
      
      // Scroll to bottom
      this.$nextTick(() => {
        if (this.$refs.consoleOutputArea) {
          this.$refs.consoleOutputArea.scrollTop = this.$refs.consoleOutputArea.scrollHeight;
        }
      });
    },
    
    // REPL methods (moved from terminal)
    async executeReplCommand() {
      if (!this.replInput.trim()) return;
      
      const command = this.replInput.trim();
      
      // Add to history
      if (this.replHistory[this.replHistory.length - 1] !== command) {
        this.replHistory.push(command);
      }
      this.replHistoryIndex = -1;
      
      // Ensure we have a console item for REPL output
      this.ensureReplConsole();
      
      // Add command to console output
      this.addReplOutput(`>>> ${command}`, 'input');
      
      // Clear input immediately for responsiveness
      this.replInput = '';
      
      // Handle special commands
      if (command === 'clear' || command === 'clear()') {
        this.clearConsole();
        return;
      }
      
      // Initialize Pyodide if not ready
      const isReady = await this.ensurePyodideReady();
      if (!isReady) {
        this.addReplOutput('Python environment failed to initialize', 'error');
        return;
      }
      
      // Execute Python code with Pyodide
      try {
        const result = this.pyodide.runPython(command);
        if (result !== undefined && result !== null) {
          this.addReplOutput(String(result), 'output');
        }
      } catch (error) {
        this.addReplOutput(error.toString(), 'error');
      }
    },
    
    // Helper method to ensure REPL console exists
    ensureReplConsole() {
      // Check if we have a console selected with resultList
      if (!this.ideInfo.consoleSelected || !this.ideInfo.consoleSelected.resultList) {
        // Create a REPL console item if it doesn't exist
        const replConsole = {
          id: 'repl-console',
          name: 'REPL',
          path: 'REPL',
          resultList: [],
          run: false,
          stop: false,
          waitingForInput: false,
          inputPrompt: ''
        };
        
        // Check if REPL console already exists in consoleItems
        const existingRepl = this.ideInfo.consoleItems.find(item => item.id === 'repl-console');
        if (!existingRepl) {
          this.$store.commit('ide/pushConsoleItem', replConsole);
        }
        
        // Select the REPL console
        this.$store.commit('ide/selectConsoleItem', 'repl-console');
      }
    },
    
    // Helper method to add output to REPL console
    addReplOutput(text, type = 'output') {
      // Use the store mutation to add output properly
      if (this.ideInfo.consoleSelected && this.ideInfo.consoleSelected.id) {
        this.$store.commit('ide/addConsoleOutput', {
          id: this.ideInfo.consoleSelected.id,
          type: type,
          text: text
        });
        
        // Scroll to bottom after adding output
        this.$nextTick(() => {
          if (this.$refs.consoleOutputArea) {
            this.$refs.consoleOutputArea.scrollTop = this.$refs.consoleOutputArea.scrollHeight;
          }
        });
      }
    },
    
    navigateReplHistory(direction) {
      if (this.replHistory.length === 0) return;
      
      if (direction === 'up') {
        if (this.replHistoryIndex === -1) {
          this.replHistoryIndex = this.replHistory.length - 1;
        } else if (this.replHistoryIndex > 0) {
          this.replHistoryIndex--;
        }
      } else if (direction === 'down') {
        if (this.replHistoryIndex === -1) return;
        if (this.replHistoryIndex < this.replHistory.length - 1) {
          this.replHistoryIndex++;
        } else {
          this.replHistoryIndex = -1;
          this.replInput = '';
          return;
        }
      }
      
      if (this.replHistoryIndex >= 0) {
        this.replInput = this.replHistory[this.replHistoryIndex];
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
/* Layout Structure */
.total-frame {
  position: fixed;
  width: 100%;
  height: calc(100% - 50px);
  top: 50px;
  left: 0;
  display: flex;
  flex-direction: row;
}

/* Left Sidebar */
.left-sidebar {
  background: var(--bg-sidebar, #282828);
  color: var(--text-primary, #CCCCCC);
  height: 100%;
  overflow: auto;
  flex-shrink: 0;
  position: absolute;
  left: 0;
  top: 0;
  z-index: 10;
}

/* Center Frame */
.center-frame {
  position: absolute;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary, #1E1E1E);
  min-width: 500px; /* Ensure minimum width for editor */
  overflow: hidden;
}

/* Editor Section */
.editor-section {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: height 0.3s ease;
  flex: 1;
  min-height: 200px; /* Ensure minimum editor height */
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

/* Console Section */
.console-section {
  background: var(--bg-secondary, #252526);
  border-top: 1px solid var(--border-primary, #3c3c3c);
  transition: height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  display: flex;
  z-index: 5; /* Lower z-index to stay below right sidebar */
  flex-direction: column;
}

.console-section.collapsed {
  overflow: hidden;
}

/* Console Resizer */
.console-resizer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 5px;
  cursor: ns-resize;
  background: transparent;
  z-index: 20;
  transition: background-color 0.2s ease;
}

.console-resizer:hover {
  background: rgba(0, 122, 204, 0.3);
}

.console-resizer.resizing {
  background: var(--accent-color, #007ACC);
}

.resizer-handle.horizontal {
  width: 40px;
  height: 2px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--text-secondary, #858585);
  border-radius: 1px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.console-resizer:hover .resizer-handle.horizontal,
.console-resizer.resizing .resizer-handle.horizontal {
  opacity: 1;
}

.console-header {
  height: 35px;
  background: var(--bg-secondary, #2A2A2D);
  border-bottom: 1px solid var(--border-primary, #3c3c3c);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 12px;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease;
}

.console-header:hover {
  background: var(--bg-hover, #313133);
}

.console-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-icon {
  display: inline-block;
  transition: transform 0.3s ease;
  font-size: 12px;
  color: var(--text-secondary, #969696);
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

.console-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #CCCCCC);
}

.console-count {
  font-size: 12px;
  color: var(--text-secondary, #969696);
}

.console-header-right {
  display: flex;
  gap: 8px;
}

.console-action-btn {
  background: transparent;
  border: 1px solid var(--border-secondary, #464647);
  color: var(--text-secondary, #969696);
  padding: 4px 12px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.console-action-btn:hover {
  background: var(--bg-hover, #3A3A3C);
  border-color: var(--accent-color, #007ACC);
  color: var(--text-primary, #FFFFFF);
}

.console-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: calc(100% - 35px);
}

.console-tab-bar {
  height: 30px;
  background: var(--bg-tertiary, #1E1E1E);
  border-bottom: 1px solid var(--border-secondary, #464647);
}

.console-output-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--bg-primary, #1E1E1E);
  padding: 12px;
  font-family: 'Courier New', Consolas, monospace;
  font-size: 13px;
  line-height: 1.4;
}

/* Console output styles */
.console-line {
  margin-bottom: 2px;
}

.console-text {
  color: var(--text-primary, #CCCCCC);
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.console-error {
  color: var(--error-color, #F44747);
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.console-input-prompt {
  color: var(--info-color, #3794FF);
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.prompt-arrow {
  color: var(--accent-color, #007ACC);
  font-weight: bold;
}

.console-system {
  color: var(--text-secondary, #969696);
  margin: 0;
  font-style: italic;
  white-space: pre-wrap;
}

/* Console input area when waiting for program input */
.console-input-area {
  border-top: 1px solid var(--border-secondary, #464647);
  padding: 8px 12px;
  background: var(--bg-tertiary, #1A1A1A);
}

.input-prompt {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--text-secondary, #969696);
  font-size: 13px;
}

.prompt-icon {
  font-size: 16px;
}

.input-field-container {
  display: flex;
  gap: 8px;
}

.program-input-field {
  flex: 1;
  background: var(--bg-primary, #1E1E1E);
  border: 1px solid var(--border-secondary, #464647);
  color: var(--text-primary, #FFFFFF);
  padding: 6px 10px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  outline: none;
}

.program-input-field:focus {
  border-color: var(--accent-color, #007ACC);
}

.input-submit-btn {
  background: var(--accent-color, #007ACC);
  color: white;
  border: none;
  padding: 6px 16px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 13px;
  transition: background-color 0.2s ease;
}

.input-submit-btn:hover {
  background: #1a8cff;
}

/* REPL Section */
.repl-section {
  border-top: 1px solid var(--border-primary, #3c3c3c);
  background: var(--bg-secondary, #252526);
  padding: 8px 12px;
  flex-shrink: 0; /* Prevent shrinking */
  margin-top: auto; /* Push to bottom */
}

.repl-prompt {
  display: flex;
  align-items: center;
}

.prompt-symbol {
  color: var(--accent-color, #007ACC);
  font-weight: bold;
  margin-right: 8px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.repl-input {
  flex: 1;
  background: var(--bg-primary, #1E1E1E);
  border: 1px solid var(--border-secondary, #464647);
  color: var(--text-primary, #FFFFFF);
  font-family: 'Courier New', monospace;
  font-size: 14px;
  padding: 6px 8px;
  border-radius: 3px;
  outline: none;
  transition: border-color 0.2s ease;
}

.repl-input:focus {
  border-color: var(--accent-color, #007ACC);
}

.repl-input::placeholder {
  color: var(--text-muted, #6A6A6A);
}

/* Right Sidebar */
.right-sidebar {
  background: var(--bg-sidebar, #252526);
  height: 100%;
  display: flex;
  flex-direction: column;
  position: absolute;
  top: 0;
  right: 0;
  border-left: 1px solid var(--border-primary, #3c3c3c);
  z-index: 20; /* Higher z-index to stay above console section */
}

/* Preview Tabs */
.preview-tabs {
  height: 35px;
  background: var(--bg-secondary, #2A2A2D);
  border-bottom: 1px solid var(--border-primary, #3c3c3c);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
}

.preview-tab-list {
  display: flex;
  flex: 1;
  overflow-x: auto;
  gap: 2px;
}

.preview-tab {
  background: transparent;
  border: none;
  color: var(--text-secondary, #969696);
  padding: 6px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  font-size: 13px;
  white-space: nowrap;
}

.preview-tab:hover {
  background: var(--bg-hover, #2F2F31);
  color: var(--text-primary, #CCCCCC);
}

.preview-tab.active {
  background: var(--bg-active, #1E1E1E);
  color: var(--text-primary, #FFFFFF);
  border-bottom-color: var(--accent-color, #007ACC);
}

.tab-icon {
  font-size: 14px;
}

.tab-title {
  font-size: 13px;
}

.tab-close {
  margin-left: 4px;
  opacity: 0.6;
  transition: opacity 0.2s ease;
  font-size: 16px;
  line-height: 1;
}

.tab-close:hover {
  opacity: 1;
  color: var(--error-color, #F44747);
}

.preview-tab-add {
  background: transparent;
  border: none;
  color: var(--text-secondary, #969696);
  padding: 4px 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.preview-tab-add:hover {
  background: var(--bg-hover, #2F2F31);
  color: var(--accent-color, #007ACC);
}

/* Preview Content */
.preview-content {
  flex: 1;
  overflow: hidden;
  background: var(--bg-primary, #1E1E1E);
}

.preview-panel {
  height: 100%;
  overflow: auto;
}

.output-panel {
  height: 100%;
  padding: 12px;
}

.output-content {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.output-line {
  margin-bottom: 4px;
}

.output-line.error {
  color: var(--error-color, #F44747);
}

.output-line.warning {
  color: var(--warning-color, #FFCC00);
}

.output-line.info {
  color: var(--info-color, #3794FF);
}

.output-line pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.image-preview-panel {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: var(--bg-pattern, #1A1A1A);
}

.image-preview-panel img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.pdf-preview-panel {
  height: 100%;
}

.pdf-preview-panel iframe {
  width: 100%;
  height: 100%;
}

.data-preview-panel {
  height: 100%;
  overflow: auto;
  padding: 12px;
  position: relative;
  z-index: 21; /* Ensure CSV content and scrollbars are above everything */
}

/* Sidebar Resizers */
.sidebar-resizer {
  width: 5px;
  height: 100%;
  background: var(--border-primary, #3c3c3c);
  cursor: col-resize;
  position: absolute;
  transition: background-color 0.2s ease;
  z-index: 50;
}

.sidebar-resizer:hover {
  background: var(--accent-color, #007ACC);
}

.sidebar-resizer.resizing {
  background: var(--accent-color, #007ACC);
}

/* Visual feedback when approaching resize limits */
.sidebar-resizer.resizing.at-limit {
  background: var(--warning-color, #FFA500);
}

.sidebar-resizer.left {
  /* Position will be set inline via :style */
}

.sidebar-resizer.right {
  /* Position will be set inline via :style */
}

.resizer-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 30px;
  background: var(--text-secondary, #858585);
  border-radius: 1px;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.sidebar-resizer:hover .resizer-handle,
.sidebar-resizer.resizing .resizer-handle {
  opacity: 1;
}

/* Prevent resizer from going into editor area */
.sidebar-resizer.left {
  min-left: 150px;
  max-left: calc(100vw - 800px); /* min editor + right sidebar */
}

.sidebar-resizer.right {
  min-right: 300px;
  max-right: calc(100vw - 650px); /* min editor + left sidebar */
}

/* Show Preview Button */
.show-preview-btn {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: var(--accent-color, #007ACC);
  color: white;
  padding: 8px 6px;
  border-radius: 4px 0 0 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  z-index: 15;
  transition: all 0.2s ease;
}

.show-preview-btn:hover {
  background: #1a8cff;
  padding-right: 10px;
}

.show-preview-btn .tab-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: bold;
}

/* Animations */
@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(0);
    opacity: 1;
  }
  to {
    transform: translateY(-100%);
    opacity: 0;
  }
}

.console-section {
  animation: slideDown 0.3s ease-out;
}

.console-section.collapsed {
  animation: slideUp 0.3s ease-out;
}

/* Console Mode Tabs (Legacy - Hidden) */
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

body {
  scrollbar-track-color: #3C3F41;
}

.top-menu {
  position: fixed;
  width: 100%;
  height: 50px;
  top: 0;
  left: 0;
  background: #313131;
  display: flex;
  align-items: center;
  z-index: 9999;
}
/* Scrollbar styles */
.left-sidebar::-webkit-scrollbar,
.console-output-area::-webkit-scrollbar,
.preview-content::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.left-sidebar::-webkit-scrollbar-thumb,
.console-output-area::-webkit-scrollbar-thumb,
.preview-content::-webkit-scrollbar-thumb {
  background: #87939A;
  border-radius: 3px;
}

.left-sidebar::-webkit-scrollbar-track,
.console-output-area::-webkit-scrollbar-track,
.preview-content::-webkit-scrollbar-track {
  background: #2F2F2F;
}

/* Context Menu */
.context-menu {
  position: fixed;
  background: var(--bg-secondary, #252526);
  border: 1px solid var(--border-primary, #3c3c3c);
  border-radius: 4px;
  padding: 4px 0;
  min-width: 150px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 10000;
}

.context-menu-item {
  padding: 8px 16px;
  cursor: pointer;
  color: var(--text-primary, #CCCCCC);
  font-size: 13px;
  transition: background-color 0.2s ease;
}

.context-menu-item:hover {
  background: var(--bg-hover, #094771);
}

.context-menu-divider {
  height: 1px;
  background: var(--border-secondary, #464647);
  margin: 4px 0;
}

/* Responsive Design */
@media (max-width: 1400px) {
  .left-sidebar {
    max-width: 200px;
  }
  
  .right-sidebar {
    max-width: 350px;
  }
  
  .console-height {
    max-height: 250px;
  }
}

@media (max-width: 1200px) {
  .left-sidebar {
    width: 180px !important;
  }
  
  .right-sidebar {
    width: 300px !important;
  }
}

@media (max-width: 900px) {
  /* Hide sidebars on small screens */
  .left-sidebar {
    width: 0 !important;
    display: none;
  }
  
  .sidebar-resizer.left {
    display: none;
  }
  
  .center-frame {
    left: 0 !important;
    right: 0 !important;
  }
  
  .right-sidebar {
    display: none;
  }
  
  .sidebar-resizer.right {
    display: none;
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
