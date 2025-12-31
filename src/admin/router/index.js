/**
 * Admin Panel Router
 * Handles routing for all admin panel pages
 */

import { createRouter, createWebHistory } from 'vue-router'
import store from '../store'

// Views
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import Users from '../views/Users.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'Users',
    component: Users,
    meta: { requiresAuth: true }
  },
  {
    path: '/users/:id',
    name: 'UserDetail',
    component: () => import('../views/UserDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/files',
    name: 'FileBrowser',
    component: () => import('../views/FileBrowser.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/grading',
    name: 'Grading',
    component: () => import('../views/Grading.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: () => import('../views/Analytics.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/audit',
    name: 'AuditLog',
    component: () => import('../views/AuditLog.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory('/'),
  routes
})

// Navigation guard for authentication
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth) {
    // Check if user is authenticated
    const isAuthenticated = await store.dispatch('auth/checkSession')

    if (!isAuthenticated) {
      // Redirect to login
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }

  // If going to login while already authenticated, redirect to dashboard
  if (to.name === 'Login') {
    const isAuthenticated = await store.dispatch('auth/checkSession')
    if (isAuthenticated) {
      next({ name: 'Dashboard' })
      return
    }
  }

  next()
})

export default router
