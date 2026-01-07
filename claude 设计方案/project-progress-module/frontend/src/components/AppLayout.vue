<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-wrapper">
      <AppTopbar />
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.main-wrapper {
  flex: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left 0.3s;
}

.main-content {
  flex: 1;
  background: #F8FAFC;
}

/* 当侧边栏收起时 */
.app-layout:has(.sidebar.collapsed) .main-wrapper {
  margin-left: 80px;
}

@media (max-width: 1024px) {
  .main-wrapper {
    margin-left: 0;
  }
}
</style>
