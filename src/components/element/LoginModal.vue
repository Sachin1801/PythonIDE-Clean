<template>
  <div v-if="visible" class="login-modal-overlay" @click.self="close">
    <div class="login-modal">
      <div class="login-header">
        <h2>Sign In to Python IDE</h2>
        <button class="close-btn" @click="close">×</button>
      </div>
      
      <div class="login-body">
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="username">Username (Student ID)</label>
            <input
              id="username"
              v-model="username"
              type="text"
              placeholder="e.g., sa9082"
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
          
          <div v-if="isFirstLogin" class="info-message">
            <p>First time? Your initial password is: <code>{{ username }}2024</code></p>
            <p>Please change it after logging in.</p>
          </div>
          
          <button type="submit" class="login-btn" :disabled="loading">
            <span v-if="loading">Signing in...</span>
            <span v-else>Sign In</span>
          </button>
        </form>
        
        <div class="login-footer">
          <p class="demo-info">Demo Accounts:</p>
          <ul class="demo-accounts">
            <li>Student: <code>sa9082</code> / <code>sa90822024</code></li>
            <li>Professor: <code>professor</code> / <code>ChangeMeASAP2024!</code></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginModal',
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
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.login-modal {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.login-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e5e5;
}

.login-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.login-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #4CAF50;
}

.form-group input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.error-message {
  background: #ffebee;
  color: #c62828;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
  font-size: 14px;
}

.info-message {
  background: #e3f2fd;
  color: #1565c0;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
  font-size: 13px;
}

.info-message code {
  background: #1565c0;
  color: white;
  padding: 2px 4px;
  border-radius: 3px;
}

.login-btn {
  width: 100%;
  padding: 12px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}

.login-btn:hover:not(:disabled) {
  background: #45a049;
}

.login-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.login-footer {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e5e5;
}

.demo-info {
  font-size: 13px;
  color: #666;
  margin-bottom: 10px;
  font-weight: 500;
}

.demo-accounts {
  list-style: none;
  padding: 0;
  margin: 0;
}

.demo-accounts li {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.demo-accounts code {
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  color: #333;
}
</style>