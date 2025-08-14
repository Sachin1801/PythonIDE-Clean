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
      @open-repl="openREPL"
      @open-settings="showSettingsModal = true"
    ></TopMenu>
    
    <!-- Settings Modal -->
    <SettingsModal 
      v-model="showSettingsModal"
      @update-line-numbers="updateLineNumbers"
      @update-word-wrap="updateWordWrap"
      @update-auto-save="updateAutoSave"
      @update-auto-save-interval="updateAutoSaveInterval"
    />
    <div id="total-frame" class="total-frame">
      <!-- Main Horizontal Splitpanes for Left/Center/Right -->
      <splitpanes class="default-theme main-splitpanes">
        <!-- Left Sidebar Pane - Always present in DOM -->
        <pane :size="leftSidebarSize" :min-size="0" :max-size="40">
          <div id="left-sidebar" class="left-sidebar" v-show="leftSidebarVisible">
            <ProjTree 
              v-on:get-item="getFile"
              @context-menu="showContextMenu"
            ></ProjTree>
          </div>
        </pane>
        
        <!-- Center Content Pane -->
        <pane :size="centerSize" :min-size="30">
          <div id="center-frame" class="center-frame">
            <!-- Nested Horizontal Splitpanes for Editor/Console -->
            <splitpanes horizontal class="default-theme">
              <!-- Editor Pane -->
              <pane :size="editorPaneSize" :min-size="5">
                <div class="editor-section">
          <div class="editor-tab-bar">
            <CodeTabs
              v-if="ideInfo.codeItems.length > 0"
              v-on:select-item="selectFile"
              v-on:close-item="closeFile"
              @toggle-sidebar="toggleLeftSidebar">
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
              </pane>
              
              <!-- Console Pane -->
              <pane :size="consolePaneSize" :min-size="5" :max-size="95">
                <div class="console-section">
              <!-- Console Header with Collapse/Expand Button -->
          <div class="console-header">
            <div class="console-header-left">
              <span class="console-title">{{ isReplMode ? 'Python REPL' : 'Console' }}</span>
            </div>
            <div class="console-header-center">
              <button class="console-expand-arrow" 
                      @click="handleConsoleUpArrow" 
                      title="Maximize console"
                      v-if="consoleMode !== 'maximized'">
                <ChevronUp :size="16" />
              </button>
              <button class="console-expand-arrow" 
                      @click="handleConsoleRestore" 
                      title="Restore console"
                      v-if="consoleMode === 'maximized'">
                <Minimize2 :size="16" />
              </button>
              <button class="console-expand-arrow" 
                      @click="handleConsoleDownArrow" 
                      title="Minimize console"
                      v-if="consoleMode === 'normal'">
                <ChevronDown :size="16" />
              </button>
            </div>
            <div class="console-header-right" v-if="consoleExpanded">
              <button class="console-action-btn" 
                      @click.stop="toggleReplMode" 
                      :class="{ 'active': isReplMode }"
                      :title="isReplMode ? 'Exit REPL Mode' : 'Start Python REPL'">
                <span>{{ isReplMode ? 'Exit REPL' : 'REPL' }}</span>
              </button>
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
                    <span>{{ result.text || result.content || result }}</span>
                  </div>
                  
                  <!-- System message -->
                  <pre v-else-if="result.type === 'system'" class="console-system">{{ result.text || result.content || result }}</pre>
                  
                  <!-- Default fallback -->
                  <pre v-else class="console-text">{{ typeof result === 'object' ? (result.text || result.content || JSON.stringify(result)) : result }}</pre>
                </div>
              </template>
            </div>
            
            <!-- Input field when waiting for input (moved outside output area) -->
            <div v-if="ideInfo.consoleSelected && ideInfo.consoleSelected.waitingForInput" class="console-input-area">
              <div class="input-prompt">
                <span class="prompt-icon">💬</span>
                <span>{{ ideInfo.consoleSelected.inputPrompt || 'Enter input:' }}</span>
              </div>
              <div class="input-field-container">
                <textarea
                  v-model="programInput"
                  @keydown="handleProgramInputKeydown"
                  ref="programInputField"
                  class="program-input-field"
                  placeholder="Type your input and press Enter..."
                  :rows="programInputRows"
                  autofocus
                ></textarea>
                <button @click="sendProgramInput" class="input-submit-btn">Send</button>
              </div>
            </div>
            
            <!-- REPL Input Area (like p5.js) -->
            <div v-if="isReplMode" class="repl-section">
              <div class="repl-prompt">
                <span class="prompt-symbol">{{ replPrompt || '>>> ' }}</span>
                <textarea 
                  class="repl-input"
                  placeholder="Enter Python code..."
                  v-model="replInput"
                  @keydown="handleReplKeydown"
                  ref="replInputField"
                  :rows="replInputRows">
                </textarea>
              </div>
            </div>
          </div>
                </div>
              </pane>
            </splitpanes>
          </div>
        </pane>
        
                 <!-- Right Sidebar Pane - Always present in DOM -->
         <pane :size="rightSidebarSize" :min-size="0" :max-size="50">
           <div id="right-sidebar" class="right-sidebar">
            <!-- Hidden placeholder when sidebar is not visible -->
            <div v-show="!rightSidebarVisible || previewTabs.length === 0" class="right-sidebar-placeholder">
              <!-- Empty space with proper background -->
            </div>
            
            <!-- Preview/Output Tabs -->
            <div class="preview-tabs" v-show="rightSidebarVisible && previewTabs.length > 0">
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
            <div class="preview-content" v-show="rightSidebarVisible && previewTabs.length > 0">
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
        </pane>
      </splitpanes>
      
      <!-- Right Panel Control Arrows -->
      <div v-if="rightPanelMode !== 'closed' && previewTabs.length > 0" class="right-panel-controls">
        <button 
          class="control-arrow left-arrow"
          @click="handleLeftArrowClick"
          :title="'Expand preview to full width'"
          v-if="rightPanelMode === 'normal'"
        >
          <ChevronLeft :size="16" />
        </button>
        <button 
          class="control-arrow right-arrow"
          @click="handleRightArrowClick"
          :title="rightPanelMode === 'expanded' ? 'Restore to normal size' : 'Collapse preview panel'"
        >
          <ChevronRight :size="16" />
        </button>
      </div>
      
      <!-- Show Preview Button (when hidden but has content) -->
      <div v-if="rightPanelMode === 'closed' && previewTabs.length > 0" 
           class="show-preview-btn" 
           @click="restoreRightPanel"
           title="Show Preview Panel">
        <span class="tab-count">{{ previewTabs.length }}</span>
        <span>◀</span>
      </div>
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
    
    <!-- REPL Modal -->
    <div v-if="showREPL" class="repl-modal">
      <div class="repl-modal-content">
        <div class="repl-modal-header">
          <h3>Python REPL (Interactive Console)</h3>
          <button @click="closeREPL" class="repl-close-btn">✕</button>
        </div>
        <div class="repl-modal-body">
          <PythonREPL />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';
import * as types from '../../store/mutation-types';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ChevronLeft, ChevronRight, ChevronUp, ChevronDown, Minimize2 } from 'lucide-vue-next';
import TopMenu from './pages/ide/TopMenu';
import CodeTabs from './pages/ide/CodeTabs';
import UnifiedConsole from './pages/ide/UnifiedConsole';
import ConsoleTabs from './pages/ide/ConsoleTabs';
import ProjTree from './pages/ide/ProjTree';
import IdeEditor from './pages/ide/IdeEditor';
import PythonREPL from './pages/ide/PythonREPL';
import DialogProjs from './pages/ide/dialog/DialogProjs';
import DialogText from './pages/ide/dialog/DialogText';
import DialogDelete from './pages/ide/dialog/DialogDelete';
import DialogUpload from './pages/ide/dialog/DialogUpload';
import CsvViewer from './pages/ide/CsvViewer';
import SettingsModal from './pages/ide/SettingsModal';
import DualModeREPL from './DualModeREPL';
const path = require('path');

export default {
  data() {
    return {
      showDeleteDialog: false,
      showFileDialog: false,
      showProjsDialog: false,
      showUploadDialog: false,
      showSettingsModal: false,
      showREPL: false,
      isReplMode: false,  // Toggle between normal console and REPL mode
      replSessionId: null,  // Track active REPL session
      showCover: true,
      showContextMenu: false,
      contextMenuPosition: { x: 0, y: 0 },
      contextMenuTarget: null,
      leftSidebarVisible: true,
      
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
      consoleMaximized: false,
      previousConsoleHeight: 200,
      rightPanelExpanded: false,
      previousRightWidth: 400,
      
      // Right panel state management
      rightPanelMode: 'closed', // 'closed', 'normal', 'expanded'
      
      // Console state management
      consoleMode: 'collapsed', // 'collapsed', 'normal', 'maximized'
      consolePreviousMode: 'normal', // For restoration from maximized
      wasConsoleOpenBeforeRightExpand: false, // Track console state before right panel expansion
      
      // Legacy properties (keep for compatibility)
      rightPanelState: 'normal',
      rightPanelNormalWidth: 400,
      previousConsoleState: {
        expanded: true,
        height: 200
      },
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
      programInputRows: 1,
      
      // Word wrap
      wordWrap: true, // Enabled by default
      
      // Console/REPL
      replInput: '',
      replHistory: [],
      replHistoryIndex: -1,
      replPrompt: '>>> ',
      replInputRows: 1,
      replContinuationMode: false,
      
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
      pyodideReady: false,
      
      // REPL mode configuration (for dual-mode)
      replMode: 'auto', // 'backend', 'pyodide', or 'auto'
      pyodideNamespace: null,
      pyodideInitialized: false
    }
  },
  mixins: [DualModeREPL],
  components: {
    Splitpanes,
    Pane,
    TopMenu,
    CodeTabs,
    UnifiedConsole,
    ConsoleTabs,
    ProjTree,
    IdeEditor,
    PythonREPL,
    DialogProjs,
    DialogText,
    DialogDelete,
    DialogUpload,
    CsvViewer,
    SettingsModal,
    ChevronLeft,
    ChevronRight,
    ChevronUp,
    ChevronDown,
    Minimize2,
  },
  created() {
  },
  mounted() {
    // Initialize throttled resize handlers for better performance
    this.throttledHandleResizeLeft = this.throttle(this.handleResizeLeft, 16); // ~60fps
    this.throttledHandleResizeRight = this.throttle(this.handleResizeRight, 16);
    this.throttledHandleResizeConsole = this.throttle(this.handleResizeConsole, 16);

    // Initialize WebSocket if needed
    try {
      console.log('🔌 [VmIde] Initializing WebSocket...');
      if (!this.wsInfo || !this.wsInfo.rws) {
        this.$store.dispatch('websocket/init', {});
        console.log('✅ [VmIde] WebSocket initialization dispatched');
      } else {
        console.log('ℹ️ [VmIde] WebSocket already initialized');
      }
    } catch (error) {
      console.error('❌ [VmIde] Error initializing WebSocket:', error);
    }

    // TEMPORARY: Add a test preview tab to show the right sidebar
    // Remove this after testing
    this.addPreviewTab('image', 'test_image.png', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==');
    
    // Set initial state for testing
    this.rightPanelMode = 'normal';
    this.consoleMode = 'collapsed';
    
    // Set up WebSocket message handler for REPL after a delay to ensure WebSocket is ready
    this.$nextTick(() => {
      setTimeout(() => {
        try {
          this.setupWebSocketHandler();
        } catch (error) {
          console.error('Error in setupWebSocketHandler:', error);
        }
      }, 500);
    });
    
    // Load user layout preferences
    this.loadLayoutPreferences();
    
    // Add window resize listener to validate layout
    window.addEventListener('resize', this.validateLayout);
    
    const self = this;
    const t = setInterval(() => {
      console.log("⏱️ [VmIde] WebSocket check:", { 
        connected: self.wsInfo.connected, 
        wsInfo: self.wsInfo 
      });
      if (self.wsInfo.connected) {
        console.log("📡 [VmIde] WebSocket connected, listing projects...");
        this.$store.dispatch(`ide/${types.IDE_LIST_PROJECTS}`, {
          callback: (dict) => {
            console.log("📋 [VmIde] Project list response:", dict);
            clearInterval(t);
            if (dict.code == 0) {
              console.log("✅ [VmIde] Projects found:", dict.data);
              this.$store.commit('ide/handleProjects', dict.data);
              // Load all default projects instead of just one
              self.loadAllDefaultProjects();
            } else {
              console.error("❌ [VmIde] Failed to list projects:", dict);
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
    },
    // Computed properties for splitpanes sizes (in percentages)
    leftSidebarSize() {
      // Always return a size, even when hidden
      // This ensures splitpanes can properly manage the panes
      return this.leftSidebarVisible ? 20 : 0;
    },
    rightSidebarSize() {
      // Handle different states based on new mode system
      if (this.rightPanelMode === 'closed' || this.previewTabs.length === 0) {
        return 0;
      }
      if (this.rightPanelMode === 'expanded') {
        // Take 70% of non-sidebar space when expanded
        const leftSize = this.leftSidebarVisible ? 20 : 0;
        return 100 - leftSize - 10; // Leave 10% for minimal editor
      }
      // Normal state - 30%
      return 30;
    },
    centerSize() {
      // Calculate center size based on what's visible
      const leftSize = this.leftSidebarVisible ? 20 : 0;
      const rightSize = this.rightSidebarSize;  // Access as property, not function
      return 100 - leftSize - rightSize;
    },
    // New computed properties for console sizing
    editorPaneSize() {
      // Vertical sizing within center frame
      if (this.consoleMode === 'maximized') return 5;  // Just header visible
      if (this.consoleMode === 'collapsed') return 95; // Console minimized
      return 70; // Normal - editor gets 70%
    },
    consolePaneSize() {
      // Vertical sizing within center frame
      if (this.consoleMode === 'maximized') return 95;  // Almost full height
      if (this.consoleMode === 'collapsed') return 5;   // Just header
      return 30; // Normal - console gets 30%
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
    // Utility function for throttling resize events using requestAnimationFrame
    throttle(func, delay) {
      let lastRun = 0;
      let rafId = null;
      const context = this;
      
      return function(...args) {
        const now = Date.now();
        
        if (now - lastRun >= delay) {
          func.apply(context, args);
          lastRun = now;
        } else if (!rafId) {
          rafId = requestAnimationFrame(() => {
            func.apply(context, args);
            lastRun = Date.now();
            rafId = null;
          });
        }
      };
    },
    
    toggleLeftSidebar(visible) {
      this.leftSidebarVisible = visible;
    },
    updateLineNumbers(value) {
      // Update line numbers in all editors
      this.$store.commit('ide/setEditorOption', { option: 'lineNumbers', value });
    },
    updateWordWrap(value) {
      this.wordWrap = value;
      this.$store.commit('ide/setEditorOption', { option: 'lineWrapping', value });
    },
    updateAutoSave(value) {
      this.$store.commit('ide/setAutoSave', value);
      if (value) {
        this.startAutoSave();
      } else {
        this.stopAutoSave();
      }
    },
    updateAutoSaveInterval(value) {
      this.$store.commit('ide/setAutoSaveInterval', value);
      if (this.$store.state.ide.autoSave) {
        this.stopAutoSave();
        this.startAutoSave();
      }
    },
    startAutoSave() {
      if (this.autoSaveTimer) {
        clearInterval(this.autoSaveTimer);
      }
      const interval = this.$store.state.ide.autoSaveInterval || 60;
      this.autoSaveTimer = setInterval(() => {
        this.saveAllFiles();
      }, interval * 1000);
    },
    stopAutoSave() {
      if (this.autoSaveTimer) {
        clearInterval(this.autoSaveTimer);
        this.autoSaveTimer = null;
      }
    },
    saveAllFiles() {
      // Auto-save all open files
      this.ideInfo.codeItems.forEach(item => {
        if (item.changed) {
          this.saveFile(item);
        }
      });
    },
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
      this.programInputRows = 1;
    },
    
    toggleWordWrap() {
      this.wordWrap = !this.wordWrap;
      localStorage.setItem('word-wrap', this.wordWrap);
      // The change will be picked up by the CodeEditor component
    },
    
    openREPL() {
      // Instead of opening modal, toggle REPL mode in console
      this.toggleReplMode();
    },
    
    closeREPL() {
      // Deprecated - use toggleReplMode instead
      this.showREPL = false;
    },
    
    async toggleReplMode() {
      if (this.isReplMode) {
        // Exit REPL mode
        if (this.replSessionId) {
          await this.stopReplSession();
        }
        this.isReplMode = false;
        this.replPrompt = '>>> ';
        this.replInput = '';
        this.replInputRows = 1;
      } else {
        // Enter REPL mode
        this.isReplMode = true;
        
        // Clear console for REPL
        this.clearConsole();
        
        // Ensure console is expanded
        if (!this.consoleExpanded) {
          this.consoleExpanded = true;
        }
        
        // Start REPL session
        await this.startReplSession();
        
        // Focus input
        this.$nextTick(() => {
          if (this.$refs.replInputField) {
            this.$refs.replInputField.focus();
          }
        });
      }
    },
    
    async startReplSession() {
      await this.startDualModeReplSession();
    },
    
    async stopReplSession() {
      await this.stopDualModeReplSession();
    },
    
    getPythonVersion() {
      // This could be fetched from backend
      return '3.x';
    },
    
    setupWebSocketHandler() {
      // Add a handler for WebSocket messages
      try {
        if (!this.wsInfo || !this.wsInfo.rws) {
          console.log('WebSocket not ready, retrying...');
          setTimeout(() => this.setupWebSocketHandler(), 500);
          return;
        }
        
        // Store original onmessage if exists
        const originalOnMessage = this.wsInfo.rws.onmessage;
        
        this.wsInfo.rws.onmessage = (event) => {
          // Handle REPL messages FIRST before the store consumes them
          try {
            const message = JSON.parse(event.data);
            
            // Log ALL WebSocket messages to debug
            console.log("📥 [VmIde] ALL WebSocket msg:", {
              id: message.id,
              cmd_id: message.cmd_id,
              code: message.code,
              cmd: message.cmd,
              programId: message.data?.program_id,
              ourSessionId: this.replSessionId,
              fullMsg: message
            });
            
            // Check if this is a REPL message - check ALL possible ID fields
            // The backend might send responses with the command ID, not session ID
            // Also check for any program output when REPL is active
            const isRepl = (
                message.id === this.replSessionId || 
                message.cmd_id === this.replSessionId ||
                (message.data && message.data.program_id === this.replSessionId) ||
                // If REPL is active and this looks like output, capture it
                (this.isReplMode && this.replSessionId && 
                 (message.code === 0 || message.code === 2000 || message.code === 1111) &&
                 message.data && (message.data.stdout || message.data.stderr || message.data.program_id))
            );
                
            console.log(`🔍 Match check: id=${message.id===this.replSessionId}, cmd_id=${message.cmd_id===this.replSessionId}, prog_id=${message.data?.program_id===this.replSessionId}, isReplMode=${this.isReplMode}, code=${message.code}`);
                
            if (isRepl) {
              console.log('🎯 REPL message matched!');
              this.handleBackendReplResponse(message);
            }
          } catch (e) {
            // Not JSON or parsing error, ignore
          }
          
          // THEN call original handler so store can process other messages
          if (originalOnMessage) {
            originalOnMessage(event);
          }
        };
        
        console.log('WebSocket handler for REPL set up successfully');
      } catch (error) {
        console.error('Error setting up WebSocket handler:', error);
      }
    },
    
    handleReplMessage(message) {
      console.log('Handling REPL message:', message);
      this.handleReplResponse(message);
    },
    
    handleReplResponse(dict) {
      console.log('Processing REPL response:', dict);
      
      if (!dict) return;
      
      // Handle different response codes
      if (dict.code === 0 || dict.code === '0') {
        // Success response with output
        if (dict.data) {
          if (dict.data.stdout) {
            this.addReplOutput(dict.data.stdout, 'output');
          }
          if (dict.data.stderr) {
            this.addReplOutput(dict.data.stderr, 'error');
          }
          if (dict.data.output) {
            this.addReplOutput(dict.data.output, 'output');
          }
        }
      } else if (dict.code === 2000 || dict.cmd === 'python_output') {
        // Python output during execution
        if (dict.data) {
          if (dict.data.stdout) {
            this.addReplOutput(dict.data.stdout, 'output');
          }
          if (dict.data.stderr) {
            this.addReplOutput(dict.data.stderr, 'error');
          }
        }
      } else if (dict.code === 1111 || dict.cmd === 'python_ended') {
        // REPL session ended
        this.addReplOutput('\nREPL session ended', 'system');
        this.isReplMode = false;
        this.replSessionId = null;
        this.replPrompt = '>>> ';
      } else if (dict.code === -1 || dict.error) {
        // Error response
        const errorMsg = dict.error || dict.data?.error || 'Unknown error';
        this.addReplOutput('Error: ' + errorMsg, 'error');
      }
      
      // Scroll to bottom after adding output
      this.$nextTick(() => {
        if (this.$refs.consoleOutputArea) {
          this.$refs.consoleOutputArea.scrollTop = this.$refs.consoleOutputArea.scrollHeight;
        }
      });
    },
    
    toggleRightSidebar() {
      // Only allow toggling if there are tabs to show
      if (this.previewTabs.length > 0 || this.rightSidebarVisible) {
        this.rightSidebarVisible = !this.rightSidebarVisible;
        localStorage.setItem('right-sidebar-visible', this.rightSidebarVisible);
      }
    },

    expandRightPanel() {
      // Expand right panel to take full code editor space
      if (!this.rightPanelExpanded) {
        this.previousRightWidth = this.rightSidebarWidth;
        const windowWidth = window.innerWidth;
        const leftWidth = this.leftSidebarVisible ? this.leftSidebarWidth : 0;
        // Take all available space except left sidebar (and 10px for resizers)
        this.rightSidebarWidth = windowWidth - leftWidth - 10;
        this.rightPanelExpanded = true;
        
        // Force close console when expanding right panel
        if (this.consoleExpanded) {
          this.consoleExpanded = false;
          this.consoleMaximized = false;
          this.updateEditorHeight();
        }
      }
    },

    collapseRightPanel() {
      // Restore right panel to previous width
      if (this.rightPanelExpanded) {
        this.rightSidebarWidth = this.previousRightWidth;
        this.rightPanelExpanded = false;
        // Restore console if it was open before
        if (this.previousConsoleHeight > 0) {
          this.consoleExpanded = true;
          this.updateEditorHeight();
        }
      } else {
        // If not expanded, just minimize it
        this.rightSidebarWidth = 300;
      }
    },
    
    // Right panel control methods
    handleLeftArrowClick() {
      if (this.rightPanelMode === 'normal') {
        // Save console state before forcing it closed
        this.wasConsoleOpenBeforeRightExpand = (this.consoleMode !== 'collapsed');
        
        // Force close console to maximize space
        this.consoleMode = 'collapsed';
        this.consoleExpanded = false;
        this.consoleMaximized = false;
        
        // Expand right panel to take over editor space
        this.rightPanelMode = 'expanded';
        this.rightSidebarVisible = true;
        
        this.saveLayoutPreferences();
      }
      // Left arrow only works from normal state
    },
    
    handleRightArrowClick() {
      if (this.rightPanelMode === 'expanded') {
        // From expanded, return to normal (30%)
        this.rightPanelMode = 'normal';
        
        // Restore console if it was open before expansion
        if (this.wasConsoleOpenBeforeRightExpand) {
          this.consoleMode = 'normal';
          this.consoleExpanded = true;
        }
      } else if (this.rightPanelMode === 'normal') {
        // From normal, close completely
        this.rightPanelMode = 'closed';
        this.rightSidebarVisible = false;
      }
      
      this.saveLayoutPreferences();
    },
    
    expandRightPanelToFull() {
      // Save current state before expanding
      if (this.rightPanelState === 'normal') {
        this.rightPanelNormalWidth = this.rightSidebarWidth;
      }
      
      // Save console state
      this.previousConsoleState.expanded = this.consoleExpanded;
      this.previousConsoleState.height = this.consoleHeight;
      
      // Force close console
      this.consoleExpanded = false;
      this.consoleMaximized = false;
      
      // Calculate new width (take all space except left sidebar)
      const windowWidth = window.innerWidth;
      const leftWidth = this.leftSidebarVisible ? this.leftSidebarWidth : 0;
      this.rightSidebarWidth = windowWidth - leftWidth - 10; // 10px for resizers
      
      // Update state
      this.rightPanelState = 'expanded';
      this.rightPanelExpanded = true;
      this.rightSidebarVisible = true;
      
      this.updateEditorHeight();
      this.saveLayoutPreferences();
    },
    
    collapseRightPanelCompletely() {
      // Save current width if in normal state
      if (this.rightPanelState === 'normal') {
        this.rightPanelNormalWidth = this.rightSidebarWidth;
      }
      
      // Collapse the panel
      this.rightSidebarVisible = false;
      this.rightPanelState = 'collapsed';
      this.rightPanelExpanded = false;
      
      this.saveLayoutPreferences();
    },
    
    restoreRightPanelToNormal() {
      // Restore to normal width
      this.rightSidebarWidth = this.rightPanelNormalWidth || 400;
      this.rightSidebarVisible = true;
      this.rightPanelState = 'normal';
      this.rightPanelExpanded = false;
      
      // Restore console if it was open before expansion
      if (this.previousConsoleState.expanded) {
        this.consoleExpanded = true;
        this.consoleHeight = this.previousConsoleState.height || 200;
      }
      
      this.updateEditorHeight();
      this.saveLayoutPreferences();
    },
    
    restoreRightPanel() {
      // Called when clicking the show preview button
      // Restore to normal state
      this.rightPanelMode = 'normal';
      this.rightSidebarVisible = true;
      this.saveLayoutPreferences();
    },
    
    // Console control methods
    handleConsoleUpArrow() {
      if (this.consoleMode === 'collapsed' || this.consoleMode === 'normal') {
        this.consolePreviousMode = this.consoleMode;
        this.consoleMode = 'maximized';
        this.consoleMaximized = true;
        this.consoleExpanded = true;
        this.updateEditorHeight();
      }
    },
    
    handleConsoleDownArrow() {
      if (this.consoleMode === 'normal') {
        this.consoleMode = 'collapsed';
        this.consoleExpanded = false;
        this.consoleMaximized = false;
        this.updateEditorHeight();
      }
      // Do nothing if maximized or already collapsed
    },
    
    handleConsoleRestore() {
      if (this.consoleMode === 'maximized') {
        this.consoleMode = this.consolePreviousMode || 'normal';
        this.consoleMaximized = false;
        this.consoleExpanded = (this.consoleMode === 'normal');
        this.updateEditorHeight();
      }
    },

    expandConsole() {
      // Expand console to take most of the vertical space in the center frame
      // This works with splitpanes by changing the consoleExpanded flag
      if (!this.consoleMaximized) {
        this.consoleMaximized = true;
        this.consoleExpanded = true;
        // The console will take 70% when maximized (see template)
      }
    },

    restoreConsole() {
      // Restore console to normal size (30%)
      if (this.consoleMaximized) {
        this.consoleMaximized = false;
        this.consoleExpanded = true;
      }
    },

    collapseConsole() {
      // Minimize console completely (only header visible at 5%)
      this.consoleExpanded = false;
      this.consoleMaximized = false;
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
      
      // Make sure right sidebar is visible and in normal mode
      if (this.rightPanelMode === 'closed') {
        this.rightPanelMode = 'normal';
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
      console.log('🚀 [loadAllDefaultProjects] Starting to load default projects');
      const self = this;
      const defaultProjects = ['Local', 'Lecture Notes', 'Python'];
      const loadedProjects = [];
      let loadCount = 0;
      
      console.log('📋 [loadAllDefaultProjects] Project list:', this.ideInfo.projList);
      
      defaultProjects.forEach(projectName => {
        // Check if project exists in the list
        const projectExists = this.ideInfo.projList.some(p => p.name === projectName);
        console.log(`🔍 [loadAllDefaultProjects] Checking ${projectName}: exists=${projectExists}`);
        
        if (projectExists) {
          this.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
            projectName: projectName,
            callback: (dict) => {
              console.log(`📥 [loadAllDefaultProjects] Response for ${projectName}:`, dict);
              if (dict.code == 0) {
                loadedProjects.push(dict.data);
                loadCount++;
                
                // When all projects are loaded, combine them
                if (loadCount === defaultProjects.filter(p => 
                  self.ideInfo.projList.some(proj => proj.name === p)
                ).length) {
                  console.log('✅ [loadAllDefaultProjects] All projects loaded:', loadedProjects);
                  self.$store.commit('ide/handleMultipleProjects', loadedProjects);
                  // Also set the first project as current for compatibility
                  if (loadedProjects.length > 0) {
                    self.$store.commit('ide/handleProject', loadedProjects[0]);
                  }
                }
              } else {
                console.error(`❌ [loadAllDefaultProjects] Failed to load ${projectName}:`, dict);
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
      // Check if it's a media or data file
      const mediaExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.pdf'];
      const dataExtensions = ['.csv'];
      const isMediaFile = mediaExtensions.some(ext => path.toLowerCase().endsWith(ext));
      const isDataFile = dataExtensions.some(ext => path.toLowerCase().endsWith(ext));
      
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
      } else if (isDataFile) {
        // For CSV files, fetch content and display in preview panel
        const fileName = path.split('/').pop();
        
        this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
          projectName: this.ideInfo.currProj?.data?.name,
          filePath: path,
          callback: (response) => {
            if (response.code === 0 && response.data) {
              // Parse CSV content and add to preview panel
              const csvContent = response.data.content || response.data;
              self.addPreviewTab('data', fileName, csvContent, path);
              
              // Make sure right sidebar is visible
              if (!self.rightSidebarVisible) {
                self.rightSidebarVisible = true;
              }
              
              // Update file tree selection
              if (save !== false) {
                self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
              }
            } else {
              console.error('Failed to get CSV file:', path, response);
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

      // Open console at normal state (30%) when running program
      if (this.consoleMode === 'collapsed') {
        this.consoleMode = 'normal';
        this.consoleExpanded = true;
        this.consoleMaximized = false;
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
      
      // Open console at normal state (30%) when running program
      if (this.consoleMode === 'collapsed') {
        this.consoleMode = 'normal';
        this.consoleExpanded = true;
        this.consoleMaximized = false;
      }
      
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
      
      // Use throttled version for smooth performance
      document.addEventListener('mousemove', this.throttledHandleResizeLeft);
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
      document.removeEventListener('mousemove', this.throttledHandleResizeLeft);
      document.removeEventListener('mouseup', this.stopResizeLeft);
      this.validateLayout();
      this.saveLayoutPreferences();
    },
    
    startResizeRight(event) {
      this.isResizingRight = true;
      this.startX = event.clientX;
      this.startWidth = this.rightSidebarWidth;
      
      // Use throttled version for smooth performance
      document.addEventListener('mousemove', this.throttledHandleResizeRight);
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
      document.removeEventListener('mousemove', this.throttledHandleResizeRight);
      document.removeEventListener('mouseup', this.stopResizeRight);
      this.validateLayout();
      this.saveLayoutPreferences();
    },
    
    // Console resizing methods
    startResizeConsole(event) {
      this.isResizingConsole = true;
      this.startY = event.clientY;
      this.startHeight = this.consoleHeight;
      
      // Use throttled version for smooth performance
      document.addEventListener('mousemove', this.throttledHandleResizeConsole);
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
      
      // Remove throttled event listener
      document.removeEventListener('mousemove', this.throttledHandleResizeConsole);
      document.removeEventListener('mouseup', this.stopResizeConsole);
      
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
        wordWrap: this.wordWrap,
        // New state preferences
        rightPanelMode: this.rightPanelMode,
        consoleMode: this.consoleMode,
        consolePreviousMode: this.consolePreviousMode,
        wasConsoleOpenBeforeRightExpand: this.wasConsoleOpenBeforeRightExpand
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
          
          // Load new state preferences
          this.rightPanelMode = preferences.rightPanelMode || 'closed';
          this.consoleMode = preferences.consoleMode || 'collapsed';
          this.consolePreviousMode = preferences.consolePreviousMode || 'normal';
          this.wasConsoleOpenBeforeRightExpand = preferences.wasConsoleOpenBeforeRightExpand || false;
          
          // Update visibility based on mode
          this.rightSidebarVisible = (this.rightPanelMode !== 'closed');
          this.consoleExpanded = (this.consoleMode !== 'collapsed');
          this.consoleMaximized = (this.consoleMode === 'maximized');
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
    
    // Handle keydown for program input
    handleProgramInputKeydown(event) {
      if (event.key === 'Enter') {
        if (event.shiftKey) {
          // Shift+Enter: new line
          event.preventDefault();
          const start = event.target.selectionStart;
          const end = event.target.selectionEnd;
          const value = this.programInput;
          this.programInput = value.substring(0, start) + '\n' + value.substring(end);
          
          // Move cursor after the newline
          this.$nextTick(() => {
            event.target.selectionStart = event.target.selectionEnd = start + 1;
            this.updateProgramInputRows();
          });
        } else {
          // Enter without Shift: send input
          event.preventDefault();
          this.sendProgramInput();
        }
      } else if (event.key === 'Tab') {
        // Tab: insert 4 spaces
        event.preventDefault();
        const start = event.target.selectionStart;
        const end = event.target.selectionEnd;
        const value = this.programInput;
        this.programInput = value.substring(0, start) + '    ' + value.substring(end);
        
        // Move cursor after the spaces
        this.$nextTick(() => {
          event.target.selectionStart = event.target.selectionEnd = start + 4;
          this.updateProgramInputRows();
        });
      }
      
      // Auto-adjust rows
      this.$nextTick(() => {
        this.updateProgramInputRows();
      });
    },
    
    updateProgramInputRows() {
      // Calculate rows based on content and scrollHeight
      const maxRows = 7;
      const lines = this.programInput.split('\n').length;
      
      if (this.$refs.programInputField) {
        // Reset to 1 row to get accurate scrollHeight
        this.programInputRows = 1;
        this.$nextTick(() => {
          const textarea = this.$refs.programInputField;
          const lineHeight = parseInt(window.getComputedStyle(textarea).lineHeight) || 20;
          const scrollHeight = textarea.scrollHeight;
          const calculatedRows = Math.ceil(scrollHeight / lineHeight);
          this.programInputRows = Math.min(maxRows, Math.max(1, calculatedRows));
        });
      } else {
        this.programInputRows = Math.min(maxRows, Math.max(1, lines));
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
      
      // Clear input field and reset rows
      this.programInput = '';
      this.programInputRows = 1;
      
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
    
    // REPL methods
    handleReplKeydown(event) {
      if (event.key === 'Enter') {
        if (event.shiftKey) {
          // Shift+Enter: new line for multi-line input
          event.preventDefault();
          const start = event.target.selectionStart;
          const end = event.target.selectionEnd;
          const value = this.replInput;
          this.replInput = value.substring(0, start) + '\n' + value.substring(end);
          
          // Move cursor after the newline
          this.$nextTick(() => {
            event.target.selectionStart = event.target.selectionEnd = start + 1;
            this.updateReplRows();
          });
        } else {
          // Enter without Shift: execute
          event.preventDefault();
          this.executeReplCommand();
        }
      } else if (event.key === 'Tab') {
        // Tab: insert 4 spaces for indentation
        event.preventDefault();
        const start = event.target.selectionStart;
        const end = event.target.selectionEnd;
        const value = this.replInput;
        this.replInput = value.substring(0, start) + '    ' + value.substring(end);
        
        // Move cursor after the spaces
        this.$nextTick(() => {
          event.target.selectionStart = event.target.selectionEnd = start + 4;
          this.updateReplRows();
        });
      } else if (event.key === 'ArrowUp' && event.target.selectionStart === 0 && !this.replInput.includes('\n')) {
        // Up arrow at start of input: navigate history
        event.preventDefault();
        this.navigateReplHistory('up');
      } else if (event.key === 'ArrowDown' && !this.replInput.includes('\n')) {
        // Down arrow: navigate history
        event.preventDefault();
        this.navigateReplHistory('down');
      }
      
      // Auto-adjust rows after any key press
      this.$nextTick(() => {
        this.updateReplRows();
      });
    },
    
    updateReplRows() {
      // Calculate rows based on content and scrollHeight
      const maxRows = 7;
      const lines = this.replInput.split('\n').length;
      
      if (this.$refs.replInputField) {
        // Reset to 1 row to get accurate scrollHeight
        this.replInputRows = 1;
        this.$nextTick(() => {
          const textarea = this.$refs.replInputField;
          const lineHeight = parseInt(window.getComputedStyle(textarea).lineHeight) || 20;
          const scrollHeight = textarea.scrollHeight;
          const calculatedRows = Math.ceil(scrollHeight / lineHeight);
          this.replInputRows = Math.min(maxRows, Math.max(1, calculatedRows));
        });
      } else {
        this.replInputRows = Math.min(maxRows, Math.max(1, lines));
      }
    },
    
    async executeReplCommand() {
      const command = this.replInput;
      await this.executeReplCommandDualMode(command);
    },
    
    // Helper method to ensure REPL console exists
    ensureReplConsole() {
      console.log("🔍 [VmIde] ensureReplConsole called");
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
      console.log(`📢 [VmIde] addReplOutput: [${type}] ${text}`);
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
    
    // Note: Pyodide initialization is now handled by DualModeREPL mixin
    
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
        // Pyodide initialization is now handled by DualModeREPL mixin when needed
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
  /* Use normal flow inside Splitpanes */
  position: relative;
}

/* Center Frame */
.center-frame {
  /* Must participate in Splitpanes layout */
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary, #1E1E1E);
  min-width: 0; /* Allow pane to shrink without forcing overflow */
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
  transition: background-color 0.15s ease;
  /* Performance optimizations */
  will-change: background-color;
  transform: translateZ(0);
  backface-visibility: hidden;
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
  transform: translate3d(-50%, -50%, 0);
  background: var(--text-secondary, #858585);
  border-radius: 1px;
  opacity: 0;
  transition: opacity 0.15s ease;
  /* Performance optimizations */
  will-change: opacity;
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

.console-header-center {
  display: flex;
  gap: 4px;
  align-items: center;
}

.console-expand-arrow {
  background: transparent;
  border: 1px solid var(--border-primary, #3c3c3c);
  border-radius: 4px;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary, #B5B5B5);
  transition: all 0.2s;
  width: 28px;
  height: 28px;
}

.console-expand-arrow:hover {
  background: var(--accent-color, #007ACC);
  color: white;
  border-color: var(--accent-color, #007ACC);
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
  min-height: 0; /* Important for flexbox overflow to work properly */
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
  position: sticky;
  bottom: 0;
  z-index: 10;
  margin-top: auto; /* Push to bottom of flex container */
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
  resize: none; /* Prevent manual resize */
  overflow-y: auto; /* Scroll when exceeds max-height */
  min-height: 32px; /* Approximately 1 line */
  max-height: 150px; /* Approximately 7 lines */
  line-height: 20px;
  transition: height 0.15s ease;
}

.program-input-field:focus {
  border-color: var(--accent-color, #007ACC);
  box-shadow: 0 0 0 1px var(--accent-color, #007ACC);
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
  resize: none; /* Prevent manual resize */
  overflow-y: auto; /* Scroll when exceeds max-height */
  min-height: 32px; /* Approximately 1 line */
  max-height: 150px; /* Approximately 7 lines */
  line-height: 20px;
  transition: border-color 0.2s ease, height 0.15s ease;
}

.repl-input:focus {
  border-color: var(--accent-color, #007ACC);
  box-shadow: 0 0 0 1px var(--accent-color, #007ACC);
}

.repl-input::placeholder {
  color: var(--text-muted, #6A6A6A);
}

/* Right Sidebar */
.right-sidebar {
  background: var(--bg-sidebar, #252526);
  height: 100%;
  width: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--border-primary, #3c3c3c);
  z-index: 20; /* Higher z-index to stay above console section */
}

/* Right sidebar placeholder when hidden */
.right-sidebar-placeholder {
  width: 100%;
  height: 100%;
  background: var(--bg-sidebar, #252526);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary, #858585);
  font-size: 14px;
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
  overflow: hidden; /* Let CsvViewer handle its own scrolling */
  display: flex;
  flex-direction: column;
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
  transition: background-color 0.15s ease;
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  /* Performance optimizations */
  will-change: left, right, background-color;
  transform: translateZ(0);
  backface-visibility: hidden;
}

.sidebar-resizer:hover {
  background: var(--accent-color, #007ACC);
}

.sidebar-resizer.resizing {
  background: var(--accent-color, #007ACC);
}

/* Arrow buttons for resizer */
.resizer-arrows {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 60;
}

.resizer-arrow {
  background: var(--bg-secondary, #2A2A2D);
  border: 1px solid var(--border-primary, #3c3c3c);
  border-radius: 4px;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary, #B5B5B5);
  transition: all 0.2s;
  width: 24px;
  height: 24px;
}

.resizer-arrow:hover {
  background: var(--accent-color, #007ACC);
  color: white;
  border-color: var(--accent-color, #007ACC);
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
  transform: translate3d(-50%, -50%, 0);
  width: 2px;
  height: 30px;
  background: var(--text-secondary, #858585);
  border-radius: 1px;
  opacity: 0.6;
  transition: opacity 0.15s ease;
  /* Performance optimizations */
  will-change: opacity;
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

/* Right Panel Control Arrows */
.right-panel-controls {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 100;
  pointer-events: none; /* Let clicks pass through except on buttons */
}

.right-panel-controls .control-arrow {
  pointer-events: auto;
  background: var(--bg-secondary, #2d2d30);
  border: 1px solid var(--border-primary, #3c3c3c);
  color: var(--text-primary, #cccccc);
  width: 24px;
  height: 24px;
  border-radius: 4px 0 0 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  opacity: 0.7;
}

.right-panel-controls .control-arrow:hover {
  background: var(--accent-color, #007ACC);
  color: white;
  opacity: 1;
  transform: translateX(-2px);
}

.right-panel-controls .control-arrow:active {
  transform: translateX(0);
}

/* Light theme support for control arrows */
[data-theme="light"] .right-panel-controls .control-arrow {
  background: #ffffff;
  border-color: #e0e0e0;
  color: #333333;
}

[data-theme="light"] .right-panel-controls .control-arrow:hover {
  background: #007ACC;
  color: white;
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

/* REPL Modal Styles */
.repl-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.repl-modal-content {
  width: 90%;
  max-width: 1200px;
  height: 80%;
  background: #1e1e1e;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.repl-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #2d2d30;
  border-bottom: 1px solid #3e3e42;
  border-radius: 8px 8px 0 0;
}

.repl-modal-header h3 {
  margin: 0;
  color: #d4d4d4;
  font-size: 18px;
}

.repl-close-btn {
  background: transparent;
  border: none;
  color: #d4d4d4;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.repl-close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.repl-modal-body {
  flex: 1;
  overflow: hidden;
  border-radius: 0 0 8px 8px;
}

/* REPL Mode Indicator in Console Header */
.repl-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #4ec9b0;
  border-radius: 50%;
  margin-left: 8px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Console action button active state */
.console-action-btn.active {
  background: var(--accent-color, #007ACC);
  color: white;
}

/* Main splitpanes container */
.main-splitpanes {
  height: 100%;
  width: 100%;
}

/* Hide old resizers since splitpanes handles them */
.sidebar-resizer {
  display: none !important;
}

/* Splitpanes Styling - for all splitpanes */
.splitpanes.default-theme .splitpanes__splitter {
  background-color: var(--border-primary, #3c3c3c);
  position: relative;
  z-index: 20;
}

/* Style vertical splitters (between sidebars and center) */
.main-splitpanes.splitpanes--vertical > .splitpanes__splitter {
  width: 8px;
  background-color: var(--border-primary, #3c3c3c);
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-splitpanes.splitpanes--vertical > .splitpanes__splitter:hover {
  background-color: var(--accent-color, #007ACC);
}

/* Add arrow indicators for vertical splitters */
.main-splitpanes.splitpanes--vertical > .splitpanes__splitter::before {
  content: '⋮';
  color: rgba(255, 255, 255, 0.3);
  font-size: 20px;
  font-weight: bold;
}

.main-splitpanes.splitpanes--vertical > .splitpanes__splitter:hover::before {
  color: rgba(255, 255, 255, 0.8);
}

/* Console horizontal splitter */
#center-frame .splitpanes--horizontal > .splitpanes__splitter {
  height: 8px;
  cursor: ns-resize;
  background-color: var(--border-primary, #3c3c3c);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

#center-frame .splitpanes--horizontal > .splitpanes__splitter:hover {
  background-color: var(--accent-color, #007ACC);
}

/* Add horizontal drag indicator */
#center-frame .splitpanes--horizontal > .splitpanes__splitter::before {
  content: '⋯';
  color: rgba(255, 255, 255, 0.3);
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 2px;
}

  #center-frame .splitpanes--horizontal > .splitpanes__splitter:hover::before {
    color: rgba(255, 255, 255, 0.8);
  }

/* Theme Support for Preview Panels and Tabs */

/* Light Theme */
[data-theme="light"] .right-sidebar {
  background: var(--bg-sidebar, #f3f3f3);
  border-left-color: var(--border-primary, #e0e0e0);
}

[data-theme="light"] .right-sidebar-placeholder {
  background: var(--bg-sidebar, #f3f3f3);
  color: var(--text-secondary, #6a6a6a);
}

[data-theme="light"] .preview-tabs {
  background: var(--bg-secondary, #e8e8e8);
  border-bottom-color: var(--border-primary, #d0d0d0);
}

[data-theme="light"] .preview-tab {
  color: var(--text-secondary, #616161);
}

[data-theme="light"] .preview-tab:hover {
  background: var(--bg-hover, #d4d4d4);
  color: var(--text-primary, #333333);
}

[data-theme="light"] .preview-tab.active {
  background: var(--bg-active, #ffffff);
  color: var(--text-primary, #333333);
  border-bottom-color: var(--accent-color, #0078d4);
}

[data-theme="light"] .preview-tab-add {
  color: var(--text-secondary, #616161);
}

[data-theme="light"] .preview-tab-add:hover {
  background: var(--bg-hover, #d4d4d4);
  color: var(--accent-color, #0078d4);
}

[data-theme="light"] .preview-content {
  background: var(--bg-primary, #ffffff);
}

[data-theme="light"] .image-preview-panel {
  background: var(--bg-pattern, #f8f8f8);
}

[data-theme="light"] .output-panel {
  background: var(--bg-primary, #ffffff);
  color: var(--text-primary, #333333);
}

[data-theme="light"] .pdf-preview-panel {
  background: var(--bg-primary, #ffffff);
}

/* High Contrast Theme */
[data-theme="high-contrast"] .right-sidebar {
  background: var(--bg-sidebar, #000000);
  border-left: 2px solid var(--border-primary, #ffffff);
}

[data-theme="high-contrast"] .right-sidebar-placeholder {
  background: var(--bg-sidebar, #000000);
  color: var(--text-secondary, #ffffff);
}

[data-theme="high-contrast"] .preview-tabs {
  background: var(--bg-secondary, #000000);
  border-bottom: 2px solid var(--border-primary, #ffffff);
}

[data-theme="high-contrast"] .preview-tab {
  color: var(--text-secondary, #ffffff);
  border: 1px solid transparent;
}

[data-theme="high-contrast"] .preview-tab:hover {
  background: var(--bg-hover, #1a1a1a);
  color: var(--text-primary, #ffffff);
  border-color: var(--accent-color, #ffff00);
}

[data-theme="high-contrast"] .preview-tab.active {
  background: var(--bg-active, #0f0f0f);
  color: var(--text-primary, #ffffff);
  border-color: var(--accent-color, #ffff00);
  border-bottom-color: var(--accent-color, #ffff00);
}

[data-theme="high-contrast"] .preview-tab-add {
  color: var(--text-secondary, #ffffff);
}

[data-theme="high-contrast"] .preview-tab-add:hover {
  background: var(--bg-hover, #1a1a1a);
  color: var(--accent-color, #ffff00);
}

[data-theme="high-contrast"] .preview-content {
  background: var(--bg-primary, #000000);
}

[data-theme="high-contrast"] .image-preview-panel {
  background: var(--bg-pattern, #0f0f0f);
}

[data-theme="high-contrast"] .output-panel {
  background: var(--bg-primary, #000000);
  color: var(--text-primary, #ffffff);
}

[data-theme="high-contrast"] .pdf-preview-panel {
  background: var(--bg-primary, #000000);
}

/* Fix layout */
#center-frame .splitpanes {
  height: 100%;
}

#center-frame .splitpanes__pane {
  overflow: hidden;
  /* Ensure no white gaps show; inherit dark background */
  background: var(--bg-primary, #1E1E1E);
}

.splitpanes__pane .editor-section,
.splitpanes__pane .console-section {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
