<template>
  <div id="admin-app" class="dark">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'AdminApp',
  mounted() {
    // Force dark theme for admin panel
    document.documentElement.setAttribute('data-theme', 'dark')
    document.documentElement.classList.add('dark')
  }
}
</script>

<style>
#admin-app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  background-color: var(--admin-bg-primary);
  color: var(--admin-text-primary);
}
</style>
