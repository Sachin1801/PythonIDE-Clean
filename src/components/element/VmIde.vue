<template>
  <div class="main-wrapper ide-wrapper ide-container">
    <TwoHeaderMenu class="two-header-menu"
      :consoleLimit="consoleLimit"
      :hasRunProgram="hasRunProgram"
      :currentUser="currentUser"
      @set-text-dialog="setTextDialog"
      @set-del-dialog="setDelDialog"
      @set-projs-dialog="setProjsDialog"
      v-on:run-item="runPathSelected"
      @stop-item="stop"
      @clear-console="clearConsole"
      @share-project="shareProject"
      @sign-in="handleSignIn"
      @open-upload-dialog="showUploadDialog = true"
      @download-file="downloadFile"
      @open-settings="showSettingsModal = true"
      @open-file-browser="openFileBrowser"
      @duplicate-file="duplicateFile"
      @save-as-file="saveAsFile"
      @open-move-dialog="openMoveDialog"
      @delete-file="deleteFileFromMenu"
      @delete-selected-file="deleteSelectedFile"
      @share-file="shareFile"
      @undo="handleUndo"
      @redo="handleRedo"
      @cut="handleCut"
      @copy="handleCopy"
      @paste="handlePaste"
      @find="handleFind"
      @replace="handleReplace"
      @comment="handleComment"
      @toggle-console="toggleConsole"
      @toggle-preview-panel="togglePreviewPanel"
      @toggle-sidebar="toggleLeftSidebar"
      @show-keyboard-shortcuts="showKeyboardShortcutsModal = !showKeyboardShortcutsModal"
    ></TwoHeaderMenu>
    
    <!-- Settings Modal -->
    <SettingsModal 
      v-model="showSettingsModal"
      @update-font-size="updateFontSize"
      @update-line-numbers="updateLineNumbers"
      @update-word-wrap="updateWordWrap"
      @update-auto-save="updateAutoSave"
      @update-auto-save-interval="updateAutoSaveInterval"
    />
    
    <!-- Keyboard Shortcuts Modal -->
    <KeyboardShortcutsModal 
      v-model="showKeyboardShortcutsModal"
    />
    
    <!-- Find/Replace Modal -->
    <FindReplaceModal 
      v-model="showFindReplaceModal"
      :mode="findReplaceMode"
    />
    
    <div id="total-frame" class="total-frame">
      <!-- Main Horizontal Splitpanes for Left/Center/Right -->
      <splitpanes :class="['default-theme', 'main-splitpanes', { 'has-right-content': previewTabs.length > 0 }]">
        <!-- Left Sidebar Pane - Always present in DOM -->
        <pane :size="leftSidebarSize" :min-size="leftSidebarMinSize" :max-size="leftSidebarMaxSize">
          <div id="left-sidebar" class="left-sidebar" v-show="leftSidebarVisible && windowWidth > 900">
            <ProjTree 
              v-on:get-item="getFile"
              @get-item-right-panel="getFileForRightPanel"
              @context-menu="showContextMenu"
              @rename-item="handleRenameItem"
              @delete-item="handleDeleteItem"
              @download-item="handleDownloadItem"
              @new-file="handleNewFileFromTree"
              @new-folder="handleNewFolderFromTree"
            ></ProjTree>
          </div>
        </pane>
        
        <!-- Center Content Pane -->
        <pane :size="centerSize" :min-size="30">
          <div id="center-frame" class="center-frame">
            <!-- Fullscreen Preview -->
            <FullscreenPreview 
              @open-in-right-panel="getFileForRightPanel" 
            />
            <!-- Nested Horizontal Splitpanes for Editor/Console -->
            <splitpanes horizontal class="default-theme">
              <!-- Editor Pane -->
              <pane :size="editorPaneSize" :min-size="5" :max-size="95">
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
            <template v-for="(item, index) in ideInfo.codeItems" :key="`${item.projectName || 'default'}:${item.path}`">
              <IdeEditor 
                :codeItem="item"
                :codeItemIndex="index"
                :consoleLimit="consoleLimit"
                :wordWrap="wordWrap"
                @run-item="runPathSelected"
                v-if="isSelectedFile(item)" 
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
              <!-- Collapsed state: Only up arrow -->
              <button class="console-expand-arrow" 
                      @click="handleConsoleUpArrow" 
                      title="Open console"
                      v-if="consoleMode === 'collapsed'">
                <ChevronUp :size="16" />
              </button>
              
              <!-- Normal state: Both up arrow (maximize) and down arrow (collapse) -->
              <button class="console-expand-arrow" 
                      @click="handleConsoleUpArrow" 
                      title="Maximize console"
                      v-if="consoleMode === 'normal'">
                <ChevronUp :size="16" />
              </button>
              <button class="console-expand-arrow" 
                      @click="handleConsoleDownArrow" 
                      title="Collapse console"
                      v-if="consoleMode === 'normal'">
                <ChevronDown :size="16" />
              </button>
              
              <!-- Maximized state: Restore button and down arrow -->
              <button class="console-expand-arrow" 
                      @click="handleConsoleRestore" 
                      title="Restore console"
                      v-if="consoleMode === 'maximized'">
                <Minimize2 :size="16" />
              </button>
              <button class="console-expand-arrow" 
                      @click="handleConsoleDownArrow" 
                      title="Collapse console"
                      v-if="consoleMode === 'maximized'">
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
                  <!-- Regular output (filter out prompts) -->
                  <pre v-if="(result.type === 'output' || result.type === 'text') && !isPromptOutput(result)" class="console-text">{{ result.text || result.content || result }}</pre>
                  
                  <!-- Error output -->
                  <pre v-else-if="result.type === 'error'" class="console-error">{{ result.text || result.content || result }}</pre>
                  
                  <!-- Input prompt -->
                  <div v-else-if="result.type === 'input' || result.type === 'input-prompt'" class="console-input-prompt">
                    <span>{{ result.text || result.content || result }}</span>
                  </div>
                  
                  <!-- System message -->
                  <pre v-else-if="result.type === 'system'" class="console-system">{{ result.text || result.content || result }}</pre>
                  
                  <!-- REPL prompt -->
                  <span v-else-if="result.type === 'repl-prompt'" class="console-repl-prompt">{{ result.text || '>>> ' }}</span>
                  
                  <!-- User input in REPL -->
                  <pre v-else-if="result.type === 'user-input'" class="console-user-input" v-html="highlightPythonCode(result.text || result.content || result)"></pre>
                  
                  <!-- REPL input (properly formatted with prompt) -->
                  <div v-else-if="result.type === 'repl-input'" class="console-repl-entry">
                    <!-- Handle multiline input - only first line shows >>>, others have no prompt (like IDLE) -->
                    <template v-if="isMultilineCode(result.content || result.text || result)">
                      <div v-for="(line, index) in splitCodeLines(result.content || result.text || result)" 
                           :key="'line-' + index" 
                           class="console-repl-line">
                        <!-- Only show prompt on first line, like Python IDLE -->
                        <span v-if="index === 0" class="console-repl-prompt">{{ result.prompt || '>>> ' }}</span>
                        <pre class="console-repl-input" :class="{ 'no-prompt': index > 0 }" v-html="highlightPythonCode(line)"></pre>
                      </div>
                    </template>
                    
                    <!-- Single line input -->
                    <div v-else class="console-repl-line">
                      <span class="console-repl-prompt">{{ result.prompt || '>>> ' }}</span>
                      <pre class="console-repl-input" v-html="highlightPythonCode(result.content || result.text || result)"></pre>
                    </div>
                  </div>
                  
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
            <div v-if="isReplMode || (ideInfo.consoleSelected && ideInfo.consoleSelected.waitingForReplInput)" class="repl-section">
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
         <pane :size="rightSidebarSize" :min-size="rightSidebarMinSize" :max-size="rightSidebarMaxSize" :push-other-panes="false">
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
                  
                  <!-- Media Preview Panel (Images and PDFs) -->
                  <div v-else-if="tab.type === 'image' || tab.type === 'pdf'" class="media-preview-panel">
                    <MediaViewer :codeItem="getMediaCodeItem(tab)" :codeItemIndex="0" />
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
    <DialogNewFile v-if="showNewFileDialog" v-model="showNewFileDialog" @file-created="handleFileCreated"></DialogNewFile>
    <DialogNewFolder v-if="showNewFolderDialog" v-model="showNewFolderDialog" @folder-created="handleFolderCreated"></DialogNewFolder>
    <DialogFileBrowser 
      v-model="showFileBrowserDialog" 
      :mode="fileBrowserMode"
      :fileToMove="fileToMove"
      @open-file="handleOpenFile"
      @move-file="handleMoveFile"
    />
    
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
    
    <!-- Login Modal -->
    <LoginModal 
      :visible="showLoginModal"
      @close="showLoginModal = false"
      @login-success="handleLoginSuccess"
    />
  </div>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';
import * as types from '../../store/mutation-types';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ChevronLeft, ChevronRight, ChevronUp, ChevronDown, Minimize2 } from 'lucide-vue-next';
import TwoHeaderMenu from './pages/ide/TwoHeaderMenu';
import CodeTabs from './pages/ide/CodeTabs';
import HybridConsole from './pages/ide/HybridConsole';
import ConsoleTabs from './pages/ide/ConsoleTabs';
import ProjTree from './pages/ide/ProjTree';
import IdeEditor from './pages/ide/IdeEditor';
import PythonREPL from './pages/ide/PythonREPL';
import DialogProjs from './pages/ide/dialog/DialogProjs';
import DialogText from './pages/ide/dialog/DialogText';
import DialogDelete from './pages/ide/dialog/DialogDelete';
import DialogUpload from './pages/ide/dialog/DialogUpload';
import DialogNewFile from './pages/ide/dialog/DialogNewFile';
import DialogNewFolder from './pages/ide/dialog/DialogNewFolder';
import DialogFileBrowser from './pages/ide/dialog/DialogFileBrowser';
import CsvViewer from './pages/ide/CsvViewer';
import MediaViewer from './pages/ide/editor/MediaViewer';
import SettingsModal from './pages/ide/SettingsModal';
import KeyboardShortcutsModal from './pages/ide/KeyboardShortcutsModal';
import FindReplaceModal from './pages/ide/FindReplaceModal';
import FullscreenPreview from './pages/ide/FullscreenPreview';
import DualModeREPL from './DualModeREPL';
import LoginModal from './LoginModal';
const path = require('path');

export default {
  data() {
    return {
      showDeleteDialog: false,
      showFileDialog: false,
      showProjsDialog: false,
      showUploadDialog: false,
      showNewFileDialog: false,
      showNewFolderDialog: false,
      showFileBrowserDialog: false,
      showLoginModal: false,
      fileBrowserMode: 'open',
      fileToMove: null,
      showSettingsModal: false,
      showKeyboardShortcutsModal: false,
      showFindReplaceModal: false,
      findReplaceMode: 'find',
      showREPL: false,
      isReplMode: false,  // Toggle between normal console and REPL mode
      replSessionId: null,  // Track active REPL session
      showCover: true,
      showContextMenu: false,
      contextMenuPosition: { x: 0, y: 0 },
      contextMenuTarget: null,
      windowWidth: window.innerWidth,  // Track window width for responsive behavior
      leftSidebarVisible: true,
      currentUser: null,
      
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
      
      // Per-file console state management
      fileConsoleStates: {}, // Map of filePath -> { mode, expanded, maximized, consoleId }
      activeFilePath: null, // Currently active file path
      
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
      pyodideInitialized: false,
      
      // WebSocket handler reference (non-reactive)
      wsMessageHandler: null
    }
  },
  mixins: [DualModeREPL],
  components: {
    Splitpanes,
    Pane,
    TwoHeaderMenu,
    CodeTabs,
    HybridConsole,
    ConsoleTabs,
    ProjTree,
    IdeEditor,
    LoginModal,
    PythonREPL,
    DialogProjs,
    DialogText,
    DialogDelete,
    DialogUpload,
    DialogNewFile,
    DialogNewFolder,
    DialogFileBrowser,
    CsvViewer,
    MediaViewer,
    SettingsModal,
    KeyboardShortcutsModal,
    FindReplaceModal,
    FullscreenPreview,
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

    // Check if user is already logged in
    const sessionId = localStorage.getItem('session_id');
    const username = localStorage.getItem('username');
    
    if (sessionId && username) {
      console.log('🔑 [VmIde] Found existing session for:', username);
      this.currentUser = {
        username: username,
        role: localStorage.getItem('role'),
        full_name: localStorage.getItem('full_name'),
        session_id: sessionId
      };
      
      // Initialize WebSocket only if logged in
      try {
        console.log('🔌 [VmIde] Initializing WebSocket with authentication...');
        if (!this.wsInfo || !this.wsInfo.rws) {
          this.$store.dispatch('websocket/init', {});
          console.log('✅ [VmIde] WebSocket initialization dispatched');
        } else {
          console.log('ℹ️ [VmIde] WebSocket already initialized');
        }
      } catch (error) {
        console.error('❌ [VmIde] Error initializing WebSocket:', error);
      }
    } else {
      console.log('🔒 [VmIde] No session found, user needs to login');
      // Don't initialize WebSocket until after login
      // User will click Sign In button to show login modal
      return;
    }

    // Test image removed - right panel will only show when actual content is loaded
    
    // Set initial state
    this.rightPanelMode = 'closed';  // Start with right panel closed
    this.consoleMode = 'collapsed';  // Start with console collapsed
    
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
    // Only start WebSocket timer if logged in
    if (sessionId && username) {
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
    } // Close the if (sessionId && username) block
    
    window.addEventListener('resize', this.resize);
    
    // Apply saved editor settings on mount
    this.$nextTick(() => {
      this.applyInitialEditorSettings();
    });
  },
  
  beforeUnmount() {
    window.removeEventListener('resize', this.validateLayout);
    window.removeEventListener('resize', this.resize);
    
    // Clean up WebSocket handler - no need to remove since WebSocket module handles it
    if (this.wsMessageHandler) {
      // The WebSocket module will clean up event listeners when the connection closes
      this.wsMessageHandler = null;
    }
    
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
      // Check if we're on a small screen
      if (this.windowWidth <= 900) {
        return 0;  // Return 0 for mobile to completely hide
      }
      
      // Calculate appropriate size based on window width
      let sidebarSize = 20; // Default 20%
      
      // Adjust for medium screens to prevent gaps
      if (this.windowWidth <= 1400 && this.windowWidth > 1200) {
        // Calculate exact percentage to fill the pane properly
        const pixelWidth = Math.min(250, this.windowWidth * 0.2);
        sidebarSize = (pixelWidth / this.windowWidth) * 100;
      } else if (this.windowWidth <= 1200) {
        sidebarSize = (180 / this.windowWidth) * 100;
      }
      
      // Use 0.1 instead of 0 to avoid null reference errors in splitpanes
      return this.leftSidebarVisible ? sidebarSize : 0.1;
    },
    leftSidebarMinSize() {
      // On mobile, set min size to 0 to allow complete hiding
      return this.windowWidth <= 900 ? 0 : 0.1;
    },
    leftSidebarMaxSize() {
      // On mobile, set max size to 0 to prevent any expansion
      if (this.windowWidth <= 900) return 0;
      
      // Adjust max size based on window width to prevent gaps
      if (this.windowWidth <= 1400 && this.windowWidth > 1200) {
        return 30; // Limit to 30% at medium screens
      }
      return 40;
    },
    rightSidebarSize() {
      // Check if we're on a small screen
      if (this.windowWidth <= 900) {
        return 0;  // Return 0 for mobile to completely hide
      }
      
      // For screens between 900-1200px, hide right sidebar completely
      if (this.windowWidth <= 1200) {
        return 0;  // Return 0 to completely hide and give space to center
      }
      
      // If no preview tabs, return 0 to not take any space
      if (this.previewTabs.length === 0) {
        return 0;  // Return 0 when no content to show
      }
      
      // Handle different states based on new mode system
      if (this.rightPanelMode === 'closed') {
        return 0;  // Return 0 when closed to not take space
      }
      if (this.rightPanelMode === 'expanded') {
        // Take 70% of non-sidebar space when expanded
        const leftSize = this.leftSidebarVisible ? 20 : 0;
        return 100 - leftSize - 10; // Leave 10% for minimal editor
      }
      // Normal state - 30%
      return 30;
    },
    rightSidebarMinSize() {
      // Allow complete hiding on screens up to 1200px
      return this.windowWidth <= 1200 ? 0 : 0.1;
    },
    rightSidebarMaxSize() {
      // Prevent expansion on smaller screens
      if (this.windowWidth <= 900) return 0;
      if (this.windowWidth <= 1200) return 0; // Also prevent expansion on medium screens
      return 50;
    },
    centerSize() {
      // On small screens, center takes full width
      if (this.windowWidth <= 900) {
        return 100;
      }
      
      // For screens between 900-1200px, account for left sidebar only
      if (this.windowWidth <= 1200) {
        const leftSize = this.leftSidebarVisible ? 
          (this.windowWidth <= 1200 ? (180 / this.windowWidth) * 100 : 20) : 0;
        return 100 - leftSize; // Center takes all remaining space
      }
      
      // Calculate center size based on what's visible
      const leftSize = this.leftSidebarVisible ? this.leftSidebarSize : 0;
      const rightSize = this.rightSidebarSize;  // Access as property, not function
      
      // If right sidebar has no content or is 0, give that space to center
      if (rightSize === 0) {
        return 100 - leftSize;
      }
      
      return Math.max(30, 100 - leftSize - rightSize); // Ensure minimum 30% for center
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
    // Watch for preview tabs changes to manage right panel state
    'previewTabs.length': function(newLength, oldLength) {
      // When all tabs are closed, ensure right panel is properly closed
      if (newLength === 0 && oldLength > 0) {
        this.rightPanelMode = 'closed';
        this.rightSidebarVisible = false;
      }
    },
    
    // Watch for tab changes to save/restore console state
    'ideInfo.codeSelected': function(newFile, oldFile) {
      // Only handle console state changes when actually switching between different files
      if (newFile && oldFile && newFile.path && oldFile.path && newFile.path !== oldFile.path) {
        this.handleTabChange(newFile, oldFile);
      } else if (newFile && !oldFile) {
        // First file opened
        this.activeFilePath = newFile.path;
        this.loadFileConsoleState(newFile.path);
      }
    },
    
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
    applyInitialEditorSettings() {
      // Apply saved font size if exists
      const savedFontSize = localStorage.getItem('fontSize');
      if (savedFontSize) {
        this.updateFontSize(savedFontSize);
      }
      
      // Apply saved line numbers setting if exists
      const savedLineNumbers = localStorage.getItem('showLineNumbers');
      if (savedLineNumbers !== null) {
        this.updateLineNumbers(savedLineNumbers === 'true');
      }
    },
    updateFontSize(value) {
      // Update font size in all CodeMirror editors
      const fontSize = parseInt(value) + 'px';
      
      // Update all existing CodeMirror instances
      const editors = document.querySelectorAll('.CodeMirror');
      editors.forEach(editor => {
        if (editor.CodeMirror) {
          editor.style.fontSize = fontSize;
          editor.CodeMirror.refresh();
        }
      });
      
      // Update CSS for future editors
      const style = document.getElementById('codemirror-font-size') || document.createElement('style');
      style.id = 'codemirror-font-size';
      style.innerHTML = `.CodeMirror { font-size: ${fontSize} !important; } .CodeMirror pre { font-size: ${fontSize} !important; }`;
      if (!document.getElementById('codemirror-font-size')) {
        document.head.appendChild(style);
      }
      
      // Store in localStorage for persistence
      localStorage.setItem('editorFontSize', value);
    },
    updateLineNumbers(value) {
      // Update line numbers in all CodeMirror editors
      const editors = document.querySelectorAll('.CodeMirror');
      editors.forEach(editor => {
        if (editor.CodeMirror) {
          editor.CodeMirror.setOption('lineNumbers', value);
        }
      });
      
      // Store in localStorage for persistence
      localStorage.setItem('editorLineNumbers', value);
      
      // Also update the store for new editors
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
      // Add welcome message for REPL-only mode
      if (this.ideInfo.consoleSelected) {
        this.addReplOutput('Python Interactive Shell - Enter Python code and press Enter to execute', 'system');
        this.addReplOutput('Use Shift+Enter for multiline code', 'system');
      }
      
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
      // Add a handler for WebSocket messages using the store's mutation
      try {
        if (!this.wsInfo || !this.wsInfo.rws) {
          console.log('WebSocket not ready, retrying...');
          setTimeout(() => this.setupWebSocketHandler(), 500);
          return;
        }
        
        // Create a new message handler
        const wsMessageHandler = (event) => {
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
              console.log('🎯 REPL message matched - routing to REPL handler only!');
              this.handleReplResponse(message);  // Call the existing method
              // CRITICAL: Don't let this message be processed by normal handlers to prevent duplicate output
              return;  // Early return to prevent further processing
            }
          } catch (e) {
            // Not JSON or parsing error, ignore
          }
          
        };
        
        // Use the store's addEventListener mutation to properly add the listener
        this.$store.commit('websocket/addEventListener', {
          wsKey: 'default',
          type: 'message', 
          listener: wsMessageHandler
        });
        
        // Store reference for cleanup
        this.wsMessageHandler = wsMessageHandler;
        
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
      console.log('🎯 [REPL] Processing REPL response:', dict);
      console.log('🎯 [REPL] Response code:', dict?.code, 'Data keys:', dict?.data ? Object.keys(dict.data) : 'no data');
      
      if (!dict) return;
      
      // Handle different response codes
      if (dict.code === 0 || dict.code === '0') {
        // Success response with output
        if (dict.data) {
          if (dict.data.stdout) {
            // Filter out REPL prompts from stdout but allow other content
            const output = dict.data.stdout;
            console.log('🔍 [REPL] Processing stdout:', JSON.stringify(output));
            
            // Only filter pure REPL prompts, allow everything else
            if (!output.match(/^(>>>|\.\.\.)\s*$/) && output.trim() !== '') {
              this.addReplOutput(output, 'output');
            } else if (output.trim() === '') {
              // For empty lines, still add them to maintain formatting
              this.addReplOutput('', 'output');
            }
          }
          if (dict.data.stderr) {
            this.addReplOutput(dict.data.stderr, 'error');
          }
          if (dict.data.output) {
            this.addReplOutput(dict.data.output, 'output');
          }
        }
      } else if (dict.code === 2000) {
        // Input request from Python script
        console.log('Input request received:', dict.data);
        if (dict.data && dict.data.prompt) {
          // Show the input prompt
          this.addReplOutput(dict.data.prompt, 'output');
          // The input field should already be visible in the console
        }
      } else if (dict.code === 5000) {
        // Entering REPL mode after script execution
        console.log('Entering REPL mode after script execution');
        this.isReplMode = true;
        // REPL mode starting - no extra messages needed
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
      if (this.consoleMode === 'collapsed') {
        // From collapsed, go to normal (30%)
        this.consoleMode = 'normal';
        this.consoleExpanded = true;
        this.consoleMaximized = false;
        this.updateEditorHeight();
      } else if (this.consoleMode === 'normal') {
        // From normal, go to maximized
        this.consolePreviousMode = 'normal';
        this.consoleMode = 'maximized';
        this.consoleMaximized = true;
        this.consoleExpanded = true;
        this.updateEditorHeight();
      }
    },
    
    handleConsoleDownArrow() {
      // From either normal or maximized, go to collapsed
      if (this.consoleMode === 'normal' || this.consoleMode === 'maximized') {
        this.consoleMode = 'collapsed';
        this.consoleExpanded = false;
        this.consoleMaximized = false;
        this.updateEditorHeight();
      }
    },
    
    handleConsoleRestore() {
      if (this.consoleMode === 'maximized') {
        this.consoleMode = this.consolePreviousMode || 'normal';
        this.consoleMaximized = false;
        this.consoleExpanded = (this.consoleMode === 'normal');
        this.updateEditorHeight();
      }
    },
    
    // Per-file console management
    handleTabChange(newFile, oldFile) {
      // CRITICAL: Stop REPL session when switching files
      if (this.isReplMode && this.replSessionId) {
        console.log('🔄 [VmIde] File switched - stopping REPL session');
        this.stopReplSession();
      }
      
      // Save current console state for the old file
      if (oldFile && oldFile.path && this.activeFilePath) {
        this.saveFileConsoleState(this.activeFilePath);
      }
      
      // Load console state for the new file
      if (newFile && newFile.path) {
        this.activeFilePath = newFile.path;
        this.loadFileConsoleState(newFile.path);
      }
    },
    
    saveFileConsoleState(filePath) {
      // Only save if it's a Python file
      if (!filePath || !filePath.endsWith('.py')) return;
      
      // Find the console item for this file
      const fileConsole = this.ideInfo.consoleItems.find(
        item => item.path === filePath
      );
      
      // Save the current console state
      this.fileConsoleStates[filePath] = {
        mode: this.consoleMode,
        expanded: this.consoleExpanded,
        maximized: this.consoleMaximized,
        consoleId: fileConsole ? fileConsole.id : null,
        hasOutput: fileConsole && fileConsole.resultList && fileConsole.resultList.length > 0
      };
    },
    
    loadFileConsoleState(filePath) {
      // Only handle Python files
      if (!filePath || !filePath.endsWith('.py')) {
        // For non-Python files, hide console
        this.consoleMode = 'collapsed';
        this.consoleExpanded = false;
        this.consoleMaximized = false;
        return;
      }
      
      const savedState = this.fileConsoleStates[filePath];
      
      if (savedState) {
        // Restore saved console state
        this.consoleMode = savedState.mode || 'collapsed';
        this.consoleExpanded = savedState.expanded || false;
        this.consoleMaximized = savedState.maximized || false;
        
        // Find and select the console for this file if it exists
        if (savedState.consoleId && this.ideInfo.consoleItems) {
          const fileConsole = this.ideInfo.consoleItems.find(
            item => item.id === savedState.consoleId
          );
          if (fileConsole) {
            // Use nextTick to avoid interfering with tab switching
            this.$nextTick(() => {
              this.$store.commit('ide/setConsoleSelected', fileConsole);
            });
          }
        }
      } else {
        // New file - start with collapsed console
        this.consoleMode = 'collapsed';
        this.consoleExpanded = false;
        this.consoleMaximized = false;
      }
      
      // Use nextTick to avoid blocking UI updates
      this.$nextTick(() => {
        this.updateEditorHeight();
      });
    },
    
    getOrCreateFileConsole(filePath) {
      // Safety check - ensure filePath is valid
      if (!filePath || typeof filePath !== 'string') {
        console.error('getOrCreateFileConsole: Invalid file path provided:', filePath);
        return null;
      }
      
      // Find existing console for this file
      let fileConsole = this.ideInfo.consoleItems.find(
        item => item.path === filePath
      );
      
      if (!fileConsole) {
        // Create new console item for this file
        const fileName = filePath.split('/').pop();
        const newConsoleItem = {
          id: this.ideInfo.consoleId,
          path: filePath,
          name: fileName,
          run: false,
          resultList: [],
          waitingForInput: false,
          inputPrompt: ''
        };
        this.$store.commit('ide/addConsoleItem', newConsoleItem);
        this.$store.commit('ide/setConsoleId', this.ideInfo.consoleId + 1);
        
        // Return the newly created item from the store
        fileConsole = this.ideInfo.consoleItems.find(
          item => item.id === newConsoleItem.id
        );
      }
      
      return fileConsole;
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
        
        // Hide sidebar and set to closed mode if no tabs left
        if (this.previewTabs.length === 0) {
          this.rightSidebarVisible = false;
          this.rightPanelMode = 'closed';
        }
      }
    },
    
    addPreviewTab(type, title, content, filePath, projectName) {
      console.log('[addPreviewTab] Adding tab:', {
        type: type,
        title: title,
        filePath: filePath,
        projectName: projectName,
        hasContent: !!content
      });
      
      // Check if tab already exists for this file
      const existingTab = this.previewTabs.find(tab => tab.filePath === filePath && tab.projectName === projectName);
      
      if (existingTab) {
        // Tab already exists, just switch to it
        this.selectedPreviewTab = existingTab.id;
        
        // Update content if it has changed
        if (existingTab.content !== content) {
          // Clean up old blob URL if it exists
          if (existingTab.type === 'pdf' && existingTab.content && existingTab.content.startsWith('blob:')) {
            URL.revokeObjectURL(existingTab.content);
          }
          existingTab.content = content;
        }
      } else {
        // Create new tab with projectName
        const id = `${type}-${++this.previewTabCounter}`;
        this.previewTabs.push({ id, type, title, content, filePath, projectName });
        this.selectedPreviewTab = id;
      }
      
      // Make sure right sidebar is visible and in normal mode
      // Force the panel to open if it was closed
      if (this.rightPanelMode === 'closed' || !this.rightSidebarVisible) {
        this.rightPanelMode = 'normal';
        this.rightSidebarVisible = true;
        
        // Force Vue to update the view
        this.$nextTick(() => {
          // Ensure the panel is actually visible after the next render cycle
          if (!this.rightSidebarVisible) {
            this.rightSidebarVisible = true;
          }
        });
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
      // Ensure we have a valid fileName
      if (!fileInfo || !fileInfo.fileName) {
        console.error('[downloadFile] Invalid fileInfo:', fileInfo);
        ElMessage.error('Cannot download: invalid file information');
        return;
      }
      
      // Check if it's a binary file
      const binaryExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.pdf', '.zip', '.tar', '.gz'];
      const isBinary = binaryExtensions.some(ext => fileInfo.fileName.toLowerCase().endsWith(ext));
      
      this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
        projectName: fileInfo.projectName,
        filePath: fileInfo.filePath,
        binary: isBinary,
        callback: (dict) => {
          console.log('[downloadFile] Response:', { code: dict.code, hasData: !!dict.data, dataKeys: dict.data ? Object.keys(dict.data) : [] });
          
          if (dict.code == 0) {
            // Get the actual content - it might be in dict.data.content or dict.data
            let fileContent = dict.data?.content || dict.data;
            
            // For binary files, ensure we have valid base64 data
            let blob;
            if (isBinary) {
              try {
                // Check if fileContent is an object with content property
                if (typeof fileContent === 'object' && fileContent.content) {
                  fileContent = fileContent.content;
                }
                
                // Validate base64 string
                if (typeof fileContent !== 'string') {
                  throw new Error('Binary content is not a string');
                }
                
                // Remove any data URL prefix if present
                if (fileContent.includes(',')) {
                  fileContent = fileContent.split(',')[1];
                }
                
                // Decode base64 to binary
                const binaryString = atob(fileContent);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                  bytes[i] = binaryString.charCodeAt(i);
                }
                blob = new Blob([bytes], { type: 'application/octet-stream' });
              } catch (e) {
                console.error('[downloadFile] Error decoding binary data:', e);
                ElMessage.error('Failed to decode file data: ' + e.message);
                return;
              }
            } else {
              // Text file
              blob = new Blob([fileContent], { type: 'text/plain' });
            }
            
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
    handleFileCreated(data) {
      // Handle file creation from new file dialog
      console.log('[handleFileCreated] File created:', data);
      
      if (data && data.path && data.projectName) {
        // Open the newly created file
        this.getFile(data.path, true, data.projectName);
      }
      
      // Refresh the project tree
      this.refreshProjectTree();
    },
    handleFolderCreated(data) {
      // Handle folder creation from new folder dialog
      console.log('[handleFolderCreated] Folder created:', data);
      
      // Refresh the project tree
      this.refreshProjectTree();
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
    isSelectedFile(item) {
      // Check if this file is the currently selected one
      // Compare both path and projectName to ensure uniqueness
      return this.ideInfo.codeSelected && 
             this.ideInfo.codeSelected.path === item.path &&
             this.ideInfo.codeSelected.projectName === item.projectName;
    },
    getParentData(path) {
      // First try to use treeRef's current node
      if (this.ideInfo.treeRef && this.ideInfo.treeRef.currentNode && this.ideInfo.treeRef.currentNode.parent) {
        return this.ideInfo.treeRef.currentNode.parent.data;
      }
      
      // If we have multi-root data, search through all projects
      if (this.ideInfo.multiRootData && this.ideInfo.multiRootData.children) {
        for (let project of this.ideInfo.multiRootData.children) {
          const parent = this.findParentInTree(project, path);
          if (parent) return parent;
        }
      }
      
      // Fall back to current project data
      if (this.ideInfo.currProj && this.ideInfo.currProj.data) {
        return this.findParentInTree(this.ideInfo.currProj.data, path);
      }
      
      return null;
    },
    
    findParentInTree(node, targetPath) {
      if (!node || !node.children) return null;
      
      // Check if this node is the parent
      for (let child of node.children) {
        if (child.path === targetPath) {
          return node;
        }
      }
      
      // Recursively search children
      for (let child of node.children) {
        if (targetPath.startsWith(child.path + '/') || child.path === targetPath) {
          const found = this.findParentInTree(child, targetPath);
          if (found) return found;
        }
      }
      
      return null;
    },
    isFileExist(name, isCreate) {
      let exist = false;
      
      // Check if nodeSelected exists
      if (!this.ideInfo.nodeSelected) {
        return false;
      }
      
      if (isCreate) {
        // Check if children exists before using some
        exist = this.ideInfo.nodeSelected.children && 
                this.ideInfo.nodeSelected.children.some(item => item.name === name);
      }
      else {
        // For rename, check siblings
        const parentData = this.getParentData(this.ideInfo.nodeSelected.path);
        if (parentData && parentData.children) {
          exist = parentData.children.some(item => item.name === name);
        }
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
      
      // Get current username from localStorage
      const username = localStorage.getItem('username');
      
      // Build list of projects to load - use actual project names from the server
      const projectsToLoad = [];
      
      // Check for user's personal directory (e.g., "Local/sa9082")
      const userProject = this.ideInfo.projList.find(p => p.name === `Local/${username}`);
      if (userProject) {
        projectsToLoad.push(userProject.name);
      }
      
      // Add other standard projects if they exist
      const standardProjects = ['Lecture Notes', 'Assignments', 'Tests'];
      standardProjects.forEach(proj => {
        if (this.ideInfo.projList.some(p => p.name === proj)) {
          projectsToLoad.push(proj);
        }
      });
      
      console.log('📋 [loadAllDefaultProjects] Projects to load:', projectsToLoad);
      console.log('📋 [loadAllDefaultProjects] Available projects:', this.ideInfo.projList);
      
      if (projectsToLoad.length === 0) {
        console.warn('⚠️ [loadAllDefaultProjects] No projects to load');
        return;
      }
      
      const loadedProjects = [];
      let loadCount = 0;
      
      projectsToLoad.forEach(projectName => {
        console.log(`🔍 [loadAllDefaultProjects] Loading project: ${projectName}`);
        
        this.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
          projectName: projectName,
          callback: (dict) => {
            console.log(`📥 [loadAllDefaultProjects] Response for ${projectName}:`, dict);
            if (dict.code == 0) {
              loadedProjects.push(dict.data);
              loadCount++;
              
              // When all projects are loaded, combine them
              if (loadCount === projectsToLoad.length) {
                console.log('✅ [loadAllDefaultProjects] All projects loaded:', loadedProjects);
                self.$store.commit('ide/handleMultipleProjects', loadedProjects);
                // Also set the user's project as current
                const userProjectData = loadedProjects.find(p => p.name === `Local/${username}`);
                if (userProjectData) {
                  self.$store.commit('ide/handleProject', userProjectData);
                } else if (loadedProjects.length > 0) {
                  // Fallback to first project if user project not found
                  self.$store.commit('ide/handleProject', loadedProjects[0]);
                }
              }
            } else {
              console.error(`❌ [loadAllDefaultProjects] Failed to load ${projectName}:`, dict);
              loadCount++; // Still increment to avoid hanging
            }
          }
        });
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
              self.getFile(self.ideInfo.currProj.config.openList[i], false, self.ideInfo.currProj.data.name);
            }
          }
        }
      });
    },
    getFile(path, save, projectName, openInPanel = false) {
      const self = this;
      
      console.log('[getFile] Called with:', {
        path: path,
        save: save,
        projectName: projectName,
        openInPanel: openInPanel
      });
      
      // Determine the project name - from parameter, current selection, or current project
      const actualProjectName = projectName || 
                               (this.ideInfo.nodeSelected && this.ideInfo.nodeSelected.projectName) ||
                               this.ideInfo.currProj?.data?.name ||
                               this.ideInfo.currProj?.config?.name;
      
      // Check if it's a media or data file
      const mediaExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.pdf'];
      const dataExtensions = ['.csv'];
      const isMediaFile = mediaExtensions.some(ext => path.toLowerCase().endsWith(ext));
      const isDataFile = dataExtensions.some(ext => path.toLowerCase().endsWith(ext));
      
      // If it's a preview file and openInPanel is false, open in fullscreen
      if ((isMediaFile || isDataFile) && !openInPanel) {
        // Open preview files in fullscreen mode by default
        this.openFullscreenPreview(path, actualProjectName);
        return;
      }
      
      // Otherwise, handle normally (open in panel if preview file and openInPanel is true)
      if (isMediaFile) {
        // For media files, add tab without preloading content
        // MediaViewer component will handle loading with retry logic
        const fileName = path.split('/').pop();
        const fileExt = path.toLowerCase().split('.').pop();
        const previewType = fileExt === 'pdf' ? 'pdf' : 'image';
        
        console.log('[getFile] Adding media file tab:', {
          originalPath: path,
          fileName: fileName,
          fileExt: fileExt,
          actualProjectName: actualProjectName
        });
        
        // Add to preview tabs without content - MediaViewer will load it
        self.addPreviewTab(previewType, fileName, null, path, actualProjectName);
        
        // Still update the file tree selection
        if (save !== false) {
          self.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
        }
      } else if (isDataFile) {
        // For CSV files, fetch content and display in preview panel
        const fileName = path.split('/').pop();
        
        this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
          projectName: actualProjectName,
          filePath: path,
          callback: (response) => {
            if (response.code === 0 && response.data) {
              // Parse CSV content and add to preview tabs
              const csvContent = response.data.content || response.data;
              self.addPreviewTab('data', fileName, csvContent, path, actualProjectName);
              
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
        // For regular files (like .py), close any fullscreen preview first
        if (this.ideInfo.fullscreenPreview && this.ideInfo.fullscreenPreview.active) {
          this.$store.commit('ide/closeFullscreenPreview');
        }
        
        // Then fetch content as before
        // Extract relative path from the full path
        let relativePath = path;
        if (actualProjectName && path.startsWith(actualProjectName + '/')) {
          relativePath = path.substring(actualProjectName.length + 1);
        }
        
        console.log('[getFile] Getting file with relative path:', {
          originalPath: path,
          projectName: actualProjectName,
          relativePath: relativePath
        });
        
        this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
          projectName: actualProjectName, // Ensure project name is passed
          filePath: relativePath,
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
    getFileForRightPanel(path, projectName) {
      // Open preview files specifically in the right panel
      // This is called from context menu "Open in Right Panel" option
      this.getFile(path, false, projectName, true); // openInPanel = true
    },
    
    getMediaCodeItem(tab) {
      // Create a codeItem object that MediaViewer expects
      // Use the tab's projectName if available, otherwise fall back to current project
      const projectName = tab.projectName || 
                          this.ideInfo.currProj?.data?.name ||
                          this.ideInfo.currProj?.config?.name;
      
      console.log('[getMediaCodeItem] Creating media code item:', {
        tabTitle: tab.title,
        tabFilePath: tab.filePath,
        tabProjectName: tab.projectName,
        actualProjectName: projectName,
        hasContent: !!tab.content,
        contentType: tab.content ? (tab.content.startsWith('data:') ? 'data-url' : tab.content.startsWith('blob:') ? 'blob-url' : 'other') : 'none'
      });
      
      // If content is already loaded (from fullscreen), mark as preloaded
      if (tab.content && tab.content.startsWith('data:')) {
        return {
          name: tab.title,
          path: tab.filePath,
          projectName: projectName,
          content: tab.content,
          preloaded: true
        };
      } else if (tab.content && tab.content.startsWith('blob:')) {
        // For PDF blob URLs
        return {
          name: tab.title,
          path: tab.filePath,
          projectName: projectName,
          content: tab.content,
          preloaded: true
        };
      }
      
      // Otherwise, let MediaViewer load it
      return {
        name: tab.title,
        path: tab.filePath,
        projectName: projectName,
        preloaded: false
      };
    },
    
    openFullscreenPreview(path, projectName) {
      // Open preview files in fullscreen modal
      const self = this;
      const fileName = path.split('/').pop();
      const fileExt = path.toLowerCase().split('.').pop();
      const mediaExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.pdf'];
      const dataExtensions = ['.csv'];
      const isMediaFile = mediaExtensions.some(ext => path.toLowerCase().endsWith(ext));
      const isDataFile = dataExtensions.some(ext => path.toLowerCase().endsWith(ext));
      
      if (isMediaFile) {
        // Fetch binary content for media files
        this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
          projectName: projectName,
          filePath: path,
          binary: true,
          callback: (response) => {
            if (response.code === 0 && response.data) {
              let base64Content = response.data.content || response.data;
              
              if (base64Content && base64Content.length > 0) {
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
                
                // Create data URL for both images and PDFs
                // SimplePdfViewer expects base64 data, not blob URLs
                const previewContent = `data:${mimeType};base64,${base64Content}`;
                
                // Set fullscreen preview in store
                const fileData = {
                  name: fileName,
                  path: path,
                  projectName: projectName,
                  content: previewContent,
                  type: fileExt === 'pdf' ? 'pdf' : 'image'
                };
                
                self.$store.commit('ide/setFullscreenPreview', { 
                  file: fileData, 
                  content: previewContent 
                });
              } else {
                self.$message.error(`Failed to load ${fileName}: No content received`);
              }
            } else {
              self.$message.error(`Failed to load ${fileName}`);
            }
          }
        });
      } else if (isDataFile) {
        // Fetch CSV content for fullscreen preview
        this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
          projectName: projectName,
          filePath: path,
          callback: (response) => {
            if (response.code === 0 && response.data) {
              const csvContent = response.data.content || response.data;
              
              // Set fullscreen preview in store for CSV
              const fileData = {
                name: fileName,
                path: path,
                projectName: projectName,
                content: csvContent,
                type: 'csv'
              };
              
              self.$store.commit('ide/setFullscreenPreview', { 
                file: fileData, 
                content: csvContent 
              });
            } else {
              self.$message.error(`Failed to load ${fileName}`);
            }
          }
        });
      }
    },
    setTextDialog(data) {
      // Check if this is for new file (use new dialog)
      if (data.type === 'create-file' && data.title === 'New File') {
        this.showNewFileDialog = true;
        return;
      }
      
      // Otherwise use the old dialog
      this.dialogType = data.type;
      this.dialogTitle = data.title;
      this.dialogText = data.text;
      this.dialogTips = data.tips;
      this.showFileDialog = true;
      this.showProjsDialog = false;
    },
    handleRenameItem(data) {
      // Handle rename from project tree
      console.log('[handleRenameItem] Received rename request:', data);
      const { oldPath, newName, type, projectName } = data;
      
      // Get the project name - IMPORTANT: use the one from data first!
      const actualProjectName = projectName || this.ideInfo.currProj?.config?.name || this.ideInfo.currProj?.data?.name;
      
      console.log('[handleRenameItem] Using project:', actualProjectName);
      console.log('[handleRenameItem] Data projectName:', projectName);
      console.log('[handleRenameItem] Current project:', this.ideInfo.currProj?.data?.name);
      console.log('[handleRenameItem] Renaming:', { oldPath, newName, type, actualProjectName });
      
      // Directly call the rename method since the prompt was already shown in ProjTree
      if (type === 'file') {
        this.renameFile(newName, oldPath, actualProjectName);
      } else if (type === 'dir' || type === 'folder') {
        this.renameFolder(newName, oldPath, actualProjectName);
      }
    },
    handleDeleteItem(data) {
      // Handle delete from project tree
      const { path, type, projectName } = data;
      console.log('[handleDeleteItem] Deleting:', type, 'at path:', path, 'in project:', projectName);
      
      if (type === 'file') {
        this.deleteFile(path, projectName);
      } else if (type === 'dir' || type === 'folder') {
        this.deleteFolder(path, projectName);
      }
    },
    handleDownloadItem(data) {
      // Handle download from project tree
      console.log('[handleDownloadItem] Download request:', data);
      
      if (!data || !data.path) {
        console.error('[handleDownloadItem] Invalid data:', data);
        ElMessage.error('Cannot download: no file selected');
        return;
      }
      
      // Extract filename from path
      const fileName = data.path.split('/').pop() || data.label || data.name || 'download';
      
      // Convert data structure to what downloadFile expects
      const fileInfo = {
        fileName: fileName,
        filePath: data.path,
        projectName: data.projectName || this.ideInfo.currProj?.data?.name || this.ideInfo.currProj?.config?.name
      };
      
      console.log('[handleDownloadItem] Downloading:', fileInfo);
      this.downloadFile(fileInfo);
    },
    openFileBrowser() {
      this.fileBrowserMode = 'open';
      this.fileToMove = null;
      this.showFileBrowserDialog = true;
    },
    shareProject() {
      // Handle share project functionality
      this.$message.info('Share project feature coming soon!');
    },
    handleSignIn() {
      console.log('handleSignIn called');
      
      // Check if already logged in
      const existingSession = localStorage.getItem('session_id');
      const existingUsername = localStorage.getItem('username');
      
      if (existingSession && existingUsername) {
        // User is already logged in, ask if they want to switch accounts
        ElMessageBox.confirm(
          `You are already logged in as ${existingUsername}. Do you want to sign out and login with a different account?`,
          'Already Logged In',
          {
            confirmButtonText: 'Sign Out',
            cancelButtonText: 'Cancel',
            type: 'info',
          }
        ).then(() => {
          // User wants to sign out and login again
          localStorage.removeItem('session_id');
          localStorage.removeItem('username');
          localStorage.removeItem('role');
          localStorage.removeItem('full_name');
          
          // Reload to clear the session
          window.location.reload();
        }).catch(() => {
          // User cancelled, do nothing
        });
        return;
      }
      
      // Show login modal for new login
      console.log('Setting showLoginModal to true');
      this.showLoginModal = true;
      console.log('showLoginModal is now:', this.showLoginModal);
      
      // Force Vue to update
      this.$nextTick(() => {
        console.log('After nextTick, showLoginModal:', this.showLoginModal);
        console.log('Login modal element:', document.querySelector('.login-modal-overlay'));
      });
    },
    handleLoginSuccess(userData) {
      console.log('Login success received:', userData);
      
      // Handle successful login
      if (userData) {
        this.currentUser = userData;
        
        // Show success message using ElMessage
        ElMessage.success(`Welcome, ${userData.full_name || userData.username}!`);
        
        // Since session is now stored in localStorage,
        // reload the page to reinitialize with the authenticated session
        // This avoids Vuex mutation issues with WebSocket reconnection
        setTimeout(() => {
          window.location.reload();
        }, 500);
      } else {
        console.error('No user data received in handleLoginSuccess');
      }
    },
    reconnectWebSocket() {
      // Disconnect existing WebSocket
      if (this.wsInfo && this.wsInfo.rws) {
        this.wsInfo.rws.close();
      }
      
      // Reconnect with authentication
      setTimeout(() => {
        this.$store.dispatch('websocket/init');
      }, 500);
    },
    handleNewFileFromTree() {
      // Open new file dialog - same functionality as File > New File
      const nodeSelected = this.ideInfo.nodeSelected;
      if (!nodeSelected || (nodeSelected.type !== 'dir' && nodeSelected.type !== 'folder')) {
        // Select the root folder if no folder is selected
        const rootFolder = this.ideInfo.currProj?.data;
        if (rootFolder) {
          this.$store.commit('ide/setNodeSelected', rootFolder);
        }
      }
      
      // Open the text dialog for creating a new file
      this.setTextDialog({
        type: 'create-file',
        title: 'New File',
        tips: 'Enter file name:',
        text: 'untitled.py'
      });
    },
    handleNewFolderFromTree() {
      // Open new folder dialog
      const nodeSelected = this.ideInfo.nodeSelected;
      if (!nodeSelected || (nodeSelected.type !== 'dir' && nodeSelected.type !== 'folder')) {
        // Select the root folder if no folder is selected
        const rootFolder = this.ideInfo.currProj?.data;
        if (rootFolder) {
          this.$store.commit('ide/setNodeSelected', rootFolder);
        }
      }
      this.showNewFolderDialog = true;
    },
    shareFile() {
      // Handle share file functionality
      this.$message.info('Share file feature coming soon!');
    },
    // Edit menu handlers
    handleUndo() {
      // Trigger undo in the active editor
      const activeEditor = this.getActiveCodeMirrorInstance();
      if (activeEditor) {
        activeEditor.undo();
      } else {
        document.execCommand('undo');
      }
    },
    handleRedo() {
      // Trigger redo in the active editor
      const activeEditor = this.getActiveCodeMirrorInstance();
      if (activeEditor) {
        activeEditor.redo();
      } else {
        document.execCommand('redo');
      }
    },
    handleCut() {
      // Trigger cut in the active editor
      const activeEditor = this.getActiveCodeMirrorInstance();
      if (activeEditor && activeEditor.somethingSelected()) {
        const selection = activeEditor.getSelection();
        navigator.clipboard.writeText(selection);
        activeEditor.replaceSelection('');
      } else {
        document.execCommand('cut');
      }
    },
    handleCopy() {
      // Trigger copy in the active editor
      const activeEditor = this.getActiveCodeMirrorInstance();
      if (activeEditor && activeEditor.somethingSelected()) {
        const selection = activeEditor.getSelection();
        navigator.clipboard.writeText(selection);
      } else {
        document.execCommand('copy');
      }
    },
    handlePaste() {
      // Trigger paste in the active editor
      const activeEditor = this.getActiveCodeMirrorInstance();
      if (activeEditor) {
        navigator.clipboard.readText().then(text => {
          activeEditor.replaceSelection(text);
        }).catch(() => {
          document.execCommand('paste');
        });
      } else {
        document.execCommand('paste');
      }
    },
    handleFind() {
      // Open custom Find/Replace modal in find mode
      this.findReplaceMode = 'find';
      this.showFindReplaceModal = true;
    },
    handleReplace() {
      // Open custom Find/Replace modal in replace mode
      this.findReplaceMode = 'replace';
      this.showFindReplaceModal = true;
    },
    handleComment() {
      // Toggle comment in the active editor
      const activeEditor = this.getActiveCodeMirrorInstance();
      if (activeEditor) {
        activeEditor.toggleComment();
      }
    },
    getActiveCodeMirrorInstance() {
      // Get the active CodeMirror instance from the current editor
      const activeEditorElement = document.querySelector('.editor-content .code-editor-flex .CodeMirror');
      if (activeEditorElement && activeEditorElement.CodeMirror) {
        return activeEditorElement.CodeMirror;
      }
      return null;
    },
    // View menu handlers
    toggleConsole(visible) {
      // Toggle console/REPL visibility
      if (visible) {
        this.consoleMode = 'normal';
        this.consolePaneSize = 30;
        
        // If no console is selected, start an empty REPL
        if (!this.ideInfo.consoleSelected || !this.ideInfo.consoleSelected.id) {
          this.startEmptyRepl();
        }
      } else {
        this.consoleMode = 'collapsed';
        this.consolePaneSize = 5;
      }
    },
    
    startEmptyRepl() {
      // Create a REPL console item for empty REPL
      const replConsole = {
        id: 'empty-repl-' + Date.now(),
        name: 'Python REPL',
        path: 'REPL',
        resultList: [],
        run: false,
        stop: false,
        waitingForInput: false,
        inputPrompt: ''
      };
      
      // Add to console items
      this.$store.commit('ide/pushConsoleItem', replConsole);
      this.$store.commit('ide/selectConsoleItem', replConsole.id);
      
      // Start the empty REPL on server
      this.sendMessage({
        cmd: 'start_python_repl',
        cmd_id: replConsole.id,
        data: {
          projectName: this.ideInfo.currProj?.data?.name || 'Local'
        }
      });
      
      // Mark as running
      this.$store.commit('ide/updateConsoleItem', {
        id: replConsole.id,
        run: true
      });
    },
    togglePreviewPanel(visible) {
      // Toggle preview panel visibility
      if (visible && this.previewTabs.length === 0) {
        // Add a default preview tab if none exists
        this.$message.info('No files to preview. Open an image, PDF, or CSV file.');
      } else if (!visible) {
        this.rightPanelMode = 'closed';
      } else {
        this.rightPanelMode = 'normal';
      }
    },
    handleOpenFile(filePath) {
      // Open the selected file from the file browser
      this.getFile(filePath);
      this.showFileBrowserDialog = false;
    },
    async duplicateFile(data) {
      const { originalPath, newName, projectName } = data;
      const self = this;
      
      console.log('🔍 [DEBUG] duplicateFile called with:', { originalPath, newName, projectName });
      
      // Get the parent directory
      const lastSlash = originalPath.lastIndexOf('/');
      const parentPath = lastSlash > 0 ? originalPath.substring(0, lastSlash) : '/';
      
      // Generate unique filename with auto-numbering
      const uniqueName = await this.generateUniqueFileName(newName, parentPath, projectName);
      const newPath = parentPath + '/' + uniqueName;
      
      console.log('🔍 [DEBUG] Generated unique filename:', uniqueName);
      console.log('🔍 [DEBUG] New file path will be:', newPath);
      
      // First, get the original file content
      this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
        projectName: projectName,
        filePath: originalPath,
        callback: (dict) => {
          if (dict.code == 0) {
            const content = dict.data.content || dict.data;
            
            console.log('🔍 [DEBUG] Original file content retrieved, length:', content?.length);
            
            // Create the duplicate file with unique name
            // First create the file, then write the content
            self.$store.dispatch(`ide/${types.IDE_CREATE_FILE}`, {
              projectName: projectName,
              parentPath: parentPath,
              fileName: uniqueName,
              callback: (createDict) => {
                if (createDict.code == 0) {
                  console.log('🔍 [DEBUG] File created successfully, now writing content');
                  
                  // Now write the content to the created file
                  self.$store.dispatch(`ide/${types.IDE_WRITE_FILE}`, {
                    projectName: projectName,
                    filePath: newPath,
                    fileData: content,
                    complete: true,
                    callback: (writeDict) => {
                      if (writeDict.code == 0) {
                        console.log('🔍 [DEBUG] File duplicated successfully as:', uniqueName);
                        ElMessage.success(`File duplicated as ${uniqueName}`);
                        self.refreshProjectTree();
                      } else {
                        console.error('🔍 [DEBUG] Failed to write content to duplicate file:', writeDict);
                        ElMessage.error('Failed to write content to duplicate file');
                      }
                    }
                  });
                } else {
                  console.error('🔍 [DEBUG] Failed to create duplicate file:', createDict);
                  ElMessage.error('Failed to create duplicate file');
                }
              }
            });
          } else {
            console.error('🔍 [DEBUG] Failed to read original file:', dict);
            ElMessage.error('Failed to read original file');
          }
        }
      });
    },
    
    async generateUniqueFileName(proposedName, parentPath, projectName) {
      // Extract file extension and base name
      const lastDotIndex = proposedName.lastIndexOf('.');
      const extension = lastDotIndex > 0 ? proposedName.substring(lastDotIndex) : '';
      const baseName = lastDotIndex > 0 ? proposedName.substring(0, lastDotIndex) : proposedName;
      
      console.log('🔍 [DEBUG] generateUniqueFileName:', { proposedName, baseName, extension, parentPath });
      
      // Get list of existing files in the directory
      const existingFiles = await this.getExistingFilesInDirectory(parentPath, projectName);
      console.log('🔍 [DEBUG] Existing files in directory:', existingFiles);
      
      // Check if the proposed name is already unique
      if (!existingFiles.includes(proposedName)) {
        console.log('🔍 [DEBUG] Proposed name is already unique:', proposedName);
        return proposedName;
      }
      
      // Generate numbered variants until we find a unique one
      for (let i = 1; i < 1000; i++) {
        const numberedName = i === 1 ? 
          `${baseName}_copy${extension}` : 
          `${baseName}_copy_${i}${extension}`;
          
        if (!existingFiles.includes(numberedName)) {
          console.log('🔍 [DEBUG] Found unique name:', numberedName);
          return numberedName;
        }
      }
      
      // Fallback with timestamp if we somehow hit the limit
      const timestamp = Date.now();
      const fallbackName = `${baseName}_copy_${timestamp}${extension}`;
      console.log('🔍 [DEBUG] Using timestamp fallback:', fallbackName);
      return fallbackName;
    },
    
    async getExistingFilesInDirectory(directoryPath, projectName) {
      return new Promise((resolve) => {
        // Get the current project tree data
        const projectData = this.ideInfo.currProj?.data;
        if (!projectData) {
          console.log('🔍 [DEBUG] No project data available');
          resolve([]);
          return;
        }
        
        // Find the target directory in the tree
        const findDirectory = (node, targetPath) => {
          if (node.path === targetPath && node.type === 'dir') {
            return node;
          }
          if (node.children) {
            for (const child of node.children) {
              const result = findDirectory(child, targetPath);
              if (result) return result;
            }
          }
          return null;
        };
        
        const targetDir = findDirectory(projectData, directoryPath);
        console.log('🔍 [DEBUG] Found target directory:', targetDir);
        
        if (targetDir && targetDir.children) {
          // Extract filenames from the directory
          const filenames = targetDir.children
            .filter(child => child.type === 'file')
            .map(child => child.label || child.name);
          console.log('🔍 [DEBUG] Extracted filenames:', filenames);
          resolve(filenames);
        } else {
          console.log('🔍 [DEBUG] Directory not found or has no children');
          resolve([]);
        }
      });
    },
    async saveAsFile(fileInfo) {
      console.log('🔍 [DEBUG] VmIde.saveAsFile() called with:', fileInfo);
      
      // Save As - allows user to choose location and rename file
      if (!fileInfo || !fileInfo.fileName) {
        console.log('🔍 [DEBUG] Invalid fileInfo - no fileName');
        ElMessage.error('No file selected to save');
        return;
      }
      
      // First try to get content from editor if file is open
      const codeItem = this.ideInfo.codeItems.find(item => 
        item.filePath === fileInfo.filePath && 
        (item.projectName === fileInfo.projectName || (!item.projectName && !fileInfo.projectName))
      );
      
      console.log('🔍 [DEBUG] Looking for codeItem with filePath:', fileInfo.filePath);
      console.log('🔍 [DEBUG] Available codeItems:', this.ideInfo.codeItems?.map(item => ({ filePath: item.filePath, projectName: item.projectName })));
      console.log('🔍 [DEBUG] Found codeItem:', !!codeItem);
      
      if (codeItem) {
        // File is open in editor, use editor content
        console.log('🔍 [DEBUG] Using editor content, calling performSaveAs');
        await this.performSaveAs(fileInfo, codeItem.content);
      } else {
        // File is not open in editor, read from server
        console.log('🔍 [DEBUG] File not in editor, reading from server');
        this.readFileForSaveAs(fileInfo);
      }
    },
    
    readFileForSaveAs(fileInfo) {
      console.log('🔍 [DEBUG] readFileForSaveAs called with:', fileInfo);
      
      // Check if it's a binary file
      const binaryExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.pdf', '.zip', '.tar', '.gz'];
      const isBinary = binaryExtensions.some(ext => fileInfo.fileName.toLowerCase().endsWith(ext));
      
      console.log('🔍 [DEBUG] File is binary:', isBinary);
      console.log('🔍 [DEBUG] Dispatching IDE_GET_FILE with:', {
        projectName: fileInfo.projectName,
        filePath: fileInfo.filePath,
        binary: isBinary
      });
      
      this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
        projectName: fileInfo.projectName,
        filePath: fileInfo.filePath,
        binary: isBinary,
        callback: async (dict) => {
          console.log('🔍 [DEBUG] IDE_GET_FILE callback received:', { code: dict.code, hasData: !!dict.data });
          
          if (dict.code == 0) {
            // Get the actual content
            let fileContent = dict.data?.content || dict.data;
            
            if (isBinary) {
              // For binary files, we need to handle base64 data differently
              ElMessage.info('Binary files should be downloaded using the Download option instead.');
              return;
            } else {
              // For text files, use the content directly
              if (typeof fileContent === 'object' && fileContent.content) {
                fileContent = fileContent.content;
              }
              await this.performSaveAs(fileInfo, fileContent);
            }
          } else {
            ElMessage.error('Failed to read file content');
          }
        }
      });
    },
    
    async performSaveAs(fileInfo, content) {
      console.log('🔍 [DEBUG] performSaveAs called with fileInfo:', fileInfo);
      console.log('🔍 [DEBUG] Content length:', content?.length);
      
      // Determine file type for proper MIME type
      const getFileType = (fileName) => {
        const ext = fileName.toLowerCase().split('.').pop();
        const mimeTypes = {
          'py': 'text/x-python',
          'js': 'text/javascript',
          'html': 'text/html',
          'css': 'text/css',
          'json': 'application/json',
          'md': 'text/markdown',
          'txt': 'text/plain',
          'csv': 'text/csv',
          'xml': 'text/xml'
        };
        return mimeTypes[ext] || 'text/plain';
      };

      const mimeType = getFileType(fileInfo.fileName);

      // Check for File System Access API support and HTTPS requirement
      const hasFileSystemAccess = 'showSaveFilePicker' in window;
      const isSecureContext = window.isSecureContext;
      
      // Try modern File System Access API first (Chrome 86+, Edge 86+, requires HTTPS)
      if (hasFileSystemAccess && isSecureContext) {
        try {
          // Configure file type options
          const fileExtension = fileInfo.fileName.split('.').pop() || 'txt';
          const options = {
            suggestedName: fileInfo.fileName,
            types: [{
              description: `${fileExtension.toUpperCase()} files`,
              accept: {
                [mimeType]: ['.' + fileExtension]
              }
            }],
            excludeAcceptAllOption: false // Allow "All Files" option
          };

          // Show save file picker with proper error handling
          const fileHandle = await window.showSaveFilePicker(options);
          
          // Create writable stream
          const writable = await fileHandle.createWritable();
          
          // Write file content with progress for large files
          if (content.length > 1024 * 1024) { // Files larger than 1MB
            const chunks = content.match(/.{1,65536}/g) || []; // 64KB chunks
            for (const chunk of chunks) {
              await writable.write(chunk);
            }
          } else {
            await writable.write(content);
          }
          
          // Close the stream
          await writable.close();
          
          ElMessage.success(`File saved successfully as: ${fileHandle.name}`);
          return;
        } catch (error) {
          // User cancelled or error occurred
          if (error.name === 'AbortError') {
            return; // User cancelled - no error message
          }
          if (error.name === 'NotAllowedError') {
            ElMessage.warning('File access permission denied. Using fallback download method.');
          } else {
            console.warn('File System Access API failed:', error);
          }
          // Fall through to legacy method
        }
      } else if (hasFileSystemAccess && !isSecureContext) {
        console.warn('File System Access API requires HTTPS. Using fallback method.');
      }

      // Fallback method for older browsers or when File System Access API fails
      try {
        // Create blob with proper UTF-8 encoding
        const blob = new Blob([content], { 
          type: mimeType + ';charset=utf-8' 
        });
        
        // Check if the download attribute is supported
        const testLink = document.createElement('a');
        const isDownloadSupported = 'download' in testLink;
        
        if (isDownloadSupported) {
          // Modern approach with download attribute
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = fileInfo.fileName;
          
          // Ensure link is properly configured for all browsers
          link.style.display = 'none';
          link.setAttribute('target', '_blank');
          link.setAttribute('rel', 'noopener noreferrer');
          
          document.body.appendChild(link);
          
          // Trigger download with cross-browser support
          if (typeof link.click === 'function') {
            link.click();
          } else {
            // Fallback for older browsers
            const event = new MouseEvent('click', {
              view: window,
              bubbles: true,
              cancelable: true
            });
            link.dispatchEvent(event);
          }
          
          // Cleanup with proper timing
          setTimeout(() => {
            if (document.body.contains(link)) {
              document.body.removeChild(link);
            }
            window.URL.revokeObjectURL(url);
          }, 150);
          
          ElMessage.success('File downloaded to your default downloads folder');
        } else {
          // Very old browser fallback - open in new window
          const url = window.URL.createObjectURL(blob);
          const newWindow = window.open(url, '_blank');
          
          if (newWindow) {
            ElMessage.info('File opened in new window. Use browser\'s save function to download.');
            // Cleanup after window opens
            setTimeout(() => {
              window.URL.revokeObjectURL(url);
            }, 1000);
          } else {
            throw new Error('Popup blocked or browser not supported');
          }
        }
      } catch (error) {
        console.error('Save As failed:', error);
        
        // Last resort - copy to clipboard if available
        if (navigator.clipboard && navigator.clipboard.writeText) {
          try {
            await navigator.clipboard.writeText(content);
            ElMessage.warning('Could not download file. Content copied to clipboard instead.');
          } catch (clipboardError) {
            ElMessage.error('Failed to save file. Please try using a modern browser.');
          }
        } else {
          ElMessage.error('Failed to save file. Please try using a modern browser.');
        }
      }
    },
    openMoveDialog(fileData) {
      this.fileBrowserMode = 'move';
      this.fileToMove = fileData;
      this.showFileBrowserDialog = true;
    },
    handleMoveFile(data) {
      const { oldPath, newPath, projectName } = data;
      const self = this;
      
      // First get the file content
      this.$store.dispatch(`ide/${types.IDE_GET_FILE}`, {
        projectName: projectName,
        filePath: oldPath,
        callback: (dict) => {
          if (dict.code == 0) {
            const content = dict.data.content || dict.data;
            
            // Create file at new location
            self.$store.dispatch(`ide/${types.IDE_CREATE_FILE}`, {
              projectName: projectName,
              filePath: newPath,
              content: content,
              callback: (createDict) => {
                if (createDict.code == 0) {
                  // Delete the original file
                  self.$store.dispatch(`ide/${types.IDE_DEL_FILE}`, {
                    projectName: projectName,
                    filePath: oldPath,
                    callback: (delDict) => {
                      if (delDict.code == 0) {
                        ElMessage.success('File moved successfully');
                        self.refreshProjectTree();
                        
                        // If the moved file was open, update its path
                        const openFile = self.ideInfo.codeItems.find(item => 
                          item.filePath === oldPath && item.projectName === projectName
                        );
                        if (openFile) {
                          openFile.filePath = newPath;
                          openFile.fileName = newPath.substring(newPath.lastIndexOf('/') + 1);
                        }
                      } else {
                        ElMessage.error('Failed to delete original file after move');
                      }
                    }
                  });
                } else {
                  ElMessage.error('Failed to create file at new location');
                }
              }
            });
          } else {
            ElMessage.error('Failed to read file for moving');
          }
        }
      });
      
      this.showFileBrowserDialog = false;
    },
    deleteFileFromMenu(data) {
      // Delete file from File menu
      this.handleDeleteItem(data);
    },
    deleteSelectedFile(data) {
      // Delete the selected file (called from the trash button in second header)
      this.handleDeleteItem(data);
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
      console.log('[deleteFile] Deleting file:', filePath, 'from project:', projectName || this.ideInfo.currProj.config.name);
      
      // Get the actual project name if in multi-root mode
      const actualProjectName = projectName || this.ideInfo.currProj.config.name || this.ideInfo.currProj.data?.name;
      
      this.$store.dispatch(`ide/${types.IDE_DEL_FILE}`, {
        projectName: actualProjectName,
        filePath: filePath,
        callback: (dict) => {
          console.log('[deleteFile] Response:', dict);
          if (dict.code == 0) {
            const parentData = self.getParentData(filePath);
            if (parentData) {
              self.$store.commit('ide/handleDelFile', {parentData, filePath});
            }
            
            // Refresh the tree to show changes
            self.refreshProjectTree();
            
            ElMessage({
              type: 'success',
              message: 'File deleted successfully',
              duration: 2000
            });
          } else {
            ElMessage({
              type: 'error',
              message: 'Failed to delete file',
              duration: 3000
            });
          }
        }
      });
    },
    deleteFolder(folderPath, projectName) {
      const self = this;
      console.log('[deleteFolder] Deleting folder:', folderPath, 'from project:', projectName || this.ideInfo.currProj.config.name);
      
      // Get the actual project name if in multi-root mode
      const actualProjectName = projectName || this.ideInfo.currProj.config.name || this.ideInfo.currProj.data?.name;
      
      this.$store.dispatch(`ide/${types.IDE_DEL_FOLDER}`, {
        projectName: actualProjectName,
        folderPath: folderPath,
        callback: (dict) => {
          console.log('[deleteFolder] Response:', dict);
          if (dict.code == 0) {
            const parentData = self.getParentData(folderPath);
            if (parentData)
              self.$store.commit('ide/handleDelFolder', {parentData, folderPath});
            
            // Refresh the tree to show changes
            self.refreshProjectTree();
            
            ElMessage({
              type: 'success',
              message: 'Folder deleted successfully',
              duration: 2000
            });
          } else {
            ElMessage({
              type: 'error',
              message: 'Failed to delete folder',
              duration: 3000
            });
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
      
      // Determine the actual old path
      let actualOldPath = oldPath;
      if (actualOldPath === undefined) {
        if (this.ideInfo.nodeSelected && this.ideInfo.nodeSelected.path) {
          actualOldPath = this.ideInfo.nodeSelected.path;
        } else {
          console.error('Cannot rename: no path provided and nodeSelected is null');
          ElMessage.error('Cannot rename: no file selected');
          return;
        }
      }
      
      console.log('[renameFile] Starting rename:', { actualOldPath, newName, projectName });
      
      // Use the projectName passed in, not the current project
      const actualProjectName = projectName || this.ideInfo.currProj?.config?.name || this.ideInfo.currProj?.data?.name;
      console.log('[renameFile] Using project name:', actualProjectName);
      
      this.$store.dispatch(`ide/${types.IDE_RENAME_FILE}`, {
        projectName: actualProjectName,
        oldPath: actualOldPath,
        fileName: newName,
        callback: (dict) => {
          console.log('[renameFile] Backend response:', dict);
          if (dict.code == 0) {
            // After successful backend rename, we need to:
            // 1. Update any open tabs with the new filename
            // 2. Refresh the project tree
            // 3. Update the selection
            
            // Calculate the new path
            const newPath = actualOldPath.substring(0, actualOldPath.lastIndexOf('/') + 1) + newName;
            console.log('[renameFile] New path will be:', newPath);
            
            // Update open tabs if the file is open
            for (let i = 0; i < self.ideInfo.codeItems.length; i++) {
              if (self.ideInfo.codeItems[i].path === actualOldPath) {
                console.log('[renameFile] Updating open tab from', actualOldPath, 'to', newPath);
                self.ideInfo.codeItems[i].path = newPath;
                self.ideInfo.codeItems[i].name = newName;
                break;
              }
            }
            
            // Refresh the project tree - use the actual project name
            self.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
              projectName: actualProjectName,
              callback: (projectDict) => {
                if (projectDict.code == 0) {
                  self.$store.commit('ide/handleProject', projectDict.data);
                  
                  // Update path selection to the new path
                  self.$store.commit('ide/setPathSelected', newPath);
                  
                  // If we're in multi-root mode, also refresh all projects
                  if (self.ideInfo.multiRootData) {
                    console.log('[renameFile] Refreshing all projects in multi-root mode');
                    self.loadAllDefaultProjects();
                  }
                  
                  ElMessage.success('File renamed successfully');
                }
              }
            });
          } else {
            console.error('[renameFile] Rename failed:', dict);
            const errorMsg = dict.data?.message || dict.message || 'Unknown error';
            ElMessage.error('Failed to rename file: ' + errorMsg);
          }
        }
      });
    },
    renameFolder(newName, oldPath, projectName) {
      const self = this;
      
      // Determine the actual old path
      let actualOldPath = oldPath;
      if (actualOldPath === undefined) {
        if (this.ideInfo.nodeSelected && this.ideInfo.nodeSelected.path) {
          actualOldPath = this.ideInfo.nodeSelected.path;
        } else {
          console.error('Cannot rename folder: no path provided and nodeSelected is null');
          ElMessage.error('Cannot rename folder: no folder selected');
          return;
        }
      }
      
      console.log('[renameFolder] Starting rename:', { actualOldPath, newName, projectName });
      
      // Use the projectName passed in, not the current project
      const actualProjectName = projectName || this.ideInfo.currProj?.config?.name || this.ideInfo.currProj?.data?.name;
      console.log('[renameFolder] Using project name:', actualProjectName);
      
      this.$store.dispatch(`ide/${types.IDE_RENAME_FOLDER}`, {
        projectName: actualProjectName,
        oldPath: actualOldPath,
        folderName: newName,
        callback: (dict) => {
          console.log('[renameFolder] Backend response:', dict);
          if (dict.code == 0) {
            // After successful backend rename, we need to:
            // 1. Update any open tabs with paths inside the renamed folder
            // 2. Refresh the project tree
            // 3. Update the selection
            
            // Calculate the new path
            const newPath = actualOldPath.substring(0, actualOldPath.lastIndexOf('/') + 1) + newName;
            console.log('[renameFolder] New path will be:', newPath);
            
            // Update open tabs if any files inside the folder are open
            for (let i = 0; i < self.ideInfo.codeItems.length; i++) {
              if (self.ideInfo.codeItems[i].path.startsWith(actualOldPath + '/')) {
                const relativePath = self.ideInfo.codeItems[i].path.substring(actualOldPath.length);
                const updatedPath = newPath + relativePath;
                console.log('[renameFolder] Updating open tab from', self.ideInfo.codeItems[i].path, 'to', updatedPath);
                self.ideInfo.codeItems[i].path = updatedPath;
              }
            }
            
            // Refresh the project tree - use the actual project name
            self.$store.dispatch(`ide/${types.IDE_GET_PROJECT}`, {
              projectName: actualProjectName,
              callback: (projectDict) => {
                if (projectDict.code == 0) {
                  self.$store.commit('ide/handleProject', projectDict.data);
                  
                  // Update path selection to the new path
                  self.$store.commit('ide/setPathSelected', newPath);
                  
                  // If we're in multi-root mode, also refresh all projects
                  if (self.ideInfo.multiRootData) {
                    console.log('[renameFolder] Refreshing all projects in multi-root mode');
                    self.loadAllDefaultProjects();
                  }
                  
                  ElMessage.success('Folder renamed successfully');
                }
              }
            });
          } else {
            console.error('[renameFolder] Rename failed:', dict);
            const errorMsg = dict.data?.message || dict.message || 'Unknown error';
            ElMessage.error('Failed to rename folder: ' + errorMsg);
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
      // Check if we're switching from a different file
      const previousFile = this.ideInfo.codeSelected;
      const isFileSwitch = previousFile && previousFile.path !== item.path;
      
      // If switching files and previous file is a Python file
      if (isFileSwitch && previousFile.path && previousFile.path.endsWith('.py')) {
        // Find the console for the previous file
        const prevFileConsole = this.ideInfo.consoleItems.find(
          consoleItem => consoleItem.path === previousFile.path
        );
        
        // Stop the program if it's running (but not REPL)
        if (prevFileConsole && prevFileConsole.run && !this.isReplMode) {
          this.stop(prevFileConsole.id);
          
          // Clear any input prompts
          if (prevFileConsole.waitingForInput) {
            this.$store.commit('ide/updateConsoleItem', {
              id: prevFileConsole.id,
              waitingForInput: false,
              inputPrompt: ''
            });
          }
        }
        
        // Save the console state for the previous file (preserves output)
        this.saveFileConsoleState(previousFile.path);
      }
      
      // Update store first to ensure tab switches properly
      this.$store.commit('ide/setPathSelected', item.path);
      this.$store.commit('ide/setCodeSelected', item);
      
      // Then set the active file path for console management
      this.activeFilePath = item.path;
      
      // If switching to a Python file, reset console to collapsed but load its content
      if (isFileSwitch && item.path && item.path.endsWith('.py')) {
        // Find or create console for this file
        let fileConsole = this.ideInfo.consoleItems.find(
          consoleItem => consoleItem.path === item.path
        );
        
        if (!fileConsole) {
          // Create a new console for this file if it doesn't exist
          fileConsole = {
            id: this.$store.state.ide.consoleId,
            name: item.name,
            path: item.path,
            resultList: [],
            run: false,
            stop: false,
            waitingForInput: false,
            inputPrompt: ''
          };
          this.$store.commit('ide/pushConsoleItem', fileConsole);
        }
        
        // Select this file's console (preserves its output)
        this.$store.commit('ide/setConsoleSelected', fileConsole);
        
        // Always reset to collapsed state when switching files
        this.consoleMode = 'collapsed';
        this.consoleExpanded = false;
        this.consoleMaximized = false;
        
        this.$nextTick(() => {
          this.updateEditorHeight();
        });
      }
      
      // Update tree selection if needed
      if (this.ideInfo.currProj.pathSelected && this.ideInfo.treeRef) {
        this.ideInfo.treeRef.setCurrentKey(this.ideInfo.currProj.pathSelected);
        this.$store.commit('ide/setNodeSelected', this.ideInfo.treeRef.getCurrentNode());
      }
      
      // Save project state
      this.$store.dispatch(`ide/${types.IDE_SAVE_PROJECT}`, {});
    },
    closeFile(item) {
      // Clean up console state for this file
      if (item.path && item.path.endsWith('.py')) {
        // Save the current state before closing
        if (this.activeFilePath === item.path) {
          this.saveFileConsoleState(item.path);
        }
        
        // Remove the console item for this file
        const consoleItems = this.ideInfo.consoleItems.filter(
          consoleItem => consoleItem.path !== item.path
        );
        this.$store.commit('ide/setConsoleItems', consoleItems);
        
        // Clean up stored state if needed (optional - keep for session)
        // delete this.fileConsoleStates[item.path];
      }
      
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
      // Update window width for responsive behavior
      this.windowWidth = window.innerWidth;
      
      // Force Vue to update computed properties
      this.$forceUpdate();
    },
    runPathSelected() {
      // Check if there's a file selected
      const currentFilePath = this.ideInfo.currProj.pathSelected;
      
      if (!currentFilePath || currentFilePath === '' || currentFilePath === null) {
        // Show notification that no script is open
        ElMessage({
          type: 'warning',
          message: 'No script is open to run. Please open a Python file first.',
          duration: 3000
        });
        return;
      }
      
      // Ensure console is expanded when running
      if (!this.consoleExpanded) {
        this.consoleExpanded = true;
        this.updateEditorHeight();
      }
      
      // Don't create output tab in right panel anymore - console is sufficient
      
      // Get or create console for this specific file
      const fileConsole = this.getOrCreateFileConsole(currentFilePath);
      
      // Clear previous results and mark as not running yet using a mutation
      this.$store.commit('ide/resetConsoleItem', {
        consoleId: fileConsole.id,
        run: false,
        stop: false,
        resultList: []
      });
      
      // Select this file's console
      this.$store.commit('ide/setConsoleSelected', fileConsole);
      
      // Update the console ID
      this.$store.commit('ide/assignConsoleSelected', {
        id: this.ideInfo.consoleId
      });
      
      // Save the console state for this file  
      this.saveFileConsoleState(currentFilePath);

      // Open console at normal state (30%) when running program
      if (this.consoleMode === 'collapsed') {
        this.consoleMode = 'normal';
        this.consoleExpanded = true;
        this.consoleMaximized = false;
      }
      
      // Get the project name for the current file
      const projectName = this.ideInfo.codeSelected?.projectName || 
                         this.ideInfo.currProj?.data?.name ||
                         this.ideInfo.currProj?.config?.name;
      
      // Remove duplicate console item creation - this was causing multiple input fields
      const runId = this.ideInfo.consoleId;
      
      // Set replSessionId so we can receive the output from HybridREPLThread
      this.replSessionId = runId;
      console.log(`[VmIde] Setting replSessionId to ${runId} for Python program execution`);
      
      this.$store.dispatch(`ide/${types.IDE_RUN_PYTHON_PROGRAM}`, {
        msgId: runId,
        projectName: projectName,
        filePath: this.ideInfo.currProj.pathSelected,
        callback: {
          limits: -1,
          callback: (dict) => {
            console.log('🔍 [VmIde] Script execution callback:', dict);
            
            // CRITICAL: Don't process REPL messages through handleRunResult  
            // Check if this message belongs to the current REPL session
            const isReplMessage = (
              dict.id === this.replSessionId || 
              dict.cmd_id === this.replSessionId ||
              (dict.data && dict.data.program_id === this.replSessionId) ||
              // If REPL is active and this is output, it belongs to REPL
              (this.isReplMode && this.replSessionId && 
               (dict.code === 0 || dict.code === 2000 || dict.code === 5000) &&
               dict.data && (dict.data.stdout || dict.data.stderr))
            );
            
            // CRITICAL FIX: Always allow program start/end messages through to store
            const isProgramLifecycleMessage = (
              dict.data === null || dict.data === undefined || // Program start signal
              dict.code === 2000 ||                           // Input request signals
              dict.code === 4000 || dict.code === 5000        // Error or REPL transition signals
            );
            
            console.log('🔍 [Script] Callback - isReplMessage:', isReplMessage, 'isProgramLifecycle:', isProgramLifecycleMessage, 'code:', dict.code, 'id:', dict.id, 'replSessionId:', this.replSessionId);
            
            if (!isReplMessage || isProgramLifecycleMessage) {
              // Process all non-REPL messages and all program lifecycle messages through normal console handling
              console.log('✅ [Script] Processing through handleRunResult');
              this.$store.commit('ide/handleRunResult', dict);
            } else {
              console.log('⏭️ [Script] Skipping - will be handled by REPL');
            }
            
            // Check if this should trigger REPL mode (non-duplicate message only)
            if (dict.code === 5000 && !isReplMessage) {
              console.log('🎯 [VmIde] Script completed, entering REPL mode');
              this.isReplMode = true;
            }
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
      
      // Get the project name for the console's file
      const projectName = this.ideInfo.consoleSelected?.projectName ||
                         this.ideInfo.currProj?.data?.name ||
                         this.ideInfo.currProj?.config?.name;
      
      const runId = this.ideInfo.consoleSelected.id;
      
      // Set replSessionId so we can receive the output from HybridREPLThread
      this.replSessionId = runId;
      console.log(`[VmIde] Setting replSessionId to ${runId} for Python program re-run`);
      
      this.$store.dispatch(`ide/${types.IDE_RUN_PYTHON_PROGRAM}`, {
        msgId: runId,
        projectName: projectName,
        filePath: this.ideInfo.consoleSelected.path,
        callback: {
          limits: -1,
          callback: (dict) => {
            // CRITICAL: Don't process REPL messages through handleRunResult at all
            // Check if this message belongs to the current REPL session
            const isReplMessage = (
              dict.id === this.replSessionId || 
              dict.cmd_id === this.replSessionId ||
              (dict.data && dict.data.program_id === this.replSessionId) ||
              // If REPL is active and this is output, it belongs to REPL
              (this.isReplMode && this.replSessionId && 
               (dict.code === 0 || dict.code === 2000 || dict.code === 5000) &&
               dict.data && (dict.data.stdout || dict.data.stderr))
            );
            
            // CRITICAL FIX: Always allow program start/end messages through to store
            const isProgramLifecycleMessage = (
              dict.data === null || dict.data === undefined || // Program start signal
              dict.code === 2000 ||                           // Input request signals
              dict.code === 4000 || dict.code === 5000        // Error or REPL transition signals
            );
            
            console.log('🔍 [REPL] Callback - isReplMessage:', isReplMessage, 'isProgramLifecycle:', isProgramLifecycleMessage, 'code:', dict.code, 'id:', dict.id, 'replSessionId:', this.replSessionId);
            
            if (!isReplMessage || isProgramLifecycleMessage) {
              // Process all non-REPL messages and all program lifecycle messages through normal console handling
              console.log('✅ [REPL] Processing through handleRunResult');
              this.$store.commit('ide/handleRunResult', dict);
            } else {
              console.log('⏭️ [REPL] Skipping - will be handled by WebSocket');
            }
            // REPL messages are handled by the WebSocket listener above
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
          // Enter without Shift: check if we should execute or continue multiline
          event.preventDefault();
          
          // Get cursor position and current line
          const cursorPos = event.target.selectionStart;
          const textBeforeCursor = this.replInput.substring(0, cursorPos);
          const lines = textBeforeCursor.split('\n');
          const currentLine = lines[lines.length - 1];
          
          // Check if we're on an empty line in a multiline context
          const isEmptyLine = currentLine.trim() === '';
          const hasMultipleLines = this.replInput.includes('\n');
          
          if (isEmptyLine && hasMultipleLines) {
            // Empty line in multiline context - execute the code
            this.executeReplCommand();
          } else if (this.shouldContinueMultiline(this.replInput)) {
            // Code needs continuation - add new line
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
            // Execute the command
            this.executeReplCommand();
          }
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
      // Clean up the command - remove trailing empty lines but preserve internal structure
      let command = this.replInput;
      
      // Remove trailing empty lines only
      while (command.endsWith('\n\n')) {
        command = command.slice(0, -1);
      }
      
      // Don't execute if command is empty or only whitespace
      if (!command || !command.trim()) {
        this.replInput = '';
        this.replInputRows = 1;
        return;
      }
      
      // Check if we're in script-to-REPL mode (after script execution)
      if (this.ideInfo.consoleSelected && this.ideInfo.consoleSelected.waitingForReplInput) {
        // Send command to the existing console's REPL session
        const consoleId = this.ideInfo.consoleSelected.id;
        
        // Clear input
        this.replInput = '';
        this.replInputRows = 1;
        
        // Add command to console output using mutation
        this.$store.commit('ide/addConsoleOutput', {
          id: consoleId,
          type: 'user-input',
          text: `>>> ${command}`
        });
        
        // Send command via WebSocket
        if (this.wsInfo && this.wsInfo.rws && this.wsInfo.rws.readyState === WebSocket.OPEN) {
          const msg = {
            cmd: 'send_program_input',
            id: consoleId,
            data: {
              program_id: consoleId,
              input: command
            }
          };
          this.wsInfo.rws.send(JSON.stringify(msg));
          
          // Mark as not waiting for input temporarily using mutation
          this.$store.commit('ide/setConsoleWaitingForReplInput', {
            id: consoleId,
            waiting: false
          });
        }
      } else {
        // Use regular REPL mode
        await this.executeReplCommandDualMode(command);
      }
    },
    
    // Check if code needs multiline continuation
    shouldContinueMultiline(code) {
      if (!code || !code.trim()) return false;
      
      const lines = code.split('\n');
      const lastLine = lines[lines.length - 1].trim();
      
      // Check if last line ends with colon (def, if, for, while, try, etc.)
      if (lastLine.endsWith(':')) {
        return true;
      }
      
      // Check if we're inside a multiline construct that needs continuation
      const cleanCode = code.trim();
      
      // Count indentation levels to detect incomplete blocks
      let openBlocks = 0;
      let currentIndent = 0;
      
      for (const line of lines) {
        if (line.trim() === '') continue;
        
        const lineIndent = line.search(/\S/);
        if (lineIndent === -1) continue; // Skip empty lines
        
        // Check for block-starting keywords
        const trimmedLine = line.trim();
        if (trimmedLine.match(/^(def|class|if|elif|else|for|while|with|try|except|finally)\b.*:/)) {
          openBlocks++;
          currentIndent = lineIndent;
        } else if (lineIndent <= currentIndent && openBlocks > 0 && !trimmedLine.match(/^(elif|else|except|finally)\b/)) {
          openBlocks = Math.max(0, openBlocks - 1);
          currentIndent = lineIndent;
        }
      }
      
      // If we have open blocks and the last line is not indented properly, continue
      return openBlocks > 0 && !lastLine.match(/^(return|break|continue|pass|raise)\b/);
    },
    
    // Syntax highlighting method for Python code in REPL
    highlightPythonCode(code) {
      if (!code || typeof code !== 'string') return code;
      
      // Use Prism.js if available
      if (typeof Prism !== 'undefined' && Prism.languages && Prism.languages.python) {
        try {
          return Prism.highlight(code, Prism.languages.python, 'python');
        } catch (error) {
          console.warn('Prism.js highlighting failed:', error);
          return this.simpleHighlight(code);
        }
      }
      
      // Fallback to simple highlighting
      return this.simpleHighlight(code);
    },
    
    // Check if output is just a prompt that should be filtered
    isPromptOutput(result) {
      const content = result.text || result.content || result;
      if (typeof content !== 'string') return false;
      
      // Filter out standalone prompts
      return (
        content.match(/^\s*>>>\s*$/) ||              // >>> with any whitespace
        content.match(/^\s*\.\.\.\s*$/) ||           // ... with any whitespace  
        content.match(/^>>>\s*\n*$/) ||              // >>> with trailing newlines
        content.match(/^\.\.\.\s*\n*$/) ||           // ... with trailing newlines
        content.trim() === '>>>' ||                  // just ">>>"
        content.trim() === '...' ||                  // just "..."
        content === '>>> ' ||                        // exact prompt match
        content === '... '                           // exact continuation match
      );
    },
    
    // Simple syntax highlighting fallback
    simpleHighlight(code) {
      if (!code) return code;
      
      let highlighted = this.escapeHtml(code);
      
      // Python keywords
      const keywords = [
        'def', 'class', 'if', 'elif', 'else', 'try', 'except', 'finally',
        'for', 'while', 'with', 'as', 'import', 'from', 'return', 'yield',
        'lambda', 'pass', 'break', 'continue', 'raise', 'assert', 'del',
        'and', 'or', 'not', 'in', 'is', 'None', 'True', 'False', 'async', 'await'
      ];
      
      const keywordRegex = new RegExp(`\\b(${keywords.join('|')})\\b`, 'g');
      highlighted = highlighted.replace(keywordRegex, '<span class="python-keyword">$1</span>');
      
      // Strings (simple version - handles both single and double quotes)
      highlighted = highlighted.replace(/(["'])((?:\\.|(?!\1).)*?)\1/g, 
        '<span class="python-string">$1$2$1</span>');
      
      // Numbers (integers and floats)
      highlighted = highlighted.replace(/\b(\d+\.?\d*)\b/g, 
        '<span class="python-number">$1</span>');
      
      // Comments
      highlighted = highlighted.replace(/(#.*$)/gm, 
        '<span class="python-comment">$1</span>');
      
      // Built-in functions
      const builtins = ['print', 'input', 'range', 'len', 'str', 'int', 
                        'float', 'list', 'dict', 'set', 'tuple', 'type',
                        'sum', 'max', 'min', 'abs', 'round', 'sorted', 'reversed'];
      const builtinRegex = new RegExp(`\\b(${builtins.join('|')})\\b`, 'g');
      highlighted = highlighted.replace(builtinRegex, '<span class="python-builtin">$1</span>');
      
      return highlighted;
    },
    
    // Escape HTML to prevent XSS
    escapeHtml(text) {
      const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      };
      return text.replace(/[&<>"']/g, m => map[m]);
    },
    
    // Check if code contains multiple lines (for proper REPL display)
    isMultilineCode(code) {
      if (!code || typeof code !== 'string') return false;
      return code.includes('\n') && code.trim() !== '';
    },
    
    // Split code into lines for multiline display
    splitCodeLines(code) {
      if (!code || typeof code !== 'string') return [code || ''];
      return code.split('\n');
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
  height: calc(100% - 80px);
  top: 80px;
  left: 0;
  display: flex;
  flex-direction: row;
}

/* Left Sidebar */
.left-sidebar {
  background: var(--bg-sidebar, #282828);
  color: var(--text-primary, #CCCCCC);
  height: 100%;
  width: 100%; /* Ensure sidebar fills its pane container */
  overflow: auto;
  flex-shrink: 0;
  /* Use normal flow inside Splitpanes */
  position: relative;
  box-sizing: border-box;
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
  background: var(--console-header-bg, #323336);
  border-bottom: 1px solid var(--console-header-border, #464647);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 12px;
  user-select: none;
  transition: background-color 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.console-header:hover {
  background: var(--console-header-hover, #3a3a3d);
}

/* Light theme console header */
[data-theme="light"] .console-header {
  background: #e2e6ea;
  border-bottom: 1px solid #c8cfd6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .console-header:hover {
  background: #d8dde2;
}

/* Dark theme console header (default) */
[data-theme="dark"] .console-header {
  background: #323336;
  border-bottom: 1px solid #464647;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

[data-theme="dark"] .console-header:hover {
  background: #3a3a3d;
}

/* High contrast theme console header */
[data-theme="contrast"] .console-header {
  background: #1a1a1a;
  border-bottom: 2px solid #3a3a3a;
  box-shadow: 0 1px 3px rgba(255, 255, 255, 0.1);
}

[data-theme="contrast"] .console-header:hover {
  background: #252525;
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
  border: 1px solid var(--console-header-button-border, #3c3c3c);
  border-radius: 4px;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--console-header-button-text, #B5B5B5);
  transition: all 0.2s;
  width: 28px;
  height: 28px;
}

.console-expand-arrow:hover {
  background: var(--accent-color, #007ACC);
  color: white;
  border-color: var(--accent-color, #007ACC);
}

[data-theme="light"] .console-expand-arrow {
  border: 1px solid #adb5bd;
  color: #6c757d;
}

[data-theme="light"] .console-expand-arrow:hover {
  background: #0066cc;
  border-color: #0066cc;
}

[data-theme="dark"] .console-expand-arrow {
  border: 1px solid #565656;
  color: #b5b5b5;
}

[data-theme="contrast"] .console-expand-arrow {
  border: 2px solid #4a4a4a;
  color: #ffffff;
}

[data-theme="contrast"] .console-expand-arrow:hover {
  background: #ffffff;
  color: #000000;
  border-color: #ffffff;
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
  font-weight: 600;
  color: var(--console-header-text, #E5E5E5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

[data-theme="light"] .console-title {
  color: #495057;
}

[data-theme="dark"] .console-title {
  color: #e5e5e5;
}

[data-theme="contrast"] .console-title {
  color: #ffffff;
  font-weight: 700;
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
  border: 1px solid var(--console-header-button-border, #464647);
  color: var(--console-header-button-text, #969696);
  padding: 4px 12px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.console-action-btn:hover {
  background: var(--console-header-button-hover, #3A3A3C);
  border-color: var(--accent-color, #007ACC);
  color: var(--text-primary, #FFFFFF);
}

[data-theme="light"] .console-action-btn {
  border: 1px solid #adb5bd;
  color: #6c757d;
}

[data-theme="light"] .console-action-btn:hover {
  background: #e9ecef;
  border-color: #0066cc;
  color: #212529;
}

[data-theme="dark"] .console-action-btn {
  border: 1px solid #565656;
  color: #969696;
}

[data-theme="dark"] .console-action-btn:hover {
  background: #3a3a3c;
  border-color: #007acc;
  color: #ffffff;
}

[data-theme="contrast"] .console-action-btn {
  border: 2px solid #4a4a4a;
  color: #ffffff;
}

[data-theme="contrast"] .console-action-btn:hover {
  background: #2a2a2a;
  border-color: #ffffff;
  color: #ffffff;
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
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  font-weight: 500;
  letter-spacing: 0.02em; /* Consistent character spacing for output */
}

.console-error {
  color: var(--error-color, #F44747);
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.console-input-prompt {
  color: var(--text-primary, #CCCCCC);
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
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

.console-repl-prompt {
  color: var(--accent-color, #007ACC);
  font-weight: bold;
  font-family: monospace;
}

.console-user-input {
  color: var(--text-primary, #CCCCCC);
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-weight: 500;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  letter-spacing: 0.02em; /* Match output character spacing for consistency */
}

/* REPL input with prompt - consistent formatting */
.console-repl-entry {
  margin-bottom: 4px;
}

.console-repl-line {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin: 0;
  line-height: 1.4;
}

.console-repl-prompt {
  color: var(--accent-color, #007ACC);
  font-weight: bold;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  flex-shrink: 0;
}

.console-repl-input {
  color: var(--text-primary, #CCCCCC);
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  font-weight: 500;
  flex: 1;
  letter-spacing: 0.02em; /* Match output character spacing for consistency */
}

/* Continuation lines without prompt - match IDLE shell behavior */
.console-repl-input.no-prompt {
  margin-left: 28px; /* Align with text after >>> prompt */
}

/* Syntax Highlighting Classes for Python */
.python-keyword {
  color: #569cd6; /* Blue for keywords */
  font-weight: 600;
}

.python-string {
  color: #ce9178; /* Light brown for strings */
}

.python-number {
  color: #b5cea8; /* Light green for numbers */
}

.python-comment {
  color: #6a9955; /* Green for comments */
  font-style: italic;
}

.python-builtin {
  color: #dcdcaa; /* Light yellow for built-in functions */
  font-weight: 500;
}

/* Prism.js theme overrides for inline display in REPL */
.console-repl-input pre[class*="language-"] {
  margin: 0;
  padding: 0;
  background: transparent;
  overflow: visible;
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
}

.console-repl-input code[class*="language-"] {
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
  text-shadow: none;
  background: transparent;
  padding: 0;
  letter-spacing: inherit; /* Inherit consistent character spacing */
}

/* Ensure Prism tokens inherit our theme colors */
.console-repl-input .token.keyword {
  color: #569cd6 !important;
  font-weight: 600 !important;
}

.console-repl-input .token.string {
  color: #ce9178 !important;
}

.console-repl-input .token.number {
  color: #b5cea8 !important;
}

.console-repl-input .token.comment {
  color: #6a9955 !important;
  font-style: italic !important;
}

.console-repl-input .token.builtin {
  color: #dcdcaa !important;
  font-weight: 500 !important;
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
  box-sizing: border-box;
  overflow: hidden;
}

/* Right sidebar placeholder when hidden */
.right-sidebar-placeholder {
  width: 0;
  height: 100%;
  background: var(--bg-sidebar, #252526);
  display: none; /* Don't show placeholder to avoid taking space */
  overflow: hidden;
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

.media-preview-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-pattern, #1A1A1A);
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

.two-header-menu {
  position: fixed;
  width: 100%;
  height: 80px;
  top: 0;
  left: 0;
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
    max-width: 250px;
    width: 100%; /* Fill pane container */
  }
  
  .right-sidebar {
    max-width: 350px;
  }
  
  .console-height {
    max-height: 250px;
  }
  
  /* Ensure no gaps in splitpanes at this breakpoint */
  .main-splitpanes.splitpanes--vertical > .splitpanes__pane {
    flex-shrink: 0;
  }
  
  /* Ensure splitpane panes fill their containers */
  .main-splitpanes > .splitpanes__pane:first-child {
    overflow: hidden;
  }
}

@media (max-width: 1200px) {
  .left-sidebar {
    width: 100% !important; /* Fill pane, actual size controlled by splitpanes */
    max-width: 180px;
  }
  
  /* Hide right sidebar completely on medium screens */
  .right-sidebar {
    display: none !important;
    width: 0 !important;
  }
  
  /* Force right pane to have no width */
  .main-splitpanes > .splitpanes__pane:last-child {
    width: 0 !important;
    max-width: 0 !important;
    min-width: 0 !important;
    flex: 0 0 0 !important;
    display: none !important;
  }
  
  /* Hide the right splitter on medium screens */
  .main-splitpanes.splitpanes--vertical > .splitpanes__splitter:last-of-type {
    display: none !important;
    width: 0 !important;
  }
  
  /* Ensure center pane takes remaining space */
  .main-splitpanes > .splitpanes__pane:nth-child(2) {
    flex: 1 1 auto !important;
    width: auto !important;
  }
  
  /* Ensure center frame fills its container */
  .center-frame {
    width: 100% !important;
  }
}

/* Tablet view */
@media (max-width: 1024px) {
  .left-sidebar {
    max-width: 180px;
  }
  
  .right-sidebar {
    max-width: 300px;
  }
}

/* Mobile and small tablet view */
@media (max-width: 900px) {
  /* Hide sidebars on small screens */
  .left-sidebar {
    width: 0 !important;
    display: none;
  }
  
  /* Force splitpanes to single pane layout */
  .main-splitpanes.splitpanes--vertical {
    display: flex !important;
  }
  
  /* Force all panes to have dark background to prevent white gaps */
  .splitpanes__pane {
    background: var(--bg-primary, #1E1E1E) !important;
  }
  
  /* Hide the splitpane container for left sidebar - more specific selectors */
  .main-splitpanes.splitpanes--vertical > .splitpanes__pane:first-child {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    max-width: 0 !important;
    min-width: 0 !important;
    flex: 0 0 0 !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    position: absolute !important;
    left: -9999px !important;
  }
  
  /* Hide ALL splitter handles */
  .main-splitpanes.splitpanes--vertical > .splitpanes__splitter {
    display: none !important;
    width: 0 !important;
  }
  
  /* Make center pane take full width - more specific */
  .main-splitpanes.splitpanes--vertical > .splitpanes__pane:nth-child(2),
  .main-splitpanes.splitpanes--vertical > .splitpanes__pane:nth-child(3) {
    width: 100% !important;
    max-width: 100% !important;
    flex: 1 1 100% !important;
  }
  
  /* Specifically target the center frame to ensure full width */
  #center-frame {
    width: 100% !important;
    left: 0 !important;
    right: 0 !important;
  }
  
  .sidebar-resizer.left {
    display: none;
  }
  
  .center-frame {
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
  }
  
  .right-sidebar {
    display: none !important;
  }
  
  /* Hide the splitpane container for right sidebar - more specific */
  .main-splitpanes.splitpanes--vertical > .splitpanes__pane:last-child {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    max-width: 0 !important;
    min-width: 0 !important;
    flex: 0 0 0 !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    position: absolute !important;
    right: -9999px !important;
  }
  
  .sidebar-resizer.right {
    display: none;
  }
  
  /* Adjust console for mobile */
  .console-header {
    height: 40px;
  }
  
  .console-title {
    font-size: 14px;
  }
}

/* Very small mobile screens */
@media (max-width: 480px) {
  
  .console-header {
    height: 36px;
  }
  
  .console-action-btn {
    padding: 4px 8px;
    font-size: 12px;
  }
  
  .editor-tab-bar {
    font-size: 12px;
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
  background: var(--bg-primary, #1E1E1E) !important;
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

/* Fix white background on all splitpanes panes */
.splitpanes__pane {
  background: transparent !important;
  transition: none; /* Prevent transition gaps */
}

/* Ensure main splitpanes have proper background */
.main-splitpanes > .splitpanes__pane {
  background: var(--bg-primary, #1E1E1E) !important;
  overflow: hidden; /* Prevent content overflow during resize */
}

/* Specific fix for left sidebar pane to prevent gaps */
.main-splitpanes > .splitpanes__pane:first-child {
  min-width: 0;
  flex-shrink: 0;
}

/* Fix for right sidebar pane to prevent gaps */
.main-splitpanes > .splitpanes__pane:last-child {
  min-width: 0;
  transition: none;
}

/* Special rule for 1100-1200px range to prevent right sidebar gaps */
@media (min-width: 1100px) and (max-width: 1200px) {
  .main-splitpanes > .splitpanes__pane:last-child {
    width: 0 !important;
    max-width: 0 !important;
    display: none !important;
  }
  
  .main-splitpanes > .splitpanes__pane:nth-child(2) {
    flex: 1 1 auto !important;
    width: calc(100% - var(--left-sidebar-width, 180px)) !important;
  }
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

/* Disable right splitter when right panel is empty */
.main-splitpanes.splitpanes--vertical > .splitpanes__splitter:last-of-type {
  pointer-events: none;
  cursor: default;
  opacity: 0.3;
}

/* Enable right splitter only when right panel has content */
.main-splitpanes.splitpanes--vertical.has-right-content > .splitpanes__splitter:last-of-type {
  pointer-events: auto;
  cursor: col-resize;
  opacity: 1;
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

[data-theme="light"] .media-preview-panel {
  background: var(--bg-pattern, #f8f8f8);
}

[data-theme="light"] .output-panel {
  background: var(--bg-primary, #ffffff);
  color: var(--text-primary, #333333);
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

[data-theme="high-contrast"] .media-preview-panel {
  background: var(--bg-pattern, #0f0f0f);
}

[data-theme="high-contrast"] .output-panel {
  background: var(--bg-primary, #000000);
  color: var(--text-primary, #ffffff);
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
