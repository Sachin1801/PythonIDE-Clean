<template>
  <aside class="admin-sidebar" :class="{ collapsed }">
    <div class="sidebar-logo">
      <Shield class="logo-icon" :size="24" />
      <span v-if="!collapsed" class="logo-text">Admin Panel</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <component :is="item.icon" class="nav-icon" :size="20" />
        <span v-if="!collapsed" class="nav-text">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <div class="user-info" v-if="!collapsed">
        <div class="user-name">{{ fullName }}</div>
        <div class="user-role">{{ role }}</div>
      </div>
      <button class="logout-btn" @click="handleLogout" :title="collapsed ? 'Logout' : ''">
        <LogOut class="nav-icon" :size="20" />
        <span v-if="!collapsed" class="nav-text">Logout</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import {
  LayoutDashboard,
  Users,
  FolderOpen,
  ClipboardCheck,
  BarChart3,
  FileText,
  Settings,
  LogOut,
  Shield
} from 'lucide-vue-next'

export default {
  name: 'AdminSidebar',
  components: {
    LayoutDashboard,
    Users,
    FolderOpen,
    ClipboardCheck,
    BarChart3,
    FileText,
    Settings,
    LogOut,
    Shield
  },
  props: {
    collapsed: {
      type: Boolean,
      default: false
    }
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()

    const navItems = [
      { path: '/dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
      { path: '/users', label: 'Users', icon: 'Users' },
      { path: '/files', label: 'File Browser', icon: 'FolderOpen' },
      { path: '/grading', label: 'Grading', icon: 'ClipboardCheck' },
      { path: '/analytics', label: 'Analytics', icon: 'BarChart3' },
      { path: '/audit', label: 'Audit Log', icon: 'FileText' },
      { path: '/settings', label: 'Settings', icon: 'Settings' }
    ]

    const fullName = computed(() => store.getters['auth/fullName'])
    const role = computed(() => store.getters['auth/user']?.role || 'professor')

    const isActive = (path) => {
      return route.path === path || route.path.startsWith(path + '/')
    }

    const handleLogout = async () => {
      await store.dispatch('auth/logout')
      router.push('/login')
    }

    return {
      navItems,
      fullName,
      role,
      isActive,
      handleLogout
    }
  }
}
</script>

<style scoped>
.admin-sidebar {
  width: var(--admin-sidebar-width);
  background-color: var(--admin-bg-secondary);
  border-right: 1px solid var(--admin-border-color);
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  z-index: 100;
  transition: width 0.3s ease;
}

.admin-sidebar.collapsed {
  width: var(--admin-sidebar-collapsed-width);
}

.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid var(--admin-border-color);
  font-size: 18px;
  font-weight: 600;
  color: var(--admin-text-white);
}

.logo-icon {
  font-size: 24px;
  margin-right: 12px;
}

.collapsed .logo-icon {
  margin-right: 0;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: var(--admin-text-secondary);
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background-color: var(--admin-bg-hover);
  color: var(--admin-text-primary);
}

.nav-item.active {
  background-color: var(--admin-bg-active);
  color: var(--admin-text-white);
  border-left-color: var(--admin-primary);
}

.nav-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
  margin-right: 12px;
}

.collapsed .nav-icon {
  margin-right: 0;
}

.nav-text {
  white-space: nowrap;
  overflow: hidden;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--admin-border-color);
}

.user-info {
  margin-bottom: 12px;
  padding: 8px;
  background-color: var(--admin-bg-tertiary);
  border-radius: 8px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--admin-text-primary);
}

.user-role {
  font-size: 12px;
  color: var(--admin-text-secondary);
  text-transform: capitalize;
}

.logout-btn {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 12px;
  background-color: transparent;
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  color: var(--admin-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background-color: rgba(220, 53, 69, 0.2);
  border-color: var(--admin-danger);
  color: var(--admin-danger);
}
</style>
