<template>
  <AdminLayout>
    <div class="dashboard">
      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon primary">
            <Users :size="28" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalUsers }}</div>
            <div class="stat-label">Total Users</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon success">
            <GraduationCap :size="28" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.students }}</div>
            <div class="stat-label">Students</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon info">
            <UserCog :size="28" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.professors }}</div>
            <div class="stat-label">Professors</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon warning">
            <Activity :size="28" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.activeSessions }}</div>
            <div class="stat-label">Active Sessions</div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="admin-card">
        <div class="admin-card-header">
          <h2 class="admin-card-title">Quick Actions</h2>
        </div>
        <div class="quick-actions">
          <router-link to="/users" class="action-btn">
            <span class="action-icon"><UserPlus :size="32" /></span>
            <span class="action-text">Create User</span>
          </router-link>

          <button class="action-btn" @click="showBulkImport = true">
            <span class="action-icon"><Upload :size="32" /></span>
            <span class="action-text">Bulk Import</span>
          </button>

          <router-link to="/files" class="action-btn">
            <span class="action-icon"><FolderOpen :size="32" /></span>
            <span class="action-text">Browse Files</span>
          </router-link>

          <router-link to="/grading" class="action-btn">
            <span class="action-icon"><ClipboardCheck :size="32" /></span>
            <span class="action-text">Grade Submissions</span>
          </router-link>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="admin-card">
        <div class="admin-card-header">
          <h2 class="admin-card-title">Recent Activity</h2>
          <router-link to="/audit" class="view-all-link">View All →</router-link>
        </div>
        <div v-if="recentActivity.length > 0" class="activity-list">
          <div
            v-for="activity in recentActivity"
            :key="activity.id"
            class="activity-item"
          >
            <span class="activity-icon">
              <component :is="getActivityIcon(activity.action_type)" :size="20" />
            </span>
            <div class="activity-content">
              <span class="activity-text">
                <strong>{{ activity.admin_username }}</strong>
                {{ formatActivityText(activity) }}
              </span>
              <span class="activity-time">{{ formatTime(activity.created_at) }}</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>No recent activity</p>
        </div>
      </div>

      <!-- System Status -->
      <div class="admin-card">
        <div class="admin-card-header">
          <h2 class="admin-card-title">System Status</h2>
        </div>
        <div class="system-status">
          <div class="status-item">
            <span class="status-label">Database</span>
            <span class="status-value success">● Connected</span>
          </div>
          <div class="status-item">
            <span class="status-label">File Storage</span>
            <span class="status-value success">● Online</span>
          </div>
          <div class="status-item">
            <span class="status-label">Memory Usage</span>
            <span class="status-value" :class="memoryStatusClass">
              {{ stats.memoryPercent }}%
            </span>
          </div>
          <div class="status-item">
            <span class="status-label">CPU Usage</span>
            <span class="status-value" :class="cpuStatusClass">
              {{ stats.cpuPercent }}%
            </span>
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
  Users,
  GraduationCap,
  UserCog,
  Activity,
  UserPlus,
  Upload,
  FolderOpen,
  ClipboardCheck,
  KeyRound,
  LogIn,
  LogOut,
  Pencil,
  Trash2,
  Eye,
  Download,
  FileText,
  ClipboardList
} from 'lucide-vue-next'

export default {
  name: 'AdminDashboard',
  components: {
    AdminLayout,
    Users,
    GraduationCap,
    UserCog,
    Activity,
    UserPlus,
    Upload,
    FolderOpen,
    ClipboardCheck,
    KeyRound,
    LogIn,
    LogOut,
    Pencil,
    Trash2,
    Eye,
    Download,
    FileText,
    ClipboardList
  },
  setup() {
    const store = useStore()
    const showBulkImport = ref(false)
    const loading = ref(false)

    const stats = ref({
      totalUsers: 0,
      students: 0,
      professors: 0,
      activeSessions: 0,
      memoryPercent: 0,
      cpuPercent: 0
    })

    const recentActivity = ref([])
    const token = computed(() => store.getters['auth/token'])

    const memoryStatusClass = computed(() => {
      if (stats.value.memoryPercent > 80) return 'danger'
      if (stats.value.memoryPercent > 60) return 'warning'
      return 'success'
    })

    const cpuStatusClass = computed(() => {
      if (stats.value.cpuPercent > 80) return 'danger'
      if (stats.value.cpuPercent > 60) return 'warning'
      return 'success'
    })

    const getActivityIcon = (actionType) => {
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

    const formatActivityText = (activity) => {
      const texts = {
        'admin_login': 'logged in',
        'admin_logout': 'logged out',
        'create_user': `created user ${activity.target_username || ''}`,
        'update_user': `updated user ${activity.target_username || ''}`,
        'delete_user': `deleted user ${activity.target_username || ''}`,
        'reset_password': `reset password for ${activity.target_username || ''}`,
        'bulk_import_users': 'imported users from CSV',
        'view_file': `viewed ${activity.target_path || 'a file'}`,
        'download_file': `downloaded ${activity.target_path || 'a file'}`,
        'edit_file': `edited ${activity.target_path || 'a file'}`,
        'delete_file': `deleted ${activity.target_path || 'a file'}`,
        'grade_submission': 'graded a submission'
      }
      return texts[activity.action_type] || activity.action_type
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date

      if (diff < 60000) return 'just now'
      if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
      return date.toLocaleDateString()
    }

    const fetchDashboardData = async () => {
      if (!token.value) return

      loading.value = true
      try {
        // Fetch dashboard stats
        const statsResponse = await analyticsApi.getDashboardStats(token.value)
        if (statsResponse.success && statsResponse.data) {
          stats.value = {
            totalUsers: statsResponse.data.totalUsers || 0,
            students: statsResponse.data.students || 0,
            professors: statsResponse.data.professors || 0,
            activeSessions: statsResponse.data.activeSessions || 0,
            memoryPercent: statsResponse.data.memoryPercent || 0,
            cpuPercent: statsResponse.data.cpuPercent || 0
          }
        }

        // Fetch recent activity
        const activityResponse = await analyticsApi.getRecentActivity(token.value, 5)
        if (activityResponse.success && activityResponse.data) {
          recentActivity.value = activityResponse.data
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        // Keep default values on error
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      fetchDashboardData()
    })

    return {
      stats,
      recentActivity,
      showBulkImport,
      loading,
      memoryStatusClass,
      cpuStatusClass,
      getActivityIcon,
      formatActivityText,
      formatTime
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background-color: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 28px;
}

.stat-icon.primary { background-color: rgba(0, 120, 212, 0.2); }
.stat-icon.success { background-color: rgba(40, 167, 69, 0.2); }
.stat-icon.warning { background-color: rgba(255, 193, 7, 0.2); }
.stat-icon.info { background-color: rgba(23, 162, 184, 0.2); }

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--admin-text-white);
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--admin-text-secondary);
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px;
  background-color: var(--admin-bg-tertiary);
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  color: var(--admin-text-primary);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background-color: var(--admin-bg-hover);
  border-color: var(--admin-primary);
}

.action-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.action-text {
  font-size: 14px;
  font-weight: 500;
}

.view-all-link {
  color: var(--admin-primary);
  text-decoration: none;
  font-size: 14px;
}

.view-all-link:hover {
  text-decoration: underline;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background-color: var(--admin-bg-tertiary);
  border-radius: 8px;
}

.activity-icon {
  font-size: 20px;
  margin-right: 12px;
}

.activity-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-text {
  font-size: 14px;
  color: var(--admin-text-primary);
}

.activity-time {
  font-size: 12px;
  color: var(--admin-text-muted);
}

.system-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: var(--admin-bg-tertiary);
  border-radius: 8px;
}

.status-label {
  font-size: 14px;
  color: var(--admin-text-secondary);
}

.status-value {
  font-size: 14px;
  font-weight: 500;
}

.status-value.success { color: var(--admin-success); }
.status-value.warning { color: var(--admin-warning); }
.status-value.danger { color: var(--admin-danger); }
</style>
