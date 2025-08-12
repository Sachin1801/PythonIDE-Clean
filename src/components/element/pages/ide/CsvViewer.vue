<template>
  <div class="csv-viewer-container">
    <div class="csv-controls">
      <div class="csv-info">
        <span>{{ rowCount }} rows × {{ columnCount }} columns</span>
      </div>
      <div class="csv-search">
        <input 
          v-model="searchQuery" 
          placeholder="Search..."
          class="search-input"
        />
      </div>
    </div>
    <div class="csv-table-wrapper">
      <table class="csv-table">
        <thead>
          <tr>
            <th class="row-number-header">#</th>
            <th 
              v-for="(header, index) in headers" 
              :key="index"
              class="csv-header"
              @click="sortBy(index)"
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
          <tr v-for="(row, rowIndex) in paginatedData" :key="rowIndex">
            <td class="row-number">{{ startRow + rowIndex + 1 }}</td>
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
      <div v-if="filteredData.length === 0" class="no-data">
        No data to display
      </div>
    </div>
    <div class="csv-pagination" v-if="totalPages > 1">
      <button 
        @click="currentPage = 1" 
        :disabled="currentPage === 1"
        class="pagination-btn"
      >
        First
      </button>
      <button 
        @click="currentPage--" 
        :disabled="currentPage === 1"
        class="pagination-btn"
      >
        Previous
      </button>
      <span class="page-info">
        Page {{ currentPage }} of {{ totalPages }}
      </span>
      <button 
        @click="currentPage++" 
        :disabled="currentPage === totalPages"
        class="pagination-btn"
      >
        Next
      </button>
      <button 
        @click="currentPage = totalPages" 
        :disabled="currentPage === totalPages"
        class="pagination-btn"
      >
        Last
      </button>
      <select v-model="rowsPerPage" class="rows-select">
        <option :value="25">25 rows</option>
        <option :value="50">50 rows</option>
        <option :value="100">100 rows</option>
        <option :value="500">500 rows</option>
      </select>
    </div>
  </div>
</template>

<script>
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
      currentPage: 1,
      rowsPerPage: 100
    }
  },
  computed: {
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
    totalPages() {
      return Math.ceil(this.filteredData.length / this.rowsPerPage);
    },
    startRow() {
      return (this.currentPage - 1) * this.rowsPerPage;
    },
    paginatedData() {
      const start = this.startRow;
      const end = start + this.rowsPerPage;
      return this.filteredData.slice(start, end);
    },
    rowCount() {
      return this.parsedData.rows.length;
    },
    columnCount() {
      return this.parsedData.headers.length;
    },
    headers() {
      return this.parsedData.headers;
    },
    rows() {
      return this.parsedData.rows;
    }
  },
  watch: {
    content() {
      this.currentPage = 1;
      this.sortColumn = null;
      this.sortDirection = 'asc';
    },
    searchQuery() {
      this.currentPage = 1;
    },
    rowsPerPage() {
      this.currentPage = 1;
    }
  },
  methods: {
    sortBy(columnIndex) {
      if (this.sortColumn === columnIndex) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortColumn = columnIndex;
        this.sortDirection = 'asc';
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
}

.csv-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: var(--bg-secondary, #252526);
  border-bottom: 1px solid var(--border-color, #3e3e42);
}

.csv-info {
  font-size: 14px;
  color: var(--text-secondary, #969696);
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
  overflow: auto; /* Enable both horizontal and vertical scrolling */
  position: relative;
  width: 100%;
  min-height: 0; /* Important for flexbox overflow */
  display: block;
}

/* Custom scrollbar styling for better visibility */
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
  width: max-content; /* This ensures table is as wide as its content */
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 13px;
  table-layout: auto;
  display: table;
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
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  min-width: 150px; /* Increased minimum width for better visibility */
  position: relative;
}

.csv-table th:hover {
  background: rgba(255, 255, 255, 0.05);
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
  min-width: 150px; /* Match header min-width */
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.csv-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 10px;
  background: var(--bg-secondary, #252526);
  border-top: 1px solid var(--border-color, #3e3e42);
}

.pagination-btn {
  padding: 6px 12px;
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #3e3e42);
  color: var(--text-primary, #cccccc);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  border-color: #007acc;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: var(--text-secondary, #969696);
}

.rows-select {
  padding: 6px 12px;
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #3e3e42);
  color: var(--text-primary, #cccccc);
  border-radius: 4px;
  cursor: pointer;
}

/* Light theme support */
[data-theme="light"] .csv-viewer-container {
  background: #ffffff;
  color: #333333;
}

[data-theme="light"] .csv-controls,
[data-theme="light"] .csv-table thead,
[data-theme="light"] .csv-pagination {
  background: #f3f3f3;
}

[data-theme="light"] .search-input,
[data-theme="light"] .pagination-btn,
[data-theme="light"] .rows-select {
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
</style>