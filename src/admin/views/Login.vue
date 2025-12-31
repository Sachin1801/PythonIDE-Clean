<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1 class="login-title">Admin Panel</h1>
        <p class="login-subtitle">Python Web IDE Administration</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label class="form-label">Username</label>
          <el-input
            v-model="username"
            placeholder="Enter your username"
            size="large"
            :disabled="loading"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <span class="input-icon"><User :size="18" /></span>
            </template>
          </el-input>
        </div>

        <div class="form-group">
          <label class="form-label">Password</label>
          <el-input
            v-model="password"
            type="password"
            placeholder="Enter your password"
            size="large"
            show-password
            :disabled="loading"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <span class="input-icon"><Lock :size="18" /></span>
            </template>
          </el-input>
        </div>

        <el-alert
          v-if="error"
          :title="error"
          type="error"
          :closable="false"
          show-icon
          class="login-error"
        />

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          @click="handleLogin"
          class="login-button"
        >
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </el-button>
      </form>

      <div class="login-footer">
        <p>Only professors can access the admin panel.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { User, Lock } from 'lucide-vue-next'

export default {
  name: 'AdminLogin',
  components: {
    User,
    Lock
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()

    const username = ref('')
    const password = ref('')

    const loading = computed(() => store.getters['auth/isLoading'])
    const error = computed(() => store.getters['auth/error'])

    const handleLogin = async () => {
      if (!username.value || !password.value) {
        window.ElMessage.warning('Please enter username and password')
        return
      }

      const result = await store.dispatch('auth/login', {
        username: username.value,
        password: password.value
      })

      if (result.success) {
        window.ElMessage.success('Welcome to Admin Panel')
        const redirect = route.query.redirect || '/dashboard'
        router.push(redirect)
      } else {
        window.ElMessage.error(result.error || 'Login failed')
      }
    }

    return {
      username,
      password,
      loading,
      error,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e1e1e 0%, #2d2d30 100%);
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 400px;
  background-color: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 12px;
  padding: 40px;
  box-shadow: var(--admin-shadow-lg);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--admin-text-white);
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 14px;
  color: var(--admin-text-secondary);
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--admin-text-primary);
}

.input-icon {
  font-size: 16px;
}

.login-error {
  margin-bottom: 20px;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
}

.login-footer {
  text-align: center;
  color: var(--admin-text-muted);
  font-size: 12px;
}

.login-footer p {
  margin: 0;
}

/* Element Plus overrides */
:deep(.el-input__wrapper) {
  background-color: var(--admin-bg-tertiary) !important;
  box-shadow: 0 0 0 1px var(--admin-border-color) inset !important;
}

:deep(.el-input__inner) {
  color: var(--admin-text-primary) !important;
}

:deep(.el-input__inner::placeholder) {
  color: var(--admin-text-muted) !important;
}

:deep(.el-button--primary) {
  --el-button-bg-color: var(--admin-primary);
  --el-button-border-color: var(--admin-primary);
  --el-button-hover-bg-color: var(--admin-primary-hover);
  --el-button-hover-border-color: var(--admin-primary-hover);
}
</style>
