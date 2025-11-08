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
      <!-- Main horizontal layout with splitpanes -->
      <splitpanes class="default-theme" @resized="onMainPaneResized">
        <!-- Left sidebar pane -->
        <pane v-if="leftSidebarVisible" :size="leftPaneSize" :min-size="10" :max-size="40">
          <div class="left-sidebar">
            <ProjTree 
              v-on:get-item="getFile"
              @context-menu="showContextMenu"
            ></ProjTree>
          </div>
        </pane>
        
        <!-- Center content pane -->
        <pane :size="centerPaneSize">
          <!-- Vertical split for editor and console -->
          <splitpanes horizontal class="editor-console-split" @resized="onEditorConsoleResized">
            <!-- Editor pane -->
            <pane :size="editorPaneSize" :min-size="30">
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
            
            <!-- Console pane -->
            <pane :size="consolePaneSize" :min-size="5" :max-size="70">
              <div class="console-section">
                <div class="console-header">
                  <div class="console-header-left">
                    <span class="console-title">{{ isReplMode ? 'Python REPL' : 'Console' }}</span>
                  </div>
                  <div class="console-header-center">
                    <button class="console-expand-arrow" 
                            @click="expandConsole" 
                            title="Maximize console"
                            v-if="!consoleMaximized">
                      <ChevronUp :size="16" />
                    </button>
                    <button class="console-expand-arrow" 
                            @click="restoreConsole" 
                            title="Restore console"
                            v-if="consoleMaximized">
                      <Minimize2 :size="16" />
                    </button>
                  </div>
                  <div class="console-header-right">
                    <button class="console-toggle-btn" @click="toggleReplMode" :class="{ active: isReplMode }">
                      {{ isReplMode ? 'Console' : 'REPL' }}
                    </button>
                    <button class="console-collapse-btn" @click="toggleConsole">
                      <ChevronDown :size="16" />
                    </button>
                  </div>
                </div>
                <div class="console-content">
                  <component 
                    :is="currentConsoleComponent"
                    v-if="wsInfo && wsInfo.connected"
                    :is-repl-mode="isReplMode"
                    :repl-session-id="replSessionId"
                    @session-started="handleReplSessionStarted"
                    @session-ended="handleReplSessionEnded"
                  />
                </div>
              </div>
            </pane>
          </splitpanes>
        </pane>
        
        <!-- Right sidebar pane -->
        <pane v-if="rightSidebarVisible && previewTabs.length > 0" :size="rightPaneSize" :min-size="15" :max-size="40">
          <div class="right-sidebar">
            <div class="preview-tabs">
              <div class="preview-tabs-header">
                <span>Preview</span>
                <button @click="closeAllPreviews" class="close-all-btn">✕</button>
              </div>
              <div class="preview-tabs-list">
                <div v-for="(tab, index) in previewTabs" 
                     :key="index" 
                     class="preview-tab"
                     :class="{ active: selectedPreviewTab === index }"
                     @click="selectPreviewTab(index)">
                  <span>{{ tab.title }}</span>
                  <button @click.stop="closePreviewTab(index)" class="tab-close">✕</button>
                </div>
              </div>
            </div>
            <template v-for="(tab, index) in previewTabs" :key="index">
              <div v-show="selectedPreviewTab === index" class="preview-content">
                <div v-if="tab.type === 'html'" class="html-preview-panel">
                  <iframe :src="tab.content" frameborder="0"></iframe>
                </div>
                <div v-else-if="tab.type === 'image'" class="image-preview-panel">
                  <img :src="tab.content" :alt="tab.title" />
                </div>
                <div v-else-if="tab.type === 'pdf'" class="pdf-preview-panel">
                  <iframe :src="tab.content" frameborder="0"></iframe>
                </div>
                <div v-else-if="tab.type === 'data'" class="data-preview-panel">
                  <CsvViewer :content="tab.content" />
                </div>
              </div>
            </template>
          </div>
        </pane>
      </splitpanes>
    </div>
    
    <!-- Dialogs remain the same -->
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
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

// Import other components (simplified for brevity)
export default {
  name: 'VmIdeWithSplitpanes',
  components: {
    Splitpanes,
    Pane,
    // Add all other components here from original
  },
  data() {
    return {
      // Splitpane sizes
      leftPaneSize: 20,
      centerPaneSize: 60,
      rightPaneSize: 20,
      editorPaneSize: 70,
      consolePaneSize: 30,
      
      // Other data properties from original
      leftSidebarVisible: true,
      rightSidebarVisible: false,
      consoleMaximized: false,
      isReplMode: false,
      replSessionId: null,
      previewTabs: [],
      selectedPreviewTab: 0,
      
      // Add all other data properties from original VmIde.vue
    }
  },
  computed: {
    currentConsoleComponent() {
      // Return appropriate console component
      return 'UnifiedConsole' // or DualModeREPL based on your setup
    },
    centerPaneSize() {
      if (this.rightSidebarVisible && this.previewTabs.length > 0) {
        return 100 - this.leftPaneSize - this.rightPaneSize
      }
      return 100 - this.leftPaneSize
    }
  },
  mounted() {
    // Load saved pane sizes from localStorage
    try {
      const savedLeftPaneSize = localStorage.getItem('ide_leftPaneSize')
      const savedRightPaneSize = localStorage.getItem('ide_rightPaneSize')
      const savedEditorPaneSize = localStorage.getItem('ide_editorPaneSize')
      const savedConsolePaneSize = localStorage.getItem('ide_consolePaneSize')

      if (savedLeftPaneSize) {
        const size = parseFloat(savedLeftPaneSize)
        if (size >= 10 && size <= 40) {
          this.leftPaneSize = size
        }
      }

      if (savedRightPaneSize) {
        const size = parseFloat(savedRightPaneSize)
        if (size >= 15 && size <= 40) {
          this.rightPaneSize = size
        }
      }

      if (savedEditorPaneSize) {
        const size = parseFloat(savedEditorPaneSize)
        if (size >= 30 && size <= 95) {
          this.editorPaneSize = size
        }
      }

      if (savedConsolePaneSize) {
        const size = parseFloat(savedConsolePaneSize)
        if (size >= 5 && size <= 70) {
          this.consolePaneSize = size
        }
      }
    } catch (e) {
      console.warn('Failed to load saved pane sizes from localStorage:', e)
    }
  },
  methods: {
    toggleConsole() {
      if (this.consolePaneSize > 10) {
        this.consolePaneSize = 5
      } else {
        this.consolePaneSize = 30
      }
    },
    expandConsole() {
      this.consoleMaximized = true
      this.consolePaneSize = 70
    },
    restoreConsole() {
      this.consoleMaximized = false
      this.consolePaneSize = 30
    },
    toggleLeftSidebar(visible) {
      this.leftSidebarVisible = visible
    },
    toggleReplMode() {
      this.isReplMode = !this.isReplMode
    },

    // Splitpanes resize event handlers
    onMainPaneResized(panes) {
      // Update pane sizes when user drags the splitter
      // panes is an array of objects with {min, max, size} for each pane
      if (panes && panes.length >= 2) {
        // Update left pane size
        if (this.leftSidebarVisible) {
          this.leftPaneSize = panes[0].size
        }

        // Center pane size is computed, no need to update

        // Update right pane size if visible
        if (this.rightSidebarVisible && panes.length >= 3) {
          this.rightPaneSize = panes[2].size
        }

        // Save to localStorage for persistence
        try {
          localStorage.setItem('ide_leftPaneSize', this.leftPaneSize.toString())
          if (this.rightSidebarVisible) {
            localStorage.setItem('ide_rightPaneSize', this.rightPaneSize.toString())
          }
        } catch (e) {
          console.warn('Failed to save pane sizes to localStorage:', e)
        }
      }
    },

    onEditorConsoleResized(panes) {
      // Update editor and console pane sizes
      if (panes && panes.length >= 2) {
        this.editorPaneSize = panes[0].size
        this.consolePaneSize = panes[1].size

        // Update consoleMaximized state based on size
        this.consoleMaximized = this.consolePaneSize >= 65

        // Save to localStorage
        try {
          localStorage.setItem('ide_editorPaneSize', this.editorPaneSize.toString())
          localStorage.setItem('ide_consolePaneSize', this.consolePaneSize.toString())
        } catch (e) {
          console.warn('Failed to save editor/console sizes to localStorage:', e)
        }
      }
    },

    // Add all other methods from original VmIde.vue
  }
}
</script>

<style scoped>
/* Import the custom splitpanes styles */
@import './styles/splitpanes-custom.css';

/* Keep all existing styles from original VmIde.vue */

/* Override splitpanes specific styles */
.splitpanes.default-theme .splitpanes__splitter {
  background-color: var(--border-primary, #3c3c3c);
  transition: background-color 0.15s ease;
}

.splitpanes.default-theme .splitpanes__splitter:hover {
  background-color: var(--accent-color, #007ACC);
}

.splitpanes--horizontal > .splitpanes__splitter {
  height: 5px;
  cursor: ns-resize;
}

.splitpanes--vertical > .splitpanes__splitter {
  width: 5px;
  cursor: col-resize;
}

/* Ensure proper height for total-frame */
#total-frame {
  height: calc(100vh - 40px); /* Adjust based on top menu height */
}

#total-frame .splitpanes {
  height: 100%;
}

.left-sidebar,
.editor-section,
.console-section,
.right-sidebar {
  height: 100%;
  overflow: auto;
}
</style>