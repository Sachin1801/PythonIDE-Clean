<template>
  <el-dialog
    v-model="visible"
    :title="currentUser ? `${currentUser.full_name || currentUser.username}` : 'User Profile'"
    width="450px"
    :before-close="handleClose"
    :close-on-click-modal="false"
    :close-on-press-escape="true"
    class="user-profile-modal"
  >
    <!-- Tab Navigation -->
    <div class="tab-navigation">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
      >
        <component :is="tab.icon" :size="16" />
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Profile Tab -->
      <div v-if="activeTab === 'profile'" class="profile-section">
        <div class="user-info">
          <div class="info-row">
            <label>Username:</label>
            <span>{{ currentUser?.username }}</span>
          </div>
          <div class="info-row">
            <label>Full Name:</label>
            <span>{{ currentUser?.full_name || 'Not set' }}</span>
          </div>
          <div class="info-row">
            <label>Role:</label>
            <span class="role-badge" :class="currentUser?.role">
              {{ currentUser?.role === 'professor' ? 'Professor' : 'Student' }}
            </span>
          </div>
          <div class="info-row">
            <label>Session:</label>
            <span class="session-id">{{ sessionId?.substring(0, 20) }}...</span>
          </div>
        </div>
      </div>

      <!-- Change Password Tab -->
      <div v-if="activeTab === 'change-password'" class="password-section">
        <el-form 
          ref="changePasswordForm" 
          :model="passwordForm" 
          :rules="passwordRules"
          label-position="top"
        >
          <el-form-item label="Current Password" prop="currentPassword">
            <el-input 
              v-model="passwordForm.currentPassword" 
              type="password" 
              placeholder="Enter your current password"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="New Password" prop="newPassword">
            <el-input 
              v-model="passwordForm.newPassword" 
              type="password" 
              placeholder="Enter new password (min 6 characters)"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="Confirm New Password" prop="confirmPassword">
            <el-input 
              v-model="passwordForm.confirmPassword" 
              type="password" 
              placeholder="Confirm new password"
              show-password
            />
          </el-form-item>

          <div class="form-actions">
            <el-button 
              type="primary" 
              @click="changePassword"
              :loading="loading"
            >
              Change Password
            </el-button>
            <el-button @click="resetPasswordForm">Reset</el-button>
          </div>
        </el-form>
      </div>

      <!-- Forgot Password Tab -->
      <div v-if="activeTab === 'forgot-password'" class="forgot-section">
        <div class="forgot-info">
          <p>To reset your password, you need to verify your current password first.</p>
          <p>If you don't remember your current password, please contact the administrator.</p>
        </div>

        <el-form 
          ref="forgotPasswordForm" 
          :model="forgotForm" 
          :rules="forgotRules"
          label-position="top"
        >
          <el-form-item label="Current Password" prop="currentPassword">
            <el-input 
              v-model="forgotForm.currentPassword" 
              type="password" 
              placeholder="Enter your current password to verify"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="New Password" prop="newPassword">
            <el-input 
              v-model="forgotForm.newPassword" 
              type="password" 
              placeholder="Enter new password (min 6 characters)"
              show-password
              :disabled="!passwordVerified"
            />
          </el-form-item>
          
          <el-form-item label="Confirm New Password" prop="confirmPassword">
            <el-input 
              v-model="forgotForm.confirmPassword" 
              type="password" 
              placeholder="Confirm new password"
              show-password
              :disabled="!passwordVerified"
            />
          </el-form-item>

          <div class="form-actions">
            <el-button 
              v-if="!passwordVerified"
              type="primary" 
              @click="verifyCurrentPassword"
              :loading="loading"
            >
              Verify Password
            </el-button>
            <el-button 
              v-else
              type="success" 
              @click="resetPasswordWithVerification"
              :loading="loading"
            >
              Reset Password
            </el-button>
            <el-button @click="resetForgotForm">Clear</el-button>
          </div>
        </el-form>

        <div class="admin-contact">
          <el-divider>OR</el-divider>
          <div class="contact-section">
            <h4>Contact Administrator</h4>
            <p>If you cannot remember your current password, please contact the admin:</p>
            <div class="admin-info">
              <div class="contact-method">
                <Mail :size="16" />
                <span class="admin-email">sa9082@nyu.edu</span>
              </div>
              <div class="contact-method">
                <MessageSquare :size="16" />
                <span>Include your username: <strong>{{ currentUser?.username }}</strong></span>
              </div>
            </div>
            <p class="contact-note">
              Please send an email from your Gmail account with your username and request for password reset.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Actions -->
    <template #footer>
      <div class="dialog-footer">
        <el-button 
          v-if="activeTab === 'profile'"
          type="danger" 
          @click="handleLogout"
        >
          <LogOut :size="16" />
          Logout
        </el-button>
        <el-button @click="handleClose">Close</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { User, Lock, HelpCircle, LogOut, Mail, MessageSquare } from 'lucide-vue-next';
import { ElMessage, ElMessageBox } from 'element-plus';

export default {
  name: 'UserProfileModal',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    currentUser: {
      type: Object,
      default: null
    }
  },
  emits: ['update:modelValue', 'logout', 'password-changed'],
  components: {
    User,
    Lock,
    HelpCircle,
    LogOut,
    Mail,
    MessageSquare
  },
  data() {
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('Please confirm your password'));
      } else if (value !== this.passwordForm.newPassword && value !== this.forgotForm.newPassword) {
        callback(new Error('Passwords do not match'));
      } else {
        callback();
      }
    };

    return {
      activeTab: 'profile',
      loading: false,
      passwordVerified: false,
      sessionId: localStorage.getItem('session_id'),
      
      tabs: [
        { id: 'profile', label: 'Profile', icon: 'User' },
        { id: 'change-password', label: 'Change Password', icon: 'Lock' },
        { id: 'forgot-password', label: 'Forgot Password', icon: 'HelpCircle' }
      ],
      
      passwordForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      
      forgotForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      
      passwordRules: {
        currentPassword: [
          { required: true, message: 'Please enter your current password', trigger: 'blur' }
        ],
        newPassword: [
          { required: true, message: 'Please enter a new password', trigger: 'blur' },
          { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: 'Please confirm your password', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      },
      
      forgotRules: {
        currentPassword: [
          { required: true, message: 'Please enter your current password', trigger: 'blur' }
        ],
        newPassword: [
          { required: true, message: 'Please enter a new password', trigger: 'blur' },
          { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: 'Please confirm your password', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      }
    };
  },
  computed: {
    visible: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    }
  },
  methods: {
    handleClose() {
      this.visible = false;
      this.resetAllForms();
    },
    
    async handleLogout() {
      // Directly logout without confirmation
      try {
        const response = await fetch('/api/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: this.sessionId
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          // Clear local storage
          localStorage.removeItem('session_id');
          localStorage.removeItem('username');
          localStorage.removeItem('role');
          localStorage.removeItem('full_name');
          
          // Show success message
          ElMessage.success('Logged out successfully');
          
          // Close modal
          this.handleClose();
          
          // Emit logout event
          this.$emit('logout');
          
          // Reload page after a short delay
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        } else {
          ElMessage.error('Logout failed. Please try again.');
        }
      } catch (error) {
        console.error('Logout error:', error);
        ElMessage.error('Network error during logout');
      }
    },
    
    async changePassword() {
      this.$refs.changePasswordForm.validate(async (valid) => {
        if (valid) {
          this.loading = true;
          try {
            const response = await fetch('/api/change-password', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                session_id: this.sessionId,
                old_password: this.passwordForm.currentPassword,
                new_password: this.passwordForm.newPassword
              })
            });
            
            const data = await response.json();
            
            if (data.success) {
              ElMessage.success('Password changed successfully!');
              this.$emit('password-changed');
              this.resetPasswordForm();
              this.activeTab = 'profile';
            } else {
              ElMessage.error(data.error || 'Failed to change password');
            }
          } catch (error) {
            ElMessage.error('Network error. Please try again.');
          } finally {
            this.loading = false;
          }
        }
      });
    },
    
    async verifyCurrentPassword() {
      if (!this.forgotForm.currentPassword) {
        ElMessage.warning('Please enter your current password');
        return;
      }
      
      this.loading = true;
      try {
        // Verify password by attempting to authenticate
        const response = await fetch('/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            username: this.currentUser.username,
            password: this.forgotForm.currentPassword
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          this.passwordVerified = true;
          ElMessage.success('Password verified! Now enter your new password.');
        } else {
          ElMessage.error('Incorrect password. Please try again.');
        }
      } catch (error) {
        ElMessage.error('Network error. Please try again.');
      } finally {
        this.loading = false;
      }
    },
    
    async resetPasswordWithVerification() {
      this.$refs.forgotPasswordForm.validate(async (valid) => {
        if (valid && this.passwordVerified) {
          this.loading = true;
          try {
            const response = await fetch('/api/change-password', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                session_id: this.sessionId,
                old_password: this.forgotForm.currentPassword,
                new_password: this.forgotForm.newPassword
              })
            });
            
            const data = await response.json();
            
            if (data.success) {
              ElMessage.success('Password reset successfully!');
              this.$emit('password-changed');
              this.resetForgotForm();
              this.activeTab = 'profile';
            } else {
              ElMessage.error(data.error || 'Failed to reset password');
            }
          } catch (error) {
            ElMessage.error('Network error. Please try again.');
          } finally {
            this.loading = false;
          }
        }
      });
    },
    
    resetPasswordForm() {
      this.passwordForm = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      };
      this.$refs.changePasswordForm?.clearValidate();
    },
    
    resetForgotForm() {
      this.forgotForm = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      };
      this.passwordVerified = false;
      this.$refs.forgotPasswordForm?.clearValidate();
    },
    
    resetAllForms() {
      this.resetPasswordForm();
      this.resetForgotForm();
      this.activeTab = 'profile';
    }
  }
};
</script>

<style scoped>
/* CSS Variables for theme support */
.user-profile-modal {
  --modal-bg: #ffffff;
  --modal-text: #303133;
  --modal-text-secondary: #606266;
  --modal-text-tertiary: #909399;
  --modal-border: #e4e7ed;
  --modal-bg-secondary: #f5f7fa;
  --modal-bg-light: #f9f9f9;
  --modal-primary: #409eff;
  --modal-danger: #f56c6c;
  --modal-success: #67c23a;
  --modal-warning: #e6a23c;
  --tab-hover-bg: rgba(0, 0, 0, 0.05);
  --tab-active-bg: #ffffff;
  --tab-active-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  --info-bg: #fef0f0;
  --info-border: #fde2e2;
  --info-text: #f56c6c;
}

/* Dark theme */
body[data-theme="dark"] .user-profile-modal,
body.dark-mode .user-profile-modal {
  --modal-bg: #1e1e1e;
  --modal-text: #e4e4e4;
  --modal-text-secondary: #b0b0b0;
  --modal-text-tertiary: #808080;
  --modal-border: #3a3a3a;
  --modal-bg-secondary: #2d2d2d;
  --modal-bg-light: #2a2a2a;
  --modal-primary: #5ca7ff;
  --modal-danger: #ff7878;
  --modal-success: #7ec83f;
  --modal-warning: #f0a23c;
  --tab-hover-bg: rgba(255, 255, 255, 0.1);
  --tab-active-bg: #3a3a3a;
  --tab-active-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  --info-bg: #3a2020;
  --info-border: #5a3030;
  --info-text: #ff9090;
}

/* High contrast theme */
body[data-theme="high-contrast"] .user-profile-modal,
body.high-contrast-mode .user-profile-modal {
  --modal-bg: #000000;
  --modal-text: #ffffff;
  --modal-text-secondary: #e0e0e0;
  --modal-text-tertiary: #c0c0c0;
  --modal-border: #ffffff;
  --modal-bg-secondary: #1a1a1a;
  --modal-bg-light: #0a0a0a;
  --modal-primary: #00aaff;
  --modal-danger: #ff4444;
  --modal-success: #00ff00;
  --modal-warning: #ffaa00;
  --tab-hover-bg: rgba(255, 255, 255, 0.2);
  --tab-active-bg: #1a1a1a;
  --tab-active-shadow: 0 0 0 2px #ffffff;
  --info-bg: #2a0000;
  --info-border: #ff4444;
  --info-text: #ff6666;
}

.user-profile-modal :deep(.el-dialog) {
  background-color: var(--modal-bg) !important;
  color: var(--modal-text) !important;
}

.user-profile-modal :deep(.el-dialog__wrapper) {
  background-color: transparent !important;
}

.user-profile-modal :deep(.el-dialog__title) {
  color: var(--modal-text) !important;
}

/* Force Element Plus dialog background */
body[data-theme="dark"] .user-profile-modal :deep(.el-dialog),
body.dark-mode .user-profile-modal :deep(.el-dialog) {
  background-color: #1e1e1e !important;
}

body[data-theme="high-contrast"] .user-profile-modal :deep(.el-dialog),
body.high-contrast-mode .user-profile-modal :deep(.el-dialog) {
  background-color: #000000 !important;
  border: 2px solid #ffffff !important;
}

.user-profile-modal :deep(.el-dialog__header) {
  padding: 20px 24px 10px;
  border-bottom: 1px solid var(--modal-border);
  background-color: var(--modal-bg);
}

.user-profile-modal :deep(.el-dialog__body) {
  padding: 0;
  background-color: var(--modal-bg);
}

.user-profile-modal :deep(.el-dialog__footer) {
  padding: 12px 24px;
  border-top: 1px solid var(--modal-border);
  background-color: var(--modal-bg);
}

.user-profile-modal :deep(.el-input__inner) {
  background-color: var(--modal-bg-light);
  color: var(--modal-text);
  border-color: var(--modal-border);
}

.user-profile-modal :deep(.el-input__inner:focus) {
  border-color: var(--modal-primary);
}

.user-profile-modal :deep(.el-form-item__label) {
  color: var(--modal-text-secondary);
}

.user-profile-modal :deep(.el-divider__text) {
  background-color: var(--modal-bg);
  color: var(--modal-text-secondary);
}

.tab-navigation {
  display: flex;
  gap: 4px;
  padding: 12px 24px;
  background: var(--modal-bg-secondary);
  border-bottom: 1px solid var(--modal-border);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--modal-text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-btn:hover {
  background: var(--tab-hover-bg);
  color: var(--modal-text);
}

.tab-btn.active {
  background: var(--modal-primary) !important;
  color: #ffffff !important;
  box-shadow: var(--tab-active-shadow);
}

body[data-theme="dark"] .tab-btn.active,
body.dark-mode .tab-btn.active {
  background: var(--modal-primary) !important;
  color: #ffffff !important;
}

body[data-theme="high-contrast"] .tab-btn.active,
body.high-contrast-mode .tab-btn.active {
  background: var(--modal-primary) !important;
  color: #000000 !important;
  font-weight: 600;
}

.tab-content {
  padding: 24px;
  min-height: 300px;
}

/* Profile Section */
.profile-section .user-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-row {
  display: flex;
  align-items: center;
  padding: 12px;
  background: var(--modal-bg-light);
  border-radius: 6px;
  border: 1px solid var(--modal-border);
}

.info-row label {
  flex: 0 0 120px;
  font-weight: 500;
  color: var(--modal-text-secondary);
}

.info-row span {
  flex: 1;
  color: var(--modal-text);
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.student {
  background: rgba(24, 144, 255, 0.15);
  color: var(--modal-primary);
  border: 1px solid var(--modal-primary);
}

.role-badge.professor {
  background: rgba(82, 196, 26, 0.15);
  color: var(--modal-success);
  border: 1px solid var(--modal-success);
}

.session-id {
  font-family: monospace;
  font-size: 12px;
  color: var(--modal-text-tertiary);
}

/* Password Section */
.password-section,
.forgot-section {
  max-width: 380px;
  margin: 0 auto;
}

.forgot-info {
  padding: 16px;
  background: var(--info-bg);
  border: 1px solid var(--info-border);
  border-radius: 6px;
  margin-bottom: 20px;
}

.forgot-info p {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--info-text);
  line-height: 1.5;
}

.forgot-info p:last-child {
  margin-bottom: 0;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.admin-contact {
  margin-top: 32px;
}

.contact-section {
  text-align: center;
  padding: 20px;
  background: var(--modal-bg-light);
  border-radius: 8px;
  border: 1px solid var(--modal-border);
}

.contact-section h4 {
  margin: 0 0 12px;
  color: var(--modal-text);
}

.contact-section p {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--modal-text-secondary);
}

.admin-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 16px 0;
}

.contact-method {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  color: var(--modal-text);
}

.admin-email {
  color: var(--modal-primary);
  font-weight: 500;
  font-size: 15px;
}

.contact-note {
  margin-top: 12px;
  font-size: 12px;
  color: var(--modal-text-tertiary);
  font-style: italic;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer .el-button--danger {
  margin-right: auto;
}

/* Additional high contrast styles for better visibility */
body[data-theme="high-contrast"] .user-profile-modal .tab-btn,
body.high-contrast-mode .user-profile-modal .tab-btn {
  border: 1px solid transparent;
}

body[data-theme="high-contrast"] .user-profile-modal .tab-btn:hover,
body.high-contrast-mode .user-profile-modal .tab-btn:hover {
  border-color: var(--modal-border);
}

body[data-theme="high-contrast"] .user-profile-modal .tab-btn.active,
body.high-contrast-mode .user-profile-modal .tab-btn.active {
  border-color: var(--modal-primary);
}

body[data-theme="high-contrast"] .user-profile-modal .contact-method strong,
body.high-contrast-mode .user-profile-modal .contact-method strong {
  color: var(--modal-warning);
  font-weight: 600;
}

/* Element Plus Button overrides for themes */
.user-profile-modal :deep(.el-button--primary) {
  background-color: var(--modal-primary) !important;
  border-color: var(--modal-primary) !important;
}

.user-profile-modal :deep(.el-button--danger) {
  background-color: var(--modal-danger) !important;
  border-color: var(--modal-danger) !important;
}

body[data-theme="dark"] .user-profile-modal :deep(.el-button--default),
body.dark-mode .user-profile-modal :deep(.el-button--default) {
  background-color: var(--modal-bg-secondary) !important;
  border-color: var(--modal-border) !important;
  color: var(--modal-text) !important;
}

body[data-theme="high-contrast"] .user-profile-modal :deep(.el-button--default),
body.high-contrast-mode .user-profile-modal :deep(.el-button--default) {
  background-color: var(--modal-bg-secondary) !important;
  border: 2px solid var(--modal-border) !important;
  color: var(--modal-text) !important;
}
</style>