<template>
  <AdminLayout>
    <div class="users-page">
      <!-- Toolbar -->
      <div class="toolbar">
        <div class="toolbar-left">
          <div class="search-box">
            <span class="search-icon"><Search :size="18" /></span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search users..."
              @input="handleSearch"
            />
          </div>

          <el-select v-model="roleFilter" placeholder="All Roles" @change="handleFilterChange">
            <el-option label="All Roles" value="" />
            <el-option label="Students" value="student" />
            <el-option label="Professors" value="professor" />
          </el-select>

          <el-select v-model="statusFilter" placeholder="All Status" @change="handleFilterChange">
            <el-option label="All Status" value="" />
            <el-option label="Active" value="active" />
            <el-option label="Inactive" value="inactive" />
          </el-select>
        </div>

        <div class="toolbar-right">
          <el-button @click="downloadTemplate"><Download :size="16" /> Template</el-button>
          <el-button @click="showBulkImport = true"><Upload :size="16" /> Bulk Import</el-button>
          <el-button @click="exportUsers"><FileSpreadsheet :size="16" /> Export</el-button>
          <el-button type="primary" @click="showCreateUser = true"><UserPlus :size="16" /> Create User</el-button>
        </div>
      </div>

      <!-- Users Table -->
      <div class="admin-card">
        <el-table
          :data="users"
          v-loading="loading"
          stripe
          style="width: 100%"
          @sort-change="handleSortChange"
        >
          <el-table-column prop="username" label="Username" sortable="custom" width="150" />
          <el-table-column prop="full_name" label="Name" sortable="custom" min-width="150" />
          <el-table-column prop="email" label="Email" min-width="200" />
          <el-table-column prop="role" label="Role" sortable="custom" width="120">
            <template #default="scope">
              <span class="badge" :class="scope.row.role === 'professor' ? 'badge-info' : 'badge-success'">
                {{ scope.row.role }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="Status" width="100">
            <template #default="scope">
              <span class="badge" :class="scope.row.is_active ? 'badge-success' : 'badge-danger'">
                {{ scope.row.is_active ? 'Active' : 'Inactive' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="last_login" label="Last Login" sortable="custom" width="150">
            <template #default="scope">
              {{ formatDate(scope.row.last_login) }}
            </template>
          </el-table-column>
          <el-table-column label="Actions" width="180" fixed="right">
            <template #default="scope">
              <el-button-group>
                <el-button size="small" @click="editUser(scope.row)"><Pencil :size="14" /></el-button>
                <el-button size="small" @click="resetPasswordDialog(scope.row)"><KeyRound :size="14" /></el-button>
                <el-button size="small" type="danger" @click="confirmDeleteUser(scope.row)"><Trash2 :size="14" /></el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <!-- Create User Dialog -->
      <el-dialog v-model="showCreateUser" title="Create New User" width="500px">
        <el-form :model="newUser" label-position="top">
          <el-form-item label="Username" required>
            <el-input v-model="newUser.username" placeholder="Enter username" />
          </el-form-item>
          <el-form-item label="Password" required>
            <el-input v-model="newUser.password" type="password" placeholder="Enter password" show-password />
          </el-form-item>
          <el-form-item label="Full Name">
            <el-input v-model="newUser.full_name" placeholder="Enter full name" />
          </el-form-item>
          <el-form-item label="Email">
            <el-input v-model="newUser.email" placeholder="Enter email" />
          </el-form-item>
          <el-form-item label="Role">
            <el-select v-model="newUser.role" style="width: 100%">
              <el-option label="Student" value="student" />
              <el-option label="Professor" value="professor" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCreateUser = false">Cancel</el-button>
          <el-button type="primary" @click="createUser" :loading="creating">Create</el-button>
        </template>
      </el-dialog>

      <!-- Edit User Dialog -->
      <el-dialog v-model="showEditUser" title="Edit User" width="500px">
        <el-form v-if="editingUser" :model="editingUser" label-position="top">
          <el-form-item label="Username">
            <el-input :value="editingUser.username" disabled />
          </el-form-item>
          <el-form-item label="Full Name">
            <el-input v-model="editingUser.full_name" placeholder="Enter full name" />
          </el-form-item>
          <el-form-item label="Email">
            <el-input v-model="editingUser.email" placeholder="Enter email" />
          </el-form-item>
          <el-form-item label="Role">
            <el-select v-model="editingUser.role" style="width: 100%">
              <el-option label="Student" value="student" />
              <el-option label="Professor" value="professor" />
            </el-select>
          </el-form-item>
          <el-form-item label="Status">
            <el-switch v-model="editingUser.is_active" active-text="Active" inactive-text="Inactive" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showEditUser = false">Cancel</el-button>
          <el-button type="primary" @click="updateUser" :loading="updating">Save Changes</el-button>
        </template>
      </el-dialog>

      <!-- Reset Password Dialog -->
      <el-dialog v-model="showResetPassword" title="Reset Password" width="400px">
        <p>Reset password for <strong>{{ resetPasswordUser?.username }}</strong>?</p>
        <el-form-item label="New Password (leave blank for random)">
          <el-input v-model="newPassword" type="password" placeholder="Leave blank for random password" show-password />
        </el-form-item>
        <template #footer>
          <el-button @click="showResetPassword = false">Cancel</el-button>
          <el-button type="primary" @click="resetPassword" :loading="resetting">Reset Password</el-button>
        </template>
      </el-dialog>

      <!-- Password Result Dialog -->
      <el-dialog v-model="showPasswordResult" title="Password Reset Complete" width="400px">
        <el-alert
          title="New Password"
          type="success"
          :closable="false"
          show-icon
        >
          <p style="font-size: 18px; font-weight: bold; margin: 10px 0;">{{ generatedPassword }}</p>
          <p style="color: #999;">Please share this password with the user securely.</p>
        </el-alert>
        <template #footer>
          <el-button @click="copyPassword"><Copy :size="14" /> Copy</el-button>
          <el-button type="primary" @click="showPasswordResult = false">Done</el-button>
        </template>
      </el-dialog>

      <!-- Bulk Import Dialog -->
      <el-dialog v-model="showBulkImport" title="Bulk Import Users" width="500px">
        <div class="import-info">
          <p>Upload a CSV file with the following columns:</p>
          <ul>
            <li><strong>username</strong> (required)</li>
            <li><strong>password</strong> (required)</li>
            <li>full_name (optional)</li>
            <li>email (optional)</li>
            <li>role (optional, defaults to "student")</li>
          </ul>
        </div>
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          accept=".csv"
          :on-change="handleFileChange"
        >
          <template #trigger>
            <el-button>Select CSV File</el-button>
          </template>
        </el-upload>
        <div v-if="importFile" class="selected-file">
          Selected: {{ importFile.name }}
        </div>
        <template #footer>
          <el-button @click="showBulkImport = false">Cancel</el-button>
          <el-button type="primary" @click="bulkImport" :loading="importing" :disabled="!importFile">
            Import Users
          </el-button>
        </template>
      </el-dialog>
    </div>
  </AdminLayout>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import AdminLayout from '../components/layout/AdminLayout.vue'
import usersApi from '../api/users'
import {
  Search,
  Download,
  Upload,
  FileSpreadsheet,
  UserPlus,
  Pencil,
  KeyRound,
  Trash2,
  Copy
} from 'lucide-vue-next'

export default {
  name: 'UsersPage',
  components: {
    AdminLayout,
    Search,
    Download,
    Upload,
    FileSpreadsheet,
    UserPlus,
    Pencil,
    KeyRound,
    Trash2,
    Copy
  },
  setup() {
    const store = useStore()

    // State
    const searchQuery = ref('')
    const roleFilter = ref('')
    const statusFilter = ref('')
    const currentPage = ref(1)
    const pageSize = ref(20)
    const sortBy = ref('username')
    const sortOrder = ref('asc')

    // Dialogs
    const showCreateUser = ref(false)
    const showEditUser = ref(false)
    const showResetPassword = ref(false)
    const showPasswordResult = ref(false)
    const showBulkImport = ref(false)

    // Form data
    const newUser = ref({
      username: '',
      password: '',
      full_name: '',
      email: '',
      role: 'student'
    })
    const editingUser = ref(null)
    const resetPasswordUser = ref(null)
    const newPassword = ref('')
    const generatedPassword = ref('')
    const importFile = ref(null)

    // Loading states
    const creating = ref(false)
    const updating = ref(false)
    const resetting = ref(false)
    const importing = ref(false)

    // Computed
    const users = computed(() => store.getters['users/users'])
    const total = computed(() => store.getters['users/total'])
    const loading = computed(() => store.getters['users/isLoading'])
    const token = computed(() => store.getters['auth/token'])

    // Methods
    const fetchUsers = () => {
      store.dispatch('users/fetchUsers')
    }

    const handleSearch = () => {
      store.dispatch('users/setFilters', { search: searchQuery.value })
    }

    const handleFilterChange = () => {
      store.dispatch('users/setFilters', {
        role: roleFilter.value,
        status: statusFilter.value
      })
    }

    const handleSortChange = ({ prop, order }) => {
      if (prop && order) {
        store.dispatch('users/setSort', {
          sortBy: prop,
          sortOrder: order === 'ascending' ? 'asc' : 'desc'
        })
      }
    }

    const handlePageChange = (page) => {
      store.dispatch('users/setPage', page)
    }

    const handleSizeChange = (size) => {
      store.commit('users/SET_LIMIT', size)
      store.commit('users/SET_PAGE', 1)
      fetchUsers()
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return 'Never'
      const date = new Date(dateStr)
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    const createUser = async () => {
      if (!newUser.value.username || !newUser.value.password) {
        window.ElMessage.warning('Username and password are required')
        return
      }

      creating.value = true
      const result = await store.dispatch('users/createUser', newUser.value)
      creating.value = false

      if (result.success) {
        window.ElMessage.success('User created successfully')
        showCreateUser.value = false
        newUser.value = { username: '', password: '', full_name: '', email: '', role: 'student' }
      } else {
        window.ElMessage.error(result.error || 'Failed to create user')
      }
    }

    const editUser = (user) => {
      editingUser.value = { ...user }
      showEditUser.value = true
    }

    const updateUser = async () => {
      if (!editingUser.value) return

      updating.value = true
      const result = await store.dispatch('users/updateUser', {
        userId: editingUser.value.id,
        userData: {
          full_name: editingUser.value.full_name,
          email: editingUser.value.email,
          role: editingUser.value.role,
          is_active: editingUser.value.is_active
        }
      })
      updating.value = false

      if (result.success) {
        window.ElMessage.success('User updated successfully')
        showEditUser.value = false
        fetchUsers()
      } else {
        window.ElMessage.error(result.error || 'Failed to update user')
      }
    }

    const resetPasswordDialog = (user) => {
      resetPasswordUser.value = user
      newPassword.value = ''
      showResetPassword.value = true
    }

    const resetPassword = async () => {
      if (!resetPasswordUser.value) return

      resetting.value = true
      const result = await store.dispatch('users/resetPassword', {
        userId: resetPasswordUser.value.id,
        newPassword: newPassword.value || null
      })
      resetting.value = false

      if (result.success) {
        generatedPassword.value = result.newPassword
        showResetPassword.value = false
        showPasswordResult.value = true
      } else {
        window.ElMessage.error(result.error || 'Failed to reset password')
      }
    }

    const copyPassword = () => {
      navigator.clipboard.writeText(generatedPassword.value)
      window.ElMessage.success('Password copied to clipboard')
    }

    const confirmDeleteUser = (user) => {
      window.ElMessageBox.confirm(
        `Are you sure you want to delete user "${user.username}"? This action cannot be undone.`,
        'Confirm Delete',
        {
          confirmButtonText: 'Delete',
          cancelButtonText: 'Cancel',
          type: 'warning'
        }
      ).then(async () => {
        const result = await store.dispatch('users/deleteUser', user.id)
        if (result.success) {
          window.ElMessage.success('User deleted successfully')
        } else {
          window.ElMessage.error(result.error || 'Failed to delete user')
        }
      }).catch(() => {})
    }

    const handleFileChange = (file) => {
      importFile.value = file.raw
    }

    const bulkImport = async () => {
      if (!importFile.value) return

      importing.value = true
      const result = await store.dispatch('users/bulkImport', importFile.value)
      importing.value = false

      if (result.success) {
        window.ElMessage.success(`Imported ${result.created} users. ${result.failed} failed.`)
        showBulkImport.value = false
        importFile.value = null
        if (result.errors?.length > 0) {
          console.warn('Import errors:', result.errors)
        }
      } else {
        window.ElMessage.error(result.error || 'Import failed')
      }
    }

    const downloadTemplate = async () => {
      try {
        const blob = await usersApi.downloadTemplate(token.value)
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'user_import_template.csv'
        a.click()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        window.ElMessage.error('Failed to download template')
      }
    }

    const exportUsers = async () => {
      try {
        const blob = await usersApi.exportUsers(token.value, {
          search: searchQuery.value,
          role: roleFilter.value,
          status: statusFilter.value
        })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `users_export_${new Date().toISOString().split('T')[0]}.csv`
        a.click()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        window.ElMessage.error('Failed to export users')
      }
    }

    // Lifecycle
    onMounted(() => {
      fetchUsers()
    })

    // Watch for page changes
    watch(currentPage, (newPage) => {
      handlePageChange(newPage)
    })

    return {
      // State
      searchQuery,
      roleFilter,
      statusFilter,
      currentPage,
      pageSize,
      users,
      total,
      loading,

      // Dialogs
      showCreateUser,
      showEditUser,
      showResetPassword,
      showPasswordResult,
      showBulkImport,

      // Form data
      newUser,
      editingUser,
      resetPasswordUser,
      newPassword,
      generatedPassword,
      importFile,

      // Loading states
      creating,
      updating,
      resetting,
      importing,

      // Methods
      handleSearch,
      handleFilterChange,
      handleSortChange,
      handlePageChange,
      handleSizeChange,
      formatDate,
      createUser,
      editUser,
      updateUser,
      resetPasswordDialog,
      resetPassword,
      copyPassword,
      confirmDeleteUser,
      handleFileChange,
      bulkImport,
      downloadTemplate,
      exportUsers
    }
  }
}
</script>

<style scoped>
.users-page {
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
  min-width: 250px;
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

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: capitalize;
}

.badge-success {
  background-color: rgba(40, 167, 69, 0.2);
  color: var(--admin-success);
}

.badge-info {
  background-color: rgba(0, 120, 212, 0.2);
  color: var(--admin-primary);
}

.badge-danger {
  background-color: rgba(220, 53, 69, 0.2);
  color: var(--admin-danger);
}

.import-info {
  margin-bottom: 20px;
  padding: 16px;
  background-color: var(--admin-bg-tertiary);
  border-radius: 8px;
}

.import-info p {
  margin: 0 0 8px 0;
  color: var(--admin-text-primary);
}

.import-info ul {
  margin: 0;
  padding-left: 20px;
  color: var(--admin-text-secondary);
}

.selected-file {
  margin-top: 12px;
  padding: 8px 12px;
  background-color: var(--admin-bg-tertiary);
  border-radius: 4px;
  font-size: 14px;
  color: var(--admin-text-primary);
}
</style>
