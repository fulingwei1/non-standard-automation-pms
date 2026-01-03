<template>
  <div class="notification-center">
    <!-- 通知铃铛按钮 -->
    <div class="notification-trigger" @click="togglePanel">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
      <span class="badge" v-if="unreadCount > 0">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </div>

    <!-- 通知面板 -->
    <transition name="slide">
      <div class="notification-panel" v-if="showPanel" @click.stop>
        <div class="panel-header">
          <h3>消息通知</h3>
          <div class="header-actions">
            <button class="btn-text" @click="markAllRead" v-if="unreadCount > 0">全部已读</button>
            <button class="btn-icon" @click="openSettings" title="设置">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="panel-tabs">
          <button class="tab" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">全部</button>
          <button class="tab" :class="{ active: activeTab === 'unread' }" @click="activeTab = 'unread'">
            未读 <span class="count" v-if="unreadCount">{{ unreadCount }}</span>
          </button>
        </div>

        <div class="panel-body">
          <div class="notification-list" v-if="filteredNotifications.length > 0">
            <div class="notification-item" v-for="n in filteredNotifications" :key="n.id"
                 :class="{ unread: !n.is_read }" @click="handleClick(n)">
              <div class="notification-icon" :class="getTypeClass(n.type)">
                {{ getTypeIcon(n.type) }}
              </div>
              <div class="notification-content">
                <div class="notification-title">{{ n.title }}</div>
                <div class="notification-text">{{ n.content.substring(0, 60) }}{{ n.content.length > 60 ? '...' : '' }}</div>
                <div class="notification-time">{{ formatTime(n.created_at) }}</div>
              </div>
              <button class="notification-close" @click.stop="deleteNotification(n.id)" title="删除">×</button>
            </div>
          </div>
          <div class="empty-state" v-else>
            <div class="empty-icon">🔔</div>
            <p>暂无{{ activeTab === 'unread' ? '未读' : '' }}消息</p>
          </div>
        </div>

        <div class="panel-footer">
          <button class="btn-link" @click="viewAll">查看全部消息</button>
        </div>
      </div>
    </transition>

    <!-- 设置弹窗 -->
    <div class="modal-overlay" v-if="showSettings" @click="showSettings = false">
      <div class="settings-modal" @click.stop>
        <div class="modal-header">
          <h3>提醒设置</h3>
          <button class="modal-close" @click="showSettings = false">×</button>
        </div>
        <div class="modal-body">
          <!-- 通知渠道 -->
          <div class="settings-section">
            <h4>通知渠道</h4>
            <div class="setting-item" v-for="c in channels" :key="c.code">
              <div class="setting-info">
                <span class="setting-icon">{{ c.icon }}</span>
                <div>
                  <span class="setting-name">{{ c.name }}</span>
                  <span class="setting-desc">{{ c.description }}</span>
                </div>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="settings.channels[c.code]">
                <span class="slider"></span>
              </label>
            </div>
          </div>

          <!-- 提醒类型 -->
          <div class="settings-section">
            <h4>提醒类型</h4>
            <div class="setting-item" v-for="t in reminderTypes" :key="t.code">
              <div class="setting-info">
                <div>
                  <span class="setting-name">{{ t.name }}</span>
                  <span class="setting-desc">{{ t.description }}</span>
                </div>
              </div>
              <label class="switch" v-if="t.can_disable">
                <input type="checkbox" v-model="settings.types[t.code]">
                <span class="slider"></span>
              </label>
              <span class="always-on" v-else>始终开启</span>
            </div>
          </div>

          <!-- 免打扰 -->
          <div class="settings-section">
            <h4>免打扰时段</h4>
            <div class="setting-item">
              <div class="setting-info">
                <div>
                  <span class="setting-name">开启免打扰</span>
                  <span class="setting-desc">在指定时段内不推送消息</span>
                </div>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="settings.dnd.enabled">
                <span class="slider"></span>
              </label>
            </div>
            <div class="dnd-time" v-if="settings.dnd.enabled">
              <input type="time" v-model="settings.dnd.start"> 至 <input type="time" v-model="settings.dnd.end">
            </div>
          </div>

          <!-- 提前提醒 -->
          <div class="settings-section">
            <h4>截止提前提醒</h4>
            <div class="remind-hours">
              <label v-for="h in [24, 12, 4, 1]" :key="h" class="checkbox-label">
                <input type="checkbox" :value="h" v-model="settings.deadline_remind_hours">
                <span>{{ h }}小时前</span>
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="resetSettings">重置默认</button>
          <button class="btn-primary" @click="saveSettings">保存设置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import request from '@/utils/request'

const showPanel = ref(false)
const showSettings = ref(false)
const activeTab = ref('all')
const notifications = ref([])
const unreadCount = ref(0)

const settings = ref({
  channels: { wechat: true, email: true, sms: false, in_app: true, app_push: true },
  types: { task_assigned: true, deadline_reminder: true, overdue_reminder: true, progress_urge: true, transfer_notify: true, daily_summary: true },
  dnd: { enabled: false, start: '22:00', end: '08:00' },
  deadline_remind_hours: [24, 4, 1]
})

const channels = [
  { code: 'wechat', name: '企业微信', icon: '💬', description: '通过企业微信应用推送' },
  { code: 'email', name: '邮件', icon: '📧', description: '发送到您的工作邮箱' },
  { code: 'sms', name: '短信', icon: '📱', description: '紧急事项短信通知' },
  { code: 'in_app', name: '站内消息', icon: '🔔', description: '系统内消息中心' },
  { code: 'app_push', name: 'APP推送', icon: '📲', description: '推送到移动APP' }
]

const reminderTypes = [
  { code: 'task_assigned', name: '任务分配', description: '新任务分配时通知', can_disable: true },
  { code: 'deadline_reminder', name: '截止提醒', description: '任务即将到期时提醒', can_disable: true },
  { code: 'overdue_reminder', name: '逾期提醒', description: '任务逾期时通知', can_disable: true },
  { code: 'progress_urge', name: '催办提醒', description: '收到催办时通知', can_disable: false },
  { code: 'transfer_notify', name: '转办通知', description: '收到转办任务时通知', can_disable: true },
  { code: 'daily_summary', name: '每日汇总', description: '每天早上发送任务汇总', can_disable: true }
]

const filteredNotifications = computed(() => {
  if (activeTab.value === 'unread') return notifications.value.filter(n => !n.is_read)
  return notifications.value
})

const togglePanel = () => { showPanel.value = !showPanel.value }
const openSettings = () => { showSettings.value = true; showPanel.value = false }

const getTypeIcon = (type) => {
  const icons = { task_assigned: '📋', deadline_24h: '⏰', deadline_4h: '⚠️', deadline_1h: '🔴', task_overdue: '❗', progress_urge: '📊', task_transferred: '📨', workflow_pending: '🔄', task_approved: '✅', task_rejected: '❌', daily_summary: '📅' }
  return icons[type] || '🔔'
}

const getTypeClass = (type) => {
  if (['task_overdue', 'deadline_1h', 'task_rejected'].includes(type)) return 'urgent'
  if (['deadline_4h', 'progress_urge'].includes(type)) return 'warning'
  if (['task_approved'].includes(type)) return 'success'
  return 'info'
}

const formatTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 172800000) return '昨天'
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

const handleClick = async (n) => {
  if (!n.is_read) {
    await markRead(n.id)
    n.is_read = true
    unreadCount.value--
  }
  if (n.data?.task_id) {
    window.location.href = `/task-center?task_id=${n.data.task_id}`
  }
}

const markRead = async (id) => {
  try { await request.post(`/api/v1/reminders/notifications/${id}/read`) } catch (e) {}
}

const markAllRead = async () => {
  try {
    await request.post('/api/v1/reminders/notifications/read-all')
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch (e) {}
}

const deleteNotification = async (id) => {
  try {
    await request.delete(`/api/v1/reminders/notifications/${id}`)
    notifications.value = notifications.value.filter(n => n.id !== id)
  } catch (e) {}
}

const viewAll = () => { window.location.href = '/notifications' }

const loadNotifications = async () => {
  try {
    const res = await request.get('/api/v1/reminders/notifications', { params: { page_size: 20 } })
    if (res.code === 200) {
      notifications.value = res.data.notifications
      unreadCount.value = res.data.unread_count
    }
  } catch (e) {
    // 模拟数据
    notifications.value = [
      { id: '1', type: 'task_assigned', title: '📋 新任务：机械结构设计', content: '张经理给您分配了新任务\n任务：机械结构设计\n截止：2025-01-05', created_at: new Date().toISOString(), is_read: false, data: { task_id: 1001 } },
      { id: '2', type: 'deadline_4h', title: '⚠️ 任务即将到期（4小时）', content: '您有任务即将在4小时内到期\n任务：电气原理图\n请尽快完成！', created_at: new Date(Date.now() - 3600000).toISOString(), is_read: false, data: { task_id: 1002 } },
      { id: '3', type: 'task_transferred', title: '📨 收到转办任务', content: '王工将任务转办给您\n任务：设备调试\n原因：出差无法处理', created_at: new Date(Date.now() - 7200000).toISOString(), is_read: true, data: { task_id: 1003 } }
    ]
    unreadCount.value = 2
  }
}

const loadSettings = async () => {
  try {
    const res = await request.get('/api/v1/reminders/settings')
    if (res.code === 200) settings.value = res.data
  } catch (e) {}
}

const saveSettings = async () => {
  try {
    await request.put('/api/v1/reminders/settings', settings.value)
    showSettings.value = false
    alert('设置已保存')
  } catch (e) { alert('保存失败') }
}

const resetSettings = async () => {
  if (confirm('确定重置为默认设置？')) {
    try {
      await request.post('/api/v1/reminders/settings/reset')
      await loadSettings()
      alert('已重置')
    } catch (e) {}
  }
}

// 点击外部关闭
const handleClickOutside = (e) => {
  if (showPanel.value && !e.target.closest('.notification-center')) showPanel.value = false
}

// 定时刷新
let refreshTimer = null

onMounted(() => {
  loadNotifications()
  loadSettings()
  document.addEventListener('click', handleClickOutside)
  refreshTimer = setInterval(loadNotifications, 60000) // 每分钟刷新
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.notification-center { position: relative; }
.notification-trigger { position: relative; cursor: pointer; padding: 8px; border-radius: 8px; transition: background 0.2s; }
.notification-trigger:hover { background: #F1F5F9; }
.notification-trigger svg { width: 24px; height: 24px; color: #64748B; }
.badge { position: absolute; top: 2px; right: 2px; min-width: 18px; height: 18px; background: #EF4444; color: white; font-size: 11px; font-weight: 600; border-radius: 9px; display: flex; align-items: center; justify-content: center; padding: 0 5px; }

.notification-panel { position: absolute; top: 100%; right: 0; width: 380px; background: white; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); z-index: 1000; overflow: hidden; margin-top: 8px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #E2E8F0; }
.panel-header h3 { font-size: 16px; font-weight: 600; }
.header-actions { display: flex; gap: 8px; }
.btn-text { background: none; border: none; color: #6366F1; font-size: 13px; cursor: pointer; }
.btn-icon { background: none; border: none; cursor: pointer; padding: 4px; }
.btn-icon svg { width: 18px; height: 18px; color: #64748B; }

.panel-tabs { display: flex; padding: 0 20px; border-bottom: 1px solid #E2E8F0; }
.tab { padding: 12px 16px; font-size: 14px; color: #64748B; background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.tab.active { color: #6366F1; border-bottom-color: #6366F1; }
.tab .count { background: #EF4444; color: white; font-size: 11px; padding: 2px 6px; border-radius: 10px; }

.panel-body { max-height: 400px; overflow-y: auto; }
.notification-list { padding: 8px; }
.notification-item { display: flex; align-items: flex-start; gap: 12px; padding: 12px; border-radius: 10px; cursor: pointer; transition: background 0.2s; position: relative; }
.notification-item:hover { background: #F8FAFC; }
.notification-item.unread { background: #EEF2FF; }
.notification-item.unread:hover { background: #E0E7FF; }
.notification-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.notification-icon.urgent { background: #FEE2E2; }
.notification-icon.warning { background: #FEF3C7; }
.notification-icon.success { background: #DCFCE7; }
.notification-icon.info { background: #E0E7FF; }
.notification-content { flex: 1; min-width: 0; }
.notification-title { font-size: 14px; font-weight: 600; color: #0F172A; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.notification-text { font-size: 13px; color: #64748B; line-height: 1.4; margin-bottom: 4px; }
.notification-time { font-size: 12px; color: #94A3B8; }
.notification-close { position: absolute; top: 8px; right: 8px; width: 20px; height: 20px; border: none; background: none; color: #94A3B8; cursor: pointer; font-size: 16px; opacity: 0; transition: opacity 0.2s; }
.notification-item:hover .notification-close { opacity: 1; }

.empty-state { text-align: center; padding: 40px; color: #64748B; }
.empty-icon { font-size: 32px; margin-bottom: 8px; }

.panel-footer { padding: 12px 20px; border-top: 1px solid #E2E8F0; text-align: center; }
.btn-link { background: none; border: none; color: #6366F1; font-size: 14px; cursor: pointer; }

/* 设置弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 2000; display: flex; align-items: center; justify-content: center; }
.settings-modal { background: white; border-radius: 20px; width: 500px; max-width: 90vw; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #E2E8F0; }
.modal-header h3 { font-size: 18px; font-weight: 600; }
.modal-close { width: 32px; height: 32px; border: none; background: #F1F5F9; border-radius: 8px; font-size: 20px; cursor: pointer; }
.modal-body { flex: 1; overflow-y: auto; padding: 24px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 24px; border-top: 1px solid #E2E8F0; }
.btn-primary { padding: 10px 20px; background: #6366F1; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
.btn-secondary { padding: 10px 20px; background: #F1F5F9; color: #374151; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }

.settings-section { margin-bottom: 24px; }
.settings-section h4 { font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 12px; }
.setting-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #F1F5F9; }
.setting-info { display: flex; align-items: center; gap: 12px; }
.setting-icon { font-size: 20px; }
.setting-name { display: block; font-size: 14px; font-weight: 500; color: #0F172A; }
.setting-desc { font-size: 12px; color: #64748B; }
.always-on { font-size: 12px; color: #10B981; }

.switch { position: relative; width: 44px; height: 24px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; inset: 0; background: #CBD5E1; border-radius: 24px; transition: 0.3s; }
.slider:before { position: absolute; content: ""; width: 18px; height: 18px; left: 3px; bottom: 3px; background: white; border-radius: 50%; transition: 0.3s; }
.switch input:checked + .slider { background: #6366F1; }
.switch input:checked + .slider:before { transform: translateX(20px); }

.dnd-time { display: flex; align-items: center; gap: 12px; margin-top: 12px; padding: 12px; background: #F8FAFC; border-radius: 8px; }
.dnd-time input { padding: 8px 12px; border: 1px solid #E2E8F0; border-radius: 6px; }

.remind-hours { display: flex; gap: 16px; flex-wrap: wrap; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #374151; cursor: pointer; }
.checkbox-label input { width: 18px; height: 18px; accent-color: #6366F1; }

.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
