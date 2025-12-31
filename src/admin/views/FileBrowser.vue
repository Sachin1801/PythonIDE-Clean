<template>
  <AdminLayout>
    <div class="file-browser-page">
      <div class="admin-card">
        <div class="admin-card-header">
          <h3 class="admin-card-title">File Browser</h3>
        </div>
        <div class="coming-soon">
          <span class="icon">📁</span>
          <h3>File Browser Coming Soon</h3>
          <p>This feature will allow you to browse, view, and manage student files.</p>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script>
import AdminLayout from '../components/layout/AdminLayout.vue'

export default {
  name: 'FileBrowserPage',
  components: { AdminLayout }
}
</script>

<style scoped>
.coming-soon {
  text-align: center;
  padding: 80px 24px;
}
.coming-soon .icon { font-size: 64px; }
.coming-soon h3 { margin: 24px 0 12px; color: var(--admin-text-white); }
.coming-soon p { color: var(--admin-text-secondary); }
</style>
