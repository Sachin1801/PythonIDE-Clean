<template>
  <div v-if="visible" class="login-modal-overlay" @click.self="close">
    <div class="login-modal">
      <div class="login-header">
        <h3>Sign In to Python IDE</h3>
        <div class="close-btn" @click="close">
          <X :size="20" />
        </div>
      </div>
      
      <div class="login-body">
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="username">Username (Net ID)</label>
            <input
              id="username"
              v-model="username"
              type="text"
              placeholder="Enter your net id"
              required
              :disabled="loading"
              @input="clearError"
            />
          </div>
          
          <div class="form-group">
            <label for="password">Password</label>
            <input
              id="password"
              v-model="password"
              type="password"
              placeholder="Enter your password"
              required
              :disabled="loading"
              @input="clearError"
            />
          </div>
          
          <div v-if="error" class="error-message">
            {{ error }}
          </div>
          
          
          <button type="submit" class="login-btn" :disabled="loading">
            <span v-if="loading">Signing in...</span>
            <span v-else>Sign In</span>
          </button>
        </form>
        
      </div>
    </div>
  </div>
</template>

<script>
import { X } from 'lucide-vue-next';

export default {
  name: 'LoginModal',
  components: {
    X
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      username: '',
      password: '',
      loading: false,
      error: '',
      isFirstLogin: false
    }
  },
  watch: {
    username(val) {
      // Check if it looks like a student ID that might be using default password
      if (val && val.match(/^[a-z]{2}\d{4}$/)) {
        this.isFirstLogin = true;
      } else {
        this.isFirstLogin = false;
      }
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true;
      this.error = '';
      
      try {
        // Call the login API on the backend server
        const apiUrl = '/api/login';
          
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            username: this.username,
            password: this.password
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          // Store session information
          localStorage.setItem('session_id', data.session_id);
          localStorage.setItem('username', data.username);
          localStorage.setItem('role', data.role);
          localStorage.setItem('full_name', data.full_name);
          
          // Emit success event
          this.$emit('login-success', {
            username: data.username,
            role: data.role,
            full_name: data.full_name,
            session_id: data.session_id
          });
          
          // Close modal
          this.close();
          
          // Reload to initialize authenticated session
          window.location.reload();
        } else {
          this.error = data.error || 'Invalid username or password';
        }
      } catch (error) {
        console.error('Login error:', error);
        this.error = 'Connection error. Please try again.';
      } finally {
        this.loading = false;
      }
    },
    
    clearError() {
      this.error = '';
    },
    
    close() {
      this.username = '';
      this.password = '';
      this.error = '';
      this.loading = false;
      this.$emit('close');
    },
    
    async validateSession(sessionId) {
      try {
        const apiUrl = '/api/validate-session';
          
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        
        if (!data.success) {
          // Session invalid, clear storage
          localStorage.removeItem('session_id');
          localStorage.removeItem('username');
          localStorage.removeItem('role');
          localStorage.removeItem('full_name');
        }
      } catch (error) {
        console.error('Session validation error:', error);
      }
    }
  },
  mounted() {
    // Check if already logged in
    const sessionId = localStorage.getItem('session_id');
    if (sessionId) {
      // Validate session
      this.validateSession(sessionId);
    }
  }
}
</script>

<style scoped>
.login-modal-overlay {
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

.login-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--bg-primary, #1e1e1e);
  border: 1px solid var(--border-color, #464647);
  border-radius: 8px;
  width: 450px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  z-index: 9999;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.login-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #464647);
}

.login-header h3 {
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

.login-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  max-height: 60vh;
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
  box-sizing: border-box; /* Fix overflow issue */
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

.error-message {
  background: var(--error-bg, rgba(244, 71, 71, 0.1));
  color: var(--error-color, #f44747);
  padding: 10px 12px;
  border-radius: 4px;
  border: 1px solid var(--error-color, #f44747);
  margin-bottom: 15px;
  font-size: 14px;
}

.info-message {
  background: var(--info-bg, rgba(0, 122, 204, 0.1));
  color: var(--info-color, #007acc);
  padding: 10px 12px;
  border-radius: 4px;
  border: 1px solid var(--info-color, #007acc);
  margin-bottom: 15px;
  font-size: 13px;
}

.info-message code {
  background: var(--accent-color, #007acc);
  color: white;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 12px;
}

.login-btn {
  width: 100%;
  padding: 8px 20px;
  background: var(--accent-color, #007acc);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-sizing: border-box;
}

.login-btn:hover:not(:disabled) {
  background: var(--accent-hover, #005a9e);
}

.login-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


/* Light Theme Support */
[data-theme="light"] .login-modal {
  background: #ffffff;
  border-color: #d0d0d0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

[data-theme="light"] .login-header {
  border-bottom-color: #e0e0e0;
}

[data-theme="light"] .login-header h3 {
  color: #333333;
}

[data-theme="light"] .close-btn {
  color: rgba(0, 0, 0, 0.6);
}

[data-theme="light"] .close-btn:hover {
  color: rgba(0, 0, 0, 0.9);
  background: rgba(0, 0, 0, 0.08);
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

[data-theme="light"] .error-message {
  background: #fff2f0;
  color: #d63384;
  border-color: #d63384;
}

[data-theme="light"] .info-message {
  background: #e6f7ff;
  color: #1890ff;
  border-color: #1890ff;
}

[data-theme="light"] .info-message code {
  background: #1890ff;
}

[data-theme="light"] .login-btn {
  background: #1890ff;
}

[data-theme="light"] .login-btn:hover:not(:disabled) {
  background: #096dd9;
}


/* High Contrast Theme Support */
[data-theme="high-contrast"] .login-modal {
  background: #000000;
  border: 2px solid #ffffff;
  box-shadow: 0 8px 32px rgba(255, 255, 255, 0.3);
}

[data-theme="high-contrast"] .login-header {
  border-bottom: 2px solid #ffffff;
}

[data-theme="high-contrast"] .login-header h3 {
  color: #ffffff;
}

[data-theme="high-contrast"] .close-btn {
  color: #ffffff;
}

[data-theme="high-contrast"] .close-btn:hover {
  background: #333333;
  border: 1px solid #ffff00;
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

[data-theme="high-contrast"] .error-message {
  background: #000000;
  color: #ff6b6b;
  border: 2px solid #ff6b6b;
}

[data-theme="high-contrast"] .info-message {
  background: #000000;
  color: #00bfff;
  border: 2px solid #00bfff;
}

[data-theme="high-contrast"] .info-message code {
  background: #00bfff;
  color: #000000;
}

[data-theme="high-contrast"] .login-btn {
  background: #00bfff;
  color: #000000;
  border: 2px solid #ffffff;
}

[data-theme="high-contrast"] .login-btn:hover:not(:disabled) {
  background: #ffff00;
  border-color: #ffff00;
}

</style>