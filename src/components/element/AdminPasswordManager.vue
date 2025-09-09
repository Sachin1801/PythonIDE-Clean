<template>
  <div class="admin-password-manager">
    <!-- Header -->
    <div class="admin-header">
      <h1>Password Management</h1>
      <p class="admin-subtitle">Admin Editor Access Only</p>
    </div>

    <!-- Login Section (if not authenticated as admin_editor) -->
    <div v-if="!isAuthenticated" class="admin-login">
      <el-card shadow="always">
        <template #header>
          <span>Admin Authentication Required</span>
        </template>
        <el-form @submit.prevent="authenticateAdmin">
          <el-form-item label="Admin Username">
            <el-input 
              v-model="adminCredentials.username" 
              placeholder="admin_editor"
              :disabled="loading"
            />
          </el-form-item>
          <el-form-item label="Password">
            <el-input 
              v-model="adminCredentials.password" 
              type="password"
              placeholder="Enter admin password"
              :disabled="loading"
              @keyup.enter="authenticateAdmin"
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              type="primary" 
              @click="authenticateAdmin"
              :loading="loading"
              style="width: 100%"
            >
              Authenticate
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- Main Admin Panel (if authenticated) -->
    <div v-if="isAuthenticated" class="admin-panel">
      
      <!-- Action Buttons -->
      <div class="action-buttons">
        <el-button type="primary" @click="loadUsers" :loading="loading">
          <el-icon><Refresh /></el-icon>
          Refresh Users
        </el-button>
        
        <el-button type="warning" @click="showBulkPasswordReset" :loading="loading">
          <el-icon><Key /></el-icon>
          Bulk Password Reset
        </el-button>
        
        <el-button type="success" @click="generateRandomPassword">
          <el-icon><MagicStick /></el-icon>
          Generate Random Password
        </el-button>
      </div>

      <!-- Users Table -->
      <div class="users-section">
        <el-card shadow="hover">
          <template #header>
            <span>All Users ({{ users.length }})</span>
          </template>
          
          <el-table 
            :data="paginatedUsers" 
            stripe 
            style="width: 100%"
            :loading="loading"
            empty-text="No users found"
            max-height="500"
            :scrollbar-always-on="true"
          >
            <el-table-column prop="username" label="Username" width="120" />
            <el-table-column prop="full_name" label="Full Name" width="180" />
            <el-table-column prop="role" label="Role" width="100">
              <template #default="scope">
                <el-tag 
                  :type="scope.row.role === 'professor' ? 'danger' : 'primary'"
                  size="small"
                >
                  {{ scope.row.role }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="email" label="Email" width="200" />
            <el-table-column prop="last_login" label="Last Login" width="150">
              <template #default="scope">
                <span v-if="scope.row.last_login">
                  {{ formatDate(scope.row.last_login) }}
                </span>
                <span v-else class="never-logged-in">Never</span>
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="200">
              <template #default="scope">
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="resetUserPassword(scope.row)"
                  :loading="resettingUsers.has(scope.row.username)"
                >
                  Reset Password
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- Pagination -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :small="false"
              :total="users.length"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </div>

      <!-- Generated Password Display -->
      <div v-if="generatedPassword" class="generated-password">
        <el-alert
          title="Generated Password"
          type="success"
          :closable="false"
          show-icon
        >
          <template #default>
            <div class="password-display">
              <strong>{{ generatedPassword }}</strong>
              <el-button 
                size="small" 
                @click="copyToClipboard(generatedPassword)"
                style="margin-left: 10px"
              >
                Copy
              </el-button>
            </div>
          </template>
        </el-alert>
      </div>

      <!-- Reset Result Display -->
      <div v-if="lastResetResult" class="reset-result">
        <el-alert
          :title="`Password Reset: ${lastResetResult.username}`"
          :type="lastResetResult.success ? 'success' : 'error'"
          :closable="false"
          show-icon
        >
          <template #default>
            <div v-if="lastResetResult.success">
              <p><strong>User:</strong> {{ lastResetResult.username }} ({{ lastResetResult.full_name }})</p>
              <p><strong>New Password:</strong> 
                <code>{{ lastResetResult.password }}</code>
                <el-button 
                  size="small" 
                  @click="copyToClipboard(lastResetResult.password)"
                  style="margin-left: 10px"
                >
                  Copy
                </el-button>
              </p>
              <p class="success-note">✓ User will need to log in again with the new password</p>
            </div>
            <div v-else>
              <p>{{ lastResetResult.error }}</p>
            </div>
          </template>
        </el-alert>
      </div>

    </div>

    <!-- Bulk Password Reset Dialog -->
    <el-dialog
      v-model="bulkResetDialogVisible"
      title="Bulk Password Reset"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-alert
        title="Warning"
        type="warning"
        :closable="false"
        show-icon
      >
        <p>This will reset passwords for ALL users and export them to CSV.</p>
        <p>All users will be forced to log in again.</p>
      </el-alert>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="bulkResetDialogVisible = false">Cancel</el-button>
          <el-button 
            type="danger" 
            @click="confirmBulkPasswordReset"
            :loading="loading"
          >
            Confirm Reset All
          </el-button>
        </span>
      </template>
    </el-dialog>

  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Key, MagicStick } from '@element-plus/icons-vue'

export default {
  name: 'AdminPasswordManager',
  components: {
    Refresh,
    Key, 
    MagicStick
  },
  setup() {
    const isAuthenticated = ref(false)
    const loading = ref(false)
    const users = ref([])
    const generatedPassword = ref('')
    const lastResetResult = ref(null)
    const bulkResetDialogVisible = ref(false)
    const resettingUsers = ref(new Set())
    
    // Pagination for users table
    const currentPage = ref(1)
    const pageSize = ref(20) // Show 20 users per page
    
    const adminCredentials = reactive({
      username: 'admin_editor',
      password: ''
    })

    // Computed property for paginated users
    const paginatedUsers = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return users.value.slice(start, end)
    })

    // Authentication
    const authenticateAdmin = async () => {
      if (!adminCredentials.username || !adminCredentials.password) {
        ElMessage.error('Please enter both username and password')
        return
      }

      loading.value = true
      try {
        // First, login with the admin credentials
        const loginResponse = await fetch('/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: adminCredentials.username,
            password: adminCredentials.password
          })
        })

        const loginResult = await loginResponse.json()
        
        if (!loginResult.success) {
          throw new Error(loginResult.error || 'Login failed')
        }

        // Verify this is admin_editor
        if (adminCredentials.username !== 'admin_editor') {
          throw new Error('Only admin_editor can access this page')
        }

        // Test admin permissions by trying to get users list
        const response = await fetch('/api/admin/users?admin_username=' + encodeURIComponent(adminCredentials.username))
        const result = await response.json()
        
        if (result.success) {
          isAuthenticated.value = true
          users.value = result.users || []
          ElMessage.success(`Successfully authenticated as admin_editor (${result.total_count} users loaded)`)
        } else {
          throw new Error(result.error || 'Failed to load users')
        }
      } catch (error) {
        console.error('Admin authentication error:', error)
        ElMessage.error(error.message || 'Authentication failed')
        isAuthenticated.value = false
        users.value = []
      } finally {
        loading.value = false
      }
    }

    // Load users
    const loadUsers = async () => {
      if (!isAuthenticated.value) return

      loading.value = true
      try {
        const response = await fetch('/api/admin/users?admin_username=' + encodeURIComponent(adminCredentials.username))
        const result = await response.json()
        
        if (result.success) {
          users.value = result.users || []
          ElMessage.success(`Loaded ${users.value.length} users`)
        } else {
          throw new Error(result.error || 'Failed to load users')
        }
      } catch (error) {
        console.error('Load users error:', error)
        ElMessage.error(error.message || 'Failed to load users')
      } finally {
        loading.value = false
      }
    }

    // Generate random password
    const generateRandomPassword = async () => {
      try {
        const response = await fetch('/api/admin/password', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            action: 'generate_password',
            admin_username: adminCredentials.username,
            length: 12
          })
        })

        const result = await response.json()
        
        if (result.success) {
          generatedPassword.value = result.password
          ElMessage.success('Random password generated')
        } else {
          throw new Error(result.error || 'Failed to generate password')
        }
      } catch (error) {
        console.error('Generate password error:', error)
        ElMessage.error(error.message || 'Failed to generate password')
      }
    }

    // Reset individual user password
    const resetUserPassword = async (user) => {
      try {
        const result = await ElMessageBox.confirm(
          `Reset password for ${user.username} (${user.full_name})?`,
          'Confirm Password Reset',
          {
            type: 'warning',
            confirmButtonText: 'Reset Password',
            cancelButtonText: 'Cancel'
          }
        )
        
        if (result !== 'confirm') return

        resettingUsers.value.add(user.username)
        
        const response = await fetch('/api/admin/password', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            action: 'generate_random_password_for_user',
            admin_username: adminCredentials.username,
            target_username: user.username,
            length: 12
          })
        })

        const resetResult = await response.json()
        console.log('Password reset response:', resetResult) // Debug log
        
        if (resetResult.success) {
          lastResetResult.value = {
            success: true,
            username: user.username,
            full_name: resetResult.target_full_name || user.full_name,
            password: resetResult.new_password
          }
          ElMessage.success(`Password reset for ${user.username}: ${resetResult.new_password}`)
          
          // Clear generated password display
          generatedPassword.value = ''
        } else {
          lastResetResult.value = {
            success: false,
            username: user.username,
            error: resetResult.error
          }
          throw new Error(resetResult.error || 'Failed to reset password')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Reset password error:', error)
          ElMessage.error(error.message || 'Failed to reset password')
        }
      } finally {
        resettingUsers.value.delete(user.username)
      }
    }

    // Show bulk reset confirmation
    const showBulkPasswordReset = () => {
      bulkResetDialogVisible.value = true
    }

    // Confirm bulk password reset
    const confirmBulkPasswordReset = async () => {
      loading.value = true
      try {
        const response = await fetch('/api/admin/password', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            action: 'bulk_password_export',
            admin_username: adminCredentials.username
          })
        })

        const result = await response.json()
        
        if (result.success) {
          ElMessage.success(`Bulk password reset completed for ${result.users_updated} users`)
          ElMessage.info(`CSV exported: ${result.export_file}`)
          
          // Reload users to refresh last login times
          await loadUsers()
          
          // Clear other displays
          generatedPassword.value = ''
          lastResetResult.value = null
        } else {
          throw new Error(result.error || 'Bulk password reset failed')
        }
      } catch (error) {
        console.error('Bulk password reset error:', error)
        ElMessage.error(error.message || 'Bulk password reset failed')
      } finally {
        loading.value = false
        bulkResetDialogVisible.value = false
      }
    }

    // Copy to clipboard
    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text)
        ElMessage.success('Copied to clipboard')
      } catch (error) {
        console.error('Copy error:', error)
        ElMessage.error('Failed to copy to clipboard')
      }
    }

    // Format date
    const formatDate = (dateString) => {
      if (!dateString) return 'Never'
      const date = new Date(dateString)
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
    }

    // Pagination handlers
    const handleSizeChange = (newSize) => {
      pageSize.value = newSize
      currentPage.value = 1 // Reset to first page
    }

    const handleCurrentChange = (newPage) => {
      currentPage.value = newPage
    }

    // Load users on mount (if authenticated)
    onMounted(() => {
      // Check if already authenticated (in a real app, you'd check a token)
      // For now, user needs to authenticate each time
    })

    return {
      isAuthenticated,
      loading,
      users,
      paginatedUsers,
      currentPage,
      pageSize,
      generatedPassword,
      lastResetResult,
      bulkResetDialogVisible,
      resettingUsers,
      adminCredentials,
      authenticateAdmin,
      loadUsers,
      generateRandomPassword,
      resetUserPassword,
      showBulkPasswordReset,
      confirmBulkPasswordReset,
      copyToClipboard,
      formatDate,
      handleSizeChange,
      handleCurrentChange
    }
  }
}
</script>

<style scoped>
.admin-password-manager {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  overflow-y: auto;
}

.admin-header {
  text-align: center;
  margin-bottom: 30px;
}

.admin-header h1 {
  color: #409eff;
  margin-bottom: 5px;
}

.admin-subtitle {
  color: #909399;
  font-size: 14px;
}

.admin-login {
  max-width: 400px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.admin-login .el-card {
  position: relative;
  z-index: 2;
  pointer-events: auto;
}

.admin-login .el-form-item {
  pointer-events: auto;
}

.admin-login .el-input {
  pointer-events: auto;
}

.admin-login .el-button {
  pointer-events: auto;
  cursor: pointer;
}

.action-buttons {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.users-section {
  margin-bottom: 20px;
}

.users-section .el-card {
  overflow: visible;
}

.users-section .el-table {
  border-radius: 4px;
}

/* Ensure table scrollbar is always visible when needed */
.users-section .el-table__body-wrapper {
  overflow-y: auto !important;
}

/* Make sure table header stays visible during scroll */
.users-section .el-table__header-wrapper {
  position: sticky;
  top: 0;
  z-index: 10;
  background: white;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.generated-password {
  margin-bottom: 20px;
}

.password-display {
  display: flex;
  align-items: center;
  font-family: 'Courier New', monospace;
  font-size: 16px;
}

.reset-result {
  margin-bottom: 20px;
}

.reset-result code {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.success-note {
  color: #67c23a;
  font-weight: bold;
  margin-top: 10px;
}

.never-logged-in {
  color: #909399;
  font-style: italic;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Fix Element Plus modal visibility issues - only when admin panel is authenticated */
.admin-password-manager .admin-panel :deep(.el-message-box),
.admin-panel .el-message-box,
body .admin-panel :deep(.el-message-box) {
  background-color: #ffffff !important;
  background: #ffffff !important;
  border: 1px solid #dcdfe6 !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
  z-index: 3000 !important;
  opacity: 1 !important;
  visibility: visible !important;
  display: block !important;
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  min-width: 420px !important;
  max-width: 90vw !important;
}

/* Override global CSS variables specifically for admin modals */
.admin-password-manager .admin-panel :deep(.el-message-box) {
  --bg-primary: #ffffff !important;
  --border-color: #dcdfe6 !important;
}

/* Ultra-high specificity override to beat global styles */
.admin-password-manager.admin-password-manager .admin-panel :deep(.el-message-box.el-message-box.el-message-box) {
  background-color: #ffffff !important;
  background: #ffffff !important;
}

/* Force white background even when CSS variables are used */
.admin-password-manager .admin-panel :deep(.el-message-box) {
  background: white !important;
  background-color: white !important;
  background-image: none !important;
}

/* Additional fallback - override the CSS variable at the root level for admin area */
.admin-password-manager {
  --bg-primary: #ffffff;
  --border-color: #dcdfe6;
}

.admin-panel :deep(.el-message-box__header) {
  background-color: #ffffff !important;
  border-bottom: 1px solid #ebeef5 !important;
  padding: 15px 15px 10px !important;
}

.admin-panel :deep(.el-message-box__title) {
  color: #303133 !important;
  font-size: 16px !important;
  font-weight: 500 !important;
}

.admin-panel :deep(.el-message-box__content) {
  background-color: #ffffff !important;
  padding: 10px 15px !important;
  color: #606266 !important;
}

.admin-panel :deep(.el-message-box__btns) {
  background-color: #ffffff !important;
  padding: 5px 15px 15px !important;
  text-align: right !important;
}

.admin-panel :deep(.el-message-box__btns .el-button) {
  margin-left: 10px !important;
}

.admin-panel :deep(.el-message-box__btns .el-button--primary) {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: #ffffff !important;
}

.admin-panel :deep(.el-message-box__btns .el-button--primary:hover) {
  background-color: #66b1ff !important;
  border-color: #66b1ff !important;
}

/* Fix modal overlay - only when modal is active */
:deep(.el-overlay.is-message-box) {
  background-color: rgba(0, 0, 0, 0.5) !important;
  z-index: 2999 !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

/* Ensure modal wrapper is visible - only for message box */
:deep(.el-overlay-message-box) {
  z-index: 2999 !important;
  opacity: 1 !important;
  visibility: visible !important;
}

/* Fix warning icon color - only in admin panel */
.admin-panel :deep(.el-message-box-icon--warning) {
  color: #e6a23c !important;
}

/* Aggressive fix for transparency issues - only in admin panel */
.admin-panel :deep(.el-message-box),
.admin-panel :deep(.el-message-box *) {
  opacity: 1 !important;
  visibility: visible !important;
}

/* Global override - only for admin panel modals */
.admin-panel :deep(.el-message-box) {
  background: white !important;
  opacity: 1 !important;
}

/* Alternative approach - target by role - only in admin panel */
.admin-panel [role="dialog"] {
  background-color: white !important;
  opacity: 1 !important;
  visibility: visible !important;
}

/* Responsive design */
@media (max-width: 768px) {
  .admin-password-manager {
    padding: 10px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .action-buttons .el-button {
    width: 100%;
  }
  
  /* Make modal responsive on mobile */
  :deep(.el-message-box) {
    width: 90% !important;
    max-width: 420px !important;
  }
}
</style>