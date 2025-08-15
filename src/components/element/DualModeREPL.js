// Dual-Mode REPL Implementation for VmIde.vue
// This module provides both backend WebSocket REPL and Pyodide browser-based REPL

export const DualModeREPL = {
  data() {
    return {
      // REPL mode configuration
      replMode: 'auto', // 'backend', 'pyodide', or 'auto'
      pyodideNamespace: null,
      pyodideInitialized: false,
    };
  },

  methods: {
    // Initialize and start REPL session with automatic mode detection
    async startDualModeReplSession() {
      this.replSessionId = Date.now().toString();
      console.log('🚀 [REPL] Starting dual-mode REPL session:', this.replSessionId);
      console.log('📊 [REPL] Current state:', {
        wsInfo: this.wsInfo,
        wsConnected: this.wsInfo?.connected,
        wsReadyState: this.wsInfo?.rws?.readyState,
        replMode: this.replMode,
        pyodideReady: this.pyodideReady,
        pyodideInitialized: this.pyodideInitialized
      });
      
      // Ensure REPL console exists
      this.ensureReplConsole();
      
      // Determine which mode to use
      const backendAvailable = this.wsInfo && this.wsInfo.connected;
      const preferBackend = this.replMode === 'backend' || (this.replMode === 'auto' && backendAvailable);
      
      console.log('🔍 [REPL] Mode detection:', {
        backendAvailable,
        preferBackend,
        replMode: this.replMode
      });
      
      if (preferBackend && backendAvailable) {
        console.log('✅ [REPL] Using backend mode');
        await this.startBackendRepl();
      } else {
        console.log('🌐 [REPL] Using Pyodide browser mode');
        await this.startPyodideRepl();
      }
    },

    // Start backend REPL via WebSocket
    async startBackendRepl() {
      console.log('🔌 [REPL] Starting backend REPL...');
      this.addReplOutput('Connecting to backend Python REPL...', 'system');
      
      try {
        // Send start command via WebSocket
        const startMsg = {
          cmd: 'start_python_repl',
          id: this.replSessionId,
          data: {
            projectName: this.ideInfo.currProj?.data?.name || 'repl'
          }
        };
        
        console.log('📤 [REPL] Sending start message:', startMsg);
        console.log('🔌 [REPL] WebSocket state:', {
          rws: this.wsInfo.rws,
          readyState: this.wsInfo.rws?.readyState,
          OPEN: WebSocket.OPEN
        });
        
        // Send directly via WebSocket
        if (this.wsInfo.rws && this.wsInfo.rws.readyState === WebSocket.OPEN) {
          this.wsInfo.rws.send(JSON.stringify(startMsg));
          console.log('✅ [REPL] Start message sent successfully');
          this.addReplOutput('Backend Python REPL connected', 'system');
          this.addReplOutput('Type Python code and press Enter to execute', 'system');
        } else {
          throw new Error(`WebSocket not connected: readyState=${this.wsInfo.rws?.readyState}`);
        }
      } catch (error) {
        console.error('❌ [REPL] Backend REPL failed:', error);
        this.addReplOutput('Backend unavailable, switching to browser mode...', 'error');
        await this.startPyodideRepl();
      }
    },

    // Start Pyodide REPL in browser
    async startPyodideRepl() {
      console.log('🌐 [REPL] Starting Pyodide REPL, current state:', {
        pyodideReady: this.pyodideReady,
        pyodideInitialized: this.pyodideInitialized
      });
      
      if (!this.pyodideReady) {
        console.log('🔄 [REPL] Pyodide not ready, initializing...');
        await this.initializePyodideForRepl();
      }
      
      if (this.pyodideReady) {
        console.log('✅ [REPL] Pyodide ready for use');
        this.addReplOutput('Python 3.11 (Pyodide) REPL', 'system');
        this.addReplOutput('Running in browser - no backend required!', 'system');
        this.addReplOutput('Type Python code and press Enter to execute', 'system');
      } else {
        console.log('❌ [REPL] Failed to initialize Pyodide');
        this.addReplOutput('Failed to initialize browser Python', 'error');
        this.isReplMode = false;
      }
    },

    // Initialize Pyodide environment
    async initializePyodideForRepl() {
      console.log('🔄 [REPL] initializePyodideForRepl called, state:', {
        pyodideLoading: this.pyodideLoading,
        pyodideReady: this.pyodideReady,
        loadPyodideAvailable: typeof window.loadPyodide
      });
      
      if (this.pyodideLoading || this.pyodideReady) {
        console.log('⚠️ [REPL] Pyodide already loading or ready, skipping');
        return;
      }
      
      this.pyodideLoading = true;
      this.addReplOutput('Loading Python in browser...', 'system');
      
      try {
        // Check if Pyodide script is loaded
        if (typeof window.loadPyodide !== 'function') {
          throw new Error('Pyodide not available. Please check internet connection.');
        }
        
        console.log('📦 [REPL] Loading Pyodide from CDN...');
        
        // Load Pyodide
        this.pyodide = await window.loadPyodide({
          indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/'
        });
        
        // Create execution namespace
        this.pyodideNamespace = this.pyodide.globals.get('dict')();
        
        // Setup Python environment
        await this.pyodide.runPythonAsync(`
          import sys
          import io
          import builtins
          
          # Store the version
          python_version = sys.version
          
          # Setup for REPL
          _ = None
        `);
        
        this.pyodideReady = true;
        this.pyodideLoading = false;
        this.pyodideInitialized = true;
        console.log('✅ [REPL] Pyodide REPL ready!', {
          pyodide: this.pyodide,
          namespace: this.pyodideNamespace
        });
        
      } catch (error) {
        console.error('❌ [REPL] Pyodide initialization failed:', error);
        this.pyodideLoading = false;
        this.pyodideReady = false;
        this.addReplOutput(`Error: ${error.message}`, 'error');
      }
    },

    // Execute command in appropriate REPL
    async executeReplCommandDualMode(command) {
      console.log('🎯 [REPL] executeReplCommandDualMode called with:', command);
      
      if (!command.trim()) {
        console.log('⚠️ [REPL] Empty command, handling continuation mode');
        if (this.replContinuationMode) {
          this.replContinuationMode = false;
          this.replPrompt = '>>> ';
        }
        return;
      }
      
      // Store in history
      if (this.replHistory[this.replHistory.length - 1] !== command) {
        this.replHistory.push(command);
      }
      this.replHistoryIndex = -1;
      
      // Clear input
      this.replInput = '';
      this.replInputRows = 1;
      
      // Echo command
      this.addReplOutput(this.replPrompt + command, 'input');
      
      // Determine execution mode
      const useBackend = this.wsInfo?.connected && this.replSessionId && this.replMode !== 'pyodide';
      
      console.log('🔍 [REPL] Execution mode check:', {
        wsConnected: this.wsInfo?.connected,
        replSessionId: this.replSessionId,
        replMode: this.replMode,
        useBackend,
        pyodideReady: this.pyodideReady
      });
      
      if (useBackend) {
        console.log('📤 [REPL] Executing via backend');
        await this.executeBackendCommand(command);
      } else if (this.pyodideReady) {
        console.log('🌐 [REPL] Executing via Pyodide');
        await this.executePyodideCommand(command);
      } else {
        console.log('⚠️ [REPL] No environment ready, initializing Pyodide...');
        // Try to initialize Pyodide as fallback
        await this.startPyodideRepl();
        if (this.pyodideReady) {
          await this.executePyodideCommand(command);
        } else {
          this.addReplOutput('No Python environment available', 'error');
        }
      }
    },

    // Execute command on backend
    async executeBackendCommand(command) {
      console.log('📤 [REPL] executeBackendCommand called with:', command);
      try {
        const inputMsg = {
          cmd: 'send_program_input',
          id: Date.now().toString(),
          data: {
            program_id: this.replSessionId,
            input: command
          }
        };
        
        console.log('📨 [REPL] Sending command message:', inputMsg);
        
        if (this.wsInfo.rws && this.wsInfo.rws.readyState === WebSocket.OPEN) {
          this.wsInfo.rws.send(JSON.stringify(inputMsg));
          console.log('✅ [REPL] Command sent to backend');
        } else {
          throw new Error(`WebSocket disconnected: readyState=${this.wsInfo.rws?.readyState}`);
        }
      } catch (error) {
        console.error('❌ [REPL] Backend execution failed:', error);
        this.addReplOutput('Backend error, switching to browser mode...', 'error');
        await this.startPyodideRepl();
        if (this.pyodideReady) {
          await this.executePyodideCommand(command);
        }
      }
    },

    // Execute command in Pyodide
    async executePyodideCommand(command) {
      if (!this.pyodideReady || !this.pyodide) {
        this.addReplOutput('Browser Python not ready', 'error');
        return;
      }
      
      try {
        // Setup output capture
        await this.pyodide.runPythonAsync(`
          import sys
          from io import StringIO
          _stdout = StringIO()
          _stderr = StringIO()
          _old_stdout = sys.stdout
          _old_stderr = sys.stderr
          sys.stdout = _stdout
          sys.stderr = _stderr
        `);
        
        let result = null;
        let executionError = null;
        
        try {
          // Execute command
          result = await this.pyodide.runPythonAsync(command, { globals: this.pyodideNamespace });
          
          // Store result in _ variable for REPL behavior
          if (result !== undefined && result !== null) {
            await this.pyodide.runPythonAsync('_ = _result', {
              globals: {...this.pyodideNamespace.toJs(), _result: result}
            });
          }
        } catch (error) {
          executionError = error;
        }
        
        // Get output
        const output = await this.pyodide.runPythonAsync(`
          sys.stdout = _old_stdout
          sys.stderr = _old_stderr
          stdout_val = _stdout.getvalue()
          stderr_val = _stderr.getvalue()
          _stdout.close()
          _stderr.close()
          (stdout_val, stderr_val)
        `);
        
        // Display stdout
        if (output[0]) {
          this.addReplOutput(output[0], 'output');
        }
        
        // Display stderr
        if (output[1]) {
          this.addReplOutput(output[1], 'error');
        }
        
        // Display error if any
        if (executionError) {
          this.addReplOutput(String(executionError), 'error');
        } else if (result !== undefined && result !== null) {
          // Display result if not None
          const pyNone = this.pyodide.globals.get('None');
          if (result !== pyNone) {
            try {
              // Get string representation
              const reprStr = await this.pyodide.runPythonAsync(
                `repr(_last_val)`,
                {globals: {...this.pyodideNamespace.toJs(), _last_val: result}}
              );
              if (reprStr && reprStr !== 'None') {
                this.addReplOutput(reprStr, 'output');
              }
            } catch (e) {
              // Fallback to toString
              const str = String(result);
              if (str && str !== '[object Object]') {
                this.addReplOutput(str, 'output');
              }
            }
          }
        }
        
        // Update prompt for continuation
        if (command.trim().endsWith(':')) {
          this.replContinuationMode = true;
          this.replPrompt = '... ';
        } else {
          this.replContinuationMode = false;
          this.replPrompt = '>>> ';
        }
        
      } catch (error) {
        console.error('Pyodide execution error:', error);
        this.addReplOutput(`Error: ${error.message}`, 'error');
      }
      
      // Scroll console to bottom
      this.$nextTick(() => {
        if (this.$refs.consoleOutputArea) {
          this.$refs.consoleOutputArea.scrollTop = this.$refs.consoleOutputArea.scrollHeight;
        }
      });
    },

    // Handle backend REPL responses
    handleBackendReplResponse(message) {
      console.log('📥 [REPL] Backend response received:', {
        code: message?.code,
        hasData: !!message?.data,
        dataKeys: message?.data ? Object.keys(message.data) : [],
        fullMessage: message
      });
      
      if (!message) {
        console.log('⚠️ [REPL] Empty message received');
        return;
      }
      
      // Handle response codes
      if (message.code === 0 || message.code === '0') {
        // Output from REPL
        if (message.data) {
          if (message.data.stdout) {
            // Filter prompts we already show
            const output = message.data.stdout;
            if (!output.match(/^(>>>|\.\.\.)\\s*$/)) {
              this.addReplOutput(output, 'output');
            }
          }
          if (message.data.stderr) {
            this.addReplOutput(message.data.stderr, 'error');
          }
        }
      } else if (message.code === 2000) {
        // REPL prompt update
        if (message.data?.type === 'repl_prompt') {
          this.replPrompt = message.data.prompt || '>>> ';
          this.replContinuationMode = this.replPrompt === '... ';
        } else if (message.data?.stdout) {
          this.addReplOutput(message.data.stdout, 'output');
        }
      } else if (message.code === 1111) {
        // Session ended
        this.addReplOutput('Backend session ended', 'system');
        this.replSessionId = null;
        // Auto-switch to Pyodide
        this.addReplOutput('Switching to browser mode...', 'system');
        this.startPyodideRepl();
      }
      
      // Scroll to bottom
      this.$nextTick(() => {
        if (this.$refs.consoleOutputArea) {
          this.$refs.consoleOutputArea.scrollTop = this.$refs.consoleOutputArea.scrollHeight;
        }
      });
    },

    // Stop REPL session
    async stopDualModeReplSession() {
      // Stop backend session if active
      if (this.replSessionId && this.wsInfo?.rws?.readyState === WebSocket.OPEN) {
        const stopMsg = {
          cmd: 'stop_python_program',
          id: Date.now().toString(),
          data: {
            program_id: this.replSessionId
          }
        };
        this.wsInfo.rws.send(JSON.stringify(stopMsg));
      }
      
      // Clean up
      this.replSessionId = null;
      this.isReplMode = false;
      this.replPrompt = '>>> ';
      this.replContinuationMode = false;
      
      // Clean up Pyodide namespace but keep Pyodide loaded
      if (this.pyodideNamespace) {
        this.pyodideNamespace = this.pyodide?.globals.get('dict')();
      }
    }
  }
};

export default DualModeREPL;