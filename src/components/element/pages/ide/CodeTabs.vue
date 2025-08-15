<template>
  <!-- Single Combined Tabs Container -->
  <div class="code-tabs-container">
    <!-- Sidebar Toggle Button (on left) -->
    <button 
      v-if="sidebarVisible"
      class="sidebar__contract" 
      @click="toggleSidebar"
      aria-label="Close files navigation"
      title="Hide file explorer"
    >
      <ChevronLeft :size="16" />
    </button>
    <button 
      v-else
      class="sidebar__expand" 
      @click="toggleSidebar"
      aria-label="Open files navigation"
      title="Show file explorer"
    >
      <ChevronRight :size="16" />
    </button>
    
    <!-- Tabs List -->
    <div class="code-tab-list">
      <button
        v-for="item in codeItems"
        :key="item.path"
        :class="['code-tab', { 'active': pathSelected === item.path }]"
        @click="selectTab(item)"
      >
        <img :src="getIconUrl(item.path)" alt="" class="tab-file-icon" />
        <span class="tab-file-name">
          {{ getTabLabel(item) }}
        </span>
        <span 
          class="tab-close-btn" 
          @click.stop="removeTab(item)"
          title="Close"
        >
          ×
        </span>
      </button>
    </div>
    
    <!-- Tab Actions (on right) -->
    <div class="tab-actions">
      <!-- Tab count indicator -->
      <span class="tab-count-indicator" v-if="codeItems.length > 0">
        {{ codeItems.length }}/5
      </span>
    </div>
  </div>
</template>

<script>
import { getIconForFile } from 'vscode-icons-js';
import { ChevronLeft, ChevronRight } from 'lucide-vue-next';

export default {
  data() {
    return {
      sidebarVisible: true
    };
  },
  mounted() {
  },
  methods: {
    toggleSidebar() {
      this.sidebarVisible = !this.sidebarVisible;
      this.$emit('toggle-sidebar', this.sidebarVisible);
    },
    getIconUrl(path) {
      return require(`@/assets/vscode-icons/${getIconForFile(path.substring(path.lastIndexOf('.') + 1))}`);
    },
    getItem(path) {
      for (let i = 0; i < this.ideInfo.codeItems.length; i++) {
        if (this.ideInfo.codeItems[i].path === path) {
          return this.ideInfo.codeItems[i];
        }
      }
      return '';
    },
    getTabLabel(item) {
      // Check if there are files from different projects
      const projectNames = new Set(this.codeItems.map(i => i.projectName).filter(p => p));
      
      // If files are from multiple projects, show project name in the label
      if (projectNames.size > 1 && item.projectName) {
        return `${item.name} [${item.projectName}]`;
      }
      
      return item.name;
    },
    selectTab(item) {
      this.$emit('select-item', item);
    },
    removeTab(item) {
      this.$emit('close-item', item);
    }
  },
  watch: {
  },
  computed: {
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
    codeItems() {
      return this.ideInfo.codeItems;
    },
    currentFileName() {
      const selected = this.codeItems.find(item => item.path === this.pathSelected);
      return selected ? selected.name : 'No file selected';
    },
    pathSelected: {
      get() {
        return this.ideInfo.currProj.pathSelected;
      },
      set(val) {
        const item = this.getItem(val);
        if (!item) return;
        this.$emit('select-item', item);
      }
    }
  },
  components: {
    ChevronLeft,
    ChevronRight
  },
};
</script>

<style scoped>
/* Container for the entire tab bar */
.code-tabs-container {
  height: 35px;
  background: var(--bg-secondary, #2A2A2D);
  border-bottom: 1px solid var(--border-primary, #3c3c3c);
  display: flex;
  align-items: center;
  padding: 0 4px;
  user-select: none;
  gap: 4px;
}

/* Sidebar Toggle Buttons */
.sidebar__contract,
.sidebar__expand {
  background: transparent;
  border: none;
  padding: 6px 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: var(--text-secondary, #B5B5B5);
  flex-shrink: 0;
  border-right: 1px solid var(--border-color, #3c3c3c);
  margin-right: 8px;
  border-radius: 4px;
}

.sidebar__contract:hover,
.sidebar__expand:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary, #FFFFFF);
}

/* Tab list container */
.code-tab-list {
  display: flex;
  flex: 1;
  overflow-x: auto;
  gap: 2px;
  align-items: center;
  height: 100%;
}

/* Hide scrollbar but keep functionality */
.code-tab-list::-webkit-scrollbar {
  height: 3px;
}

.code-tab-list::-webkit-scrollbar-track {
  background: transparent;
}

.code-tab-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.code-tab-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Individual tab styling */
.code-tab {
  background: transparent;
  border: none;
  color: var(--text-secondary, #969696);
  padding: 6px 8px;
  padding-right: 28px; /* Space for close button */
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 4px;
  position: relative;
  min-width: 100px;
  max-width: 200px;
  transition: all 0.2s ease;
  font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  white-space: nowrap;
  height: 28px;
  border-bottom: 2px solid transparent;
}

/* Tab hover state */
.code-tab:hover {
  background: var(--bg-hover, #2F2F31);
  color: var(--text-primary, #CCCCCC);
}

/* Active tab */
.code-tab.active {
  background: var(--bg-active, #1E1E1E);
  color: var(--text-primary, #FFFFFF);
  border-bottom-color: var(--accent-color, #007ACC);
}

/* File icon in tab */
.tab-file-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* File name in tab */
.tab-file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: left;
  font-weight: 400;
  letter-spacing: 0.3px;
}

/* Close button */
.tab-close-btn {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  font-size: 18px;
  line-height: 1;
  color: var(--text-secondary, #969696);
  opacity: 0;
  transition: all 0.2s ease;
}

/* Show close button on tab hover */
.code-tab:hover .tab-close-btn {
  opacity: 1;
}

/* Close button hover */
.tab-close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary, #FFFFFF);
}

/* Tab count indicator */
.tab-count-indicator {
  font-size: 11px;
  color: var(--text-secondary, #969696);
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
  margin-right: 8px;
  font-weight: 500;
  white-space: nowrap;
}

/* Tab actions area */
.tab-actions {
  display: flex;
  gap: 4px;
  padding: 0 4px;
}


/* Light theme support */
[data-theme="light"] .code-tabs-container {
  background: #f3f3f3;
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .code-tab {
  color: #616161;
}

[data-theme="light"] .code-tab:hover {
  background: #e8e8e8;
  color: #333333;
}

[data-theme="light"] .code-tab.active {
  background: #ffffff;
  color: #333333;
  border-bottom-color: #007ACC;
}

[data-theme="light"] .tab-close-btn {
  color: #616161;
}

[data-theme="light"] .tab-close-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: #333333;
}
</style>
