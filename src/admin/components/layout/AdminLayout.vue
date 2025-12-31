<template>
  <div class="admin-layout">
    <Sidebar :collapsed="sidebarCollapsed" />

    <main class="admin-main" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <header class="admin-header">
        <button class="toggle-sidebar" @click="toggleSidebar">
          {{ sidebarCollapsed ? '☰' : '◀' }}
        </button>

        <h1 class="page-title">{{ pageTitle }}</h1>

        <div class="header-actions">
          <span class="welcome-text">Welcome, {{ fullName }}</span>
        </div>
      </header>

      <div class="admin-content">
        <slot></slot>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'

export default {
  name: 'AdminLayout',
  components: {
    Sidebar
  },
  setup() {
    const store = useStore()
    const route = useRoute()
    const sidebarCollapsed = ref(false)

    const fullName = computed(() => store.getters['auth/fullName'])

    const pageTitles = {
      '/dashboard': 'Dashboard',
      '/users': 'User Management',
      '/files': 'File Browser',
      '/grading': 'Grading',
      '/analytics': 'Analytics',
      '/audit': 'Audit Log',
      '/settings': 'Settings'
    }

    const pageTitle = computed(() => {
      const path = route.path
      return pageTitles[path] || 'Admin Panel'
    })

    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }

    return {
      sidebarCollapsed,
      fullName,
      pageTitle,
      toggleSidebar
    }
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.admin-main {
  flex: 1;
  margin-left: var(--admin-sidebar-width);
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
}

.admin-main.sidebar-collapsed {
  margin-left: var(--admin-sidebar-collapsed-width);
}

.admin-header {
  height: 60px;
  background-color: var(--admin-bg-secondary);
  border-bottom: 1px solid var(--admin-border-color);
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 50;
  gap: 16px;
}

.toggle-sidebar {
  background: none;
  border: none;
  color: var(--admin-text-secondary);
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.toggle-sidebar:hover {
  background-color: var(--admin-bg-hover);
  color: var(--admin-text-primary);
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--admin-text-white);
  margin: 0;
  flex: 1;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.welcome-text {
  font-size: 14px;
  color: var(--admin-text-secondary);
}

.admin-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background-color: var(--admin-bg-primary);
}
</style>
