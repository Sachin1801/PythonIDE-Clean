<template>
  <AdminLayout>
    <div class="analytics-page">
      <div class="admin-card">
        <div class="admin-card-header">
          <h3 class="admin-card-title">Analytics</h3>
        </div>
        <div class="coming-soon">
          <span class="icon">📈</span>
          <h3>Analytics Dashboard Coming Soon</h3>
          <p>This feature will provide login activity, file usage, and code execution statistics.</p>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script>
import AdminLayout from '../components/layout/AdminLayout.vue'

export default {
  name: 'AnalyticsPage',
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
