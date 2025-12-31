<template>
  <AdminLayout>
    <div class="settings-page">
      <div class="admin-card">
        <div class="admin-card-header">
          <h3 class="admin-card-title">Settings</h3>
        </div>
        <div class="coming-soon">
          <span class="icon">⚙️</span>
          <h3>Settings Coming Soon</h3>
          <p>This feature will allow you to configure system settings and manage admin accounts.</p>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script>
import AdminLayout from '../components/layout/AdminLayout.vue'

export default {
  name: 'SettingsPage',
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
