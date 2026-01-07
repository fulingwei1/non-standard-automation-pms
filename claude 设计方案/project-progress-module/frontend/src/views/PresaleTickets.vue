<template>
  <div class="presale-tickets">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>{{ isSales ? '我的支持申请' : '支持工单' }}</h1>
          <p class="subtitle">{{ isSales ? '查看和管理您提交的技术支持申请' : '处理销售提交的技术支持工单' }}</p>
        </div>
        <div class="header-right">
          <button class="btn-secondary" @click="refreshData">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
            刷新
          </button>
          <button class="btn-primary" v-if="isSales" @click="showCreateModal = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            新建申请
          </button>
        </div>
      </div>
    </header>

    <!-- 统计卡片 -->
    <section class="stats-section">
      <div class="stats-grid">
        <div class="stat-card" @click="filterStatus = ''">
          <div class="stat-icon all"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.total }}</span><span class="stat-label">全部工单</span></div>
        </div>
        <div class="stat-card pending" @click="filterStatus = 'pending'">
          <div class="stat-icon pending"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.pending }}</span><span class="stat-label">待接单</span></div>
        </div>
        <div class="stat-card processing" @click="filterStatus = 'processing'">
          <div class="stat-icon processing"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.processing }}</span><span class="stat-label">处理中</span></div>
        </div>
        <div class="stat-card completed" @click="filterStatus = 'completed'">
          <div class="stat-icon completed"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.completed }}</span><span class="stat-label">已完成</span></div>
        </div>
        <div class="stat-card" v-if="!isSales">
          <div class="stat-icon response"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.avgResponseHours }}h</span><span class="stat-label">平均响应</span></div>
        </div>
      </div>
    </section>

    <!-- 筛选和列表 -->
    <section class="list-section">
      <div class="list-header">
        <div class="tabs">
          <button class="tab" :class="{ active: filterType === '' }" @click="filterType = ''">全部</button>
          <button class="tab" v-for="t in ticketTypes" :key="t.value" :class="{ active: filterType === t.value }" @click="filterType = t.value">
            {{ t.icon }} {{ t.label }}
          </button>
        </div>
        <div class="filters">
          <select v-model="filterUrgency">
            <option value="">紧急程度</option>
            <option value="very_urgent">非常紧急</option>
            <option value="urgent">紧急</option>
            <option value="normal">普通</option>
          </select>
          <div class="search-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" v-model="searchKeyword" placeholder="搜索工单...">
          </div>
        </div>
      </div>

      <!-- 工单列表 -->
      <div class="ticket-list">
        <div class="ticket-card" v-for="ticket in filteredTickets" :key="ticket.id" 
             :class="{ urgent: ticket.urgency === 'urgent' || ticket.urgency === 'very_urgent' }"
             @click="openTicketDetail(ticket)">
          <div class="ticket-left">
            <div class="ticket-header">
              <span class="ticket-no">{{ ticket.ticket_no }}</span>
              <span class="ticket-type" :class="ticket.ticket_type">{{ ticket.ticket_type_label }}</span>
              <span class="ticket-urgency" :class="ticket.urgency">{{ ticket.urgency_label }}</span>
            </div>
            <h3 class="ticket-title">{{ ticket.title }}</h3>
            <div class="ticket-meta">
              <span class="meta-item" v-if="ticket.customer_name">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
                {{ ticket.customer_name }}
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                {{ isSales ? ticket.assignee_name || '待分配' : ticket.applicant_name }}
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                {{ formatDateTime(ticket.apply_time) }}
              </span>
              <span class="meta-item deadline" :class="{ overdue: isOverdue(ticket.deadline) }">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/></svg>
                截止: {{ formatDeadline(ticket.deadline) }}
              </span>
            </div>
          </div>
          <div class="ticket-right">
            <div class="ticket-status" :class="ticket.status">{{ ticket.status_label }}</div>
            <div class="ticket-progress" v-if="ticket.progress_percent > 0">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: ticket.progress_percent + '%' }"></div>
              </div>
              <span>{{ ticket.progress_percent }}%</span>
            </div>
            <div class="ticket-actions" v-if="!isSales && ticket.status === 'pending'">
              <button class="btn-accept" @click.stop="acceptTicket(ticket)">接单</button>
            </div>
          </div>
        </div>

        <div class="empty-state" v-if="filteredTickets.length === 0">
          <div class="empty-icon">📋</div>
          <h3>暂无工单</h3>
          <p v-if="isSales">您还没有提交过技术支持申请</p>
          <p v-else>当前没有需要处理的工单</p>
        </div>
      </div>
    </section>

    <!-- 工单详情抽屉 -->
    <div class="drawer-overlay" v-if="selectedTicket" @click="selectedTicket = null">
      <div class="drawer" @click.stop>
        <div class="drawer-header">
          <div class="drawer-title">
            <span class="ticket-type-badge" :class="selectedTicket.ticket_type">{{ selectedTicket.ticket_type_label }}</span>
            <h2>{{ selectedTicket.ticket_no }}</h2>
          </div>
          <button class="drawer-close" @click="selectedTicket = null">×</button>
        </div>
        
        <div class="drawer-body">
          <div class="detail-section">
            <div class="urgency-badge" :class="selectedTicket.urgency">{{ selectedTicket.urgency_label }}</div>
            <h3 class="detail-title">{{ selectedTicket.title }}</h3>
            <p class="detail-desc">{{ selectedTicket.description }}</p>
          </div>

          <div class="detail-section">
            <h4>基本信息</h4>
            <div class="info-grid">
              <div class="info-item"><span class="label">客户</span><span class="value">{{ selectedTicket.customer_name || '-' }}</span></div>
              <div class="info-item"><span class="label">申请人</span><span class="value">{{ selectedTicket.applicant_name }}</span></div>
              <div class="info-item"><span class="label">处理人</span><span class="value">{{ selectedTicket.assignee_name || '待分配' }}</span></div>
              <div class="info-item"><span class="label">状态</span><span class="value status" :class="selectedTicket.status">{{ selectedTicket.status_label }}</span></div>
              <div class="info-item"><span class="label">申请时间</span><span class="value">{{ formatDateTime(selectedTicket.apply_time) }}</span></div>
              <div class="info-item"><span class="label">截止时间</span><span class="value" :class="{ overdue: isOverdue(selectedTicket.deadline) }">{{ formatDateTime(selectedTicket.deadline) }}</span></div>
              <div class="info-item" v-if="selectedTicket.accept_time"><span class="label">接单时间</span><span class="value">{{ formatDateTime(selectedTicket.accept_time) }}</span></div>
              <div class="info-item" v-if="selectedTicket.actual_hours"><span class="label">实际工时</span><span class="value">{{ selectedTicket.actual_hours }}h</span></div>
            </div>
          </div>

          <div class="detail-section" v-if="selectedTicket.progress_records?.length">
            <h4>处理进度</h4>
            <div class="progress-timeline">
              <div class="timeline-item" v-for="(record, idx) in selectedTicket.progress_records" :key="idx">
                <div class="timeline-dot"></div>
                <div class="timeline-content">
                  <span class="timeline-time">{{ record.time }}</span>
                  <span class="timeline-operator">{{ record.operator }}</span>
                  <p class="timeline-text">{{ record.content }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="detail-section" v-if="selectedTicket.deliverables?.length">
            <h4>交付物</h4>
            <div class="deliverable-list">
              <div class="deliverable-item" v-for="file in selectedTicket.deliverables" :key="file.name">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span>{{ file.name }}</span>
                <button class="btn-download">下载</button>
              </div>
            </div>
          </div>

          <!-- 售前工程师操作区 -->
          <div class="action-section" v-if="!isSales && selectedTicket.status !== 'closed'">
            <div class="action-group" v-if="selectedTicket.status === 'pending'">
              <button class="btn-primary" @click="acceptTicket(selectedTicket)">接单处理</button>
            </div>
            <div class="action-group" v-if="selectedTicket.status === 'processing' || selectedTicket.status === 'accepted'">
              <div class="progress-update">
                <label>更新进度</label>
                <input type="range" min="0" max="100" step="10" v-model="updateProgress">
                <span>{{ updateProgress }}%</span>
                <button class="btn-secondary" @click="submitProgress">更新</button>
              </div>
              <textarea v-model="progressComment" placeholder="进度说明..."></textarea>
              <div class="action-buttons">
                <button class="btn-secondary" @click="uploadDeliverable">上传交付物</button>
                <button class="btn-primary" @click="completeTicket">完成工单</button>
              </div>
            </div>
          </div>

          <!-- 销售评价区 -->
          <div class="action-section" v-if="isSales && selectedTicket.status === 'completed'">
            <h4>服务评价</h4>
            <div class="rating-stars">
              <span v-for="i in 5" :key="i" class="star" :class="{ active: feedbackScore >= i }" @click="feedbackScore = i">★</span>
            </div>
            <textarea v-model="feedbackComment" placeholder="请输入您的反馈意见..."></textarea>
            <button class="btn-primary" @click="submitFeedback">提交评价</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建工单弹窗 -->
    <div class="modal-overlay" v-if="showCreateModal" @click="showCreateModal = false">
      <div class="modal create-ticket-modal" @click.stop>
        <div class="modal-header">
          <h3>新建技术支持申请</h3>
          <button @click="showCreateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>申请类型 <span class="required">*</span></label>
            <div class="type-options">
              <div class="type-option" v-for="t in ticketTypes" :key="t.value"
                   :class="{ active: newTicket.ticket_type === t.value }"
                   @click="newTicket.ticket_type = t.value">
                <span class="type-icon">{{ t.icon }}</span>
                <span class="type-name">{{ t.label }}</span>
                <span class="type-desc">{{ t.desc }}</span>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>标题 <span class="required">*</span></label>
            <input type="text" v-model="newTicket.title" placeholder="简要描述您的需求">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>客户名称</label>
              <input type="text" v-model="newTicket.customer_name" placeholder="客户公司名称">
            </div>
            <div class="form-group">
              <label>紧急程度</label>
              <select v-model="newTicket.urgency">
                <option value="normal">普通</option>
                <option value="urgent">紧急</option>
                <option value="very_urgent">非常紧急</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>详细描述</label>
            <textarea v-model="newTicket.description" rows="5" placeholder="请详细描述您的需求、背景信息、期望结果等"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>期望完成日期</label>
              <input type="date" v-model="newTicket.expected_date">
            </div>
            <div class="form-group">
              <label>附件</label>
              <button class="btn-upload">+ 上传附件</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn-primary" @click="createTicket" :disabled="!newTicket.title || !newTicket.ticket_type">提交申请</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <transition name="toast">
      <div class="toast" v-if="toastMessage" :class="toastType">{{ toastMessage }}</div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import request from '@/utils/request'

const route = useRoute()

// 角色判断
const isSales = computed(() => route.query.role === 'sales' || false)

// 数据
const tickets = ref([])
const stats = ref({ total: 0, pending: 0, processing: 0, completed: 0, avgResponseHours: 0 })

// 筛选
const filterType = ref('')
const filterStatus = ref('')
const filterUrgency = ref('')
const searchKeyword = ref('')

// 详情
const selectedTicket = ref(null)
const updateProgress = ref(0)
const progressComment = ref('')
const feedbackScore = ref(0)
const feedbackComment = ref('')

// 新建
const showCreateModal = ref(false)
const newTicket = ref({
  title: '',
  ticket_type: '',
  urgency: 'normal',
  customer_name: '',
  description: '',
  expected_date: ''
})

// 提示
const toastMessage = ref('')
const toastType = ref('success')

// 工单类型
const ticketTypes = [
  { value: 'consult', label: '技术咨询', icon: '💬', desc: '技术问题解答' },
  { value: 'survey', label: '需求调研', icon: '📋', desc: '现场调研需求' },
  { value: 'solution', label: '方案设计', icon: '📝', desc: '技术方案编制' },
  { value: 'quotation', label: '报价支持', icon: '💰', desc: '成本估算报价' },
  { value: 'tender', label: '投标支持', icon: '🏆', desc: '投标技术支持' },
  { value: 'meeting', label: '技术交流', icon: '🤝', desc: '客户技术交流' },
  { value: 'site_visit', label: '现场勘查', icon: '🔍', desc: '现场勘查评估' }
]

// 计算属性
const filteredTickets = computed(() => {
  let result = tickets.value
  if (filterType.value) result = result.filter(t => t.ticket_type === filterType.value)
  if (filterStatus.value) result = result.filter(t => t.status === filterStatus.value)
  if (filterUrgency.value) result = result.filter(t => t.urgency === filterUrgency.value)
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(t => t.title.toLowerCase().includes(kw) || t.customer_name?.toLowerCase().includes(kw))
  }
  return result
})

// 方法
const formatDateTime = (dt) => dt ? new Date(dt).toLocaleString('zh-CN') : '-'
const formatDeadline = (dt) => {
  if (!dt) return '-'
  const d = new Date(dt)
  const now = new Date()
  const diff = d - now
  if (diff < 0) return '已逾期'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时'
  return d.toLocaleDateString('zh-CN')
}
const isOverdue = (dt) => dt && new Date(dt) < new Date()

const showToast = (msg, type = 'success') => {
  toastMessage.value = msg
  toastType.value = type
  setTimeout(() => { toastMessage.value = '' }, 3000)
}

const openTicketDetail = async (ticket) => {
  try {
    const res = await request.get(`/api/v1/presale/tickets/${ticket.id}`)
    if (res.code === 200) {
      selectedTicket.value = res.data
      updateProgress.value = res.data.progress_percent || 0
    }
  } catch (e) {
    selectedTicket.value = ticket
  }
}

const acceptTicket = async (ticket) => {
  try {
    await request.post(`/api/v1/presale/tickets/${ticket.id}/accept`)
    showToast('接单成功')
    ticket.status = 'accepted'
    ticket.status_label = '已接单'
    selectedTicket.value = null
    loadData()
  } catch (e) {
    showToast('接单失败', 'error')
  }
}

const submitProgress = async () => {
  if (!selectedTicket.value) return
  try {
    await request.post(`/api/v1/presale/tickets/${selectedTicket.value.id}/progress`, {
      progress_percent: updateProgress.value,
      comment: progressComment.value
    })
    showToast('进度已更新')
    progressComment.value = ''
  } catch (e) {
    showToast('更新失败', 'error')
  }
}

const completeTicket = async () => {
  if (!selectedTicket.value) return
  const hours = prompt('请输入实际工时:', '4')
  if (hours === null) return
  try {
    await request.post(`/api/v1/presale/tickets/${selectedTicket.value.id}/complete`, {
      actual_hours: parseFloat(hours)
    })
    showToast('工单已完成')
    selectedTicket.value = null
    loadData()
  } catch (e) {
    showToast('操作失败', 'error')
  }
}

const uploadDeliverable = () => {
  alert('上传交付物功能开发中')
}

const submitFeedback = async () => {
  if (!selectedTicket.value || feedbackScore.value === 0) return
  try {
    await request.post(`/api/v1/presale/tickets/${selectedTicket.value.id}/feedback`, {
      satisfaction_score: feedbackScore.value,
      feedback: feedbackComment.value
    })
    showToast('感谢您的评价')
    selectedTicket.value = null
    loadData()
  } catch (e) {
    showToast('提交失败', 'error')
  }
}

const createTicket = async () => {
  if (!newTicket.value.title || !newTicket.value.ticket_type) return
  try {
    await request.post('/api/v1/presale/tickets', newTicket.value)
    showToast('申请已提交')
    showCreateModal.value = false
    newTicket.value = { title: '', ticket_type: '', urgency: 'normal', customer_name: '', description: '', expected_date: '' }
    loadData()
  } catch (e) {
    showToast('提交失败', 'error')
  }
}

const loadData = async () => {
  try {
    const res = await request.get('/api/v1/presale/tickets', { params: { role: isSales.value ? 'sales' : 'presale' } })
    if (res.code === 200) {
      tickets.value = res.data.tickets
      calculateStats()
    }
  } catch (e) {
    tickets.value = getMockData()
    calculateStats()
  }
}

const calculateStats = () => {
  stats.value = {
    total: tickets.value.length,
    pending: tickets.value.filter(t => t.status === 'pending').length,
    processing: tickets.value.filter(t => ['accepted', 'processing'].includes(t.status)).length,
    completed: tickets.value.filter(t => t.status === 'completed' || t.status === 'closed').length,
    avgResponseHours: 1.8
  }
}

const refreshData = () => loadData()

const getMockData = () => [
  { id: 1001, ticket_no: 'PS20250103001', title: 'XX汽车传感器测试设备技术咨询', ticket_type: 'consult', ticket_type_label: '技术咨询', urgency: 'urgent', urgency_label: '紧急', customer_name: 'XX汽车科技', applicant_name: '张销售', assignee_name: '王工', apply_time: '2025-01-03 09:30:00', deadline: '2025-01-03 11:30:00', status: 'processing', status_label: '处理中', progress_percent: 60 },
  { id: 1002, ticket_no: 'PS20250103002', title: 'YY电子连接器测试设备方案设计', ticket_type: 'solution', ticket_type_label: '方案设计', urgency: 'normal', urgency_label: '普通', customer_name: 'YY电子科技', applicant_name: '李销售', assignee_name: '王工', apply_time: '2025-01-02 14:00:00', deadline: '2025-01-07 14:00:00', status: 'processing', status_label: '处理中', progress_percent: 30 },
  { id: 1003, ticket_no: 'PS20250103003', title: 'ZZ医疗设备测试线技术交流', ticket_type: 'meeting', ticket_type_label: '技术交流', urgency: 'normal', urgency_label: '普通', customer_name: 'ZZ医疗器械', applicant_name: '张销售', assignee_name: null, apply_time: '2025-01-03 10:00:00', deadline: '2025-01-04 10:00:00', status: 'pending', status_label: '待接单', progress_percent: 0 }
]

onMounted(() => loadData())
</script>

<style scoped>
.presale-tickets { min-height: 100vh; background: #F8FAFC; }
.page-header { background: white; padding: 24px 32px; border-bottom: 1px solid #E2E8F0; }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.header-content h1 { font-size: 24px; font-weight: 700; color: #0F172A; }
.subtitle { font-size: 14px; color: #64748B; margin-top: 4px; }
.header-right { display: flex; gap: 12px; }
.btn-primary, .btn-secondary { display: flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 10px; font-weight: 600; cursor: pointer; border: none; transition: all 0.2s; }
.btn-primary { background: linear-gradient(135deg, #6366F1, #4F46E5); color: white; }
.btn-secondary { background: white; color: #374151; border: 1px solid #E2E8F0; }
.btn-primary svg, .btn-secondary svg { width: 18px; height: 18px; }

.stats-section { padding: 24px 32px; }
.stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.stat-card { background: white; border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 16px; cursor: pointer; transition: all 0.2s; }
.stat-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-2px); }
.stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-icon svg { width: 24px; height: 24px; color: white; }
.stat-icon.all { background: linear-gradient(135deg, #6366F1, #4F46E5); }
.stat-icon.pending { background: linear-gradient(135deg, #F59E0B, #D97706); }
.stat-icon.processing { background: linear-gradient(135deg, #3B82F6, #2563EB); }
.stat-icon.completed { background: linear-gradient(135deg, #10B981, #059669); }
.stat-icon.response { background: linear-gradient(135deg, #8B5CF6, #7C3AED); }
.stat-value { font-size: 28px; font-weight: 700; color: #0F172A; display: block; }
.stat-label { font-size: 13px; color: #64748B; }

.list-section { padding: 0 32px 32px; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 16px; }
.tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.tab { padding: 8px 16px; background: white; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 13px; color: #64748B; cursor: pointer; }
.tab.active { background: #6366F1; color: white; border-color: #6366F1; }
.filters { display: flex; gap: 12px; }
.filters select { padding: 8px 16px; border: 1px solid #E2E8F0; border-radius: 8px; }
.search-box { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: white; border: 1px solid #E2E8F0; border-radius: 8px; }
.search-box svg { width: 16px; height: 16px; color: #94A3B8; }
.search-box input { border: none; outline: none; font-size: 14px; width: 150px; }

.ticket-list { display: flex; flex-direction: column; gap: 12px; }
.ticket-card { background: white; border-radius: 16px; padding: 20px; display: flex; justify-content: space-between; cursor: pointer; transition: all 0.2s; border: 2px solid transparent; }
.ticket-card:hover { border-color: #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.ticket-card.urgent { border-left: 4px solid #EF4444; }
.ticket-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.ticket-no { font-size: 12px; color: #94A3B8; font-family: monospace; }
.ticket-type { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; color: white; }
.ticket-type.consult { background: #3B82F6; }
.ticket-type.solution { background: #8B5CF6; }
.ticket-type.survey { background: #10B981; }
.ticket-type.quotation { background: #F59E0B; }
.ticket-type.tender { background: #EC4899; }
.ticket-type.meeting { background: #14B8A6; }
.ticket-type.site_visit { background: #6366F1; }
.ticket-urgency { padding: 4px 10px; border-radius: 6px; font-size: 12px; }
.ticket-urgency.normal { background: #F1F5F9; color: #64748B; }
.ticket-urgency.urgent { background: #FEF3C7; color: #92400E; }
.ticket-urgency.very_urgent { background: #FEE2E2; color: #991B1B; }
.ticket-title { font-size: 16px; font-weight: 600; color: #0F172A; margin-bottom: 10px; }
.ticket-meta { display: flex; flex-wrap: wrap; gap: 16px; }
.meta-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #64748B; }
.meta-item svg { width: 14px; height: 14px; }
.meta-item.deadline.overdue { color: #DC2626; }
.ticket-right { display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }
.ticket-status { padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500; }
.ticket-status.pending { background: #FEF3C7; color: #92400E; }
.ticket-status.accepted, .ticket-status.processing { background: #DBEAFE; color: #1E40AF; }
.ticket-status.review { background: #E0E7FF; color: #4338CA; }
.ticket-status.completed { background: #D1FAE5; color: #065F46; }
.ticket-status.closed { background: #F1F5F9; color: #475569; }
.ticket-progress { display: flex; align-items: center; gap: 8px; }
.ticket-progress .progress-bar { width: 80px; height: 6px; background: #E2E8F0; border-radius: 3px; overflow: hidden; }
.ticket-progress .progress-fill { height: 100%; background: #6366F1; }
.ticket-progress span { font-size: 12px; font-weight: 600; color: #6366F1; }
.btn-accept { padding: 8px 20px; background: #10B981; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }

.empty-state { text-align: center; padding: 60px; color: #64748B; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }

/* 抽屉 */
.drawer-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; justify-content: flex-end; }
.drawer { width: 560px; max-width: 100%; background: white; height: 100%; overflow-y: auto; }
.drawer-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #E2E8F0; }
.drawer-title { display: flex; align-items: center; gap: 12px; }
.drawer-title h2 { font-size: 16px; color: #64748B; }
.ticket-type-badge { padding: 6px 12px; border-radius: 6px; font-size: 13px; color: white; }
.drawer-close { width: 32px; height: 32px; border: none; background: #F1F5F9; border-radius: 8px; font-size: 20px; cursor: pointer; }
.drawer-body { padding: 24px; }
.detail-section { margin-bottom: 24px; }
.detail-section h4 { font-size: 13px; font-weight: 600; color: #64748B; margin-bottom: 12px; }
.urgency-badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; margin-bottom: 10px; }
.urgency-badge.normal { background: #F1F5F9; color: #64748B; }
.urgency-badge.urgent { background: #FEF3C7; color: #92400E; }
.urgency-badge.very_urgent { background: #FEE2E2; color: #991B1B; }
.detail-title { font-size: 20px; font-weight: 700; color: #0F172A; margin-bottom: 10px; }
.detail-desc { font-size: 14px; color: #475569; line-height: 1.6; white-space: pre-wrap; }
.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-item .label { font-size: 12px; color: #94A3B8; }
.info-item .value { font-size: 14px; font-weight: 500; color: #0F172A; }
.info-item .value.overdue { color: #DC2626; }
.info-item .value.status { padding: 4px 10px; border-radius: 6px; display: inline-block; width: fit-content; }

.progress-timeline { border-left: 2px solid #E2E8F0; padding-left: 20px; }
.timeline-item { position: relative; margin-bottom: 16px; }
.timeline-dot { position: absolute; left: -26px; top: 4px; width: 10px; height: 10px; background: #6366F1; border-radius: 50%; }
.timeline-time { font-size: 12px; color: #94A3B8; }
.timeline-operator { font-size: 12px; color: #6366F1; margin-left: 8px; }
.timeline-text { font-size: 14px; color: #374151; margin-top: 4px; }

.deliverable-list { display: flex; flex-direction: column; gap: 8px; }
.deliverable-item { display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: #F8FAFC; border-radius: 8px; }
.deliverable-item svg { width: 20px; height: 20px; color: #64748B; }
.deliverable-item span { flex: 1; font-size: 14px; }
.btn-download { padding: 6px 12px; background: #6366F1; color: white; border: none; border-radius: 6px; font-size: 12px; cursor: pointer; }

.action-section { padding-top: 24px; border-top: 1px solid #E2E8F0; }
.action-group { margin-bottom: 16px; }
.progress-update { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.progress-update label { font-size: 14px; color: #374151; }
.progress-update input[type="range"] { flex: 1; }
.progress-update span { font-weight: 600; color: #6366F1; }
.action-section textarea { width: 100%; padding: 12px; border: 1px solid #E2E8F0; border-radius: 8px; min-height: 80px; margin-bottom: 12px; }
.action-buttons { display: flex; gap: 12px; }

.rating-stars { margin-bottom: 16px; }
.star { font-size: 32px; color: #E2E8F0; cursor: pointer; transition: color 0.2s; }
.star.active { color: #F59E0B; }

/* 新建弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: center; justify-content: center; }
.modal { background: white; border-radius: 20px; max-height: 90vh; overflow-y: auto; }
.create-ticket-modal { width: 640px; max-width: 95%; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #E2E8F0; }
.modal-header h3 { font-size: 18px; font-weight: 600; }
.modal-header button { width: 32px; height: 32px; border: none; background: #F1F5F9; border-radius: 8px; font-size: 20px; cursor: pointer; }
.modal-body { padding: 24px; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px; }
.required { color: #EF4444; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 12px 16px; border: 1px solid #E2E8F0; border-radius: 10px; font-size: 14px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.type-options { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.type-option { padding: 12px; border: 2px solid #E2E8F0; border-radius: 12px; text-align: center; cursor: pointer; transition: all 0.2s; }
.type-option:hover { border-color: #6366F1; }
.type-option.active { border-color: #6366F1; background: #EEF2FF; }
.type-icon { font-size: 24px; display: block; margin-bottom: 6px; }
.type-name { font-size: 13px; font-weight: 600; color: #0F172A; display: block; }
.type-desc { font-size: 11px; color: #94A3B8; display: block; margin-top: 4px; }

.btn-upload { padding: 12px 20px; border: 1px dashed #CBD5E1; background: white; border-radius: 10px; color: #64748B; cursor: pointer; width: 100%; }

.modal-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 24px; border-top: 1px solid #E2E8F0; }

/* Toast */
.toast { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); padding: 12px 24px; background: #10B981; color: white; border-radius: 10px; font-weight: 500; z-index: 2000; }
.toast.error { background: #EF4444; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 20px); }

@media (max-width: 1024px) { .stats-grid { grid-template-columns: repeat(3, 1fr); } .type-options { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } .drawer { width: 100%; } }
</style>
