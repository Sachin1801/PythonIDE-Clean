import * as types from '../mutation-types';
const path = require('path');

const ideInfo = {
  codeHeight: 0,
  codeItems: [],
  consoleItems: [],
  codeSelected: {},
  consoleSelected: {},
  consoleId: 10001,
  currProj: {
    config: {},
    data: {},
    expandedKeys: [],
    pathSelected: null,
  },
  allProjects: [], // Store all loaded projects
  multiRootData: null, // Combined tree data for multiple projects
  treeRef: null,
  nodeSelected: null,
  projList: [],
  // Fullscreen preview state
  fullscreenPreview: {
    active: false,
    file: null,
    content: null
  }
}

const state = {
  ideInfo: ideInfo
};

const getters = {
  ideInfo(state) {
    return state.ideInfo;
  }
};

const mutations = {
  addConsoleOutput(state, { id, type, text }) {
    for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
      if (state.ideInfo.consoleItems[i].id === id) {
        state.ideInfo.consoleItems[i].resultList.push({ type, text });
        break;
      }
    }
  },
  clearConsoleOutput(state, consoleId) {
    for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
      if (state.ideInfo.consoleItems[i].id === consoleId) {
        state.ideInfo.consoleItems[i].resultList = [];
        break;
      }
    }
  },
  setConsoleWaiting(state, { id, waiting, prompt }) {
    for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
      if (state.ideInfo.consoleItems[i].id === id) {
        state.ideInfo.consoleItems[i].waitingForInput = waiting;
        if (prompt !== undefined) {
          state.ideInfo.consoleItems[i].inputPrompt = prompt;
        }
        // Clear prompt when not waiting
        if (!waiting) {
          state.ideInfo.consoleItems[i].inputPrompt = '';
        }
        console.log(`[STORE] Console ${id} waiting state set to:`, waiting);
        break;
      }
    }
  },
  pushConsoleItem(state, consoleItem) {
    // Check if item already exists
    const exists = state.ideInfo.consoleItems.find(item => item.id === consoleItem.id);
    if (!exists) {
      state.ideInfo.consoleItems.push(consoleItem);
    }
  },
  selectConsoleItem(state, consoleId) {
    const consoleItem = state.ideInfo.consoleItems.find(item => item.id === consoleId);
    if (consoleItem) {
      state.ideInfo.consoleSelected = consoleItem;
    }
  },
  handleProjects(state, data) {
    state.ideInfo.projList = data;
    let lastAccessTime = 0;
    for (var i = 0; i < state.ideInfo.projList.length; i++) {
      if (state.ideInfo.projList[i].lastAccessTime > lastAccessTime) {
        lastAccessTime = state.ideInfo.projList[i].lastAccessTime;
        state.ideInfo.currProj.config.name = state.ideInfo.projList[i].name;
      }
    }
  },
  handleProject(state, data) {
    // Don't clear codeItems to preserve open tabs across project switches
    // state.ideInfo.codeItems = [];
    state.ideInfo.currProj.expandedKeys = [];
    state.ideInfo.currProj.config = data.config || {};
    state.ideInfo.currProj.data = data;
    state.ideInfo.currProj.pathSelected = state.ideInfo.currProj.config.selectFilePath;
    if (data.config !== undefined && data.config.expendKeys !== undefined) {
      state.ideInfo.currProj.expandedKeys = data.config.expendKeys;
      state.ideInfo.currProj.expandedKeys.sort();
    }
    if (state.ideInfo.currProj.pathSelected && state.ideInfo.treeRef) {
      state.ideInfo.nodeSelected = state.ideInfo.treeRef.getCurrentNode();
    }
  },
  handleMultipleProjects(state, projects) {
    // Store all projects
    state.ideInfo.allProjects = projects;
    
    // Create a virtual root with all projects as children
    const multiRoot = {
      label: 'Projects',
      path: '/',
      type: 'root',
      uuid: 'root',
      children: []
    };
    
    // Function to add projectName and fix UUIDs in a tree
    const addProjectNameAndFixUuid = (node, projectName) => {
      node.projectName = projectName;
      // Fix root project UUID to be unique per project
      if (node.path === '/') {
        node.uuid = `${projectName}_root`;
      }
      if (node.children) {
        node.children.forEach(child => addProjectNameAndFixUuid(child, projectName));
      }
    };
    
    // Add each project as a root folder
    projects.forEach(project => {
      if (project) {
        // Clone the project and add projectName to all nodes
        const projectCopy = JSON.parse(JSON.stringify(project));
        addProjectNameAndFixUuid(projectCopy, project.name);
        projectCopy.isProjectRoot = true;
        multiRoot.children.push(projectCopy);
      }
    });
    
    state.ideInfo.multiRootData = multiRoot;
  },
  handleDelProject(state, projectName) {
    for (var i = 0; i < state.ideInfo.projList.length; i++) {
      if (state.ideInfo.projList[i].name === projectName) {
        state.ideInfo.projList.splice(i, 1);
        break;
      }
    }
  },
  handleDelFolder(state, {parentData, folderPath}) {
    if (parentData && parentData.children) {
      for (var i = 0; i < parentData.children.length; i++) {
        if (parentData.children[i].path === folderPath) {
          parentData.children.splice(i, 1);
          break;
        }
      }
    }
    const codeItems = [];
    for (let i = 0; i < state.ideInfo.codeItems.length; i++) {
      if (state.ideInfo.codeItems[i].path.indexOf(folderPath) !== 0) {
        codeItems.push(state.ideInfo.codeItems[i]);
      }
    }
    state.ideInfo.codeItems = codeItems;
    if (state.ideInfo.currProj.pathSelected && state.ideInfo.currProj.pathSelected.indexOf(folderPath) === 0) {
      state.ideInfo.currProj.pathSelected = codeItems.length > 0 ? codeItems[0].path : '';
    }
    const expandedKeys = [];
    for (let i = 0; i < state.ideInfo.currProj.expandedKeys.length; i++) {
      if (state.ideInfo.currProj.expandedKeys[i].indexOf(folderPath) !== 0) {
        expandedKeys.push(state.ideInfo.currProj.expandedKeys[i]);
      }
    }
    state.ideInfo.currProj.expandedKeys = expandedKeys;
  },
  handleGetFile(state, {filePath, data, save, isMedia, projectName}) {
    // Create unique identifier for cross-project files
    const currentProjectName = projectName || state.ideInfo.currProj?.data?.name || 'default';
    
    // Check if file is already open - compare by path AND project name
    for (let i = 0; i < state.ideInfo.codeItems.length; i++) {
      // Check if the same file from the same project is already open
      if (state.ideInfo.codeItems[i].path === filePath && 
          state.ideInfo.codeItems[i].projectName === currentProjectName) {
        state.ideInfo.currProj.pathSelected = filePath;
        state.ideInfo.codeSelected = state.ideInfo.codeItems[i];
        return;
      }
    }
    
    // Check tab limit (max 5 tabs)
    const MAX_TABS = 5;
    if (state.ideInfo.codeItems.length >= MAX_TABS) {
      // Remove the oldest tab (first item) to make room
      const closedTab = state.ideInfo.codeItems.shift();
      console.log(`Tab limit (${MAX_TABS}) reached. Closed "${closedTab.name}" to open new file.`);
      
      // Show notification (if ElMessage is available)
      if (typeof window !== 'undefined' && window.ElMessage) {
        window.ElMessage({
          type: 'warning',
          message: `Tab limit (${MAX_TABS}) reached. Closed "${closedTab.name}" to open new file.`,
          duration: 3000
        });
      }
    }
    
    // Add new file tab
    state.ideInfo.codeItems.push({
      name: path.basename(filePath),
      content: data,
      path: filePath,
      projectName: currentProjectName,
      codemirror: null,
      isMedia: isMedia || false,
    });
    
    if (save !== false || state.ideInfo.currProj.pathSelected === filePath) {
      state.ideInfo.currProj.pathSelected = filePath;
      state.ideInfo.codeSelected = state.ideInfo.codeItems[state.ideInfo.codeItems.length - 1];
      // self.saveProject();
      if (state.ideInfo.treeRef) {
        state.ideInfo.treeRef.setCurrentKey(state.ideInfo.currProj.pathSelected);
        state.ideInfo.nodeSelected = state.ideInfo.treeRef.getCurrentNode();
      }
    }
  },
  handleDelFile(state, {parentData, filePath}) {
    for (let i = 0; i < state.ideInfo.codeItems.length; i++) {
      if (state.ideInfo.codeItems[i].path === filePath) {
        if (i > 0) {
          state.ideInfo.currProj.pathSelected = state.ideInfo.codeItems[i - 1].path;
        }
        else if (i < state.ideInfo.codeItems.length - 1) {
          state.ideInfo.currProj.pathSelected = state.ideInfo.codeItems[i + 1].path; 
        }
        state.ideInfo.codeItems.splice(i, 1);
        break;
      }
    }
    if (parentData) {
      for (let i = 0; i < parentData.children.length; i++) {
        if (parentData.children[i].path === filePath) {
          parentData.children.splice(i, 1);
          break;
        }
      }
    }
    // self.saveProject(self.getProject);
  },
  addChildrenNode(state, {name, path, type}) {
    if (!state.ideInfo.nodeSelected || state.ideInfo.nodeSelected.type !== 'dir') return;
    state.ideInfo.nodeSelected.children.push({
      name: name,
      label: name,
      uuid: path,
      path: path,
      type: type,
      children: [],
    });
    state.ideInfo.currProj.expandedKeys.push(state.ideInfo.nodeSelected.path);
    if (type == 'file') {
      state.ideInfo.currProj.pathSelected = path;

      state.ideInfo.codeItems.push({
        name: name,
        content: '',
        path: path,
        codemirror: null,
      });
      state.ideInfo.codeSelected = state.ideInfo.codeItems[state.ideInfo.codeItems.length - 1];
    }
    else {
      state.ideInfo.currProj.expandedKeys.push(path);
    }
  },
  handleRename(state, name) {
    if (!state.ideInfo.nodeSelected || !state.ideInfo.nodeSelected.type) return;
    if (state.ideInfo.nodeSelected.path === '/') {
      // rename project
      state.ideInfo.currProj.config.name = name;
      state.ideInfo.currProj.data.name = name;
      state.ideInfo.currProj.data.label = name;
    }
    else {
      // rename file/folder
      const renameNodeData = (nodeData, parentPath) => {
        nodeData.path = path.join(parentPath, nodeData.name);
        nodeData.uuid = nodeData.path;
        if (nodeData.type === 'dir' && nodeData.children) {
          for (let i = 0; i < nodeData.children.length; i++) {
            renameNodeData(nodeData.children[i], nodeData.path);
          }
        }
      }
      const newPath = path.join(path.dirname(state.ideInfo.nodeSelected.path), name);

      // rename code item
      for (let i = 0; i < state.ideInfo.codeItems.length; i++) {
        if (state.ideInfo.codeItems[i].path === state.ideInfo.nodeSelected.path) {
          state.ideInfo.codeItems[i].name = name;
          state.ideInfo.codeItems[i].path = newPath;
        }
        else if (state.ideInfo.codeItems[i].path.indexOf(state.ideInfo.nodeSelected.path) === 0) {
          state.ideInfo.codeItems[i].path = state.ideInfo.codeItems[i].path.replace(state.ideInfo.nodeSelected.path, newPath);
        }
      }
      // rename console item
      for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
        if (state.ideInfo.consoleItems[i].path === state.ideInfo.nodeSelected.path) {
          state.ideInfo.consoleItems[i].name = name;
          state.ideInfo.consoleItems[i].path = newPath;
        }
        else if (state.ideInfo.consoleItems[i].path.indexOf(state.ideInfo.nodeSelected.path) === 0) {
          state.ideInfo.consoleItems[i].path = state.ideInfo.consoleItems[i].path.replace(state.ideInfo.nodeSelected.path, newPath);
        }
      }
      // rename expand key
      for (let i = 0; i < state.ideInfo.currProj.expandedKeys.length; i++) {
        if (state.ideInfo.currProj.expandedKeys[i].indexOf(state.ideInfo.nodeSelected.path) === 0) {
          state.ideInfo.currProj.expandedKeys[i] = state.ideInfo.currProj.expandedKeys[i].replace(state.ideInfo.nodeSelected.path, newPath);
        }
      }
      // rename path selected
      if (state.ideInfo.currProj.pathSelected.indexOf(state.ideInfo.nodeSelected.path) === 0) {
        state.ideInfo.currProj.pathSelected = state.ideInfo.currProj.pathSelected.replace(state.ideInfo.nodeSelected.path, newPath);
      }

      // rename node selected name
      state.ideInfo.nodeSelected.name = name;
      state.ideInfo.nodeSelected.label = name;
      // rename node selected path and all children item path
      renameNodeData(state.ideInfo.nodeSelected, path.dirname(state.ideInfo.nodeSelected.path));
    }
  },
  handleCreateFile(state, filePath) {
    state.ideInfo.currProj.expandedKeys.push(filePath);
    state.ideInfo.currProj.pathSelected = filePath;
  },
  handleCreateFolder(state, folderPath) {
    state.ideInfo.currProj.expandedKeys.push(folderPath);
  },
  handleRunResult(state, dict) {
    if (dict.code === 0) {
      if (dict.data === null || dict.data.stdout === undefined || dict.data.stdout === null) {
        // Program starts, first set the running state to True and clear the output
        for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
          if (state.ideInfo.consoleItems[i].id !== dict.id) continue;
          if (!state.ideInfo.consoleItems[i].run) {
            state.ideInfo.consoleItems[i].resultList = [];
          }
          state.ideInfo.consoleItems[i].run = true;
          break;
        }
      }
      else {
        for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
          if (state.ideInfo.consoleItems[i].id !== dict.id) continue;
          // Limit saving results to a maximum of 30000 lines
          if (state.ideInfo.consoleItems[i].resultList.length > 30000) {
            // Exceeds the maximum number of lines, discard the first 100 lines
            state.ideInfo.consoleItems[i].resultList.splice(0, 100);
          }
          // Push the result into the result list
          state.ideInfo.consoleItems[i].resultList.push(`${dict.data.stdout}`);
          // Limit refreshing only the selected Console's results
          // if (state.ideInfo.consoleSelected.id !== state.ideInfo.consoleItems[i].id && !window.GlobalUtil.model.socketModel.socketInfo.connected) {
          //   break;
          // }
          // const textArea = document.getElementById('console-' + state.ideInfo.consoleItems[i].id)
          // if (textArea !== undefined && textArea !== null) {
          //   textArea.scrollTop = textArea.scrollHeight;
          // }
          break;
        }
      }
    }
    else if (dict.code === 2000) {
      // Input request from program
      console.log('[FRONTEND-INPUT-DEBUG] *** RECEIVED INPUT REQUEST!', dict);
      console.log('[FRONTEND-INPUT-DEBUG] Data:', dict.data);
      console.log('[FRONTEND-INPUT-DEBUG] Prompt:', dict.data?.prompt);
      
      // Input request received
      for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
        if (state.ideInfo.consoleItems[i].id !== dict.id) continue;
        
        console.log('[FRONTEND-INPUT-DEBUG] Found matching console item at index:', i);
        
        // Show input prompt in console
        const prompt = dict.data && dict.data.prompt ? dict.data.prompt : "";
        console.log('[FRONTEND-INPUT-DEBUG] Setting prompt:', prompt);
        
        // Don't add prompt to resultList as it will be shown in the input area
        // Mark console as waiting for input
        // Set waiting for input
        state.ideInfo.consoleItems[i].waitingForInput = true;
        state.ideInfo.consoleItems[i].inputPrompt = prompt;
        
        console.log('[FRONTEND-INPUT-DEBUG] Console item updated with waitingForInput=true');
        console.log('[FRONTEND-INPUT-DEBUG] Console item state:', state.ideInfo.consoleItems[i]);
        
        break;
      }
    }
    else if (dict.code === 2001) {
      // Input processed confirmation from backend
      console.log('[FRONTEND-INPUT-DEBUG] Input processed confirmation received');
      for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
        if (state.ideInfo.consoleItems[i].id !== dict.id) continue;
        
        // Ensure the waiting state is cleared
        state.ideInfo.consoleItems[i].waitingForInput = false;
        state.ideInfo.consoleItems[i].inputPrompt = '';
        console.log('[FRONTEND-INPUT-DEBUG] Console waiting state cleared after input processed');
        break;
      }
    }
    else if (dict.code === 3000) {
      // Matplotlib figure display
      for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
        if (state.ideInfo.consoleItems[i].id !== dict.id) continue;
        
        // Add figure marker to result list
        state.ideInfo.consoleItems[i].resultList.push(`[Matplotlib Figure Displayed]`);
        
        // Open figure in new window/tab
        if (dict.data && dict.data.data) {
          const win = window.open('', '_blank');
          if (win) {
            win.document.write(`
              <html>
                <head><title>Matplotlib Figure</title></head>
                <body style="margin:0;padding:20px;background:#f0f0f0;text-align:center;">
                  <img src="${dict.data.data}" style="max-width:100%;height:auto;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                  <br><br>
                  <button onclick="downloadImage()" style="padding:10px 20px;font-size:16px;cursor:pointer;">Download Image</button>
                  <script>
                    function downloadImage() {
                      const a = document.createElement('a');
                      a.href = document.querySelector('img').src;
                      a.download = 'matplotlib_figure_' + Date.now() + '.png';
                      a.click();
                    }
                  </script>
                </body>
              </html>
            `);
          }
        }
        break;
      }
    }
    else {
      // Program ends (code 1111 or any other error code), set the program state to False and display all output
      for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
        if (state.ideInfo.consoleItems[i].id !== dict.id) continue;
        // If no program is running in the current terminal, clear the output first (usually occurs when file doesn't exist or is not a py file or input command is empty or command is not a string)
        if (!state.ideInfo.consoleItems[i].run && !state.ideInfo.consoleItems[i].stop) {
          state.ideInfo.consoleItems[i].resultList = [];
        }
        if (dict.data && dict.data.stdout) {
          state.ideInfo.consoleItems[i].resultList.push(`${dict.data.stdout}`);
        }
        const textArea = document.getElementById('console-' + state.ideInfo.consoleItems[i].id)
        if (textArea !== undefined && textArea !== null) {
          textArea.scrollTop = textArea.scrollHeight;
        }
        state.ideInfo.consoleItems[i].run = false;
        break;
      }
    }
  },
  handleStopResult(state, { consoleId, dict }) {
    if (dict.code === 0) {
      for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
        if (consoleId && state.ideInfo.consoleItems[i].id !== consoleId) continue;
        state.ideInfo.consoleItems[i].stop = true;
        state.ideInfo.consoleItems[i].run = false;
      }
    }
  },
  addExpandNodeKey(state, key) {
    if (state.ideInfo.currProj.expandedKeys.indexOf(key) < 0) {
      state.ideInfo.currProj.expandedKeys.push(key);
      // _this.saveProject();
    }
  },
  delExpandNodeKey(state, key) {
    state.ideInfo.currProj.expandedKeys.splice(state.ideInfo.currProj.expandedKeys.findIndex(item => item === key), 1);
  },
  setNodeSelected(state, selected) {
    state.ideInfo.nodeSelected = selected;
  },
  setPathSelected(state, selected) {
    state.ideInfo.currProj.pathSelected = selected;
  },
  setCodeSelected(state, selected) {
    state.ideInfo.codeSelected = selected;
  },
  setConsoleSelected(state, selected) {
    state.ideInfo.consoleSelected = selected;
  },
  setTreeRef(state, treeRef) {
    state.ideInfo.treeRef = treeRef;
  },
  assignConsoleSelected(state, item) {
    if (item && typeof item === 'object')
      Object.assign(state.ideInfo.consoleSelected, item);
  },
  spliceConsoleItems(state, { start, count }) {
    state.ideInfo.consoleItems.splice(start, count);
  },
  setConsoleId(state, consoleId) {
    state.ideInfo.consoleId = consoleId;
  },
  addConsoleItem(state, item) {
    state.ideInfo.consoleItems.push(item);
  },
  resetConsoleItem(state, { consoleId, run, stop, resultList }) {
    // Find the console item and reset its properties
    for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
      if (state.ideInfo.consoleItems[i].id === consoleId) {
        if (run !== undefined) state.ideInfo.consoleItems[i].run = run;
        if (stop !== undefined) state.ideInfo.consoleItems[i].stop = stop;
        if (resultList !== undefined) state.ideInfo.consoleItems[i].resultList = resultList;
        break;
      }
    }
  },
  setConsoleItems(state, items) {
    state.ideInfo.consoleItems = items;
  },

  addCodeItem(state, item) {
    state.ideInfo.codeItems.push(item);
  },
  setCodeItems(state, items) {
    state.ideInfo.codeItems = items;
  },
  setCodeItemMirror(state, { index, codemirror }) {
    state.ideInfo.codeItems[index].codemirror = codemirror;
  },
  setCodeItemContent(state, { index, content }) {
    state.ideInfo.codeItems[index].content = content;
  },
  setCodeHeight(state, height) {
    state.ideInfo.codeHeight = height;
  },
  // Fullscreen preview mutations
  setFullscreenPreview(state, { file, content }) {
    state.ideInfo.fullscreenPreview = {
      active: true,
      file: file,
      content: content
    };
  },
  closeFullscreenPreview(state) {
    state.ideInfo.fullscreenPreview = {
      active: false,
      file: null,
      content: null
    };
  }
};

const actions = {
  [types.IDE_LIST_PROJECTS](context, { wsKey, msgId, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      msgId: msgId,
      cmd: types.IDE_LIST_PROJECTS,
      data: {}, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_GET_PROJECT](context, { wsKey, projectName, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_GET_PROJECT,
      data: {
        projectName: projectName
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_CREATE_PROJECT](context, { wsKey, projectName, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_CREATE_PROJECT,
      data: {
        projectName: projectName
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_DEL_PROJECT](context, { wsKey, projectName, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_DEL_PROJECT,
      data: {
        projectName: projectName
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_RENAME_PROJECT](context, { wsKey, oldName, newName, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_RENAME_PROJECT,
      data: {
        oldName: oldName,
        newName: newName,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_SAVE_PROJECT](context, { wsKey, callback }) {
    const openList = []
    for(let i = 0; i < context.state.ideInfo.codeItems.length; i++) {
      openList.push(context.state.ideInfo.codeItems[i].path);
    }
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_SAVE_PROJECT,
      data: {
        projectName: context.state.ideInfo.currProj.data.name,
        expendKeys: context.state.ideInfo.currProj.expandedKeys,
        openList: openList,
        selectFilePath: context.state.ideInfo.currProj.pathSelected,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_CREATE_FILE](context, { wsKey, projectName, parentPath, fileName, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_CREATE_FILE,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        parentPath: parentPath || context.state.ideInfo.nodeSelected.path,
        fileName: fileName,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_WRITE_FILE](context, { wsKey, projectName, filePath, fileData, complete, line, column, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_WRITE_FILE,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        filePath: filePath,
        fileData: fileData,
        complete: complete,
        line: line,
        column: column
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_GET_FILE](context, { wsKey, projectName, filePath, binary, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_GET_FILE,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        filePath: filePath,
        binary: binary || false
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_DEL_FILE](context, { wsKey, projectName, filePath, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_DEL_FILE,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        filePath: filePath
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_RENAME_FILE](context, { wsKey, projectName, oldPath, fileName, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_RENAME_FILE,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        oldPath: oldPath || context.state.ideInfo.nodeSelected.path,
        newName: fileName,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_CREATE_FOLDER](context, { wsKey, projectName, parentPath, folderName, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_CREATE_FOLDER,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        parentPath: parentPath || context.state.ideInfo.nodeSelected.path,
        folderName: folderName,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_DEL_FOLDER](context, { wsKey, projectName, folderPath, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_DEL_FOLDER,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        folderPath: folderPath,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_RENAME_FOLDER](context, { wsKey, projectName, oldPath, folderName, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_RENAME_FOLDER,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        oldPath: oldPath || context.state.ideInfo.nodeSelected.path,
        newName: folderName,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_AUTOCOMPLETE_PYTHON](context, { wsKey, source, line, column, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_AUTOCOMPLETE_PYTHON,
      data: {
        source: source,
        line: line,
        column: column,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_RUN_PIP_COMMAND](context, { wsKey, msgId, command, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      msgId: msgId,
      cmd: types.IDE_RUN_PIP_COMMAND,
      data: {
        command: command,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_RUN_PYTHON_PROGRAM](context, { wsKey, msgId, projectName, filePath, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      msgId: msgId,
      cmd: types.IDE_RUN_PYTHON_PROGRAM,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        filePath: filePath,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_STOP_PYTHON_PROGRAM](context, { wsKey, consoleId, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_STOP_PYTHON_PROGRAM,
      data: {
        program_id: consoleId,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_SEND_PROGRAM_INPUT](context, { wsKey, program_id, input, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_SEND_PROGRAM_INPUT,
      data: {
        program_id: program_id,
        input: input,
      }, 
      callback: callback,
    }, { root: true });
  },
  sendBugReport(context, reportData) {
    return new Promise((resolve, reject) => {
      context.dispatch('websocket/sendCmd', {
        wsKey: 'main',
        msgId: Date.now(),
        cmd: 'send_bug_report',
        data: reportData,
        callback: {
          limits: 1,
          callback: (response) => {
            if (response && response.data) {
              resolve(response.data);
            } else {
              reject(new Error('Failed to send bug report'));
            }
          }
        }
      }, { root: true });
    });
  }
};

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
