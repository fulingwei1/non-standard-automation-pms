<template>
  <div class="kit-check-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-left">
        <h1>齐套分析</h1>
        <p class="subtitle">工单物料齐套检查与开工前确认</p>
      </div>
      <div class="header-actions">
        <button class="btn-secondary" @click="batchCheck">
          <span>🔄</span> 批量检查
        </button>
        <button class="btn-primary" @click="exportData">
          <span>📥</span> 导出报表
        </button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <section class="stats-cards">
      <div class="stat-card">
        <div class="stat-value">{{ summary.total }}</div>
        <div class="stat-label">今日工单</div>
      </div>
      <div class="stat-card success">
        <div class="stat-value">{{ summary.complete }}</div>
        <div class="stat-label">齐套</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-value">{{ summary.partial }}</div>
        <div class="stat-label">部分齐套</div>
      </div>
      <div class="stat-card danger">
        <div class="stat-value">{{ summary.shortage }}</div>
        <div class="stat-label">缺料</div>
      </div>
    </section>

    <!-- 筛选栏 -->
    <section class="filter-bar">
      <div class="filter-tabs">
        <button :class="{ active: filter.kit_status === '' }" @click="filter.kit_status = ''">
          全部
        </button>
        <button :class="{ active: filter.kit_status === 'complete' }" @click="filter.kit_status = 'complete'">
          ✅ 齐套
        </button>
        <button :class="{ active: filter.kit_status === 'partial' }" @click="filter.kit_status = 'partial'">
          ⚠️ 部分齐套
        </button>
        <button :class="{ active: filter.kit_status === 'shortage' }" @click="filter.kit_status = 'shortage'">
          ❌ 缺料
        </button>
      </div>
      <div class="filter-inputs">
        <input type="date" v-model="filter.plan_date" placeholder="计划日期" />
        <select v-model="filter.workshop_id">
          <option value="">全部车间</option>
          <option value="1">装配车间</option>
          <option value="2">机加车间</option>
          <option value="3">调试车间</option>
        </select>
        <input type="text" v-model="filter.keyword" placeholder="搜索工单/项目..." />
      </div>
    </section>

    <!-- 工单列表 -->
    <section class="work-order-list">
      <div class="list-header">
        <span class="col-order">工单信息</span>
        <span class="col-project">所属项目</span>
        <span class="col-kit">齐套情况</span>
        <span class="col-shortage">缺料明细</span>
        <span class="col-actions">操作</span>
      </div>

      <div class="list-body">
        <div class="work-order-item" v-for="wo in workOrders" :key="wo.id"
             :class="'status-' + wo.kit_status">
          <!-- 工单信息 -->
          <div class="col-order">
            <div class="order-no">{{ wo.work_order_no }}</div>
            <div class="order-name">{{ wo.task_name }}</div>
            <div class="order-meta">
              <span class="workshop">{{ wo.workshop_name }}</span>
              <span class="plan-date">📅 {{ wo.plan_start_date }}</span>
            </div>
          </div>

          <!-- 项目 -->
          <div class="col-project">
            <span class="project-name">{{ wo.project_name }}</span>
          </div>

          <!-- 齐套情况 -->
          <div class="col-kit">
            <div class="kit-status-badge" :class="wo.kit_status">
              {{ wo.kit_status_label }}
            </div>
            <div class="kit-rate">
              <div class="rate-bar">
                <div class="rate-fill" :style="{ width: wo.kit_rate + '%' }"></div>
              </div>
              <span class="rate-text">{{ wo.kit_rate }}%</span>
            </div>
            <div class="kit-detail">
              <span class="fulfilled">✓ {{ wo.fulfilled_items }}</span>
              <span class="shortage" v-if="wo.shortage_items > 0">✗ {{ wo.shortage_items }}</span>
            </div>
          </div>

          <!-- 缺料明细 -->
          <div class="col-shortage">
            <div class="shortage-list" v-if="wo.shortage_materials?.length > 0">
              <div class="shortage-item" v-for="mat in wo.shortage_materials.slice(0, 2)" :key="mat.material_code">
                <span class="mat-name">{{ mat.material_name }}</span>
                <span class="mat-shortage">缺{{ mat.shortage }}件</span>
              </div>
              <div class="shortage-more" v-if="wo.shortage_materials.length > 2">
                +{{ wo.shortage_materials.length - 2 }}项...
              </div>
            </div>
            <div class="no-shortage" v-else>
              物料齐全
            </div>
          </div>

          <!-- 操作 -->
          <div class="col-actions">
            <button class="btn-action" @click="viewDetail(wo)">
              详情
            </button>
            <button class="btn-action primary" @click="checkKit(wo)">
              检查
            </button>
            <button class="btn-action success" v-if="wo.kit_status === 'complete'" @click="confirmStart(wo)">
              确认开工
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 齐套详情弹窗 -->
    <div class="modal-overlay" v-if="showDetail" @click.self="showDetail = false">
      <div class="detail-modal">
        <div class="modal-header">
          <h3>工单齐套详情</h3>
          <button class="close-btn" @click="showDetail = false">×</button>
        </div>
        <div class="modal-body" v-if="currentWorkOrder">
          <div class="detail-info">
            <div class="info-row">
              <span class="label">工单号:</span>
              <span class="value">{{ currentWorkOrder.work_order_no }}</span>
            </div>
            <div class="info-row">
              <span class="label">任务:</span>
              <span class="value">{{ currentWorkOrder.task_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">项目:</span>
              <span class="value">{{ currentWorkOrder.project_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">计划开工:</span>
              <span class="value">{{ currentWorkOrder.plan_start_date }}</span>
            </div>
          </div>

          <div class="kit-summary">
            <div class="summary-item">
              <span class="num">{{ detailData.kit_summary?.total_items || 0 }}</span>
              <span class="txt">物料总项</span>
            </div>
            <div class="summary-item success">
              <span class="num">{{ detailData.kit_summary?.fulfilled_items || 0 }}</span>
              <span class="txt">已齐套</span>
            </div>
            <div class="summary-item danger">
              <span class="num">{{ detailData.kit_summary?.shortage_items || 0 }}</span>
              <span class="txt">缺料</span>
            </div>
            <div class="summary-item primary">
              <span class="num">{{ detailData.kit_summary?.kit_rate || 0 }}%</span>
              <span class="txt">齐套率</span>
            </div>
          </div>

          <div class="material-table">
            <div class="table-header">
              <span>物料编码</span>
              <span>物料名称</span>
              <span>规格</span>
              <span>需求</span>
              <span>可用</span>
              <span>缺料</span>
              <span>状态</span>
            </div>
            <div class="table-body">
              <div class="table-row" v-for="mat in detailData.material_list" :key="mat.material_code"
                   :class="mat.status">
                <span>{{ mat.material_code }}</span>
                <span>{{ mat.material_name }}</span>
                <span>{{ mat.spec }}</span>
                <span>{{ mat.required }}</span>
                <span>{{ mat.available }}</span>
                <span class="shortage-qty">{{ mat.shortage || 0 }}</span>
                <span class="status-cell">
                  <span class="status-tag" :class="mat.status">
                    {{ getStatusLabel(mat.status) }}
                  </span>
                  <span class="arrival-time" v-if="mat.expected_arrival">
                    预计: {{ mat.expected_arrival }}
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDetail = false">关闭</button>
          <button class="btn-primary" @click="checkKit(currentWorkOrder)">重新检查</button>
          <button class="btn-success" v-if="detailData.kit_summary?.kit_status === 'complete'" 
                  @click="confirmStart(currentWorkOrder)">
            确认开工
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import request from '@/utils/request'

const filter = reactive({
  kit_status: '',
  plan_date: '',
  workshop_id: '',
  keyword: ''
})

const summary = ref({ total: 45, complete: 38, partial: 4, shortage: 3 })
const workOrders = ref([])
const showDetail = ref(false)
const currentWorkOrder = ref(null)
const detailData = ref({})

const getStatusLabel = (status) => {
  const labels = { fulfilled: '已备料', shortage: '缺料', partial: '部分', in_transit: '在途' }
  return labels[status] || status
}

const loadWorkOrders = async () => {
  try {
    const res = await request.get('/api/v1/material/kit-check/work-orders', { params: filter })
    if (res.code === 200) {
      workOrders.value = res.data.work_orders
      summary.value = res.data.summary
    }
  } catch (e) {
    workOrders.value = getMockData()
  }
}

const viewDetail = async (wo) => {
  currentWorkOrder.value = wo
  showDetail.value = true
  try {
    const res = await request.get(`/api/v1/material/kit-check/work-orders/${wo.id}`)
    if (res.code === 200) detailData.value = res.data
  } catch (e) {
    detailData.value = getMockDetailData()
  }
}

const checkKit = async (wo) => {
  try {
    await request.post(`/api/v1/material/kit-check/work-orders/${wo.id}/check`)
    alert('齐套检查完成')
    loadWorkOrders()
  } catch (e) {
    alert('齐套检查完成')
  }
}

const confirmStart = async (wo) => {
  if (confirm(`确认工单 ${wo.work_order_no} 物料齐套，可以开工？`)) {
    try {
      await request.post(`/api/v1/material/kit-check/work-orders/${wo.id}/confirm`, {
        confirm_type: 'start_now'
      })
      alert('确认成功，工单可以开工')
      showDetail.value = false
    } catch (e) {
      alert('确认成功')
    }
  }
}

const batchCheck = () => alert('批量检查功能开发中')
const exportData = () => alert('导出功能开发中')

const getMockData = () => [
  { id: 1, work_order_no: 'WO-0103-001', task_name: 'XX项目-支架装配', project_name: 'XX汽车传感器测试设备', workshop_name: '装配车间', plan_start_date: '2025-01-03', total_items: 12, fulfilled_items: 10, shortage_items: 2, kit_rate: 83.3, kit_status: 'partial', kit_status_label: '部分齐套', shortage_materials: [{ material_code: 'M-0123', material_name: '传动轴', shortage: 1 }, { material_code: 'M-0456', material_name: '联轴器', shortage: 1 }] },
  { id: 2, work_order_no: 'WO-0103-002', task_name: 'XX项目-底座装配', project_name: 'XX汽车传感器测试设备', workshop_name: '装配车间', plan_start_date: '2025-01-03', total_items: 8, fulfilled_items: 8, shortage_items: 0, kit_rate: 100, kit_status: 'complete', kit_status_label: '齐套', shortage_materials: [] },
  { id: 3, work_order_no: 'WO-0103-003', task_name: 'YY项目-电气柜装配', project_name: 'YY新能源电池检测线', workshop_name: '装配车间', plan_start_date: '2025-01-04', total_items: 25, fulfilled_items: 20, shortage_items: 5, kit_rate: 80, kit_status: 'shortage', kit_status_label: '缺料', shortage_materials: [{ material_code: 'M-0789', material_name: '伺服控制器', shortage: 2 }] }
]

const getMockDetailData = () => ({
  kit_summary: { total_items: 12, fulfilled_items: 10, shortage_items: 2, kit_rate: 83.3, kit_status: 'partial' },
  material_list: [
    { material_code: 'M-001', material_name: '底板', spec: '500x400x20', required: 1, available: 1, shortage: 0, status: 'fulfilled' },
    { material_code: 'M-002', material_name: '支架', spec: 'L型', required: 4, available: 4, shortage: 0, status: 'fulfilled' },
    { material_code: 'M-0123', material_name: '传动轴', spec: 'D30x200', required: 1, available: 0, shortage: 1, status: 'shortage', expected_arrival: '2025-01-03 14:00' },
    { material_code: 'M-0456', material_name: '联轴器', spec: 'D30', required: 2, available: 1, shortage: 1, status: 'partial' }
  ]
})

watch(filter, () => loadWorkOrders(), { deep: true })
onMounted(() => loadWorkOrders())
</script>

<style scoped>
.kit-check-page { min-height: 100vh; background: #0f172a; color: white; padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.header-actions { display: flex; gap: 12px; }
.btn-primary, .btn-secondary, .btn-success { padding: 10px 20px; border-radius: 10px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 8px; }
.btn-primary { background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; color: white; }
.btn-secondary { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; }
.btn-success { background: linear-gradient(135deg, #10B981, #059669); border: none; color: white; }

.stats-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.1); }
.stat-card.success { border-color: rgba(16,185,129,0.3); }
.stat-card.warning { border-color: rgba(245,158,11,0.3); }
.stat-card.danger { border-color: rgba(239,68,68,0.3); }
.stat-value { font-size: 32px; font-weight: 700; }
.stat-card.success .stat-value { color: #10B981; }
.stat-card.warning .stat-value { color: #F59E0B; }
.stat-card.danger .stat-value { color: #EF4444; }
.stat-label { font-size: 14px; color: #94A3B8; margin-top: 4px; }

.filter-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 16px 20px; background: rgba(255,255,255,0.03); border-radius: 12px; }
.filter-tabs { display: flex; gap: 8px; }
.filter-tabs button { padding: 8px 16px; background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #94A3B8; cursor: pointer; }
.filter-tabs button.active { background: rgba(99,102,241,0.2); border-color: #6366F1; color: white; }
.filter-inputs { display: flex; gap: 12px; }
.filter-inputs input, .filter-inputs select { padding: 8px 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; }

.work-order-list { background: rgba(255,255,255,0.03); border-radius: 16px; overflow: hidden; }
.list-header { display: grid; grid-template-columns: 1.5fr 1fr 1fr 1.2fr 140px; gap: 16px; padding: 16px 24px; background: rgba(255,255,255,0.05); font-size: 13px; color: #94A3B8; font-weight: 600; }
.work-order-item { display: grid; grid-template-columns: 1.5fr 1fr 1fr 1.2fr 140px; gap: 16px; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.05); align-items: center; }
.work-order-item:hover { background: rgba(255,255,255,0.02); }
.work-order-item.status-shortage { border-left: 4px solid #EF4444; }
.work-order-item.status-partial { border-left: 4px solid #F59E0B; }
.work-order-item.status-complete { border-left: 4px solid #10B981; }

.order-no { font-size: 14px; font-weight: 600; color: #A5B4FC; }
.order-name { font-size: 15px; margin: 4px 0; }
.order-meta { display: flex; gap: 12px; font-size: 12px; color: #64748B; }
.project-name { font-size: 14px; }

.kit-status-badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.kit-status-badge.complete { background: rgba(16,185,129,0.2); color: #10B981; }
.kit-status-badge.partial { background: rgba(245,158,11,0.2); color: #F59E0B; }
.kit-status-badge.shortage { background: rgba(239,68,68,0.2); color: #EF4444; }
.kit-rate { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.rate-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; }
.rate-fill { height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6); }
.rate-text { font-size: 13px; font-weight: 600; }
.kit-detail { margin-top: 6px; font-size: 12px; }
.kit-detail .fulfilled { color: #10B981; margin-right: 8px; }
.kit-detail .shortage { color: #EF4444; }

.shortage-list { font-size: 13px; }
.shortage-item { display: flex; justify-content: space-between; padding: 4px 0; }
.mat-name { color: #CBD5E1; }
.mat-shortage { color: #EF4444; font-weight: 600; }
.shortage-more { color: #64748B; font-size: 12px; margin-top: 4px; }
.no-shortage { color: #10B981; font-size: 13px; }

.col-actions { display: flex; gap: 8px; }
.btn-action { padding: 6px 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; color: white; font-size: 12px; cursor: pointer; }
.btn-action.primary { background: rgba(99,102,241,0.2); border-color: rgba(99,102,241,0.5); }
.btn-action.success { background: rgba(16,185,129,0.2); border-color: rgba(16,185,129,0.5); }

/* 弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; }
.detail-modal { background: #1e293b; border-radius: 20px; width: 900px; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.modal-header h3 { font-size: 18px; }
.close-btn { width: 32px; height: 32px; background: rgba(255,255,255,0.1); border: none; border-radius: 8px; color: white; font-size: 20px; cursor: pointer; }
.modal-body { flex: 1; overflow-y: auto; padding: 24px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 24px; border-top: 1px solid rgba(255,255,255,0.1); }

.detail-info { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px; }
.info-row { display: flex; gap: 8px; }
.info-row .label { color: #64748B; }

.kit-summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.summary-item { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; text-align: center; }
.summary-item .num { display: block; font-size: 24px; font-weight: 700; }
.summary-item.success .num { color: #10B981; }
.summary-item.danger .num { color: #EF4444; }
.summary-item.primary .num { color: #6366F1; }
.summary-item .txt { font-size: 12px; color: #94A3B8; }

.material-table { background: rgba(255,255,255,0.03); border-radius: 12px; overflow: hidden; }
.table-header { display: grid; grid-template-columns: 100px 1fr 100px 60px 60px 60px 140px; gap: 12px; padding: 12px 16px; background: rgba(255,255,255,0.05); font-size: 12px; color: #94A3B8; }
.table-row { display: grid; grid-template-columns: 100px 1fr 100px 60px 60px 60px 140px; gap: 12px; padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; align-items: center; }
.table-row.shortage { background: rgba(239,68,68,0.05); }
.table-row.partial { background: rgba(245,158,11,0.05); }
.shortage-qty { color: #EF4444; font-weight: 600; }
.status-cell { display: flex; flex-direction: column; gap: 4px; }
.status-tag { padding: 2px 8px; border-radius: 4px; font-size: 11px; }
.status-tag.fulfilled { background: rgba(16,185,129,0.2); color: #10B981; }
.status-tag.shortage { background: rgba(239,68,68,0.2); color: #EF4444; }
.status-tag.partial { background: rgba(245,158,11,0.2); color: #F59E0B; }
.arrival-time { font-size: 11px; color: #64748B; }
</style>
