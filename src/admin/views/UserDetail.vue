<template>
  <AdminLayout>
    <div class="user-detail-page">
      <div class="page-header">
        <router-link to="/users" class="back-link">← Back to Users</router-link>
        <h2>User Details</h2>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading user details...</p>
      </div>

      <div v-else-if="user" class="user-content">
        <div class="admin-card">
          <div class="admin-card-header">
            <h3 class="admin-card-title">Profile Information</h3>
            <el-button type="primary" @click="editUser">Edit Profile</el-button>
          </div>

          <div class="profile-grid">
            <div class="profile-item">
              <label>Username</label>
              <span>{{ user.username }}</span>
            </div>
            <div class="profile-item">
              <label>Full Name</label>
              <span>{{ user.full_name || 'Not set' }}</span>
            </div>
            <div class="profile-item">
              <label>Email</label>
              <span>{{ user.email || 'Not set' }}</span>
            </div>
            <div class="profile-item">
              <label>Role</label>
              <span class="badge" :class="user.role === 'professor' ? 'badge-info' : 'badge-success'">
                {{ user.role }}
              </span>
            </div>
            <div class="profile-item">
              <label>Status</label>
              <span class="badge" :class="user.is_active ? 'badge-success' : 'badge-danger'">
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <div class="profile-item">
              <label>Last Login</label>
              <span>{{ formatDate(user.last_login) }}</span>
            </div>
            <div class="profile-item">
              <label>Created At</label>
              <span>{{ formatDate(user.created_at) }}</span>
            </div>
          </div>
        </div>

        <div class="admin-card">
          <div class="admin-card-header">
            <h3 class="admin-card-title">Actions</h3>
          </div>
          <div class="actions-grid">
            <el-button @click="resetPassword">🔑 Reset Password</el-button>
            <el-button @click="viewFiles">📁 View Files</el-button>
            <el-button @click="viewActivity">📋 View Activity</el-button>
            <el-button type="danger" @click="deleteUser">🗑️ Delete User</el-button>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <p>User not found</p>
      </div>
    </div>
  </AdminLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '../components/layout/AdminLayout.vue'

export default {
  name: 'UserDetailPage',
  components: {
    AdminLayout
  },
  setup() {
    const store = useStore()
    const route = useRoute()
    const router = useRouter()

    const user = computed(() => store.getters['users/currentUser'])
    const loading = computed(() => store.getters['users/isLoading'])

    const formatDate = (dateStr) => {
      if (!dateStr) return 'Never'
      return new Date(dateStr).toLocaleString()
    }

    const editUser = () => {
      // TODO: Implement edit dialog
      window.ElMessage.info('Edit feature coming soon')
    }

    const resetPassword = () => {
      // TODO: Implement reset password
      window.ElMessage.info('Reset password feature coming soon')
    }

    const viewFiles = () => {
      router.push(`/files?user=${user.value?.username}`)
    }

    const viewActivity = () => {
      router.push(`/audit?user=${user.value?.id}`)
    }

    const deleteUser = () => {
      // TODO: Implement delete with confirmation
      window.ElMessage.info('Delete feature coming soon')
    }

    onMounted(() => {
      const userId = route.params.id
      if (userId) {
        store.dispatch('users/fetchUser', userId)
      }
    })

    return {
      user,
      loading,
      formatDate,
      editUser,
      resetPassword,
      viewFiles,
      viewActivity,
      deleteUser
    }
  }
}
</script>

<style scoped>
.user-detail-page {
  max-width: 800px;
}

.page-header {
  margin-bottom: 24px;
}

.back-link {
  color: var(--admin-text-secondary);
  text-decoration: none;
  font-size: 14px;
}

.back-link:hover {
  color: var(--admin-primary);
}

.page-header h2 {
  margin: 8px 0 0 0;
  color: var(--admin-text-white);
}

.loading-state {
  text-align: center;
  padding: 48px;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.profile-item {
  display: flex;
  flex-direction: column;
}

.profile-item label {
  font-size: 12px;
  color: var(--admin-text-muted);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.profile-item span {
  font-size: 16px;
  color: var(--admin-text-primary);
}

.actions-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: capitalize;
}

.badge-success { background-color: rgba(40, 167, 69, 0.2); color: var(--admin-success); }
.badge-info { background-color: rgba(0, 120, 212, 0.2); color: var(--admin-primary); }
.badge-danger { background-color: rgba(220, 53, 69, 0.2); color: var(--admin-danger); }
</style>
