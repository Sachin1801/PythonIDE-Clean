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
    meta: { title: 'Admin Password Manager' },
  },
]

export const router = createRouter({
  // history: createWebHashHistory(), // Hash Mode
  history: createWebHistory(), // HTML5 Mode
  routes: routes
})

export default router
