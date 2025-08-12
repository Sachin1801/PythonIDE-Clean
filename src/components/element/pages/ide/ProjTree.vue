<template>
  <div class="proj-tree-container">
    <div class="tree-header">
      <span class="tree-title">Project Files</span>
      <div class="refresh-btn" @click="refreshTree" title="Refresh">
        <RefreshCw :size="16" />
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
      >
      <template #default="{ node, data }">
        <span>
          <img :src="getIconUrl(data)" alt="" class="node-icon" />
          <span class="node-label">{{ node.label }}</span>
        </span>
      </template>
    </el-tree>
  </div>
</template>

<script>
import * as types from '../../../../store/mutation-types';
import { getIconForFile, getIconForFolder, getIconForOpenFolder } from 'vscode-icons-js';
import { RefreshCw } from 'lucide-vue-next';
import { ElMessage } from 'element-plus';

export default {
  components: {
    RefreshCw,
  },
  data() {
    return {
      getFile: true,
      treeProps: {
        uuid: 'uuid',
        label: 'label',
        children: 'children',
      },
    }
  },
  methods: {
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
                  // Update current project if it was refreshed
                  const currentProjData = refreshedProjects.find(p => p.name === self.ideInfo.currProj.data.name);
                  if (currentProjData) {
                    self.$store.commit('ide/handleProject', currentProjData);
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
              self.$store.commit('ide/handleProject', dict.data);
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
      this.$store.commit('ide/setNodeSelected', data);
      
      // In multi-root mode, we need to set the correct project as current
      if (this.ideInfo.multiRootData && data.projectName) {
        // Find and set the project that contains this file
        const project = this.ideInfo.allProjects.find(p => p.name === data.projectName);
        if (project) {
          this.$store.commit('ide/handleProject', project);
        }
      }
      
      if (data.type === 'file')
        this.$emit('get-item', data.path);
      // if (this.getFile === true && data.type === 'file') {
      //   this.$emit('get-item', data.path);
      // }
      // this.getFile = true;
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
    treeData() {
      // Use multi-root data if available, otherwise fall back to single project
      if (this.ideInfo.multiRootData && this.ideInfo.multiRootData.children.length > 0) {
        return this.ideInfo.multiRootData.children;
      }
      return this.ideInfo.currProj.data ? [this.ideInfo.currProj.data] : [];
    },
    expandedKeys() {
      return this.ideInfo ? this.ideInfo.currProj.expandedKeys : [];
    },
    defaultExpandedKeys() {
      const expandedKeys = [];
      
      // Always expand root folders in multi-root mode
      if (this.ideInfo.multiRootData && this.ideInfo.multiRootData.children.length > 0) {
        this.ideInfo.multiRootData.children.forEach(project => {
          if (project.uuid) {
            expandedKeys.push(project.uuid);
          }
        });
      }
      
      // Also process existing expanded keys
      if (this.expandedKeys !== undefined) {
        for (let i = 0; i < this.expandedKeys.length; i++) {
          let prefix = '';
          const tmp = this.expandedKeys[i].split('/');
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
  background-color: #383B3D;
}
.ide-project-list .el-tree-node__content:hover {
  /* style when mouse hovers over node */
  background-color: #383B3D;
}
.ide-project-list .el-tree-node:focus>.el-tree-node__content {
  /* style for selected nodes with children */
  /* background-color: rgb(26, 37, 51); */
  background: #383B3D;
  /* color: #FFF; */
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

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  color: #CCCCCC;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #409eff;
}

.refresh-btn:hover svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
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
}
</style>


