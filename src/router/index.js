import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: '/',
    name: 'VmIndex',
    redirect: '/editor',
  },
  {
    path: '/editor',
    component: () => import('@/components/element/VmIde'),
    meta: { title: 'Vm Web IDE' },
  },
  {
    path: '/test-splitpanes',
    component: () => import('@/components/element/TestSplitpanes'),
    meta: { title: 'Test Splitpanes' },
  },
  {
    path: '/editor-new',
    component: () => import('@/components/element/VmIdeWithSplitpanes'),
    meta: { title: 'Vm Web IDE - New' },
  },
  {
    path: '/admin/users',
    component: () => import('@/components/element/AdminPasswordManager'),
    meta: {
      title: 'Admin Password Manager',
      requiresAuth: true,
      requiresAdmin: true
    },
    beforeEnter: (to, from, next) => {
      // Check if user is logged in
      const sessionId = localStorage.getItem('session_id');
      const username = localStorage.getItem('username');
      const role = localStorage.getItem('role');

      // If not logged in at all, redirect to main editor (which will show login)
      if (!sessionId || !username) {
        console.log('Admin page: No session found, redirecting to /editor');
        next('/editor');
        return;
      }

      // Check if user is admin_editor specifically
      if (username !== 'admin_editor') {
        console.log('Admin page: User is not admin_editor, redirecting to /editor');
        alert('Access Denied: Only admin_editor can access this page');
        next('/editor');
        return;
      }

      // User is admin_editor, allow access
      console.log('Admin page: Access granted for admin_editor');
      next();
    }
  },
]

export const router = createRouter({
  // history: createWebHashHistory(), // Hash Mode
  history: createWebHistory(), // HTML5 Mode
  routes: routes
})

export default router
