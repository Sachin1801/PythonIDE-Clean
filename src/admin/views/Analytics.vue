<template>
  <AdminLayout>
    <div class="analytics-page">
      <!-- Time Range Selector -->
      <div class="toolbar">
        <h2 class="page-title"><BarChart3 :size="24" /> Analytics</h2>
        <div class="toolbar-actions">
          <el-select v-model="selectedDays" @change="fetchAllData">
            <el-option :value="7" label="Last 7 days" />
            <el-option :value="14" label="Last 14 days" />
            <el-option :value="30" label="Last 30 days" />
            <el-option :value="60" label="Last 60 days" />
            <el-option :value="90" label="Last 90 days" />
          </el-select>
          <el-button @click="fetchAllData"><RefreshCw :size="16" /> Refresh</el-button>
        </div>
      </div>

      <!-- Summary Cards -->
      <div class="summary-grid" v-loading="loadingSummary">
        <div class="summary-card">
          <div class="summary-icon login"><LogIn :size="24" /></div>
          <div class="summary-content">
            <div class="summary-value">{{ summary.logins.total }}</div>
            <div class="summary-label">Total Logins</div>
            <div class="summary-sub">{{ summary.logins.unique_users }} unique users</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-icon success"><CheckCircle :size="24" /></div>
          <div class="summary-content">
            <div class="summary-value">{{ loginSuccessRate }}%</div>
            <div class="summary-label">Login Success Rate</div>
            <div class="summary-sub">{{ summary.logins.successful }} successful</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-icon exec"><Play :size="24" /></div>
          <div class="summary-content">
            <div class="summary-value">{{ summary.executions.total }}</div>
            <div class="summary-label">Code Executions</div>
            <div class="summary-sub">{{ summary.executions.active_coders }} active coders</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-icon time"><Clock :size="24" /></div>
          <div class="summary-content">
            <div class="summary-value">{{ summary.executions.avg_duration }}ms</div>
            <div class="summary-label">Avg Execution Time</div>
            <div class="summary-sub">{{ execSuccessRate }}% success rate</div>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="charts-row">
        <!-- Login Trends Chart -->
        <div class="admin-card chart-card">
          <div class="admin-card-header">
            <h3 class="admin-card-title"><LogIn :size="18" /> Login Activity</h3>
          </div>
          <div class="chart-container" v-loading="loadingLoginTrends">
            <div v-if="loginTrends.length > 0" class="bar-chart">
              <div
                v-for="(item, index) in loginTrends"
                :key="index"
                class="bar-group"
              >
                <div class="bar-wrapper">
                  <div
                    class="bar success"
                    :style="{ height: getBarHeight(item.successful, maxLoginValue) + '%' }"
                    :title="`${item.successful} successful`"
                  ></div>
                  <div
                    class="bar failed"
                    :style="{ height: getBarHeight(item.failed, maxLoginValue) + '%' }"
                    :title="`${item.failed} failed`"
                  ></div>
                </div>
                <div class="bar-label">{{ formatDateShort(item.date) }}</div>
              </div>
            </div>
            <div v-else class="empty-chart">
              <TrendingUp :size="48" />
              <p>No login data for this period</p>
            </div>
          </div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot success"></span> Successful</span>
            <span class="legend-item"><span class="legend-dot failed"></span> Failed</span>
          </div>
        </div>

        <!-- Execution Trends Chart -->
        <div class="admin-card chart-card">
          <div class="admin-card-header">
            <h3 class="admin-card-title"><Play :size="18" /> Code Executions</h3>
          </div>
          <div class="chart-container" v-loading="loadingExecTrends">
            <div v-if="execTrends.length > 0" class="bar-chart">
              <div
                v-for="(item, index) in execTrends"
                :key="index"
                class="bar-group"
              >
                <div class="bar-wrapper">
                  <div
                    class="bar success"
                    :style="{ height: getBarHeight(item.successful, maxExecValue) + '%' }"
                    :title="`${item.successful} successful`"
                  ></div>
                  <div
                    class="bar failed"
                    :style="{ height: getBarHeight(item.failed, maxExecValue) + '%' }"
                    :title="`${item.failed} errors`"
                  ></div>
                </div>
                <div class="bar-label">{{ formatDateShort(item.date) }}</div>
              </div>
            </div>
            <div v-else class="empty-chart">
              <TrendingUp :size="48" />
              <p>No execution data for this period</p>
            </div>
          </div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot success"></span> Success (exit 0)</span>
            <span class="legend-item"><span class="legend-dot failed"></span> Errors</span>
          </div>
        </div>
      </div>

      <!-- Top Users -->
      <div class="admin-card">
        <div class="admin-card-header">
          <h3 class="admin-card-title"><Trophy :size="18" /> Most Active Students</h3>
          <el-radio-group v-model="topUsersMetric" size="small" @change="fetchTopUsers">
            <el-radio-button value="logins">By Logins</el-radio-button>
            <el-radio-button value="executions">By Executions</el-radio-button>
          </el-radio-group>
        </div>
        <div v-loading="loadingTopUsers">
          <el-table :data="topUsers" stripe style="width: 100%">
            <el-table-column type="index" label="#" width="60" />
            <el-table-column prop="username" label="Username" width="150" />
            <el-table-column prop="full_name" label="Name" min-width="150" />
            <el-table-column prop="count" label="Total" width="100">
              <template #default="scope">
                <span class="count-badge">{{ scope.row.count }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="successful" label="Successful" width="100">
              <template #default="scope">
                <span class="success-count">{{ scope.row.successful }}</span>
              </template>
            </el-table-column>
            <el-table-column label="Success Rate" width="120">
              <template #default="scope">
                <el-progress
                  :percentage="getSuccessRate(scope.row)"
                  :stroke-width="8"
                  :color="getProgressColor(getSuccessRate(scope.row))"
                />
              </template>
            </el-table-column>
            <el-table-column prop="last_activity" label="Last Active" width="150">
              <template #default="scope">
                {{ formatDate(scope.row.last_activity) }}
              </template>
            </el-table-column>
          </el-table>

          <div v-if="topUsers.length === 0" class="empty-state">
            <Users :size="48" />
            <p>No activity data for this period</p>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import AdminLayout from '../components/layout/AdminLayout.vue'
import analyticsApi from '../api/analytics'
import {
  BarChart3,
  RefreshCw,
  LogIn,
  CheckCircle,
  Play,
  Clock,
  TrendingUp,
  Trophy,
  Users
} from 'lucide-vue-next'

export default {
  name: 'AnalyticsPage',
  components: {
    AdminLayout,
    BarChart3,
    RefreshCw,
    LogIn,
    CheckCircle,
    Play,
    Clock,
    TrendingUp,
    Trophy,
    Users
  },
  setup() {
    const store = useStore()

    // State
    const selectedDays = ref(30)
    const summary = ref({
      logins: { total: 0, successful: 0, unique_users: 0 },
      executions: { total: 0, successful: 0, active_coders: 0, avg_duration: 0 }
    })
    const loginTrends = ref([])
    const execTrends = ref([])
    const topUsers = ref([])
    const topUsersMetric = ref('logins')

    // Loading states
    const loadingSummary = ref(false)
    const loadingLoginTrends = ref(false)
    const loadingExecTrends = ref(false)
    const loadingTopUsers = ref(false)

    // Computed
    const token = computed(() => store.getters['auth/token'])

    const loginSuccessRate = computed(() => {
      if (summary.value.logins.total === 0) return 0
      return Math.round((summary.value.logins.successful / summary.value.logins.total) * 100)
    })

    const execSuccessRate = computed(() => {
      if (summary.value.executions.total === 0) return 0
      return Math.round((summary.value.executions.successful / summary.value.executions.total) * 100)
    })

    const maxLoginValue = computed(() => {
      if (loginTrends.value.length === 0) return 1
      return Math.max(...loginTrends.value.map(d => d.total)) || 1
    })

    const maxExecValue = computed(() => {
      if (execTrends.value.length === 0) return 1
      return Math.max(...execTrends.value.map(d => d.total)) || 1
    })

    // Methods
    const fetchSummary = async () => {
      if (!token.value) return
      loadingSummary.value = true
      try {
        const response = await analyticsApi.getSummary(token.value, selectedDays.value)
        if (response.success) {
          summary.value = response.data
        }
      } catch (error) {
        console.error('Failed to fetch summary:', error)
      } finally {
        loadingSummary.value = false
      }
    }

    const fetchLoginTrends = async () => {
      if (!token.value) return
      loadingLoginTrends.value = true
      try {
        const response = await analyticsApi.getLoginTrends(token.value, selectedDays.value)
        if (response.success) {
          loginTrends.value = response.data
        }
      } catch (error) {
        console.error('Failed to fetch login trends:', error)
      } finally {
        loadingLoginTrends.value = false
      }
    }

    const fetchExecTrends = async () => {
      if (!token.value) return
      loadingExecTrends.value = true
      try {
        const response = await analyticsApi.getExecutionTrends(token.value, selectedDays.value)
        if (response.success) {
          execTrends.value = response.data
        }
      } catch (error) {
        console.error('Failed to fetch execution trends:', error)
      } finally {
        loadingExecTrends.value = false
      }
    }

    const fetchTopUsers = async () => {
      if (!token.value) return
      loadingTopUsers.value = true
      try {
        const response = await analyticsApi.getTopUsers(
          token.value,
          topUsersMetric.value,
          10,
          selectedDays.value
        )
        if (response.success) {
          topUsers.value = response.data
        }
      } catch (error) {
        console.error('Failed to fetch top users:', error)
      } finally {
        loadingTopUsers.value = false
      }
    }

    const fetchAllData = () => {
      fetchSummary()
      fetchLoginTrends()
      fetchExecTrends()
      fetchTopUsers()
    }

    const getBarHeight = (value, max) => {
      if (max === 0) return 0
      return Math.max((value / max) * 100, 2)
    }

    const formatDateShort = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return `${date.getMonth() + 1}/${date.getDate()}`
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '—'
      const date = new Date(dateStr)
      return date.toLocaleDateString()
    }

    const getSuccessRate = (row) => {
      if (row.count === 0) return 0
      return Math.round((row.successful / row.count) * 100)
    }

    const getProgressColor = (percentage) => {
      if (percentage >= 80) return '#28a745'
      if (percentage >= 50) return '#ffc107'
      return '#dc3545'
    }

    // Lifecycle
    onMounted(() => {
      fetchAllData()
    })

    return {
      // State
      selectedDays,
      summary,
      loginTrends,
      execTrends,
      topUsers,
      topUsersMetric,

      // Loading
      loadingSummary,
      loadingLoginTrends,
      loadingExecTrends,
      loadingTopUsers,

      // Computed
      loginSuccessRate,
      execSuccessRate,
      maxLoginValue,
      maxExecValue,

      // Methods
      fetchAllData,
      fetchTopUsers,
      getBarHeight,
      formatDateShort,
      formatDate,
      getSuccessRate,
      getProgressColor
    }
  }
}
</script>

<style scoped>
.analytics-page {
  max-width: 1400px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 20px;
  color: var(--admin-text-white);
}

.toolbar-actions {
  display: flex;
  gap: 12px;
}

/* Summary Cards */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  background-color: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-icon.login { background-color: rgba(0, 120, 212, 0.2); color: var(--admin-primary); }
.summary-icon.success { background-color: rgba(40, 167, 69, 0.2); color: var(--admin-success); }
.summary-icon.exec { background-color: rgba(255, 193, 7, 0.2); color: var(--admin-warning); }
.summary-icon.time { background-color: rgba(23, 162, 184, 0.2); color: #17a2b8; }

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--admin-text-white);
  line-height: 1;
}

.summary-label {
  font-size: 13px;
  color: var(--admin-text-secondary);
  margin-top: 4px;
}

.summary-sub {
  font-size: 11px;
  color: var(--admin-text-muted);
  margin-top: 2px;
}

/* Charts */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.chart-card {
  min-height: 300px;
}

.chart-container {
  height: 200px;
  padding: 16px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 100%;
  gap: 4px;
}

.bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 40px;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  height: 150px;
  justify-content: flex-end;
}

.bar {
  width: 100%;
  min-height: 2px;
  border-radius: 2px 2px 0 0;
  transition: height 0.3s ease;
}

.bar.success {
  background-color: var(--admin-success);
}

.bar.failed {
  background-color: var(--admin-danger);
  margin-top: 2px;
}

.bar-label {
  font-size: 10px;
  color: var(--admin-text-muted);
  margin-top: 8px;
  white-space: nowrap;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 12px;
  border-top: 1px solid var(--admin-border-color);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--admin-text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.legend-dot.success { background-color: var(--admin-success); }
.legend-dot.failed { background-color: var(--admin-danger); }

.empty-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--admin-text-muted);
  gap: 12px;
}

/* Top Users */
.count-badge {
  background-color: var(--admin-primary);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}

.success-count {
  color: var(--admin-success);
  font-weight: 500;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--admin-text-muted);
  gap: 12px;
}

/* Responsive */
@media (max-width: 1200px) {
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .toolbar {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>
