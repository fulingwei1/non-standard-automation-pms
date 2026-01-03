<template>
  <header class="topbar">
    <div class="topbar-left">
      <!-- 搜索框 -->
      <div class="search-box" :class="{ focused: searchFocused }">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input 
          type="text" 
          v-model="searchQuery"
          placeholder="搜索项目、任务..."
          @focus="searchFocused = true"
          @blur="searchFocused = false"
        />
        <span class="search-shortcut">⌘K</span>
      </div>
    </div>

    <div class="topbar-right">
      <!-- 通知 -->
      <button class="icon-btn" title="通知">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        <span class="notification-dot"></span>
      </button>

      <!-- 帮助 -->
      <button class="icon-btn" title="帮助">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'

const searchQuery = ref('')
const searchFocused = ref(false)
</script>

<style scoped>
.topbar {
  height: 64px;
  background: white;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 40;
}

.topbar-left { display: flex; align-items: center; }
.topbar-right { display: flex; align-items: center; gap: 8px; }

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 320px;
  padding: 10px 14px;
  background: #F3F4F6;
  border-radius: 10px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.search-box.focused {
  background: white;
  border-color: #6366F1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.search-icon { width: 18px; height: 18px; color: #9CA3AF; flex-shrink: 0; }
.search-box input { flex: 1; border: none; background: none; font-size: 14px; outline: none; }
.search-box input::placeholder { color: #9CA3AF; }
.search-shortcut { font-size: 12px; color: #9CA3AF; background: white; padding: 4px 8px; border-radius: 6px; border: 1px solid #E5E7EB; }

.icon-btn {
  width: 40px; height: 40px; border-radius: 10px; border: none; background: transparent;
  color: #6B7280; cursor: pointer; display: flex; align-items: center; justify-content: center;
  position: relative; transition: all 0.2s;
}
.icon-btn:hover { background: #F3F4F6; color: #374151; }
.icon-btn svg { width: 20px; height: 20px; }
.notification-dot { position: absolute; top: 8px; right: 8px; width: 8px; height: 8px; background: #EF4444; border-radius: 50%; border: 2px solid white; }
</style>
