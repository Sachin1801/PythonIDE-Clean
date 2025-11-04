<template>
  <div v-if="visible" class="profile-modal-overlay" @click.self="handleClose">
    <div class="profile-modal">
      <div class="dialog-header">
        <h3>{{ currentUser ? `${currentUser.full_name || currentUser.username}` : 'User Profile' }}</h3>
        <div class="close-btn" @click="handleClose">
          <X :size="20" />
        </div>
      </div>
      
      <div class="dialog-body">
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
            <form @submit.prevent="changePassword">
              <div class="form-group">
                <label>Current Password</label>
                <input 
                  v-model="passwordForm.currentPassword" 
                  type="password" 
                  placeholder="Enter your current password"
                  :disabled="loading"
                />
              </div>
              
              <div class="form-group">
                <label>New Password</label>
                <input 
                  v-model="passwordForm.newPassword" 
                  type="password" 
                  placeholder="Enter new password (min 6 characters)"
                  :disabled="loading"
                />
              </div>
              
              <div class="form-group">
                <label>Confirm New Password</label>
                <input 
                  v-model="passwordForm.confirmPassword" 
                  type="password" 
                  placeholder="Confirm new password"
                  :disabled="loading"
                />
              </div>

              <div class="form-actions">
                <button 
                  type="submit"
                  class="btn-primary"
                  :disabled="loading"
                >
                  {{ loading ? 'Changing...' : 'Change Password' }}
                </button>
                <button 
                  type="button"
                  class="btn-secondary" 
                  @click="resetPasswordForm"
                >
                  Reset
                </button>
              </div>
            </form>
          </div>

          <!-- Forgot Password Tab (Commented Out) -->
          <!-- <div v-if="activeTab === 'forgot-password'" class="forgot-section">
            <div class="forgot-info">
              <p>To reset your password, you need to verify your current password first.</p>
              <p>If you don't remember your current password, please contact the administrator.</p>
            </div>

            <form @submit.prevent="passwordVerified ? resetPasswordWithVerification() : verifyCurrentPassword()">
              <div class="form-group">
                <label>Current Password</label>
                <input 
                  v-model="forgotForm.currentPassword" 
                  type="password" 
                  placeholder="Enter your current password to verify"
                  :disabled="loading"
                />
              </div>
              
              <div class="form-group">
                <label>New Password</label>
                <input 
                  v-model="forgotForm.newPassword" 
                  type="password" 
                  placeholder="Enter new password (min 6 characters)"
                  :disabled="!passwordVerified || loading"
                />
              </div>
              
              <div class="form-group">
                <label>Confirm New Password</label>
                <input 
                  v-model="forgotForm.confirmPassword" 
                  type="password" 
                  placeholder="Confirm new password"
                  :disabled="!passwordVerified || loading"
                />
              </div>

              <div class="form-actions">
                <button 
                  v-if="!passwordVerified"
                  type="submit"
                  class="btn-primary"
                  :disabled="loading"
                >
                  {{ loading ? 'Verifying...' : 'Verify Password' }}
                </button>
                <button 
                  v-else
                  type="submit"
                  class="btn-success"
                  :disabled="loading"
                >
                  {{ loading ? 'Resetting...' : 'Reset Password' }}
                </button>
                <button 
                  type="button"
                  class="btn-secondary" 
                  @click="resetForgotForm"
                >
                  Clear
                </button>
              </div>
            </form>

            <div class="admin-contact">
              <div class="divider">
                <span>OR</span>
              </div>
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
          </div> -->
        </div>
      </div>
        
      <!-- Footer Actions -->
      <div class="dialog-footer">
        <button 
          v-if="activeTab === 'profile'"
          class="btn-danger" 
          @click="handleLogout"
        >
          <LogOut :size="16" />
          Logout
        </button>
        <button class="btn-secondary" @click="handleClose">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
import { User, Lock, HelpCircle, LogOut, Mail, MessageSquare, X } from 'lucide-vue-next';
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
    MessageSquare,
    X
  },
  data() {
    return {
      activeTab: 'profile',
      loading: false,
      passwordVerified: false,
      sessionId: localStorage.getItem('session_id'),
      
      tabs: [
        { id: 'profile', label: 'Profile', icon: 'User' },
        { id: 'change-password', label: 'Change Password', icon: 'Lock' },
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
      // Basic validation
      if (!this.passwordForm.currentPassword) {
        ElMessage.warning('Please enter your current password');
        return;
      }
      if (!this.passwordForm.newPassword || this.passwordForm.newPassword.length < 6) {
        ElMessage.warning('New password must be at least 6 characters');
        return;
      }
      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        ElMessage.warning('Passwords do not match');
        return;
      }

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
      if (!this.passwordVerified) {
        ElMessage.warning('Please verify your current password first');
        return;
      }
      if (!this.forgotForm.newPassword || this.forgotForm.newPassword.length < 6) {
        ElMessage.warning('New password must be at least 6 characters');
        return;
      }
      if (this.forgotForm.newPassword !== this.forgotForm.confirmPassword) {
        ElMessage.warning('Passwords do not match');
        return;
      }

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
    },
    
    resetPasswordForm() {
      this.passwordForm = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      };
    },
    
    resetForgotForm() {
      this.forgotForm = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      };
      this.passwordVerified = false;
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
.profile-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #464647);
  border-radius: 8px;
  width: 550px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  z-index: 9999;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #464647);
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary, #cccccc);
}

.close-btn {
  cursor: pointer;
  color: var(--text-secondary, #969696);
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  background: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: var(--hover-bg, rgba(255, 255, 255, 0.1));
  color: var(--text-primary, #cccccc);
}

.dialog-body {
  flex: 1;
  overflow-y: auto;
  max-height: 60vh;
}

.tab-navigation {
  display: flex;
  gap: 4px;
  padding: 12px 20px;
  background: var(--bg-secondary, #252526);
  border-bottom: 1px solid var(--border-color, #464647);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--text-secondary, #969696);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--hover-bg, rgba(255, 255, 255, 0.1));
  color: var(--text-primary, #cccccc);
}

.tab-btn.active {
  background: var(--accent-color, #007acc);
  color: #ffffff;
}

.tab-content {
  padding: 20px;
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
  background: var(--input-bg, #2d2d30);
  border-radius: 4px;
  border: 1px solid var(--border-color, #464647);
}

.info-row label {
  flex: 0 0 120px;
  font-weight: 500;
  color: var(--text-secondary, #969696);
  font-size: 14px;
}

.info-row span {
  flex: 1;
  color: var(--text-primary, #cccccc);
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.student {
  background: rgba(0, 122, 204, 0.15);
  color: var(--accent-color, #007acc);
  border: 1px solid var(--accent-color, #007acc);
}

.role-badge.professor {
  background: rgba(103, 194, 58, 0.15);
  color: #67c23a;
  border: 1px solid #67c23a;
}

.session-id {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: var(--text-disabled, #6b6b6b);
}

/* Form Sections */
.password-section,
.forgot-section {
  max-width: 400px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #cccccc);
}

.form-group input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  background: var(--input-bg, #2d2d30);
  border: 1px solid var(--border-color, #464647);
  border-radius: 4px;
  color: var(--text-primary, #cccccc);
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent-color, #007acc);
  background: var(--input-focus-bg, #383838);
}

.form-group input::placeholder {
  color: var(--text-disabled, #6b6b6b);
}

.form-group input:disabled {
  background: var(--input-disabled-bg, #1a1a1a);
  cursor: not-allowed;
  opacity: 0.6;
}

.forgot-info {
  padding: 16px;
  background: var(--info-bg, rgba(0, 122, 204, 0.1));
  border: 1px solid var(--accent-color, #007acc);
  border-radius: 4px;
  margin-bottom: 20px;
}

.forgot-info p {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--accent-color, #007acc);
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

/* Buttons */
.btn-primary,
.btn-secondary,
.btn-success,
.btn-danger {
  padding: 8px 20px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: var(--accent-color, #007acc);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover, #005a9e);
}

.btn-secondary {
  background: var(--bg-secondary, #252526);
  color: var(--text-primary, #cccccc);
  border: 1px solid var(--border-color, #464647);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--hover-bg, #383838);
}

.btn-success {
  background: #67c23a;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #5daf34;
}

.btn-danger {
  background: var(--error-color, #f44747);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #e73c3c;
}

.btn-primary:disabled,
.btn-secondary:disabled,
.btn-success:disabled,
.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Admin Contact Section */
.admin-contact {
  margin-top: 32px;
}

.divider {
  text-align: center;
  margin: 20px 0;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border-color, #464647);
}

.divider span {
  background: var(--bg-primary, #1e1e1e);
  padding: 0 16px;
  color: var(--text-secondary, #969696);
  font-size: 12px;
}

.contact-section {
  text-align: center;
  padding: 20px;
  background: var(--preview-bg, #252526);
  border-radius: 4px;
  border: 1px solid var(--border-color, #464647);
}

.contact-section h4 {
  margin: 0 0 12px;
  color: var(--text-primary, #cccccc);
  font-size: 16px;
}

.contact-section p {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--text-secondary, #969696);
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
  color: var(--text-primary, #cccccc);
}

.admin-email {
  color: var(--accent-color, #007acc);
  font-weight: 500;
  font-size: 15px;
}

.contact-note {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-disabled, #6b6b6b);
  font-style: italic;
}

/* Footer */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, #464647);
}

/* Light Theme Support */
[data-theme="light"] .profile-modal {
  background: #ffffff;
  border-color: #d0d0d0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

[data-theme="light"] .dialog-header {
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .dialog-header h3 {
  color: #333333;
}

[data-theme="light"] .close-btn {
  color: rgba(0, 0, 0, 0.6);
}

[data-theme="light"] .close-btn:hover {
  color: rgba(0, 0, 0, 0.9);
  background: rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .tab-navigation {
  background: #f8f8f8;
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .tab-btn {
  color: #666666;
}

[data-theme="light"] .tab-btn:hover {
  color: #333333;
  background: rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .tab-btn.active {
  background: #1890ff;
}

[data-theme="light"] .info-row {
  background: #f8f8f8;
  border-color: #d0d0d0;
}

[data-theme="light"] .info-row label {
  color: #666666;
}

[data-theme="light"] .info-row span {
  color: #333333;
}

[data-theme="light"] .role-badge.student {
  background: rgba(24, 144, 255, 0.15);
  color: #1890ff;
  border-color: #1890ff;
}

[data-theme="light"] .session-id {
  color: #999999;
}

[data-theme="light"] .form-group label {
  color: #333333;
}

[data-theme="light"] .form-group input {
  background: #f8f8f8;
  border-color: #d0d0d0;
  color: #333333;
}

[data-theme="light"] .form-group input:focus {
  background: #ffffff;
  border-color: #1890ff;
}

[data-theme="light"] .form-group input::placeholder {
  color: #999999;
}

[data-theme="light"] .form-group input:disabled {
  background: #f0f0f0;
}

[data-theme="light"] .forgot-info {
  background: #e6f7ff;
  color: #1890ff;
  border-color: #1890ff;
}

[data-theme="light"] .btn-primary {
  background: #1890ff;
}

[data-theme="light"] .btn-primary:hover:not(:disabled) {
  background: #096dd9;
}

[data-theme="light"] .btn-secondary {
  background: #ffffff;
  color: #333333;
  border-color: #d0d0d0;
}

[data-theme="light"] .btn-secondary:hover:not(:disabled) {
  background: #f8f8f8;
}

[data-theme="light"] .divider::before {
  background: #e0e0e0;
}

[data-theme="light"] .divider span {
  background: #ffffff;
  color: #666666;
}

[data-theme="light"] .contact-section {
  background: #f8f8f8;
  border-color: #d0d0d0;
}

[data-theme="light"] .contact-section h4 {
  color: #333333;
}

[data-theme="light"] .contact-section p {
  color: #666666;
}

[data-theme="light"] .contact-method {
  color: #333333;
}

[data-theme="light"] .admin-email {
  color: #1890ff;
}

[data-theme="light"] .contact-note {
  color: #999999;
}

[data-theme="light"] .dialog-footer {
  border-top-color: #e0e0e0;
}

/* High Contrast Theme Support */
[data-theme="high-contrast"] .profile-modal {
  background: #000000;
  border: 2px solid #ffffff;
  box-shadow: 0 8px 32px rgba(255, 255, 255, 0.3);
}

[data-theme="high-contrast"] .dialog-header {
  border-bottom: 2px solid #ffffff;
}

[data-theme="high-contrast"] .dialog-header h3 {
  color: #ffffff;
}

[data-theme="high-contrast"] .close-btn {
  color: #ffffff;
}

[data-theme="high-contrast"] .close-btn:hover {
  background: #333333;
  border: 1px solid #ffff00;
}

[data-theme="high-contrast"] .tab-navigation {
  background: #000000;
  border-bottom: 2px solid #ffffff;
}

[data-theme="high-contrast"] .tab-btn {
  color: #ffffff;
  border: 1px solid transparent;
}

[data-theme="high-contrast"] .tab-btn:hover {
  border-color: #ffffff;
}

[data-theme="high-contrast"] .tab-btn.active {
  background: #00bfff;
  color: #000000;
  border-color: #00bfff;
}

[data-theme="high-contrast"] .info-row {
  background: #000000;
  border: 2px solid #ffffff;
}

[data-theme="high-contrast"] .info-row label {
  color: #ffffff;
}

[data-theme="high-contrast"] .info-row span {
  color: #ffffff;
}

[data-theme="high-contrast"] .role-badge.student {
  background: #000000;
  color: #00bfff;
  border: 2px solid #00bfff;
}

[data-theme="high-contrast"] .role-badge.professor {
  background: #000000;
  color: #00ff00;
  border: 2px solid #00ff00;
}

[data-theme="high-contrast"] .session-id {
  color: #cccccc;
}

[data-theme="high-contrast"] .form-group label {
  color: #ffffff;
}

[data-theme="high-contrast"] .form-group input {
  background: #000000;
  border: 2px solid #ffffff;
  color: #ffffff;
}

[data-theme="high-contrast"] .form-group input:focus {
  border-color: #ffff00;
}

[data-theme="high-contrast"] .form-group input::placeholder {
  color: #cccccc;
}

[data-theme="high-contrast"] .forgot-info {
  background: #000000;
  color: #00bfff;
  border: 2px solid #00bfff;
}

[data-theme="high-contrast"] .btn-primary {
  background: #00bfff;
  color: #000000;
  border: 2px solid #ffffff;
}

[data-theme="high-contrast"] .btn-primary:hover:not(:disabled) {
  background: #ffff00;
  border-color: #ffff00;
}

[data-theme="high-contrast"] .btn-secondary {
  background: #333333;
  color: #ffffff;
  border: 2px solid #ffffff;
}

[data-theme="high-contrast"] .btn-secondary:hover:not(:disabled) {
  background: #666666;
}

[data-theme="high-contrast"] .btn-success {
  background: #00ff00;
  color: #000000;
  border: 2px solid #ffffff;
}

[data-theme="high-contrast"] .btn-danger {
  background: #ff4444;
  color: #ffffff;
  border: 2px solid #ffffff;
}

[data-theme="high-contrast"] .divider::before {
  background: #ffffff;
}

[data-theme="high-contrast"] .divider span {
  background: #000000;
  color: #ffffff;
}

[data-theme="high-contrast"] .contact-section {
  background: #000000;
  border: 2px solid #ffffff;
}

[data-theme="high-contrast"] .contact-section h4 {
  color: #ffffff;
}

[data-theme="high-contrast"] .contact-section p {
  color: #ffffff;
}

[data-theme="high-contrast"] .contact-method {
  color: #ffffff;
}

[data-theme="high-contrast"] .contact-method strong {
  color: #ffff00;
  font-weight: 600;
}

[data-theme="high-contrast"] .admin-email {
  color: #00bfff;
}

[data-theme="high-contrast"] .contact-note {
  color: #cccccc;
}

[data-theme="high-contrast"] .dialog-footer {
  border-top: 2px solid #ffffff;
}
</style>