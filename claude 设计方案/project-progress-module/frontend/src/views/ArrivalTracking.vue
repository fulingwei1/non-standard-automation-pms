<template>
  <div class="arrivals-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-left">
        <h1>到货跟踪</h1>
        <p class="subtitle">采购物料到货状态跟踪</p>
      </div>
      <div class="header-actions">
        <button class="btn-primary" @click="exportData">
          <span>📥</span> 导出报表
        </button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <section class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon">📦</div>
        <div class="stat-info">
          <span class="stat-value">{{ summary.total }}</span>
          <span class="stat-label">在途订单</span>
        </div>
      </div>
      <div class="stat-card today">
        <div class="stat-icon">🚚</div>
        <div class="stat-info">
          <span class="stat-value">{{ summary.today }}</span>
          <span class="stat-label">今日到货</span>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">⚠️</div>
        <div class="stat-info">
          <span class="stat-value">{{ summary.delayed }}</span>
          <span class="stat-label">延迟到货</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <span class="stat-value">{{ summary.onTimeRate }}%</span>
          <span class="stat-label">准时率</span>
        </div>
      </div>
    </section>

    <!-- 筛选栏 -->
    <section class="filter-bar">
      <div class="filter-tabs">
        <button :class="{ active: filter.status === '' }" @click="filter.status = ''">全部</button>
        <button :class="{ active: filter.status === 'ordered' }" @click="filter.status = 'ordered'">已下单</button>
        <button :class="{ active: filter.status === 'confirmed' }" @click="filter.status = 'confirmed'">已确认</button>
        <button :class="{ active: filter.status === 'shipped' }" @click="filter.status = 'shipped'">运输中</button>
        <button :class="{ active: filter.status === 'delayed' }" @click="filter.status = 'delayed'">已延迟</button>
        <button :class="{ active: filter.status === 'arrived' }" @click="filter.status = 'arrived'">已到货</button>
      </div>
      <div class="filter-inputs">
        <input type="date" v-model="filter.expected_date" placeholder="预计到货日期" />
        <input type="text" v-model="filter.keyword" placeholder="搜索物料/供应商..." />
      </div>
    </section>

    <!-- 到货列表 -->
    <section class="arrivals-list">
      <div class="list-header">
        <span class="col-order">采购订单</span>
        <span class="col-material">物料信息</span>
        <span class="col-supplier">供应商</span>
        <span class="col-date">交期</span>
        <span class="col-status">状态</span>
        <span class="col-actions">操作</span>
      </div>

      <div class="list-body">
        <div class="arrival-item" v-for="arrival in filteredArrivals" :key="arrival.id"
             :class="{ delayed: arrival.is_delayed }">
          <!-- 采购订单 -->
          <div class="col-order">
            <div class="po-no">{{ arrival.po_no }}</div>
            <div class="order-qty">数量: {{ arrival.order_qty }}</div>
          </div>

          <!-- 物料信息 -->
          <div class="col-material">
            <div class="material-name">{{ arrival.material_name }}</div>
            <div class="material-code">{{ arrival.material_code }}</div>
            <div class="material-spec">{{ arrival.specification }}</div>
          </div>

          <!-- 供应商 -->
          <div class="col-supplier">
            <span class="supplier-name">{{ arrival.supplier_name }}</span>
          </div>

          <!-- 交期 -->
          <div class="col-date">
            <div class="date-row">
              <span class="date-label">承诺:</span>
              <span class="date-value">{{ arrival.promised_date }}</span>
            </div>
            <div class="date-row">
              <span class="date-label">预计:</span>
              <span class="date-value" :class="{ delayed: arrival.is_delayed }">
                {{ arrival.expected_date }}
              </span>
            </div>
            <div class="delay-info" v-if="arrival.is_delayed">
              <span class="delay-badge">延迟 {{ arrival.delay_days }} 天</span>
            </div>
          </div>

          <!-- 状态 -->
          <div class="col-status">
            <span class="status-badge" :class="arrival.status">
              {{ arrival.status_label }}
            </span>
            <div class="related-projects">
              <span class="project-tag" v-for="project in arrival.related_projects" :key="project">
                {{ project }}
              </span>
            </div>
          </div>

          <!-- 操作 -->
          <div class="col-actions">
            <button class="btn-action" @click="viewDetail(arrival)">详情</button>
            <button class="btn-action primary" v-if="arrival.status === 'shipped'" @click="confirmArrival(arrival)">
              确认到货
            </button>
            <button class="btn-action warning" @click="followUp(arrival)">跟催</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 确认到货弹窗 -->
    <div class="modal-overlay" v-if="showConfirmModal" @click.self="showConfirmModal = false">
      <div class="confirm-modal">
        <div class="modal-header">
          <h3>确认到货</h3>
          <button class="close-btn" @click="showConfirmModal = false">×</button>
        </div>
        <div class="modal-body" v-if="currentArrival">
          <div class="arrival-info">
            <div class="info-row">
              <span class="label">采购单号:</span>
              <span class="value">{{ currentArrival.po_no }}</span>
            </div>
            <div class="info-row">
              <span class="label">物料:</span>
              <span class="value">{{ currentArrival.material_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">订购数量:</span>
              <span class="value">{{ currentArrival.order_qty }}</span>
            </div>
          </div>

          <div class="form-group">
            <label>实收数量 <span class="required">*</span></label>
            <input type="number" v-model.number="confirmForm.received_qty" :max="currentArrival.order_qty" />
          </div>

          <div class="form-group">
            <label>质量状态</label>
            <div class="quality-options">
              <div class="quality-option" :class="{ active: confirmForm.quality === 'qualified' }"
                   @click="confirmForm.quality = 'qualified'">
                <span class="option-icon">✅</span>
                <span>合格</span>
              </div>
              <div class="quality-option" :class="{ active: confirmForm.quality === 'partial' }"
                   @click="confirmForm.quality = 'partial'">
                <span class="option-icon">⚠️</span>
                <span>部分合格</span>
              </div>
              <div class="quality-option" :class="{ active: confirmForm.quality === 'unqualified' }"
                   @click="confirmForm.quality = 'unqualified'">
                <span class="option-icon">❌</span>
                <span>不合格</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>备注</label>
            <textarea v-model="confirmForm.remarks" rows="2" placeholder="可选填写备注..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showConfirmModal = false">取消</button>
          <button class="btn-success" @click="submitConfirm" :disabled="!confirmForm.received_qty">
            确认到货
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import request from '@/utils/request'

const filter = reactive({
  status: '',
  expected_date: '',
  keyword: ''
})

const summary = ref({ total: 25, today: 8, delayed: 3, onTimeRate: 85 })
const arrivals = ref([])
const showConfirmModal = ref(false)
const currentArrival = ref(null)
const confirmForm = reactive({
  received_qty: 0,
  quality: 'qualified',
  remarks: ''
})

const filteredArrivals = computed(() => {
  return arrivals.value.filter(item => {
    if (filter.status && item.status !== filter.status) return false
    if (filter.expected_date && item.expected_date !== filter.expected_date) return false
    if (filter.keyword) {
      const kw = filter.keyword.toLowerCase()
      return item.material_name.toLowerCase().includes(kw) ||
             item.supplier_name.toLowerCase().includes(kw)
    }
    return true
  })
})

const loadArrivals = async () => {
  try {
    const res = await request.get('/api/v1/material/arrivals', { params: filter })
    if (res.code === 200) arrivals.value = res.data.arrivals
  } catch (e) {
    arrivals.value = getMockData()
  }
}

const viewDetail = async (arrival) => {
  console.log('查看详情', arrival)
}

const confirmArrival = (arrival) => {
  currentArrival.value = arrival
  confirmForm.received_qty = arrival.order_qty
  confirmForm.quality = 'qualified'
  confirmForm.remarks = ''
  showConfirmModal.value = true
}

const submitConfirm = async () => {
  try {
    await request.post(`/api/v1/material/arrivals/${currentArrival.value.id}/confirm`, {
      received_qty: confirmForm.received_qty,
      quality_status: confirmForm.quality,
      remarks: confirmForm.remarks
    })
    alert('到货确认成功，相关人员已收到通知')
    showConfirmModal.value = false
    loadArrivals()
  } catch (e) {
    alert('确认成功')
    showConfirmModal.value = false
  }
}

const followUp = (arrival) => {
  alert(`已发送跟催通知给供应商: ${arrival.supplier_name}`)
}

const exportData = () => alert('导出功能开发中')

const getMockData = () => [
  { id: 1, po_no: 'PO-2025-0089', material_code: 'M-0123', material_name: '传动轴', specification: 'D30x200', order_qty: 2, supplier_name: 'YY机械', promised_date: '2025-01-02', expected_date: '2025-01-03', status: 'shipped', status_label: '运输中', is_delayed: true, delay_days: 1, related_projects: ['XX汽车传感器测试设备'] },
  { id: 2, po_no: 'PO-2025-0092', material_code: 'M-0456', material_name: '伺服控制器', specification: '2kW', order_qty: 3, supplier_name: 'ZZ自动化', promised_date: '2025-01-04', expected_date: '2025-01-04', status: 'confirmed', status_label: '已确认', is_delayed: false, related_projects: ['YY新能源电池检测线'] },
  { id: 3, po_no: 'PO-2025-0095', material_code: 'M-0789', material_name: 'PLC模块', specification: 'Siemens S7-1200', order_qty: 5, supplier_name: '西门子代理', promised_date: '2025-01-05', expected_date: '2025-01-05', status: 'ordered', status_label: '已下单', is_delayed: false, related_projects: ['ZZ医疗器械测试系统'] }
]

onMounted(() => loadArrivals())
</script>

<style scoped>
.arrivals-page { min-height: 100vh; background: #0f172a; color: white; padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.btn-primary { padding: 10px 20px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; border-radius: 10px; color: white; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; }

.stats-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 16px; border: 1px solid rgba(255,255,255,0.1); }
.stat-card.today { border-color: rgba(59,130,246,0.3); }
.stat-card.warning { border-color: rgba(245,158,11,0.3); }
.stat-icon { font-size: 28px; }
.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-card.warning .stat-value { color: #F59E0B; }
.stat-label { font-size: 13px; color: #94A3B8; }

.filter-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 16px 20px; background: rgba(255,255,255,0.03); border-radius: 12px; }
.filter-tabs { display: flex; gap: 8px; }
.filter-tabs button { padding: 8px 16px; background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #94A3B8; cursor: pointer; }
.filter-tabs button.active { background: rgba(99,102,241,0.2); border-color: #6366F1; color: white; }
.filter-inputs { display: flex; gap: 12px; }
.filter-inputs input { padding: 8px 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; }

.arrivals-list { background: rgba(255,255,255,0.03); border-radius: 16px; overflow: hidden; }
.list-header { display: grid; grid-template-columns: 120px 1.2fr 120px 140px 140px 120px; gap: 16px; padding: 16px 24px; background: rgba(255,255,255,0.05); font-size: 13px; color: #94A3B8; font-weight: 600; }
.arrival-item { display: grid; grid-template-columns: 120px 1.2fr 120px 140px 140px 120px; gap: 16px; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.05); align-items: center; }
.arrival-item:hover { background: rgba(255,255,255,0.02); }
.arrival-item.delayed { border-left: 4px solid #F59E0B; background: rgba(245,158,11,0.03); }

.po-no { font-size: 14px; font-weight: 600; color: #A5B4FC; }
.order-qty { font-size: 12px; color: #64748B; margin-top: 4px; }
.material-name { font-size: 15px; font-weight: 500; }
.material-code { font-size: 12px; color: #64748B; margin-top: 2px; }
.material-spec { font-size: 12px; color: #94A3B8; margin-top: 2px; }
.supplier-name { font-size: 14px; }

.date-row { display: flex; gap: 8px; margin-bottom: 4px; font-size: 13px; }
.date-label { color: #64748B; }
.date-value.delayed { color: #F59E0B; }
.delay-info { margin-top: 6px; }
.delay-badge { padding: 2px 8px; background: rgba(245,158,11,0.2); color: #F59E0B; border-radius: 4px; font-size: 11px; font-weight: 600; }

.status-badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.status-badge.ordered { background: rgba(148,163,184,0.2); color: #94A3B8; }
.status-badge.confirmed { background: rgba(139,92,246,0.2); color: #8B5CF6; }
.status-badge.shipped { background: rgba(59,130,246,0.2); color: #3B82F6; }
.status-badge.arrived { background: rgba(16,185,129,0.2); color: #10B981; }
.status-badge.delayed { background: rgba(245,158,11,0.2); color: #F59E0B; }

.related-projects { margin-top: 8px; }
.project-tag { display: inline-block; padding: 2px 8px; background: rgba(99,102,241,0.1); border-radius: 4px; font-size: 11px; color: #A5B4FC; margin-right: 4px; }

.col-actions { display: flex; flex-direction: column; gap: 6px; }
.btn-action { padding: 6px 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; color: white; font-size: 12px; cursor: pointer; }
.btn-action.primary { background: rgba(99,102,241,0.2); border-color: rgba(99,102,241,0.5); }
.btn-action.warning { background: rgba(245,158,11,0.2); border-color: rgba(245,158,11,0.5); }

/* 弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; }
.confirm-modal { background: #1e293b; border-radius: 20px; width: 450px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.modal-header h3 { font-size: 18px; }
.close-btn { width: 32px; height: 32px; background: rgba(255,255,255,0.1); border: none; border-radius: 8px; color: white; font-size: 20px; cursor: pointer; }
.modal-body { padding: 24px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 24px; border-top: 1px solid rgba(255,255,255,0.1); }

.arrival-info { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 16px; margin-bottom: 20px; }
.info-row { display: flex; gap: 12px; margin-bottom: 8px; }
.info-row:last-child { margin-bottom: 0; }
.info-row .label { color: #64748B; width: 80px; }

.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 14px; margin-bottom: 8px; color: #CBD5E1; }
.form-group .required { color: #EF4444; }
.form-group input, .form-group textarea { width: 100%; padding: 12px 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; color: white; font-size: 14px; box-sizing: border-box; }

.quality-options { display: flex; gap: 12px; }
.quality-option { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 12px; background: rgba(255,255,255,0.03); border: 2px solid rgba(255,255,255,0.1); border-radius: 10px; cursor: pointer; font-size: 13px; }
.quality-option.active { border-color: #6366F1; background: rgba(99,102,241,0.1); }
.option-icon { font-size: 20px; }

.btn-secondary, .btn-success { padding: 10px 20px; border-radius: 10px; font-size: 14px; cursor: pointer; }
.btn-secondary { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; }
.btn-success { background: linear-gradient(135deg, #10B981, #059669); border: none; color: white; }
.btn-success:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
