<template>
  <div class="code-editor-container">
    <!-- <div class="file-path">/{{ ideInfo.currProj.data.name + codeItem.path }}</div> -->
    <Codemirror
      :value="codeItemContent"
      @change="codeChanged"
      class="code-editor-flex"
      id="codemirror-id"
      :options="cmOptions"
      ref="codeEditor" />
    <!-- <div class="float-clear"></div> -->
  </div>
</template>

<script>
// codemirror
import CodeMirror from 'codemirror';
import Codemirror from 'codemirror-editor-vue3';
// core styles
import 'codemirror/lib/codemirror.css'
// theme
import 'codemirror/theme/darcula.css';
import 'codemirror/theme/monokai.css';
import 'codemirror/theme/idea.css';
import 'codemirror/theme/eclipse.css';
// language - Python focused
import 'codemirror/mode/python/python';  // .py
import 'codemirror/mode/htmlmixed/htmlmixed';  // .html (for notebooks)
import 'codemirror/mode/css/css';  // .css (for notebooks)
import 'codemirror/mode/shell/shell'; // .sh
import 'codemirror/mode/sql/sql';  // .sql (for data science)
import 'codemirror/mode/xml/xml';  // .xml
import 'codemirror/mode/yaml/yaml';  // .yaml config files
// active-line
import 'codemirror/addon/selection/active-line';
// comment
import 'codemirror/addon/comment/comment';
// search
import 'codemirror/addon/search/match-highlighter';
import 'codemirror/addon/search/search';
import 'codemirror/addon/search/searchcursor';
import 'codemirror/addon/dialog/dialog';
import 'codemirror/addon/dialog/dialog.css';
// brackets
import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/addon/edit/closebrackets';
// foldgutter
import 'codemirror/addon/fold/foldgutter';
import 'codemirror/addon/fold/foldgutter.css';
// display
// import 'codemirror/addon/display/fullscreen';
// import 'codemirror/addon/display/fullscreen.css';
// hint
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';
import 'codemirror/addon/hint/sql-hint';  // Keep SQL hint for data science
// keymap
import 'codemirror/keymap/sublime';
// import PythonHint from '@/assets/lib/python-hint';

import * as types from '../../../../../store/mutation-types';
import clipboardTracker from '../../../../../utils/clipboardTracker';

export default {
  props: {
    codeItem: Object,
    codeItemIndex: Number,
    consoleLimit: Boolean,
    wordWrap: {
      type: Boolean,
      default: true
    }
  },
  data () {
    return {
      writeTimeout: null,
      codeOtherOptions: {
        py: {
          tabSize: 4,
          indentUnit: 4,
          mode: {
            name: 'text/x-python',
            version: 3,
            singleLineStringErrors: false,
          }
        },
        pyx: {
          tabSize: 4,
          indentUnit: 4,
          mode: {
            name: 'text/x-cython',
            version: 3,
            singleLineStringErrors: false,
          }
        },
        html: {
          mode: 'text/html'
        },
        css: {
          mode: 'text/css'
        },
        sh: {
          mode: 'text/x-sh'
        },
        sql: {
          mode: 'text/x-sql'
        },
        xml: {
          mode: 'application/xml'
        },
        yaml: {
          mode: 'text/x-yaml'
        },
        yml: {
          mode: 'text/x-yaml'
        },
        json: {
          mode: 'application/json'
        },
        md: {
          mode: 'text/x-markdown'
        },
        csv: {
          mode: 'text/plain'
        },
        txt: {
          mode: 'text/plain'
        }
      },
      codeBaseOptions: {
        tabSize: 2,
        theme: 'darcula',
        lineNumbers: true, // Show line number
        smartIndent: true, // Smart indent
        indentUnit: 2, // The smart indent unit is 2 spaces in length
        foldGutter: true, // Code folding
        styleActiveLine: true, // Display the style of the selected row
        matchBrackets: true,  // bracket matching
        autoCloseBrackets: true,
        styleSelectedText: true,
        highlightSelectionMatches: { showToken: /\w/, annotateScrollbar: true },
        line: true,
        lineWrapping: this.wordWrap,
        showCursorWhenSelecting: true,
        completeSingle: false,
        gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
        keyMap: 'sublime',
        extraKeys: {
          Tab: function(cm) {
            var spaces = Array(cm.getOption('indentUnit') + 1).join(' ');
            cm.replaceSelection(spaces);
          },
          // Ctrl: function(cm) {
          //   Codemirror.registerHelper('hintWords', 'python', PythonHint);
          //   cm.showHint({ hint: CodeMirror.hint.anyword })
          // },
          // Ctrl: 'autocomplete', // Autocomplete disabled

          // Ctrl+/: Comment with Line Comment
          'Ctrl-/': 'toggleComment',

          // Ctrl+D: Duplicate Line or Selection
          'Ctrl-D': 'duplicateLine',
          // 'Ctrl-D': (cm) => {
          //   // 'Ctrl-D': 'duplicateLine',  // sublime.js
          //   CodeMirror.commands.duplicateLine(cm);
          // },

          // Ctrl+Shift+K: Delete Line
          'Shift-Ctrl-K': 'deleteLine',
          // 'Shift-Ctrl-K': (cm) => {
          //   // 'Shift-Ctrl-K': 'deleteLine',  // sublime.js
          //   CodeMirror.commands.deleteLine(cm);
          // },
          
          'Ctrl-Enter': 'insertLineAfter',
          'Shift-Ctrl-Enter': 'insertLineBefore',
          'Ctrl-H': 'replace',
          'Backspace': (cm) => {
            if (cm.somethingSelected())
              cm.replaceSelection('', cm.getSelection());
            else
              CodeMirror.commands.smartBackspace(cm);
          },
          'F5' : (cm) => {
            console.log('[F5-DEBUG] F5 key pressed, isPython:', this.isPython, 'consoleLimit:', this.consoleLimit);
            if (this.isPython && !this.consoleLimit) {
              console.log('[F5-DEBUG] Emitting run-item event from F5');
              this.$emit('run-item');
            } else {
              console.log('[F5-DEBUG] F5 not processed - isPython:', this.isPython, 'consoleLimit:', this.consoleLimit);
            }
          },

          // Copy operation - track content for students
          'Ctrl-C': (cm) => {
            const selectedText = cm.getSelection();
            if (selectedText) {
              // Track copied content for clipboard validation
              clipboardTracker.trackIDECopy(selectedText);
              console.log('[CodeMirror] Copy tracked:', selectedText.substring(0, 50));

              // Copy to clipboard
              navigator.clipboard.writeText(selectedText).catch(() => {
                // Fallback for older browsers
                document.execCommand('copy');
              });
            }
            return false; // Prevent default behavior
          },

          // Cut operation - track content for students
          'Ctrl-X': (cm) => {
            const selectedText = cm.getSelection();
            if (selectedText) {
              // Track cut content for clipboard validation
              clipboardTracker.trackIDECopy(selectedText);
              console.log('[CodeMirror] Cut tracked:', selectedText.substring(0, 50));

              // Copy to clipboard and remove selection
              navigator.clipboard.writeText(selectedText).then(() => {
                cm.replaceSelection('');
              }).catch(() => {
                // Fallback for older browsers
                document.execCommand('cut');
              });
            }
            return false; // Prevent default behavior
          },

          // Paste operation - validate for students
          'Ctrl-V': async (cm) => {
            try {
              // Get clipboard content
              const clipboardText = await navigator.clipboard.readText();

              // Validate paste for students
              const isAllowed = await clipboardTracker.validatePaste(clipboardText);

              if (isAllowed) {
                // Allow paste - use CodeMirror's built-in paste
                cm.replaceSelection(clipboardText);
                console.log('[CodeMirror] Paste allowed:', clipboardText.substring(0, 50));
              } else {
                // Paste blocked - validatePaste already showed the toast
                console.log('[CodeMirror] Paste blocked for student');
              }
            } catch (error) {
              console.error('[CodeMirror] Paste error:', error);
              // Fallback to default paste if clipboard API fails
              document.execCommand('paste');
            }
          }
        },
      }
    }
  },
  mounted() {
    // this.$emit('update-item', this.codeItem.path, this.codemirror);
    this.updateEditorTheme();
    
    // Force CodeMirror to refresh after mounting to fix coordinate system
    this.$nextTick(() => {
      if (this.$refs.codeEditor && this.$refs.codeEditor.cminstance) {
        this.$refs.codeEditor.cminstance.refresh();
        // Apply saved settings after CodeMirror is ready
        this.applySavedSettings();
        // Force a coordinate system recalculation
        setTimeout(() => {
          this.$refs.codeEditor.cminstance.refresh();
        }, 100);
      }
    });
    
    
    // Listen for theme changes
    const observer = new MutationObserver(() => {
      this.updateEditorTheme();
      // Force CodeMirror to refresh after theme change
      this.$nextTick(() => {
        if (this.$refs.codeEditor && this.$refs.codeEditor.cminstance) {
          this.$refs.codeEditor.cminstance.refresh();
        }
      });
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    });
    
    // Listen for localStorage changes (font size, line numbers, etc.)
    window.addEventListener('storage', (e) => {
      if (e.key === 'fontSize') {
        this.applySavedSettings();
      } else if (e.key === 'showLineNumbers') {
        this.applySavedSettings();
      }
    });
    
    // Listen for custom font size change events (for same-tab changes)
    window.addEventListener('fontSizeChanged', () => {
      this.applySavedSettings();
    });
  },
  watch: {
    // Watch for content changes and fix coordinate system
    'codeItem.content': {
      handler() {
        this.$nextTick(() => {
          this.fixCoordinateSystem();
        });
      },
      deep: true
    }
  },
  beforeUnmount() {
    // Clean up the timeout when component is destroyed
    if (this.writeTimeout) {
      clearTimeout(this.writeTimeout);
    }
  },
  computed: {
    currentTheme() {
      const theme = document.documentElement.getAttribute('data-theme');
      return theme === 'light' ? 'idea' : 'darcula';
    },
    cmOptions() {
      const baseOptions = {...this.codeBaseOptions};
      baseOptions.theme = this.currentTheme;
      
      // Apply saved line numbers setting
      const savedLineNumbers = localStorage.getItem('showLineNumbers');
      if (savedLineNumbers !== null) {
        baseOptions.lineNumbers = savedLineNumbers === 'true';
      }
      
      return Object.assign(baseOptions, this.codeOtherOptions[this.codeItem.path.substring(this.codeItem.path.lastIndexOf('.') + 1)]);
    },
    ideInfo() {
      return this.$store.state.ide.ideInfo;
    },
    codeItemContent: {
      get() {
        return this.codeItem.content;
      },
      set(value) {
        this.$store.commit('ide/setCodeItemContent', {index: this.codeItemIndex, content: value}); 
      }
    },
    // codemirror() {
    //   return this.$refs.codeEditor.cminstance;
    // },
    
    isMarkdown() {
      return this.codeItem.path.endsWith('.md');
    },
    isPython() {
      return this.codeItem.path.endsWith('.py');
    }
  },
  components: {
    Codemirror,
  },
  watch: {
    wordWrap(newVal) {
      // Update CodeMirror lineWrapping option when prop changes
      if (this.$refs.codeEditor && this.$refs.codeEditor.codemirror) {
        this.$refs.codeEditor.codemirror.setOption('lineWrapping', newVal);
      }
    }
  },
  methods: {
    applySavedSettings() {
      // Apply saved font size
      const savedFontSize = localStorage.getItem('fontSize') || localStorage.getItem('editorFontSize');
      if (savedFontSize) {
        const fontSize = parseInt(savedFontSize) + 'px';
        const editor = this.$refs.codeEditor?.cminstance;
        if (editor) {
          const editorElement = editor.getWrapperElement();
          if (editorElement) {
            editorElement.style.fontSize = fontSize;
            editor.refresh();
          }
        }
      }
      
      // Apply saved line numbers setting
      const savedLineNumbers = localStorage.getItem('showLineNumbers') || localStorage.getItem('editorLineNumbers');
      if (savedLineNumbers !== null) {
        const showLineNumbers = savedLineNumbers === 'true' || savedLineNumbers === true;
        const editor = this.$refs.codeEditor?.cminstance;
        if (editor) {
          editor.setOption('lineNumbers', showLineNumbers);
        }
      }
    },
    updateEditorTheme() {
      if (this.$refs.codeEditor && this.$refs.codeEditor.cminstance) {
        const theme = this.currentTheme;
        this.$refs.codeEditor.cminstance.setOption('theme', theme);
        // Force refresh to apply theme changes to all elements
        this.$refs.codeEditor.cminstance.refresh();
      }
    },
    
    // Fix coordinate system issues
    fixCoordinateSystem() {
      if (this.$refs.codeEditor && this.$refs.codeEditor.cminstance) {
        const cm = this.$refs.codeEditor.cminstance;
        // Force CodeMirror to recalculate its coordinate system
        cm.refresh();
        // Force a repaint
        cm.getWrapperElement().style.display = 'none';
        cm.getWrapperElement().offsetHeight; // Force reflow
        cm.getWrapperElement().style.display = '';
        cm.refresh();
      }
    },
    

    // complete
    codeChanged(value, cm) {
      cm.closeHint();
      
      // Update content in store immediately for UI responsiveness
      this.$store.commit('ide/setCodeItemContent', {index: this.codeItemIndex, content: value});
      
      // Debounce file writing to avoid cursor issues
      if (this.writeTimeout) {
        clearTimeout(this.writeTimeout);
      }
      
      // Only auto-save on character change if auto-save is disabled in settings
      // When auto-save is enabled, the time-based system handles saving
      // Check localStorage directly as the source of truth for auto-save setting
      const autoSaveFromLocalStorage = localStorage.getItem('autoSave') === 'true';
      const autoSaveFromStore = this.$store.state.ide.ideInfo?.autoSave || false;
      
      console.log('[AUTO-SAVE-DEBUG] localStorage autoSave:', localStorage.getItem('autoSave'), 'parsed:', autoSaveFromLocalStorage);
      console.log('[AUTO-SAVE-DEBUG] Store autoSave value:', autoSaveFromStore);
      console.log('[AUTO-SAVE-DEBUG] Will use localStorage value:', autoSaveFromLocalStorage);
      
      if (!autoSaveFromLocalStorage) {
        this.writeTimeout = setTimeout(() => {
          // Write file without autocomplete (character-based save when auto-save is off)
          console.log('[CHARACTER-SAVE] Saving due to character change (auto-save disabled)');
          // Use the projectName from the codeItem if available
          const projectName = this.codeItem.projectName || this.ideInfo.currProj?.data?.name || this.ideInfo.currProj?.config?.name;
          this.$store.dispatch(`ide/${types.IDE_WRITE_FILE}`, {
            projectName: projectName,
            filePath: this.codeItem.path,
            fileData: value,
            complete: false, // Autocomplete disabled
            line: 0,
            column: 0,
            callback: (dict) => {
              // No autocomplete callback needed
            }
          });
        }, 500); // Debounce for 500ms
      } else {
        console.log('[CHARACTER-SAVE] Skipping character-based save (auto-save enabled in localStorage)');
      }
    },
    anywordHint(editor, options) {
      var WORD = /[\w$]+/, RANGE = 500;
      var word = options && options.word || WORD;
      var range = options && options.range || RANGE;
      var cur = editor.getCursor(), curLine = editor.getLine(cur.line);
      var end = cur.ch, start = end;
      while (start && word.test(curLine.charAt(start - 1))) --start;
      var curWord = start != end && curLine.slice(start, end);

      var list = options && options.list || [], seen = {};
      var re = new RegExp(word.source, "g");
      for (var dir = -1; dir <= 1; dir += 2) {
        var line = cur.line, endLine = Math.min(Math.max(line + dir * range, editor.firstLine()), editor.lastLine()) + dir;
        for (; line != endLine; line += dir) {
          var text = editor.getLine(line), m;
          m = re.exec(text);
          while (m) {
            if (line == cur.line && m[0] === curWord) {
              m = re.exec(text);
              continue;
            }
            if ((!curWord || m[0].lastIndexOf(curWord, 0) == 0) && !Object.prototype.hasOwnProperty.call(seen, m[0])) {
              seen[m[0]] = true;
              list.push(m[0]);
            }
            m = re.exec(text);
          }
        }
      }
      return {list: list, from: CodeMirror.Pos(cur.line, start), to: CodeMirror.Pos(cur.line, end)};
    },
    getPrefix(line) {
      for (var i = line.length - 1; i >= 0; i--) {
        if (!(/^[a-zA-Z0-9]+$/.test(line.charAt(i)))) {
          return line.substring(i + 1, line.length);
        }
      }
      return line;
    },
    getFirstNonBlankChar(line) {
      for (var i = 0; i < line.length; i++) {
        if (line.charAt(i) != ' ')
          return line.charAt(i);
      }
      return '';
    }
  }
}
</script>

<style>
.CodeMirror-vscrollbar::-webkit-scrollbar {/*scrollbar overall style*/
  width: 5px;     /* height and width correspond to horizontal and vertical scrollbar dimensions */
  height: 5px;
}
.CodeMirror-vscrollbar::-webkit-scrollbar-thumb {/*small block inside scrollbar*/
  /* background: #87939A; */
  background: #545a5e;
}
.CodeMirror-vscrollbar::-webkit-scrollbar-track {/*track inside scrollbar*/
  background: #2F2F2F;
}
.CodeMirror-hscrollbar::-webkit-scrollbar {/*scrollbar overall style*/
  width: 5px;     /* height and width correspond to horizontal and vertical scrollbar dimensions */
  height: 5px;
}
.CodeMirror-hscrollbar::-webkit-scrollbar-thumb {/*small block inside scrollbar*/
  /* background: #87939A; */
  background: #545a5e;
}
.CodeMirror-hscrollbar::-webkit-scrollbar-track {/*track inside scrollbar*/
  background: #2F2F2F;
}
</style>

<style scoped>
.code-editor-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.code-editor-flex {
  flex: 1;
  width: 100%;
  height: 100%;
}

/* Ensure CodeMirror fills the container */
.code-editor-flex >>> .CodeMirror {
  height: 100% !important;
}

.code-editor-flex >>> .codemirror-container {
  height: 100%;
}

/* Fix line numbers to inherit font size from editor */
.code-editor-flex >>> .CodeMirror-linenumber {
  font-size: inherit !important;
}

/* Fix for 26px font size - adjust line height to prevent overflow */
.code-editor-flex >>> .CodeMirror[style*="font-size: 26px"] {
  line-height: 1.6 !important;
}

.code-editor-flex >>> .CodeMirror[style*="font-size: 26px"] .CodeMirror-line {
  padding-top: 2px !important;
  padding-bottom: 2px !important;
}

.code-editor-flex >>> .CodeMirror[style*="font-size: 26px"] .CodeMirror-linenumber {
  line-height: 1.6 !important;
  padding-top: 2px !important;
}

.file-path {
  color: lightblue;
  font-size: 12px;
  background-color: rgba(255, 250, 226, 1.0);
  width: 100%;
  background: #2E3032;
  color: #50E3C2;
  font-family: 'Gotham-Book';
}
.CodeMirrorOveride {
  border: 1px solid #eee;
  height: 10px;
}
</style>
