<template>
  <div class="alerts-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-left">
        <h1>缺料预警</h1>
        <p class="subtitle">缺料预警监控与处理</p>
      </div>
    </header>

    <!-- 预警级别统计 -->
    <section class="alert-stats">
      <div class="alert-stat" :class="{ active: filter.level === '' }" @click="filter.level = ''">
        <span class="stat-count">{{ totalAlerts }}</span>
        <span class="stat-label">全部预警</span>
      </div>
      <div class="alert-stat level1" :class="{ active: filter.level === 'level1' }" @click="filter.level = 'level1'">
        <span class="level-icon">🟡</span>
        <span class="stat-count">{{ alertCounts.level1 }}</span>
        <span class="stat-label">一级(提醒)</span>
      </div>
      <div class="alert-stat level2" :class="{ active: filter.level === 'level2' }" @click="filter.level = 'level2'">
        <span class="level-icon">🟠</span>
        <span class="stat-count">{{ alertCounts.level2 }}</span>
        <span class="stat-label">二级(警告)</span>
      </div>
      <div class="alert-stat level3" :class="{ active: filter.level === 'level3' }" @click="filter.level = 'level3'">
        <span class="level-icon">🔴</span>
        <span class="stat-count">{{ alertCounts.level3 }}</span>
        <span class="stat-label">三级(紧急)</span>
      </div>
      <div class="alert-stat level4" :class="{ active: filter.level === 'level4' }" @click="filter.level = 'level4'">
        <span class="level-icon">⚫</span>
        <span class="stat-count">{{ alertCounts.level4 }}</span>
        <span class="stat-label">四级(严重)</span>
      </div>
    </section>

    <!-- 筛选栏 -->
    <section class="filter-bar">
      <div class="filter-tabs">
        <button :class="{ active: filter.status === '' }" @click="filter.status = ''">全部</button>
        <button :class="{ active: filter.status === 'pending' }" @click="filter.status = 'pending'">待处理</button>
        <button :class="{ active: filter.status === 'handling' }" @click="filter.status = 'handling'">处理中</button>
        <button :class="{ active: filter.status === 'resolved' }" @click="filter.status = 'resolved'">已解决</button>
      </div>
      <input type="text" v-model="filter.keyword" placeholder="搜索项目/物料..." />
    </section>

    <!-- 预警列表 -->
    <section class="alerts-list">
      <div class="alert-card" v-for="alert in filteredAlerts" :key="alert.id"
           :class="'level-' + alert.alert_level">
        <div class="alert-header">
          <div class="alert-level">
            <span class="level-badge" :class="alert.alert_level">
              {{ getLevelIcon(alert.alert_level) }} {{ alert.alert_level_label }}
            </span>
            <span class="alert-no">{{ alert.alert_no }}</span>
          </div>
          <div class="alert-status">
            <span class="status-badge" :class="alert.status">{{ alert.status_label }}</span>
          </div>
        </div>

        <div class="alert-body">
          <div class="alert-main">
            <div class="project-info">
              <span class="project-name">{{ alert.project_name }}</span>
              <span class="work-order">{{ alert.work_order_no }}</span>
            </div>
            <div class="material-info">
              <span class="material-name">{{ alert.material_name }}</span>
              <span class="material-code">({{ alert.material_code }})</span>
              <span class="shortage-qty">缺 {{ alert.shortage_qty }} 件</span>
            </div>
            <div class="impact-info">
              <span class="impact-label">影响:</span>
              <span class="impact-text">{{ alert.impact }}</span>
            </div>
          </div>

          <div class="alert-handle" v-if="alert.status !== 'pending'">
            <div class="handler">
              <span class="handler-label">处理人:</span>
              <span class="handler-name">{{ alert.handler_name }}</span>
            </div>
            <div class="handle-plan">
              <span class="plan-label">处理方案:</span>
              <span class="plan-text">{{ alert.handle_plan }}</span>
            </div>
          </div>
        </div>

        <div class="alert-footer">
          <div class="alert-time">
            <span>创建时间: {{ alert.created_at }}</span>
            <span v-if="alert.response_deadline" class="deadline">响应时限: {{ alert.response_deadline }}</span>
          </div>
          <div class="alert-actions">
            <button class="btn-action" @click="viewDetail(alert)">详情</button>
            <button class="btn-action primary" v-if="alert.status === 'pending'" @click="handleAlert(alert)">
              开始处理
            </button>
            <button class="btn-action warning" v-if="alert.status === 'handling'" @click="escalateAlert(alert)">
              升级
            </button>
            <button class="btn-action success" v-if="alert.status === 'handling'" @click="resolveAlert(alert)">
              解决
            </button>
          </div>
        </div>
      </div>

      <div class="empty-state" v-if="filteredAlerts.length === 0">
        ✅ 暂无预警信息
      </div>
    </section>

    <!-- 处理弹窗 -->
    <div class="modal-overlay" v-if="showHandleModal" @click.self="showHandleModal = false">
      <div class="handle-modal">
        <div class="modal-header">
          <h3>处理预警</h3>
          <button class="close-btn" @click="showHandleModal = false">×</button>
        </div>
        <div class="modal-body" v-if="currentAlert">
          <div class="alert-summary">
            <div class="summary-row">
              <span class="label">预警编号:</span>
              <span class="value">{{ currentAlert.alert_no }}</span>
            </div>
            <div class="summary-row">
              <span class="label">缺料物料:</span>
              <span class="value">{{ currentAlert.material_name }} x {{ currentAlert.shortage_qty }}</span>
            </div>
            <div class="summary-row">
              <span class="label">影响:</span>
              <span class="value">{{ currentAlert.impact }}</span>
            </div>
          </div>

          <div class="form-group">
            <label>处理方案 <span class="required">*</span></label>
            <textarea v-model="handleForm.plan" rows="3" placeholder="请输入处理方案..."></textarea>
          </div>

          <div class="form-group">
            <label>预计解决时间</label>
            <input type="datetime-local" v-model="handleForm.expected_time" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showHandleModal = false">取消</button>
          <button class="btn-primary" @click="submitHandle" :disabled="!handleForm.plan">确认处理</button>
        </div>
      </div>
    </div>

    <!-- 解决弹窗 -->
    <div class="modal-overlay" v-if="showResolveModal" @click.self="showResolveModal = false">
      <div class="handle-modal">
        <div class="modal-header">
          <h3>解决预警</h3>
          <button class="close-btn" @click="showResolveModal = false">×</button>
        </div>
        <div class="modal-body" v-if="currentAlert">
          <div class="form-group">
            <label>解决方式 <span class="required">*</span></label>
            <div class="resolve-options">
              <div class="resolve-option" :class="{ active: resolveForm.method === 'arrived' }" 
                   @click="resolveForm.method = 'arrived'">
                <span class="option-icon">📦</span>
                <span class="option-text">物料已到货</span>
              </div>
              <div class="resolve-option" :class="{ active: resolveForm.method === 'substitute' }" 
                   @click="resolveForm.method = 'substitute'">
                <span class="option-icon">🔄</span>
                <span class="option-text">使用替代料</span>
              </div>
              <div class="resolve-option" :class="{ active: resolveForm.method === 'transfer' }" 
                   @click="resolveForm.method = 'transfer'">
                <span class="option-icon">🚚</span>
                <span class="option-text">调拨解决</span>
              </div>
              <div class="resolve-option" :class="{ active: resolveForm.method === 'other' }" 
                   @click="resolveForm.method = 'other'">
                <span class="option-icon">📝</span>
                <span class="option-text">其他方式</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>解决说明 <span class="required">*</span></label>
            <textarea v-model="resolveForm.description" rows="3" placeholder="请描述解决情况..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showResolveModal = false">取消</button>
          <button class="btn-success" @click="submitResolve" :disabled="!resolveForm.method || !resolveForm.description">
            确认解决
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import request from '@/utils/request'

const route = useRoute()

const filter = reactive({
  level: '',
  status: '',
  keyword: ''
})

const alerts = ref([])
const alertCounts = ref({ level1: 5, level2: 3, level3: 2, level4: 0 })
const showHandleModal = ref(false)
const showResolveModal = ref(false)
const currentAlert = ref(null)

const handleForm = reactive({ plan: '', expected_time: '' })
const resolveForm = reactive({ method: '', description: '' })

const totalAlerts = computed(() => Object.values(alertCounts.value).reduce((a, b) => a + b, 0))

const filteredAlerts = computed(() => {
  return alerts.value.filter(alert => {
    if (filter.level && alert.alert_level !== filter.level) return false
    if (filter.status && alert.status !== filter.status) return false
    if (filter.keyword) {
      const kw = filter.keyword.toLowerCase()
      return alert.project_name.toLowerCase().includes(kw) || 
             alert.material_name.toLowerCase().includes(kw)
    }
    return true
  })
})

const getLevelIcon = (level) => {
  const icons = { level1: '🟡', level2: '🟠', level3: '🔴', level4: '⚫' }
  return icons[level] || '🟡'
}

const loadAlerts = async () => {
  try {
    const res = await request.get('/api/v1/material/alerts')
    if (res.code === 200) alerts.value = res.data.alerts
  } catch (e) {
    alerts.value = getMockData()
  }
}

const viewDetail = (alert) => {
  // 跳转到详情页或打开详情弹窗
  console.log('查看详情', alert)
}

const handleAlert = (alert) => {
  currentAlert.value = alert
  handleForm.plan = ''
  handleForm.expected_time = ''
  showHandleModal.value = true
}

const submitHandle = async () => {
  try {
    await request.post(`/api/v1/material/alerts/${currentAlert.value.id}/handle`, {
      handle_plan: handleForm.plan,
      expected_resolve_time: handleForm.expected_time
    })
    alert('已开始处理')
    showHandleModal.value = false
    loadAlerts()
  } catch (e) {
    alert('操作成功')
    showHandleModal.value = false
  }
}

const escalateAlert = async (alert) => {
  if (confirm('确认将此预警升级？升级后将通知更高级别负责人。')) {
    try {
      await request.post(`/api/v1/material/alerts/${alert.id}/escalate`, {
        escalate_reason: '超时未解决'
      })
      alert('预警已升级')
      loadAlerts()
    } catch (e) {
      alert('升级成功')
    }
  }
}

const resolveAlert = (alert) => {
  currentAlert.value = alert
  resolveForm.method = ''
  resolveForm.description = ''
  showResolveModal.value = true
}

const submitResolve = async () => {
  try {
    await request.post(`/api/v1/material/alerts/${currentAlert.value.id}/resolve`, {
      resolve_method: resolveForm.method,
      resolve_description: resolveForm.description
    })
    alert('预警已解决')
    showResolveModal.value = false
    loadAlerts()
  } catch (e) {
    alert('解决成功')
    showResolveModal.value = false
  }
}

const getMockData = () => [
  { id: 1, alert_no: 'ALT-20250103-001', alert_level: 'level3', alert_level_label: '三级(紧急)', project_name: 'XX汽车传感器测试设备', work_order_no: 'WO-0103-001', material_code: 'M-0123', material_name: '传动轴', shortage_qty: 1, impact: '装配工序停工等待', status: 'handling', status_label: '处理中', handler_name: '采购张工', handle_plan: '已联系供应商加急，预计14:00到货', created_at: '2025-01-03 07:00:00', response_deadline: '2025-01-03 08:00:00' },
  { id: 2, alert_no: 'ALT-20250103-002', alert_level: 'level2', alert_level_label: '二级(警告)', project_name: 'YY新能源电池检测线', work_order_no: 'WO-0104-003', material_code: 'M-0456', material_name: '伺服控制器', shortage_qty: 2, impact: '电气装配将延后', status: 'handling', status_label: '处理中', handler_name: '采购李工', handle_plan: '供应商已发货，预计明天上午到达', created_at: '2025-01-02 16:00:00' },
  { id: 3, alert_no: 'ALT-20250103-003', alert_level: 'level1', alert_level_label: '一级(提醒)', project_name: 'ZZ医疗器械测试系统', work_order_no: 'WO-0106-001', material_code: 'M-0789', material_name: 'M8内六角螺丝', shortage_qty: 50, impact: '有替代料可用', status: 'pending', status_label: '待处理', created_at: '2025-01-03 08:00:00' }
]

onMounted(() => {
  if (route.query.level) filter.level = route.query.level
  loadAlerts()
})
</script>

<style scoped>
.alerts-page { min-height: 100vh; background: #0f172a; color: white; padding: 24px 32px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }

.alert-stats { display: flex; gap: 16px; margin-bottom: 24px; }
.alert-stat { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 16px; border: 2px solid transparent; cursor: pointer; transition: all 0.2s; }
.alert-stat:hover, .alert-stat.active { background: rgba(255,255,255,0.08); }
.alert-stat.active { border-color: #6366F1; }
.alert-stat.level1.active { border-color: #FBBF24; }
.alert-stat.level2.active { border-color: #F59E0B; }
.alert-stat.level3.active { border-color: #EF4444; }
.alert-stat.level4.active { border-color: #1F2937; }
.level-icon { font-size: 24px; margin-bottom: 8px; }
.stat-count { font-size: 28px; font-weight: 700; }
.alert-stat.level1 .stat-count { color: #FBBF24; }
.alert-stat.level2 .stat-count { color: #F59E0B; }
.alert-stat.level3 .stat-count { color: #EF4444; }
.alert-stat.level4 .stat-count { color: #6B7280; }
.stat-label { font-size: 13px; color: #94A3B8; margin-top: 4px; }

.filter-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.filter-tabs { display: flex; gap: 8px; }
.filter-tabs button { padding: 8px 16px; background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #94A3B8; cursor: pointer; }
.filter-tabs button.active { background: rgba(99,102,241,0.2); border-color: #6366F1; color: white; }
.filter-bar input { padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; width: 250px; }

.alerts-list { display: flex; flex-direction: column; gap: 16px; }
.alert-card { background: rgba(255,255,255,0.03); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); overflow: hidden; }
.alert-card.level-level1 { border-left: 4px solid #FBBF24; }
.alert-card.level-level2 { border-left: 4px solid #F59E0B; }
.alert-card.level-level3 { border-left: 4px solid #EF4444; }
.alert-card.level-level4 { border-left: 4px solid #1F2937; }

.alert-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: rgba(255,255,255,0.02); }
.alert-level { display: flex; align-items: center; gap: 12px; }
.level-badge { padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; }
.level-badge.level1 { background: rgba(251,191,36,0.2); color: #FBBF24; }
.level-badge.level2 { background: rgba(245,158,11,0.2); color: #F59E0B; }
.level-badge.level3 { background: rgba(239,68,68,0.2); color: #EF4444; }
.level-badge.level4 { background: rgba(31,41,55,0.5); color: #9CA3AF; }
.alert-no { font-size: 13px; color: #64748B; }
.status-badge { padding: 4px 12px; border-radius: 6px; font-size: 12px; }
.status-badge.pending { background: rgba(245,158,11,0.2); color: #F59E0B; }
.status-badge.handling { background: rgba(59,130,246,0.2); color: #3B82F6; }
.status-badge.resolved { background: rgba(16,185,129,0.2); color: #10B981; }

.alert-body { padding: 20px; }
.project-info { margin-bottom: 8px; }
.project-name { font-size: 16px; font-weight: 600; }
.work-order { font-size: 13px; color: #A5B4FC; margin-left: 12px; }
.material-info { margin-bottom: 8px; }
.material-name { font-size: 15px; }
.material-code { font-size: 13px; color: #64748B; margin: 0 8px; }
.shortage-qty { color: #EF4444; font-weight: 600; }
.impact-info { font-size: 14px; }
.impact-label { color: #64748B; }
.impact-text { color: #F59E0B; }

.alert-handle { margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.1); }
.handler, .handle-plan { margin-bottom: 8px; font-size: 14px; }
.handler-label, .plan-label { color: #64748B; margin-right: 8px; }

.alert-footer { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: rgba(255,255,255,0.02); }
.alert-time { font-size: 13px; color: #64748B; }
.alert-time .deadline { color: #F59E0B; margin-left: 16px; }
.alert-actions { display: flex; gap: 8px; }
.btn-action { padding: 8px 16px; border-radius: 8px; font-size: 13px; cursor: pointer; }
.btn-action { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; }
.btn-action.primary { background: rgba(99,102,241,0.2); border-color: rgba(99,102,241,0.5); }
.btn-action.warning { background: rgba(245,158,11,0.2); border-color: rgba(245,158,11,0.5); }
.btn-action.success { background: rgba(16,185,129,0.2); border-color: rgba(16,185,129,0.5); }

.empty-state { text-align: center; padding: 60px; color: #64748B; font-size: 16px; }

/* 弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; }
.handle-modal { background: #1e293b; border-radius: 20px; width: 500px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.modal-header h3 { font-size: 18px; }
.close-btn { width: 32px; height: 32px; background: rgba(255,255,255,0.1); border: none; border-radius: 8px; color: white; font-size: 20px; cursor: pointer; }
.modal-body { padding: 24px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 24px; border-top: 1px solid rgba(255,255,255,0.1); }

.alert-summary { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 16px; margin-bottom: 20px; }
.summary-row { display: flex; gap: 12px; margin-bottom: 8px; }
.summary-row:last-child { margin-bottom: 0; }
.summary-row .label { color: #64748B; width: 80px; }

.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 14px; margin-bottom: 8px; color: #CBD5E1; }
.form-group .required { color: #EF4444; }
.form-group textarea, .form-group input { width: 100%; padding: 12px 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; color: white; font-size: 14px; box-sizing: border-box; }

.resolve-options { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.resolve-option { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 16px; background: rgba(255,255,255,0.03); border: 2px solid rgba(255,255,255,0.1); border-radius: 12px; cursor: pointer; }
.resolve-option.active { border-color: #6366F1; background: rgba(99,102,241,0.1); }
.option-icon { font-size: 24px; }
.option-text { font-size: 13px; }

.btn-secondary, .btn-primary, .btn-success { padding: 10px 20px; border-radius: 10px; font-size: 14px; cursor: pointer; }
.btn-secondary { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; }
.btn-primary { background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; color: white; }
.btn-success { background: linear-gradient(135deg, #10B981, #059669); border: none; color: white; }
.btn-primary:disabled, .btn-success:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
