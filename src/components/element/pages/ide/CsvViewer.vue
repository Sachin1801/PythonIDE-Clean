<template>
  <div class="csv-viewer-container">
    <div class="csv-controls">
      <div class="csv-info">
        <span>{{ rowCount }} rows × {{ columnCount }} columns</span>
        <span v-if="showLargeFileWarning" class="large-file-warning">
          ⚠️ Large file - scroll performance may vary
        </span>
      </div>
      <div class="csv-search" v-if="!isExamMode">
        <input
          v-model="searchQuery"
          placeholder="Search..."
          class="search-input"
        />
      </div>
    </div>
    <div
      ref="tableContainer"
      class="csv-table-wrapper"
      @scroll="handleScroll"
    >
      <!-- Virtual scroll spacer -->
      <div :style="{ height: totalHeight + 'px', position: 'relative' }">
        <table
          class="csv-table"
          :style="{ transform: `translateY(${offsetY}px)` }"
        >
          <thead>
            <tr>
              <th class="row-number-header">#</th>
              <th
                v-for="(header, index) in displayHeaders"
                :key="index"
                :class="['csv-header', { 'sortable': !isExamMode }]"
                @click="!isExamMode && sortBy(index)"
              >
                <div class="header-content">
                  <span>{{ header || `Column ${index + 1}` }}</span>
                  <span v-if="sortColumn === index" class="sort-icon">
                    {{ sortDirection === 'asc' ? '▲' : '▼' }}
                  </span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in visibleRows" :key="visibleStartIndex + idx">
              <td class="row-number">{{ visibleStartIndex + idx + 1 }}</td>
              <td
                v-for="(cell, cellIndex) in row"
                :key="cellIndex"
                class="csv-cell"
                :title="cell"
              >
                {{ cell }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="filteredData.length === 0" class="no-data">
        No data to display
      </div>
    </div>
    <!-- Scroll position indicator -->
    <div class="scroll-info" v-if="filteredData.length > 0">
      <span>Showing rows {{ visibleStartIndex + 1 }} - {{ Math.min(visibleEndIndex, filteredData.length) }} of {{ filteredData.length }}</span>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus';

export default {
  props: {
    content: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      headers: [],
      rows: [],
      searchQuery: '',
      sortColumn: null,
      sortDirection: 'asc',
      // Virtual scroll state
      scrollTop: 0,
      containerHeight: 400,
      rowHeight: 32, // pixels per row
      overscan: 5, // extra rows to render above/below viewport
      showLargeFileWarning: false,
      resizeObserver: null
    }
  },
  computed: {
    isExamMode() {
      // Primary check: URL-based detection (most reliable)
      // Exam IDE runs on exam.* subdomain
      const hostname = window.location.hostname;
      if (hostname.startsWith('exam.') || hostname.includes('exam')) {
        return true;
      }

      // Fallback: Check Vuex state
      const vuexValue = this.$store?.state?.ide?.ideInfo?.isExamMode;
      if (vuexValue !== undefined && vuexValue !== null) {
        return vuexValue;
      }

      // Final fallback: localStorage
      return localStorage.getItem('is_exam_mode') === 'true';
    },
    parsedData() {
      if (!this.content) return { headers: [], rows: [] };

      const lines = this.content.split('\n').filter(line => line.trim());
      if (lines.length === 0) return { headers: [], rows: [] };

      // Parse CSV
      const parseCSVLine = (line) => {
        const result = [];
        let current = '';
        let inQuotes = false;

        for (let i = 0; i < line.length; i++) {
          const char = line[i];
          const nextChar = line[i + 1];

          if (char === '"') {
            if (inQuotes && nextChar === '"') {
              current += '"';
              i++; // Skip next quote
            } else {
              inQuotes = !inQuotes;
            }
          } else if (char === ',' && !inQuotes) {
            result.push(current.trim());
            current = '';
          } else {
            current += char;
          }
        }
        result.push(current.trim());
        return result;
      };

      const headers = parseCSVLine(lines[0]);
      const rows = lines.slice(1).map(line => parseCSVLine(line));

      return { headers, rows };
    },
    filteredData() {
      let data = this.parsedData.rows;

      // Search filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        data = data.filter(row =>
          row.some(cell =>
            cell.toString().toLowerCase().includes(query)
          )
        );
      }

      // Sort
      if (this.sortColumn !== null) {
        data = [...data].sort((a, b) => {
          const aVal = a[this.sortColumn] || '';
          const bVal = b[this.sortColumn] || '';

          // Try to parse as numbers
          const aNum = parseFloat(aVal);
          const bNum = parseFloat(bVal);

          if (!isNaN(aNum) && !isNaN(bNum)) {
            return this.sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
          }

          // Sort as strings
          const result = aVal.toString().localeCompare(bVal.toString());
          return this.sortDirection === 'asc' ? result : -result;
        });
      }

      return data;
    },
    totalRows() {
      return this.filteredData.length;
    },
    totalHeight() {
      return this.totalRows * this.rowHeight;
    },
    visibleStartIndex() {
      return Math.max(0, Math.floor(this.scrollTop / this.rowHeight) - this.overscan);
    },
    visibleEndIndex() {
      const visibleCount = Math.ceil(this.containerHeight / this.rowHeight);
      return Math.min(this.totalRows, this.visibleStartIndex + visibleCount + this.overscan * 2);
    },
    visibleRows() {
      return this.filteredData.slice(this.visibleStartIndex, this.visibleEndIndex);
    },
    offsetY() {
      return this.visibleStartIndex * this.rowHeight;
    },
    rowCount() {
      return this.parsedData.rows.length;
    },
    columnCount() {
      return this.parsedData.headers.length;
    },
    displayHeaders() {
      return this.parsedData.headers;
    }
  },
  watch: {
    content() {
      this.scrollTop = 0;
      this.sortColumn = null;
      this.sortDirection = 'asc';
      this.checkLargeFile();
      // Reset scroll position
      if (this.$refs.tableContainer) {
        this.$refs.tableContainer.scrollTop = 0;
      }
    },
    searchQuery() {
      this.scrollTop = 0;
      if (this.$refs.tableContainer) {
        this.$refs.tableContainer.scrollTop = 0;
      }
    }
  },
  mounted() {
    this.initContainerHeight();
    this.setupResizeObserver();
    this.checkLargeFile();
  },
  beforeUnmount() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  },
  methods: {
    handleScroll(e) {
      this.scrollTop = e.target.scrollTop;
    },
    initContainerHeight() {
      if (this.$refs.tableContainer) {
        this.containerHeight = this.$refs.tableContainer.clientHeight || 400;
      }
    },
    setupResizeObserver() {
      if (typeof ResizeObserver !== 'undefined' && this.$refs.tableContainer) {
        this.resizeObserver = new ResizeObserver(entries => {
          for (const entry of entries) {
            this.containerHeight = entry.contentRect.height || 400;
          }
        });
        this.resizeObserver.observe(this.$refs.tableContainer);
      }
    },
    checkLargeFile() {
      if (this.parsedData.rows.length > 10000) {
        this.showLargeFileWarning = true;
        ElMessage.warning({
          message: `Large CSV file: ${this.parsedData.rows.length.toLocaleString()} rows. Using virtual scrolling for better performance.`,
          duration: 4000
        });
      } else {
        this.showLargeFileWarning = false;
      }
    },
    sortBy(columnIndex) {
      if (this.sortColumn === columnIndex) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortColumn = columnIndex;
        this.sortDirection = 'asc';
      }
      // Reset scroll to top when sorting
      this.scrollTop = 0;
      if (this.$refs.tableContainer) {
        this.$refs.tableContainer.scrollTop = 0;
      }
    }
  }
}
</script>

<style scoped>
.csv-viewer-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary, #1e1e1e);
  color: var(--text-primary, #cccccc);
  position: relative;
  overflow: hidden;
}

.csv-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: var(--bg-secondary, #252526);
  border-bottom: 1px solid var(--border-color, #3e3e42);
  flex-shrink: 0;
}

.csv-info {
  font-size: 14px;
  color: var(--text-secondary, #969696);
  display: flex;
  align-items: center;
  gap: 12px;
}

.large-file-warning {
  color: #f0ad4e;
  font-size: 12px;
}

.search-input {
  padding: 6px 12px;
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #3e3e42);
  color: var(--text-primary, #cccccc);
  border-radius: 4px;
  width: 250px;
}

.search-input:focus {
  outline: none;
  border-color: #007acc;
}

.csv-table-wrapper {
  flex: 1;
  overflow: auto;
  position: relative;
  width: 100%;
  min-height: 0;
}

/* Custom scrollbar styling */
.csv-table-wrapper::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

.csv-table-wrapper::-webkit-scrollbar-track {
  background: var(--bg-secondary, #252526);
  border-radius: 2px;
}

.csv-table-wrapper::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

.csv-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.csv-table-wrapper::-webkit-scrollbar-corner {
  background: var(--bg-secondary, #252526);
}

.csv-table {
  width: max-content;
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 13px;
  table-layout: auto;
  position: absolute;
  top: 0;
  left: 0;
}

.csv-table thead {
  position: sticky;
  top: 0;
  background: var(--bg-secondary, #252526);
  z-index: 10;
}

.csv-table th {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 2px solid var(--border-color, #3e3e42);
  border-right: 1px solid var(--border-color, #3e3e42);
  font-weight: 600;
  user-select: none;
  white-space: nowrap;
  min-width: 150px;
  position: relative;
  height: 32px;
  box-sizing: border-box;
}

.csv-table th.sortable {
  cursor: pointer;
}

.csv-table th.sortable:hover {
  background: rgba(255, 255, 255, 0.05);
}

.csv-table th:not(.sortable):not(.row-number-header) {
  cursor: default;
}

.row-number-header {
  width: 50px;
  min-width: 50px;
  text-align: center;
  background: var(--bg-tertiary, #2d2d30);
  position: sticky;
  left: 0;
  z-index: 11;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.sort-icon {
  font-size: 10px;
  color: #007acc;
}

.csv-table td {
  padding: 6px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  min-width: 150px;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  height: 32px;
  box-sizing: border-box;
}

.csv-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}

.csv-table tbody tr:nth-child(even) {
  background: rgba(255, 255, 255, 0.02);
}

.row-number {
  width: 50px;
  min-width: 50px;
  text-align: center;
  background: var(--bg-tertiary, #2d2d30);
  color: var(--text-secondary, #969696);
  font-weight: 500;
  position: sticky;
  left: 0;
  z-index: 1;
}

.csv-cell {
  color: var(--text-primary, #cccccc);
}

.no-data {
  padding: 40px;
  text-align: center;
  color: var(--text-secondary, #969696);
}

.scroll-info {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: var(--bg-secondary, #252526);
  border-top: 1px solid var(--border-color, #3e3e42);
  font-size: 12px;
  color: var(--text-secondary, #969696);
  flex-shrink: 0;
}

/* Light theme support */
[data-theme="light"] .csv-viewer-container {
  background: #ffffff;
  color: #333333;
}

[data-theme="light"] .csv-controls,
[data-theme="light"] .csv-table thead,
[data-theme="light"] .scroll-info {
  background: #f3f3f3;
}

[data-theme="light"] .search-input {
  background: #ffffff;
  border-color: #d4d4d4;
  color: #333333;
}

[data-theme="light"] .csv-table th {
  border-color: #d4d4d4;
}

[data-theme="light"] .row-number-header,
[data-theme="light"] .row-number {
  background: #f8f8f8;
}

[data-theme="light"] .csv-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.03);
}

[data-theme="light"] .csv-table tbody tr:nth-child(even) {
  background: rgba(0, 0, 0, 0.02);
}

[data-theme="light"] .large-file-warning {
  color: #856404;
}
</style>
