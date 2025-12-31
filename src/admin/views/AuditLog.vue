<template>
  <AdminLayout>
    <div class="audit-log-page">
      <!-- Toolbar -->
      <div class="toolbar">
        <div class="toolbar-left">
          <div class="search-box">
            <span class="search-icon"><Search :size="18" /></span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search user or path..."
              @input="handleSearch"
            />
          </div>

          <el-select v-model="actionTypeFilter" placeholder="All Actions" @change="handleFilterChange" clearable>
            <el-option label="All Actions" value="" />
            <el-option
              v-for="actionType in actionTypes"
              :key="actionType"
              :label="formatActionType(actionType)"
              :value="actionType"
            />
          </el-select>

          <el-select v-model="adminFilter" placeholder="All Admins" @change="handleFilterChange" clearable>
            <el-option label="All Admins" value="" />
            <el-option
              v-for="admin in admins"
              :key="admin.id"
              :label="admin.username"
              :value="admin.id"
            />
          </el-select>

          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="to"
            start-placeholder="From"
            end-placeholder="To"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleFilterChange"
            clearable
          />
        </div>

        <div class="toolbar-right">
          <el-button @click="refreshLogs"><RefreshCw :size="16" /> Refresh</el-button>
          <el-button type="primary" @click="exportLogs" :loading="exporting">
            <Download :size="16" /> Export CSV
          </el-button>
        </div>
      </div>

      <!-- Audit Log Table -->
      <div class="admin-card">
        <el-table
          :data="logs"
          v-loading="loading"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="created_at" label="Timestamp" width="180">
            <template #default="scope">
              {{ formatTimestamp(scope.row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column prop="action_type" label="Action" width="180">
            <template #default="scope">
              <div class="action-cell">
                <component :is="getActionIcon(scope.row.action_type)" :size="16" class="action-icon" />
                <span class="badge" :class="getActionClass(scope.row.action_type)">
                  {{ formatActionType(scope.row.action_type) }}
                </span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="admin_username" label="Admin" width="140">
            <template #default="scope">
              <span class="admin-name">{{ scope.row.admin_username }}</span>
            </template>
          </el-table-column>

          <el-table-column label="Target" min-width="200">
            <template #default="scope">
              <div class="target-cell">
                <span v-if="scope.row.target_username" class="target-user">
                  <User :size="14" /> {{ scope.row.target_username }}
                </span>
                <span v-if="scope.row.target_path" class="target-path">
                  <FileText :size="14" /> {{ truncatePath(scope.row.target_path) }}
                </span>
                <span v-if="!scope.row.target_username && !scope.row.target_path" class="no-target">
                  —
                </span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="ip_address" label="IP Address" width="140">
            <template #default="scope">
              <span class="ip-address">{{ scope.row.ip_address || '—' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="Details" width="100">
            <template #default="scope">
              <el-button
                v-if="scope.row.details"
                size="small"
                @click="showDetails(scope.row)"
              >
                <Eye :size="14" />
              </el-button>
              <span v-else>—</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <!-- Details Dialog -->
      <el-dialog v-model="showDetailsDialog" title="Action Details" width="500px">
        <div v-if="selectedLog" class="details-content">
          <div class="detail-row">
            <span class="detail-label">Action:</span>
            <span class="detail-value">{{ formatActionType(selectedLog.action_type) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Admin:</span>
            <span class="detail-value">{{ selectedLog.admin_username }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Timestamp:</span>
            <span class="detail-value">{{ formatTimestamp(selectedLog.created_at) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">IP Address:</span>
            <span class="detail-value">{{ selectedLog.ip_address || 'N/A' }}</span>
          </div>
          <div v-if="selectedLog.target_username" class="detail-row">
            <span class="detail-label">Target User:</span>
            <span class="detail-value">{{ selectedLog.target_username }}</span>
          </div>
          <div v-if="selectedLog.target_path" class="detail-row">
            <span class="detail-label">Target Path:</span>
            <span class="detail-value">{{ selectedLog.target_path }}</span>
          </div>
          <div v-if="selectedLog.details" class="detail-row">
            <span class="detail-label">Additional Details:</span>
            <pre class="detail-json">{{ formatDetails(selectedLog.details) }}</pre>
          </div>
        </div>
        <template #footer>
          <el-button @click="showDetailsDialog = false">Close</el-button>
        </template>
      </el-dialog>
    </div>
  </AdminLayout>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import AdminLayout from '../components/layout/AdminLayout.vue'
import auditApi from '../api/audit'
import {
  Search,
  RefreshCw,
  Download,
  Eye,
  User,
  FileText,
  LogIn,
  LogOut,
  UserPlus,
  Pencil,
  Trash2,
  KeyRound,
  Upload,
  ClipboardCheck,
  ClipboardList
} from 'lucide-vue-next'

export default {
  name: 'AuditLogPage',
  components: {
    AdminLayout,
    Search,
    RefreshCw,
    Download,
    Eye,
    User,
    FileText,
    LogIn,
    LogOut,
    UserPlus,
    Pencil,
    Trash2,
    KeyRound,
    Upload,
    ClipboardCheck,
    ClipboardList
  },
  setup() {
    const store = useStore()

    // State
    const logs = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const loading = ref(false)
    const exporting = ref(false)

    // Filters
    const searchQuery = ref('')
    const actionTypeFilter = ref('')
    const adminFilter = ref('')
    const dateRange = ref(null)

    // Filter options
    const actionTypes = ref([])
    const admins = ref([])

    // Dialog
    const showDetailsDialog = ref(false)
    const selectedLog = ref(null)

    // Debounce timer
    let searchTimer = null

    // Computed
    const token = computed(() => store.getters['auth/token'])

    // Methods
    const fetchLogs = async () => {
      if (!token.value) return

      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          limit: pageSize.value
        }

        if (searchQuery.value) params.search = searchQuery.value
        if (actionTypeFilter.value) params.action_type = actionTypeFilter.value
        if (adminFilter.value) params.admin_id = adminFilter.value
        if (dateRange.value && dateRange.value[0]) params.from_date = dateRange.value[0]
        if (dateRange.value && dateRange.value[1]) params.to_date = dateRange.value[1]

        const response = await auditApi.getLogs(token.value, params)

        if (response.success && response.data) {
          logs.value = response.data.logs
          total.value = response.data.total
        }
      } catch (error) {
        console.error('Failed to fetch audit logs:', error)
        window.ElMessage.error('Failed to fetch audit logs')
      } finally {
        loading.value = false
      }
    }

    const fetchFilterOptions = async () => {
      if (!token.value) return

      try {
        // Fetch action types
        const actionTypesResponse = await auditApi.getActionTypes(token.value)
        if (actionTypesResponse.success) {
          actionTypes.value = actionTypesResponse.data
        }

        // Fetch admins
        const adminsResponse = await auditApi.getAdmins(token.value)
        if (adminsResponse.success) {
          admins.value = adminsResponse.data
        }
      } catch (error) {
        console.error('Failed to fetch filter options:', error)
      }
    }

    const handleSearch = () => {
      clearTimeout(searchTimer)
      searchTimer = setTimeout(() => {
        currentPage.value = 1
        fetchLogs()
      }, 300)
    }

    const handleFilterChange = () => {
      currentPage.value = 1
      fetchLogs()
    }

    const handlePageChange = (page) => {
      currentPage.value = page
      fetchLogs()
    }

    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      fetchLogs()
    }

    const refreshLogs = () => {
      fetchLogs()
      fetchFilterOptions()
    }

    const exportLogs = async () => {
      exporting.value = true
      try {
        const params = {}
        if (searchQuery.value) params.search = searchQuery.value
        if (actionTypeFilter.value) params.action_type = actionTypeFilter.value
        if (adminFilter.value) params.admin_id = adminFilter.value
        if (dateRange.value && dateRange.value[0]) params.from_date = dateRange.value[0]
        if (dateRange.value && dateRange.value[1]) params.to_date = dateRange.value[1]

        const blob = await auditApi.exportLogs(token.value, params)
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `audit_log_${new Date().toISOString().split('T')[0]}.csv`
        a.click()
        window.URL.revokeObjectURL(url)
        window.ElMessage.success('Export complete')
      } catch (error) {
        console.error('Failed to export:', error)
        window.ElMessage.error('Failed to export audit logs')
      } finally {
        exporting.value = false
      }
    }

    const showDetails = (log) => {
      selectedLog.value = log
      showDetailsDialog.value = true
    }

    const formatTimestamp = (timestamp) => {
      if (!timestamp) return '—'
      const date = new Date(timestamp)
      return date.toLocaleString()
    }

    const formatActionType = (actionType) => {
      const labels = {
        'admin_login': 'Login',
        'admin_logout': 'Logout',
        'create_user': 'Create User',
        'update_user': 'Update User',
        'delete_user': 'Delete User',
        'reset_password': 'Reset Password',
        'bulk_import_users': 'Bulk Import',
        'view_file': 'View File',
        'download_file': 'Download File',
        'edit_file': 'Edit File',
        'delete_file': 'Delete File',
        'grade_submission': 'Grade Submission'
      }
      return labels[actionType] || actionType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }

    const getActionIcon = (actionType) => {
      const icons = {
        'admin_login': LogIn,
        'admin_logout': LogOut,
        'create_user': UserPlus,
        'update_user': Pencil,
        'delete_user': Trash2,
        'reset_password': KeyRound,
        'bulk_import_users': Upload,
        'view_file': Eye,
        'download_file': Download,
        'edit_file': Pencil,
        'delete_file': Trash2,
        'grade_submission': ClipboardCheck
      }
      return icons[actionType] || ClipboardList
    }

    const getActionClass = (actionType) => {
      if (actionType.includes('delete')) return 'badge-danger'
      if (actionType.includes('create') || actionType.includes('import')) return 'badge-success'
      if (actionType.includes('login') || actionType.includes('logout')) return 'badge-info'
      if (actionType.includes('update') || actionType.includes('edit') || actionType.includes('reset')) return 'badge-warning'
      return 'badge-default'
    }

    const truncatePath = (path) => {
      if (!path) return ''
      if (path.length <= 50) return path
      return '...' + path.slice(-47)
    }

    const formatDetails = (details) => {
      if (!details) return ''
      if (typeof details === 'string') {
        try {
          return JSON.stringify(JSON.parse(details), null, 2)
        } catch {
          return details
        }
      }
      return JSON.stringify(details, null, 2)
    }

    // Lifecycle
    onMounted(() => {
      fetchLogs()
      fetchFilterOptions()
    })

    return {
      // State
      logs,
      total,
      currentPage,
      pageSize,
      loading,
      exporting,

      // Filters
      searchQuery,
      actionTypeFilter,
      adminFilter,
      dateRange,
      actionTypes,
      admins,

      // Dialog
      showDetailsDialog,
      selectedLog,

      // Methods
      handleSearch,
      handleFilterChange,
      handlePageChange,
      handleSizeChange,
      refreshLogs,
      exportLogs,
      showDetails,
      formatTimestamp,
      formatActionType,
      getActionIcon,
      getActionClass,
      truncatePath,
      formatDetails
    }
  }
}
</script>

<style scoped>
.audit-log-page {
  max-width: 1400px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-box {
  display: flex;
  align-items: center;
  background-color: var(--admin-bg-tertiary);
  border: 1px solid var(--admin-border-color);
  border-radius: 4px;
  padding: 0 12px;
  min-width: 220px;
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 8px;
  color: var(--admin-text-primary);
  font-size: 14px;
}

.search-box input:focus {
  outline: none;
}

.search-icon {
  color: var(--admin-text-muted);
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.action-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-icon {
  color: var(--admin-text-secondary);
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.badge-success {
  background-color: rgba(40, 167, 69, 0.2);
  color: var(--admin-success);
}

.badge-info {
  background-color: rgba(0, 120, 212, 0.2);
  color: var(--admin-primary);
}

.badge-warning {
  background-color: rgba(255, 193, 7, 0.2);
  color: var(--admin-warning);
}

.badge-danger {
  background-color: rgba(220, 53, 69, 0.2);
  color: var(--admin-danger);
}

.badge-default {
  background-color: rgba(108, 117, 125, 0.2);
  color: var(--admin-text-secondary);
}

.admin-name {
  font-weight: 500;
  color: var(--admin-text-primary);
}

.target-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.target-user, .target-path {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.target-user {
  color: var(--admin-primary);
}

.target-path {
  color: var(--admin-text-secondary);
  font-family: monospace;
}

.no-target {
  color: var(--admin-text-muted);
}

.ip-address {
  font-family: monospace;
  font-size: 13px;
  color: var(--admin-text-secondary);
}

.details-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 12px;
  color: var(--admin-text-muted);
  text-transform: uppercase;
}

.detail-value {
  font-size: 14px;
  color: var(--admin-text-primary);
}

.detail-json {
  background-color: var(--admin-bg-tertiary);
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  margin: 0;
  color: var(--admin-text-primary);
}
</style>
