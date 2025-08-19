import ReconnectingWebSocket from 'reconnecting-websocket';

const wsInfoMap = {
  default: {
    location: {
      // Use the current page's protocol and host for WebSocket connection
      // This ensures it works both locally and when deployed
      protocol: window.location.protocol === 'https:' ? 'wss:' : 'ws:',
      host: window.location.hostname,
      port: window.location.port || (window.location.protocol === 'https:' ? '443' : '80'),
      // For local development, use the proxy path; for production use /ws directly
      pathname: window.location.hostname === 'localhost' ? '/ide-ws' : '/ws',
      search: '', // Remove query params to avoid confusion
    },
    protocols: [],
    options: {
      WebSocket: WebSocket, // WebSocket
      maxReconnectionDelay: 10000,
      minReconnectionDelay: 1000 + Math.random() * 4000,
      reconnectionDelayGrowFactor: 1.3,
      minUptime: 5000,
      connectionTimeout: 4000,
      maxRetries: Infinity,
      maxEnqueuedMessages: Infinity,
      startClosed: false,
      debug: true,
    },
    logger: console,
    rws: null, // WebSocket instance
    connected: false, // Connection status
    authenticated: false, // Authentication status
    msgId: 1, // Message ID for sending, incremental
    jsonMsgCallbacks: {}, // Callbacks for received messages
    jsonMsgHandlers: [], // Message handler function list, function parameters are data processed by JSON.parse(event.data)
  }
};

const state = {
  wsInfoMap: wsInfoMap,
};

const getters = {
  wsInfo: (state) => {
    return (wsKey) => {
      return state.wsInfoMap[wsKey || 'default'];
    }
  }
};

const mutations = {
  setLocation(state, { wsKey, location }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (location && typeof location === 'object')
      wsInfo.location = Object.assign(wsInfo.location, location);
  },
  setProtocols(state, { wsKey, protocols }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (protocols && typeof options === 'object')
      wsInfo.protocols = Object.assign(wsInfo.protocols, protocols);
  },
  setOptions(state, { wsKey, options }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (options && typeof options === 'object')
      wsInfo.options = Object.assign(wsInfo.options, options);
  },
  setRws(state, { wsKey, rws }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    wsInfo.rws = rws;
  },
  setConnected(state,  { wsKey, connected }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    wsInfo.connected = connected;
  },
  setAuthenticated(state, { wsKey, authenticated }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    wsInfo.authenticated = authenticated;
  },
  setMsgId(state, { wsKey, msgId }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    wsInfo.msgId = msgId;
  },
  addJsonMsgCallback(state, { wsKey, msgId, callback }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    wsInfo.jsonMsgCallbacks[msgId] = callback;
  },

  /**
   * Delete message callback, trigger once before deletion
   * @param wsKey: websocket instance key, defaults to 'default'
   * @param msgId: specify msgId of callback to delete, if not specified, delete all callbacks
   * @param trigger: whether to trigger before deletion, defaults to false, trigger parameter is {code: 10086}
   * Usage:
   *  1. this.$store.commit('websocket/delJsonMsgCallback', {trigger: true})
   *  2. commit('websocket/delJsonMsgCallback', {trigger: true}, { root: true })
   */
  delJsonMsgCallback(state, { wsKey, msgId, trigger }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (msgId) {
      const callbackObj = wsInfo.jsonMsgCallbacks[msgId];
      if (callbackObj) {
        if (trigger === true && callbackObj.limits !== 0) {
          callbackObj.callback({ code: 10086 });
        }
        delete wsInfo.jsonMsgCallbacks[msgId];
      }
    }
    else {
      for (const msgId in wsInfo.jsonMsgCallbacks) {
        const callbackObj = wsInfo.jsonMsgCallbacks[msgId];
        if (callbackObj && trigger === true && callbackObj.limits !== 0) {
          callbackObj.callback({ code: 10086 });
        }
        delete wsInfo.jsonMsgCallbacks[msgId];
      }
    }
  },
  setJsonMsgCallback(state, { wsKey, msgId, limits, finished }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    wsInfo.jsonMsgCallbacks[msgId].limits = limits || wsInfo.jsonMsgCallbacks[msgId].limits;
    wsInfo.jsonMsgCallbacks[msgId].limits = finished || wsInfo.jsonMsgCallbacks[msgId].finished;
  },
  callJsonMsgCallback(state,  { wsKey, dict }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    const callbackObj = wsInfo.jsonMsgCallbacks[dict.id];
    if (callbackObj) {
      if (callbackObj.limits !== 0) {
        callbackObj.callback(dict);
        callbackObj.limits -= 1;
      }
      callbackObj.finished = true;

      if (callbackObj.limits === 0) {
        delete wsInfo.jsonMsgCallbacks[dict.id];
      }
    }
  },
  
  /**
   * Disconnect WebSocket connection, triggers and deletes all message callbacks, trigger parameter is {code: 10086}
   * @param wsKey: websocket instance key, defaults to 'default'
   * Usage:
   *  1. this.$store.commit('websocket/close', { wsKey: 'default' })
   *  2. commit('websocket/close', { wsKey: 'default' }, { root: true })
   */
  close(state, { wsKey }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (wsInfo && wsInfo.rws) {
      wsInfo.rws.onopen = null;
      wsInfo.rws.onclose = null;
      wsInfo.rws.onerror = null;
      wsInfo.rws.onmessage = null;
      wsInfo.rws.close();
      // wsInfo.delJsonMsgCallback(null, true);
      // wsInfo.rws = null;
    }
  },
  
  /**
   * Reconnect WebSocket connection
   * @param wsKey: websocket instance key, defaults to 'default'
   * Usage:
   *  1. this.$store.commit('websocket/reconnect', { wsKey: 'default' })
   *  2. commit('websocket/reconnect', { wsKey: 'default' }, { root: true })
   */
  reconnect(state, { wsKey }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (wsInfo.rws) {
      wsInfo.rws.reconnect();
    }
  },

  /**
   * Send message command
   * @param wsKey: websocket instance key, defaults to 'default'
   * @param msgId: message ID, if not specified, uses incremental ID
   * @param cmd: command/interface name
   * @param data: command/interface parameters
   * @param callback: callback function (dict) => {} or object containing callback function {callback: (dict) => {}, limits: 1}
   *    callback: callback function
   *    limits: limit callback count, no callback when 0, unlimited when negative, defaults to 1
   * Usage:
   *  1. this.$store.commit('websocket/sendCmd', {cmd: 'xxxxx', data: {}, callback: (dict) => {}})
   *  2. commit('websocket/sendCmd', {cmd: 'xxxxx', data: {}, callback: (dict) => {}}, { root: true })
   */
  sendCmd(state, { wsKey, msgId, cmd, data, callback }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (!wsInfo.rws) {
      wsInfo.logger.error(`Websocket is not init`);
      return -1;
    }
    if (wsInfo.rws.readyState !== ReconnectingWebSocket.OPEN) {
      wsInfo.logger.error(`Websocket readyState is not open`);
      return -2;
    }
    const msg = {
      cmd: cmd,
      data: data || {},
    };
    msg.id = msgId || wsInfo.msgId;
    if (msg.id === wsInfo.msgId) {
      wsInfo.msgId += 1;
      if (wsInfo.msgId > 10000) {
        wsInfo.msgId = 1;
      }
    }
    if (callback) {
      if (typeof callback === 'function') {
        wsInfo.jsonMsgCallbacks[msg.id] = {
          callback: callback,
          limits: 1,
          finished: false,
        };
      }
      else if (typeof callback === 'object' && callback.callback) {
        if (callback.limits === undefined) {
          callback.limits = 1;
        }
        callback.finished = false;
        wsInfo.jsonMsgCallbacks[msg.id] = callback;
      }
    }
    const msgStr = JSON.stringify(msg);
    if (wsInfo.options.debug) {
      wsInfo.logger.log(`Websocket send: ${msgStr}`);
    }
    wsInfo.rws.send(msgStr);
    return msg.id;
    // wsOp.sendCmd(wsInfo, {msgId, cmd, data, callback});
  },

  /**
   * Add WebSocket event listener
   * @param wsKey: websocket instance key, defaults to 'default'
   * @param type: event type, open/close/error/message
   * @param listener: handler method, parameter is event
   * Usage:
   *  1. this.$store.dispatch('websocket/addEventListener', { wsKey: 'default', type: 'open', (evt) => {} })
   *  2. dispatch('websocket/addEventListener', { wsKey: 'default', type: 'open', (evt) => {} }, { root: true })
   */
   addEventListener(state, { wsKey, type, listener }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (wsInfo.rws) {
      wsInfo.rws.addEventListener(type, listener);
    }
    // wsOp.addEventListener(wsInfo, type, listener);
  },
  
  /**
   * Add WebSocket message handler
   * @param wsKey: websocket instance key, defaults to 'default'
   * @param handler: message handler method, parameter is message object
   * Usage:
   *  1. this.$store.commit('websocket/addJsonMsgHandler', { wsKey: 'default', (dict) => {} })
   *  2. commit('websocket/addJsonMsgHandler', { wsKey: 'default', (dict) => {} }, { root: true })
   */
  addJsonMsgHandler(state, { wsKey, handler }) {
    const wsInfo = state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (!wsInfo.jsonMsgHandlers.includes(handler)) {
      wsInfo.jsonMsgHandlers.push(handler);
    }
    // wsOp.addEventListener(wsInfo, handler);
  }
}

const actions = {
  /**
   * Initialize WebSocket and connect
   * @param wsKey: websocket instance key, defaults to 'default'
   * @param location: object, URL information to connect to, see location in WsInfo
   * @param options: object, additional connection options, see options in WsInfo
   * Usage:
   *  1. this.$store.dispatch('websocket/init', { wsKey: 'default' })
   *  2. dispatch('websocket/init', { wsKey: 'default' }, { root: true })
   */
  init(context, { wsKey, location, options }) {
    const wsInfo = context.state.wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    context.commit('setLocation', { wsKey: wsKey, location: location });
    context.commit('setOptions', { wsKey: wsKey, options: options });
    // Build WebSocket URL - don't include port if it's standard (80/443)
    let url;
    if (wsInfo.location.port && wsInfo.location.port !== '80' && wsInfo.location.port !== '443' && wsInfo.location.port !== '') {
      url = `${wsInfo.location.protocol}//${wsInfo.location.host}:${wsInfo.location.port}${wsInfo.location.pathname}${wsInfo.location.search}`;
    } else {
      url = `${wsInfo.location.protocol}//${wsInfo.location.host}${wsInfo.location.pathname}${wsInfo.location.search}`;
    }
    console.log('🔌 [WebSocket] Attempting connection to:', url);
    console.log('🔌 [WebSocket] Location config:', wsInfo.location);
    wsInfo.logger.log(`Websocket init: ${url}`);

    if (wsInfo.rws) {
      context.dispatch('close', { wsKey: wsKey });
    }
    const rws = new ReconnectingWebSocket(url, wsInfo.protocols, wsInfo.options);

    rws.onopen = function (evt) {
      context.commit('setConnected', { wsKey: wsKey, connected: true });
      if (wsInfo.options.debug) {
        wsInfo.logger.log(`Websocket onopen event`);
      }
      
      // Send authentication if session exists
      const sessionId = localStorage.getItem('session_id');
      if (sessionId) {
        const authMsg = {
          cmd: 'authenticate',
          session_id: sessionId
        };
        rws.send(JSON.stringify(authMsg));
        wsInfo.logger.log('Sent authentication with session:', sessionId.substring(0, 20) + '...');
      } else {
        wsInfo.logger.log('No session found, WebSocket connected without authentication');
      }
    };
    rws.onclose = function (evt) {
      context.commit('setConnected', { wsKey: wsKey, connected: false });
      if (wsInfo.options.debug) {
        wsInfo.logger.log(`Websocket onclose event`);
      }
    };
    rws.onerror = function (evt) {
      context.commit('setConnected', { wsKey: wsKey, connected: false });
      if (wsInfo.options.debug) {
        wsInfo.logger.log(`Websocket onerror event`);
      }
    };
    rws.onmessage = function (evt) {
      if (wsInfo.options.debug) {
        wsInfo.logger.log(`Websocket onmessage: ${evt.data}`);
      }
      const dict = JSON.parse(evt.data) || {};
      
      // Handle authentication response
      if (dict.type === 'auth_required') {
        wsInfo.logger.log('Authentication required by server');
        // Don't process other messages until authenticated
        return;
      } else if (dict.type === 'auth_success') {
        wsInfo.logger.log('Authentication successful:', dict.username);
        // Use mutation to set authenticated state
        context.commit('setAuthenticated', { wsKey: wsKey, authenticated: true });
        
        // Load the user's initial project structure
        const username = dict.username || localStorage.getItem('username');
        const role = dict.role || localStorage.getItem('role');
        
        // For students, load their personal directory; for professors, load all
        const projectName = role === 'student' ? `Local/${username}` : 'Local';
        
        // Request the project structure
        const getProjectMsg = {
          cmd: 'ide_get_project',
          project: projectName
        };
        rws.send(JSON.stringify(getProjectMsg));
        wsInfo.logger.log('Requested initial project:', projectName);
        
        // Now we can process queued commands
      } else if (dict.type === 'error' && dict.message && dict.message.includes('Not authenticated')) {
        wsInfo.logger.warn('Not authenticated, waiting for authentication...');
        // Use mutation to set authenticated state
        context.commit('setAuthenticated', { wsKey: wsKey, authenticated: false });
        return;
      }
      
      // Message callback
      context.commit('callJsonMsgCallback', { wsKey: wsKey, dict: dict });
      // Message processing
      for (const handler of wsInfo.jsonMsgHandlers) {
        handler(dict);
      }
    };
    context.commit('setRws', { wsKey: wsKey, rws: rws });
  },
  
  /**
   * Disconnect WebSocket connection, triggers and deletes all message callbacks, trigger parameter is {code: 10086}
   * @param wsKey: websocket instance key, defaults to 'default'
   * Usage:
   *  1. this.$store.dispatch('websocket/close', { wsKey: 'default' })
   *  2. dispatch('websocket/close', { wsKey: 'default' }, { root: true })
   */
  close(context, { wsKey }) {
    const wsInfo = wsInfoMap[wsKey || 'default'];
    if (wsInfo && wsInfo.rws) {
      context.commit('close', { wsKey: wsKey });
      context.commit('delJsonMsgCallback', { wsKey: wsKey, msgId: null, trigger: true });
      context.commit('setRws', { wsKey: wsKey, rws: null });
    }
  },
  
  /**
   * Reconnect WebSocket connection
   * @param wsKey: websocket instance key, defaults to 'default'
   * Usage:
   *  1. this.$store.dispatch('websocket/reconnect', { wsKey: 'default' })
   *  2. dispatch('websocket/reconnect', { wsKey: 'default' }, { root: true })
   */
  reconnect(context, { wsKey }) {
    const wsInfo = wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    context.commit('reconnect', { wsKey: wsKey });
  },

  /**
   * Send message command
   * @param wsKey: websocket instance key, defaults to 'default'
   * @param msgId: message ID, if not specified, uses incremental ID
   * @param cmd: command/interface name
   * @param data: command/interface parameters
   * @param callback: callback function (dict) => {} or object containing callback function {callback: (dict) => {}, limits: 1}
   *    callback: callback function
   *    limits: limit callback count, no callback when 0, unlimited when negative, defaults to 1
   * Usage:
   *  1. this.$store.dispatch('websocket/sendCmd', {cmd: 'xxxxx', data: {}, callback: (dict) => {}})
   *  2. dispatch('websocket/sendCmd', {cmd: 'xxxxx', data: {}, callback: (dict) => {}}, { root: true })
   */
  sendCmd(context, { wsKey, msgId, cmd, data, callback }) {
    const wsInfo = wsInfoMap[wsKey || 'default'];
    if (!wsInfo) return -1;
    if (!wsInfo.rws) {
      wsInfo.logger.error(`Websocket is not init`);
      return -1;
    }
    if (wsInfo.rws.readyState !== ReconnectingWebSocket.OPEN) {
      wsInfo.logger.error(`Websocket readyState is not open`);
      return -2;
    }
    const msg = {
      cmd: cmd,
      data: data || {},
    };
    msg.id = msgId || wsInfo.msgId;
    if (msg.id === wsInfo.msgId) {
      context.commit('setMsgId', { wsKey: wsKey, msgId: wsInfo.msgId + 1 });
      if (wsInfo.msgId > 10000) {
        context.commit('setMsgId', { wsKey: wsKey, msgId: 1 });
      }
    }
    if (callback) {
      if (typeof callback === 'function') {
        context.commit('addJsonMsgCallback', { wsKey: wsKey, msgId: msg.id, callback: {
          callback: callback,
          limits: 1,
          finished: false,
        } });
      }
      else if (typeof callback === 'object' && callback.callback) {
        if (callback.limits === undefined) {
          callback.limits = 1;
        }
        callback.finished = false;
        context.commit('addJsonMsgCallback', { wsKey: wsKey, msgId: msg.id, callback: callback });
      }
    }
    const msgStr = JSON.stringify(msg);
    if (wsInfo.options.debug) {
      wsInfo.logger.log(`Websocket send: ${msgStr}`);
    }
    wsInfo.rws.send(msgStr);
    return msg.id;
  }
};

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
