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
// language
import 'codemirror/mode/python/python';  // .py
import 'codemirror/mode/javascript/javascript';  // .js
import 'codemirror/mode/htmlmixed/htmlmixed';  // .html
import 'codemirror/mode/css/css';
import 'codemirror/mode/go/go';
import 'codemirror/mode/clike/clike';
import 'codemirror/mode/swift/swift';
import 'codemirror/mode/rust/rust';  // .rs
import 'codemirror/mode/ruby/ruby';  // .rb
import 'codemirror/mode/lua/lua';  // .rb
import 'codemirror/mode/sass/sass';
import 'codemirror/mode/shell/shell'; // .sh
import 'codemirror/mode/sql/sql';
import 'codemirror/mode/vue/vue';
import 'codemirror/mode/xml/xml';
import 'codemirror/mode/yaml/yaml';
// active-line
import 'codemirror/addon/selection/active-line';
// comment
import 'codemirror/addon/comment/comment';
// search
import 'codemirror/addon/search/match-highlighter';
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
import 'codemirror/addon/hint/javascript-hint';
import 'codemirror/addon/hint/css-hint';
import 'codemirror/addon/hint/xml-hint';
import 'codemirror/addon/hint/html-hint';
import 'codemirror/addon/hint/sql-hint';
// keymap
import 'codemirror/keymap/sublime';
// import PythonHint from '@/assets/lib/python-hint';

import * as types from '../../../../../store/mutation-types';

export default {
  props: {
    codeItem: Object,
    codeItemIndex: Number,
    consoleLimit: Boolean,
  },
  data () {
    return {
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
        js: {
          mode: 'text/javascript'
        },
        html: {
          mode: 'text/html'
        },
        css: {
          mode: 'text/css'
        },
        less: {
          mode: 'text/x-less'
        },
        scss: {
          mode: 'text/x-scss'
        },
        sass: {
          mode: 'text/x-sass'
        },
        go: {
          mode: 'text/x-go'
        },
        swift: {
          mode: 'text/x-swift'
        },
        rs: {
          mode: 'text/x-rustsrc'
        },
        rb: {
          mode: 'text/x-ruby'
        },
        lua: {
          mode: 'text/x-lua'
        },
        sh: {
          mode: 'text/x-sh'
        },
        sql: {
          mode: 'text/x-sql'
        },
        vue: {
          mode: 'text/x-vue'
        },
        xml: {
          mode: 'application/xml'
        },
        yaml: {
          mode: 'text/x-yaml'
        },
        h: {
          mode: 'text/x-csrc'
        },
        hpp: {
          mode: 'text/x-c++src'
        },
        c: {
          mode: 'text/x-csrc'
        },
        cc: {
          mode: 'text/x-c++src'
        },
        cpp: {
          mode: 'text/x-c++src'
        },
        m: {
          mode: 'text/x-objectivec'
        },
        mm: {
          mode: 'text/x-objectivec'
        },
        cs: {
          mode: 'text/x-csharp'
        },
        java: {
          mode: 'text/x-java'
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
        lineWrapping: false,
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
          // 'Ctrl-/': (cm) => {
          //   // 'Ctrl-/': 'toggleCommentIndented',  // sublime.js
          //   // 'Ctrl-/': 'toggleComment',  // comment.js
          //   cm.toggleComment({ indent: true });
          // },

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
            if (this.isPython && !this.consoleLimit)
              this.$emit('run-item');
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
  computed: {
    currentTheme() {
      const theme = document.documentElement.getAttribute('data-theme');
      return theme === 'light' ? 'idea' : 'darcula';
    },
    cmOptions() {
      const baseOptions = {...this.codeBaseOptions};
      baseOptions.theme = this.currentTheme;
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
  methods: {
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
      this.$store.commit('ide/setCodeItemContent', {index: this.codeItemIndex, content: value});
      
      // Write file without autocomplete
      this.$store.dispatch(`ide/${types.IDE_WRITE_FILE}`, {
        filePath: this.codeItem.path,
        fileData: value,
        complete: false, // Autocomplete disabled
        line: 0,
        column: 0,
        callback: (dict) => {
          // No autocomplete callback needed
        }
      });
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
