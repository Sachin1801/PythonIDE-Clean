<template>
  <div class="top-menu-container">
    <div class="icon-btn float-left" @click="backHome" title="Back">
      <ArrowLeft :size="24" />
    </div>
    <!-- Project List button hidden - all projects shown by default -->
    <!-- <div class="icon-btn float-left" @click="listProjects()" title="Project List">
      <FolderOpen :size="20" />
    </div> -->
    <div v-if="ideInfo && ideInfo.nodeSelected !== null && (ideInfo.nodeSelected.type === 'dir' || ideInfo.nodeSelected.type === 'folder')" class="icon-btn float-left" @click="newFile()" title="New File">
      <FilePlus :size="20" />
    </div>
    <div v-else class="icon-btn float-left disable-icon" title="New File">
      <FilePlus :size="20" />
    </div>
    <div v-if="ideInfo && ideInfo.nodeSelected !== null && (ideInfo.nodeSelected.type === 'dir' || ideInfo.nodeSelected.type === 'folder')" class="icon-btn float-left" @click="newFolder()" title="New Folder">
      <FolderPlus :size="20" />
    </div>
    <div v-else class="icon-btn float-left disable-icon" title="New Folder">
      <FolderPlus :size="20" />
    </div>
    <div v-if="ideInfo && ideInfo.nodeSelected !== null" class="icon-btn float-left" @click="rename()" title="Rename">
      <Edit2 :size="20" />
    </div>
    <div v-else class="icon-btn float-left disable-icon" title="Rename">
      <Edit2 :size="20" />
    </div>
    <div v-if="ideInfo && ideInfo.nodeSelected !== null && ideInfo.nodeSelected.path !== '/'" class="icon-btn float-left" @click="delFile()" title="Delete">
      <Trash2 :size="20" />
    </div>
    <div v-else class="icon-btn float-left disable-icon" title="Delete">
      <Trash2 :size="20" />
    </div>
    <!-- Upload/Import Button -->
    <div class="icon-btn float-left" @click="openUploadDialog()" title="Import File">
      <Upload :size="20" />
    </div>
    <!-- Download Button -->
    <div v-if="ideInfo && ideInfo.nodeSelected !== null && ideInfo.nodeSelected.type === 'file'" class="icon-btn float-left" @click="downloadFile()" title="Download File">
      <Download :size="20" />
    </div>
    <div v-else class="icon-btn float-left disable-icon" title="Select a file to download">
      <Download :size="20" />
    </div>
    <!-- Run Button -->
    <div class="icon-btn float-left" v-if="isPythonFile && !consoleLimit" @click="$emit('run-item')" title="Run current selected script">
      <Play :size="20" />
    </div>
    <div class="icon-btn float-left disable-icon" v-if="!isPythonFile && !consoleLimit" title="Cannot run, current selected file is not a Python file">
      <Play :size="20" />
    </div>
    <!-- Stop Button -->
    <div class="icon-btn float-left" @click="stopAll()" v-if="hasRunProgram" title="Stop all running scripts">
      <Square :size="20" />
    </div>
    <!-- Theme Toggle Button -->
    <div class="icon-btn float-left" @click="toggleTheme" :title="isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
      <Moon v-if="isDarkMode" :size="20" />
      <Sun v-else :size="20" />
    </div>
  </div>
</template>

<script>
import { ArrowLeft, Moon, Sun, FilePlus, FolderPlus, Edit2, Trash2, Square, Play, Upload, Download } from 'lucide-vue-next';
// import * as types from '../../../../store/mutation-types';
const path = require('path');

export default {
  props: {
    consoleLimit: Boolean,
    hasRunProgram: Boolean,
  },
  data() {
    return {
      isRun: true,
      isDarkMode: localStorage.getItem('theme') === 'dark' || true, // Default to dark mode
    }
  },
  computed: {
    ideInfo() {
      return this.$store?.state?.ide?.ideInfo || {};
    },
    isPythonFile() {
      return this.ideInfo.currProj && 
             this.ideInfo.currProj.pathSelected !== null && 
             this.ideInfo.codeItems && 
             this.ideInfo.codeItems.length > 0 && 
             this.ideInfo.currProj.pathSelected.endsWith('.py');
    },
  },
  components: {
    ArrowLeft,
    Moon,
    Sun,
    FilePlus,
    FolderPlus,
    Edit2,
    Trash2,
    Square,
    Play,
    Upload,
    Download,
  },
  mounted() {
    // Initialize theme on mount
    const savedTheme = localStorage.getItem('theme') || 'dark';
    this.isDarkMode = savedTheme === 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
  },
  methods: {
    backHome() {
      this.$router.push('/');
    },
    listProjects() {
      this.$emit('setProjsDialog', {});
    },
    newFile() {
      this.$emit('setTextDialog', {
        type: 'create-file',
        title: 'New File',
        text: '',
        tips: ''
      });
    },
    newFolder() {
      this.$emit('setTextDialog', {
        type: 'create-folder',
        title: 'New Folder',
        text: '',
        tips: ''
      });
    },
    rename() {
      if (!this.ideInfo || !this.ideInfo.nodeSelected) return;
      
      let dialogType = '';
      let dialogTitle = ''; 
      let dialogInputText = '';
      if (this.ideInfo.nodeSelected.path === '/') {
        dialogType = 'rename-project';
        dialogTitle = `Rename Project (${this.ideInfo.currProj?.data?.name || 'Unknown'})`
        dialogInputText = `${this.ideInfo.currProj?.data?.name || ''}`;
      }
      else if (this.ideInfo.nodeSelected.type === 'dir' || this.ideInfo.nodeSelected.type === 'folder') {
        const name = path.basename(this.ideInfo.nodeSelected.path);
        dialogType = 'rename-folder';
        dialogTitle = `Rename Folder (${this.ideInfo.nodeSelected.path})`
        dialogInputText = `${name}`;
      }
      else {
        const name = path.basename(this.ideInfo.currProj?.pathSelected || this.ideInfo.nodeSelected.path);
        dialogType = 'rename-file';
        dialogTitle = `Rename File (${this.ideInfo.currProj?.pathSelected || this.ideInfo.nodeSelected.path})`
        dialogInputText = `${name}`;
      }
      this.$emit('setTextDialog', {
        type: dialogType,
        title: dialogTitle,
        text: dialogInputText,
        tips: ''
      });
    },
    delFile() {
      if (!this.ideInfo || !this.ideInfo.nodeSelected) return;
      
      this.$emit('setDelDialog', {
        type: '',
        title: `Delete ${path.basename(this.ideInfo.nodeSelected.path)}?`,
        text: '',
        tips: ''
      });
    },
    // run() {
    //   let selected = false;
    //   if (this.ideInfo.consoleSelected.run === false && this.ideInfo.consoleSelected.path === this.ideInfo.currProj.pathSelected) {
    //     selected = true;
    //     this.$store.commit('ide/assignConsoleSelected', {
    //       stop: false,
    //       resultList: []
    //     });
    //   }
    //   else {
    //     for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
    //       if (this.ideInfo.consoleItems[i].run === false && this.ideInfo.consoleItems[i].path === this.ideInfo.currProj.pathSelected) {
    //         this.$store.commit('ide/setConsoleSelected', this.ideInfo.consoleItems[i]);
    //         selected = true;
    //         this.$store.commit('ide/assignConsoleSelected', {
    //           stop: false,
    //           resultList: []
    //         });
    //         break;
    //       }
    //     }
    //   }
    //   if (selected === false) {
    //     for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
    //       if (this.ideInfo.consoleItems[i].run === false && !(this.ideInfo.consoleItems[i].name === 'Terminal' && this.ideInfo.consoleItems[i].path === 'Terminal')) {
    //         this.$store.commit('ide/spliceConsoleItems', {start: i, count: 1});
    //         break;
    //       }
    //     }
    //     const item = {
    //       name: path.basename(this.ideInfo.currProj.pathSelected),
    //       path: this.ideInfo.currProj.pathSelected,
    //       resultList: [],
    //       run: false,
    //       stop: false,
    //       id: this.ideInfo.consoleId,
    //     }
    //     this.$store.commit('ide/addConsoleItem', item);
    //     this.$store.commit('ide/setConsoleSelected', item);
    //   }
    //   else {
    //     this.$store.commit('ide/assignConsoleSelected', {
    //       id: this.ideInfo.consoleId
    //     });
    //   }
    //   // for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
    //   //   if (this.ideInfo.consoleItems[i].run === false && !(this.ideInfo.consoleItems[i].name === 'Terminal' && this.ideInfo.consoleItems[i].path === 'Terminal')) {
    //   //     this.$store.commit('ide/spliceConsoleItems', {start: i, count: 1});
    //   //     break;
    //   //   }
    //   // }
    //   // const item = {
    //   //   name: path.basename(this.ideInfo.currProj.pathSelected),
    //   //   path: this.ideInfo.currProj.pathSelected,
    //   //   resultList: [],
    //   //   run: false,
    //   //   stop: false,
    //   //   id: this.ideInfo.consoleId,
    //   // }
    //   // this.$store.commit('ide/addConsoleItem', item);
    //   // this.$store.commit('ide/setConsoleSelected', item);

    //   if (!this.ideInfo.consoleItems.includes(this.ideInfo.consoleSelected)) {
    //     this.$store.commit('ide/addConsoleItem', this.ideInfo.consoleSelected);
    //   }
    //   this.$store.dispatch(`ide/${types.IDE_RUN_PYTHON_PROGRAM}`, {
    //     msgId: this.ideInfo.consoleId,
    //     filePath: this.ideInfo.currProj.pathSelected,
    //     callback: {
    //       limits: -1,
    //       callback: (dict) => {
    //         this.$store.commit('ide/handleRunResult', dict);
    //       }
    //     }
    //   });
    //   this.$store.commit('ide/setConsoleId', this.ideInfo.consoleId + 1);
    // },
    // stop(consoleId) {
    //   this.$store.dispatch(`ide/${types.IDE_STOP_PYTHON_PROGRAM}`, {
    //     consoleId: consoleId,
    //     callback: {
    //       limits: -1,
    //       callback: (dict) => {
    //         this.$store.commit('ide/handleStopResult', {
    //           consoleId: consoleId,
    //           dict: dict
    //         });
    //       }
    //     }
    //   });
    // },
    stopAll() {
      if (!this.ideInfo || !this.ideInfo.consoleItems) return;
      
      for (let i = 0; i < this.ideInfo.consoleItems.length; i++) {
        if (this.ideInfo.consoleItems[i].run === true) {
          this.$emit('stop-item', this.ideInfo.consoleItems[i].id);
          // this.stop(this.ideInfo.consoleItems[i].id);
        }
      }
      this.$emit('stop-item', null);
      // this.stop(null);
    },
    toggleTheme() {
      this.isDarkMode = !this.isDarkMode;
      const theme = this.isDarkMode ? 'dark' : 'light';
      localStorage.setItem('theme', theme);
      document.documentElement.setAttribute('data-theme', theme);
      this.$emit('theme-changed', theme);
    },
    toggleWordWrap() {
      this.$emit('toggle-word-wrap');
    },
    openUploadDialog() {
      this.$emit('open-upload-dialog');
    },
    downloadFile() {
      if (!this.ideInfo || !this.ideInfo.nodeSelected || this.ideInfo.nodeSelected.type !== 'file') return;
      
      const fileName = path.basename(this.ideInfo.nodeSelected.path);
      const filePath = this.ideInfo.nodeSelected.path;
      const projectName = this.ideInfo.nodeSelected.projectName || this.ideInfo.currProj?.data?.name;
      
      // Emit event to parent to handle download
      this.$emit('download-file', {
        fileName,
        filePath,
        projectName
      });
    }
  }
}
</script>

<style scoped>
.icon-btn {
  margin: 13px 8px;
  padding: 6px;
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #ffffff;
  border-radius: 4px;
}
.icon-btn:hover {
  transform: scale(1.1);
  color: #409eff;
  background: rgba(64, 158, 255, 0.2);
}
.icon-btn.float-left {
  margin-left: 12px;
  margin-right: 12px;
}
.icon-btn.float-left:first-child {
  margin-left: 16px;
}
.icon-btn.float-right {
  margin-left: 12px;
  margin-right: 12px;
}
.icon-btn.float-right:last-of-type {
  margin-right: 20px;
}
.disable-icon {
  opacity: 0.4;
  cursor: not-allowed;
  color: rgba(255, 255, 255, 0.4);
}
.disable-icon:hover {
  transform: none;
  color: rgba(255, 255, 255, 0.4);
  background: none;
}
.top-menu-container {
  width: 100%;
  height: 50px;
  background: #313131;
  display: flex;
  align-items: center;
}
</style>