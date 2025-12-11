import * as types from '../mutation-types';
const path = require('path');

// Utility function to check if user can edit a file
function canUserEditFile(filePath) {
  // Get current user from localStorage
  const sessionId = localStorage.getItem('session_id');
  const username = localStorage.getItem('username');
  const role = localStorage.getItem('role');

  // If not logged in, deny access
  if (!sessionId || !username || !role) {
    return false;
  }

  // Professors can edit everything
  if (role === 'professor') {
    return true;
  }

  // Students can only edit files in their own Local/{username}/ directory
  if (role === 'student') {
    const userPath = `Local/${username}`;

    // Allow if the file is inside the user's Local folder
    // Deny access to all other root-level folders (Lecture Notes, professor-created folders, etc.)
    return filePath && filePath.startsWith(userPath + '/');
  }

  return false;
}

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
  // Auto-save settings
  autoSave: false,
  autoSaveInterval: 60, // seconds
  autoSaveNotifications: true,
  // Fullscreen preview state
  fullscreenPreview: {
    active: false,
    file: null,
    content: null
  },
  // Exam mode flag (disables CSV search/sort)
  isExamMode: false
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
  setExamMode(state, isExamMode) {
    state.ideInfo.isExamMode = isExamMode;
  },
  addConsoleOutput(state, { id, type, text, prompt, content }) {
    for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
      if (state.ideInfo.consoleItems[i].id === id) {
        const outputItem = { type, text };
        // For repl-input type, also include prompt and content fields
        if (type === 'repl-input') {
          outputItem.prompt = prompt;
          outputItem.content = content || text;
        }
        state.ideInfo.consoleItems[i].resultList.push(outputItem);
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
  setConsoleWaitingForReplInput(state, { id, waiting }) {
    for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
      if (state.ideInfo.consoleItems[i].id === id) {
        state.ideInfo.consoleItems[i].waitingForReplInput = waiting;
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
    state.ideInfo.projList = data.map(proj => {
      // Ensure each project has a name property
      if (typeof proj === 'string') {
        return { name: proj, lastAccessTime: 0 };
      }
      return proj;
    });
    
    // Find the user's personal project or the most recently accessed project
    const username = localStorage.getItem('username');
    let selectedProject = null;
    
    // First priority: user's personal directory
    if (username) {
      selectedProject = state.ideInfo.projList.find(p => p.name === `Local/${username}`);
    }
    
    // Second priority: project with highest lastAccessTime
    if (!selectedProject) {
      let lastAccessTime = 0;
      for (var i = 0; i < state.ideInfo.projList.length; i++) {
        if (state.ideInfo.projList[i].lastAccessTime > lastAccessTime) {
          lastAccessTime = state.ideInfo.projList[i].lastAccessTime;
          selectedProject = state.ideInfo.projList[i];
        }
      }
    }
    
    // Third priority: first project in the list
    if (!selectedProject && state.ideInfo.projList.length > 0) {
      selectedProject = state.ideInfo.projList[0];
    }
    
    // Set the selected project name if found
    if (selectedProject) {
      state.ideInfo.currProj.config.name = selectedProject.name;
    }
  },
  handleProject(state, data) {
    // Function to ensure label and uuid exist in the tree
    const ensureNodeProperties = (node) => {
      if (!node.label && node.name) {
        node.label = node.name;
      }
      if (!node.uuid) {
        node.uuid = node.path || node.name || Math.random().toString(36);
      }
      if (node.children) {
        node.children.forEach(child => ensureNodeProperties(child));
      }
    };
    
    // Don't clear codeItems to preserve open tabs across project switches
    // state.ideInfo.codeItems = [];
    
    // Preserve current expanded keys during refresh
    const currentExpandedKeys = [...(state.ideInfo.currProj.expandedKeys || [])];
    
    state.ideInfo.currProj.config = data.config || {};
    
    // Ensure the data has proper label and uuid properties
    ensureNodeProperties(data);
    state.ideInfo.currProj.data = data;
    
    state.ideInfo.currProj.pathSelected = state.ideInfo.currProj.config.selectFilePath;
    
    // Use server config expanded keys if available, otherwise preserve current UI state
    if (data.config !== undefined && data.config.expendKeys !== undefined) {
      state.ideInfo.currProj.expandedKeys = data.config.expendKeys.filter(key => key !== null);
      state.ideInfo.currProj.expandedKeys.sort();
    } else {
      // Preserve current expanded state during refresh
      state.ideInfo.currProj.expandedKeys = currentExpandedKeys;
    }
    if (state.ideInfo.currProj.pathSelected && state.ideInfo.treeRef) {
      state.ideInfo.nodeSelected = state.ideInfo.treeRef.getCurrentNode();
    }
  },
  refreshProject(state, data) {
    // Function to ensure label and uuid exist in the tree
    const ensureNodeProperties = (node) => {
      if (!node.label && node.name) {
        node.label = node.name;
      }
      if (!node.uuid) {
        node.uuid = node.path || node.name || Math.random().toString(36);
      }
      if (node.children) {
        node.children.forEach(child => ensureNodeProperties(child));
      }
    };
    
    // Preserve current UI state during refresh
    const currentExpandedKeys = [...(state.ideInfo.currProj.expandedKeys || [])];
    const currentSelectedPath = state.ideInfo.currProj.pathSelected;
    
    // Update project data with new structure
    ensureNodeProperties(data);
    state.ideInfo.currProj.data = data;
    
    // Preserve expanded state and selected path
    state.ideInfo.currProj.expandedKeys = currentExpandedKeys;
    state.ideInfo.currProj.pathSelected = currentSelectedPath;
    
    // Update config if available but don't override UI state
    if (data.config) {
      state.ideInfo.currProj.config = { ...state.ideInfo.currProj.config, ...data.config };
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
    
    // Function to add projectName, label and fix UUIDs in a tree
    const addProjectNameAndFixUuid = (node, projectName) => {
      node.projectName = projectName;
      // Ensure label property exists (use name if label is missing)
      if (!node.label && node.name) {
        node.label = node.name;
      }
      // Generate UUID if missing
      if (!node.uuid) {
        node.uuid = node.path || node.name || Math.random().toString(36);
      }
      // Fix root project UUID to be unique per project
      if (node.path === '/' || node.path === projectName) {
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
    
    // Always make the opened file active, regardless of save flag
    state.ideInfo.currProj.pathSelected = filePath;
    state.ideInfo.codeSelected = state.ideInfo.codeItems[state.ideInfo.codeItems.length - 1];
    
    // Update tree selection to reflect the opened file
    if (state.ideInfo.treeRef) {
      state.ideInfo.treeRef.setCurrentKey(state.ideInfo.currProj.pathSelected);
      state.ideInfo.nodeSelected = state.ideInfo.treeRef.getCurrentNode();
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
          if (!state.ideInfo.consoleItems[i].run && !state.ideInfo.consoleItems[i].isReplMode) {
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
          const text = `${dict.data.stdout}`;
          
          // In REPL mode, check if output contains a new prompt
          if (state.ideInfo.consoleItems[i].isReplMode && text.includes('>>> ')) {
            // Split output and prompt
            const parts = text.split('>>> ');
            if (parts[0]) {
              state.ideInfo.consoleItems[i].resultList.push({
                type: 'text',
                text: parts[0]
              });
            }
            // Add the REPL prompt
            state.ideInfo.consoleItems[i].resultList.push({
              type: 'repl-prompt',
              text: '>>> '
            });
            // Mark as waiting for REPL input again
            state.ideInfo.consoleItems[i].waitingForReplInput = true;
          } else {
            // Regular output
            state.ideInfo.consoleItems[i].resultList.push(text);
          }
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
    else if (dict.code === 4000) {
      // Error signal from backend (timeout, infinite loop, etc.)
      console.log('[ERROR] Received code 4000 - Error signal', dict);
      for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
        if (state.ideInfo.consoleItems[i].id !== dict.id) continue;

        // Display error message if provided
        if (dict.data && dict.data.error) {
          // Error message already sent as stdout, don't duplicate
          // The error message is sent separately via code 0 with stdout
        }

        // Stop the program
        state.ideInfo.consoleItems[i].run = false;
        state.ideInfo.consoleItems[i].isReplMode = false;
        state.ideInfo.consoleItems[i].replActive = false;

        const textArea = document.getElementById('console-' + state.ideInfo.consoleItems[i].id)
        if (textArea !== undefined && textArea !== null) {
          textArea.scrollTop = textArea.scrollHeight;
        }

        break;
      }
    }
    else if (dict.code === 5000) {
      // REPL mode transition
      console.log('[REPL-MODE] Received code 5000 - REPL mode signal', dict);
      for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
        if (state.ideInfo.consoleItems[i].id !== dict.id) continue;

        // Set REPL mode flag on the console item
        state.ideInfo.consoleItems[i].isReplMode = true;
        state.ideInfo.consoleItems[i].replActive = true;

        // REPL mode started - no extra messages needed

        // Show REPL prompt
        state.ideInfo.consoleItems[i].resultList.push({
          type: 'repl-prompt',
          text: '>>> '
        });

        // Mark as waiting for REPL input
        state.ideInfo.consoleItems[i].waitingForReplInput = true;

        console.log('[REPL-MODE] Console item updated for REPL mode');

        // Focus the REPL input field
        setTimeout(() => {
          const replInput = document.querySelector('.repl-input');
          if (replInput) {
            replInput.focus();
          }
        }, 100);

        break;
      }
    }
    else {
      // Program ends (code 1111 or any other error code), set the program state to False and display all output
      for (let i = 0; i < state.ideInfo.consoleItems.length; i++) {
        if (state.ideInfo.consoleItems[i].id !== dict.id) continue;
        // Only clear output if program was never started (run=false and stop=false)
        // Don't clear if program was running and is now stopping (run=false after being true)
        // This preserves error messages from infinite loop detection
        if (!state.ideInfo.consoleItems[i].run && !state.ideInfo.consoleItems[i].stop) {
          // Only clear for initial errors (file not found, etc), not for termination after running
          // Check if console has content - if it does, program was running
          if (state.ideInfo.consoleItems[i].resultList.length === 0) {
            state.ideInfo.consoleItems[i].resultList = [];
          }
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
  updateCodeItem(state, {index, updates}) {
    if (index >= 0 && index < state.ideInfo.codeItems.length) {
      Object.assign(state.ideInfo.codeItems[index], updates);
    }
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
  },
  // Editor options mutations
  setEditorOption(state, { option, value }) {
    // Store editor options in the state if needed
    // For now, just log the change as the actual setting is handled in the component
    console.log(`Editor option ${option} set to ${value}`);
  },
  setAutoSave(state, value) {
    state.ideInfo.autoSave = value;
    console.log(`Auto-save set to ${value}`);
  },
  setAutoSaveInterval(state, value) {
    state.ideInfo.autoSaveInterval = parseInt(value);
    console.log(`Auto-save interval set to ${value} seconds`);
  },
  setAutoSaveNotifications(state, value) {
    state.ideInfo.autoSaveNotifications = value;
    console.log(`Auto-save notifications set to ${value}`);
  },
  addAutoSaveNotification(state, { message, timestamp }) {
    // This mutation is used to trigger notifications in the component
    // The actual notification display is handled in the component
    console.log(`Auto-save notification: ${message}`);
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
    // Backend doesn't support ide_save_project command currently
    // Just return success to avoid errors
    if (callback) {
      callback({ code: 0, data: {} });
    }
    return;
    
    // Original code commented out:
    /*
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
    */
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
    // Check if user has permission to write this file
    if (!canUserEditFile(filePath)) {
      const errorMsg = 'You do not have permission to save files in this directory. Students can only save files in their own Local folder.';
      console.error('[WRITE-PERMISSION-DENIED]', errorMsg, filePath);

      // Call callback with error if provided
      if (callback) {
        callback({
          code: 403,
          message: errorMsg,
          msg: errorMsg,
          path: filePath
        });
      }
      return;
    }

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
  [types.IDE_MOVE_FILE](context, { wsKey, projectName, oldPath, newPath, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_MOVE_FILE,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        oldPath: oldPath,
        newPath: newPath,
      }, 
      callback: callback,
    }, { root: true });
  },
  [types.IDE_CREATE_FOLDER](context, { wsKey, projectName, parentPath, folderName, isRootCreation, callback }) {
    // Construct the full folder path
    let folderPath = '';
    if (parentPath === '/' || parentPath === '') {
      folderPath = folderName;
    } else {
      folderPath = `${parentPath}/${folderName}`;
    }

    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_CREATE_FOLDER,
      data: {
        projectName: isRootCreation ? '' : (projectName || context.state.ideInfo.currProj.data.name),
        folderPath: folderPath,
        isRootCreation: isRootCreation || false,
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
  [types.IDE_MOVE_FOLDER](context, { wsKey, projectName, oldPath, newPath, callback }) {
    context.dispatch('websocket/sendCmd', {
      wsKey: wsKey,
      cmd: types.IDE_MOVE_FOLDER,
      data: {
        projectName: projectName || context.state.ideInfo.currProj.data.name,
        oldPath: oldPath,
        newPath: newPath,
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
  },
  saveFile(context, { codeItem, isAutoSave = false }) {
    // Check if user has permission to edit this file
    if (!canUserEditFile(codeItem.path)) {
      const errorMsg = 'You do not have permission to save files in this directory. Students can only save files in their own Local folder.';
      console.error('[SAVE-PERMISSION-DENIED]', errorMsg, codeItem.path);

      // Return a rejected promise with error details
      return Promise.reject({
        code: 403,
        message: errorMsg,
        path: codeItem.path
      });
    }

    // Use the existing IDE_WRITE_FILE action to save the file
    const logPrefix = isAutoSave ? '[AUTO-SAVE]' : '[MANUAL-SAVE]';
    console.log(`${logPrefix} Saving file: ${codeItem.path}`);

    // Use the projectName from the codeItem if available
    const projectName = codeItem.projectName || context.state.ideInfo.currProj?.data?.name || context.state.ideInfo.currProj?.config?.name;

    return context.dispatch(types.IDE_WRITE_FILE, {
      projectName: projectName,
      filePath: codeItem.path,
      fileData: codeItem.content,
      complete: false,
      line: 0,
      column: 0,
      callback: (response) => {
        if (response && response.code === 0) {
          console.log(`${logPrefix} Successfully saved: ${codeItem.path}`);
          
          // Show notification if it's auto-save and notifications are enabled
          if (isAutoSave && context.state.ideInfo.autoSaveNotifications) {
            // This will be handled in the component with ElMessage
            context.commit('addAutoSaveNotification', { 
              message: `Auto-saved: ${codeItem.name}`,
              timestamp: Date.now()
            });
          }
        } else {
          console.error(`${logPrefix} Failed to save: ${codeItem.path}`, response);
        }
      }
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
