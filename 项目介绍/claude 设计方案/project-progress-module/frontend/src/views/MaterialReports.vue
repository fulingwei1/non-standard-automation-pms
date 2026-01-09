<template>
  <div class="material-reports-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-left">
        <h1>物料统计报表</h1>
        <p class="subtitle">齐套率、缺料分析、供应商交期统计</p>
      </div>
      <div class="header-actions">
        <div class="date-range">
          <input type="date" v-model="dateRange.start" />
          <span>至</span>
          <input type="date" v-model="dateRange.end" />
        </div>
        <button class="btn-primary" @click="exportReport">
          <span>📥</span> 导出报表
        </button>
      </div>
    </header>

    <!-- 报表标签页 -->
    <section class="report-tabs">
      <button :class="{ active: activeTab === 'kit-rate' }" @click="activeTab = 'kit-rate'">
        📊 齐套率分析
      </button>
      <button :class="{ active: activeTab === 'shortage' }" @click="activeTab = 'shortage'">
        ⚠️ 缺料分析
      </button>
      <button :class="{ active: activeTab === 'supplier' }" @click="activeTab = 'supplier'">
        🚚 供应商交期
      </button>
    </section>

    <!-- 齐套率分析 -->
    <section class="report-content" v-if="activeTab === 'kit-rate'">
      <!-- 汇总指标 -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-value">{{ kitRateData.summary.avg_rate }}%</div>
          <div class="card-label">平均齐套率</div>
          <div class="card-trend up">↑ 5.2%</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ kitRateData.summary.total_orders }}</div>
          <div class="card-label">工单总数</div>
        </div>
        <div class="summary-card success">
          <div class="card-value">{{ kitRateData.summary.complete_orders }}</div>
          <div class="card-label">齐套工单</div>
        </div>
        <div class="summary-card warning">
          <div class="card-value">{{ kitRateData.summary.shortage_orders }}</div>
          <div class="card-label">缺料工单</div>
        </div>
      </div>

      <!-- 齐套率趋势图 -->
      <div class="chart-section">
        <div class="section-header">
          <h3>齐套率趋势</h3>
          <div class="chart-filter">
            <button :class="{ active: kitRateData.period === 'day' }" @click="kitRateData.period = 'day'">日</button>
            <button :class="{ active: kitRateData.period === 'week' }" @click="kitRateData.period = 'week'">周</button>
            <button :class="{ active: kitRateData.period === 'month' }" @click="kitRateData.period = 'month'">月</button>
          </div>
        </div>
        <div class="chart-container">
          <div class="chart-placeholder">
            <div class="trend-chart">
              <div class="chart-bar" v-for="(item, idx) in kitRateData.trend" :key="idx">
                <div class="bar-fill" :style="{ height: item.rate + '%' }">
                  <span class="bar-value">{{ item.rate }}%</span>
                </div>
                <span class="bar-label">{{ item.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 车间齐套率对比 -->
      <div class="chart-section">
        <div class="section-header">
          <h3>车间齐套率对比</h3>
        </div>
        <div class="workshop-comparison">
          <div class="workshop-item" v-for="ws in kitRateData.by_workshop" :key="ws.id">
            <div class="ws-info">
              <span class="ws-name">{{ ws.name }}</span>
              <span class="ws-rate">{{ ws.rate }}%</span>
            </div>
            <div class="ws-bar">
              <div class="ws-bar-fill" :style="{ width: ws.rate + '%' }" 
                   :class="{ warning: ws.rate < 85, danger: ws.rate < 70 }"></div>
            </div>
            <div class="ws-detail">
              <span>齐套: {{ ws.complete }}</span>
              <span>缺料: {{ ws.shortage }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 缺料分析 -->
    <section class="report-content" v-if="activeTab === 'shortage'">
      <!-- 汇总指标 -->
      <div class="summary-cards">
        <div class="summary-card danger">
          <div class="card-value">{{ shortageData.summary.total_alerts }}</div>
          <div class="card-label">缺料预警</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ shortageData.summary.avg_resolve_hours }}h</div>
          <div class="card-label">平均解决时长</div>
        </div>
        <div class="summary-card success">
          <div class="card-value">{{ shortageData.summary.resolved_rate }}%</div>
          <div class="card-label">解决率</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ shortageData.summary.stoppage_hours }}h</div>
          <div class="card-label">停工时长</div>
        </div>
      </div>

      <!-- 缺料原因分析 -->
      <div class="analysis-grid">
        <div class="chart-section">
          <div class="section-header">
            <h3>缺料原因分布</h3>
          </div>
          <div class="pie-chart-container">
            <div class="pie-legend">
              <div class="legend-item" v-for="item in shortageData.by_reason" :key="item.reason">
                <span class="legend-color" :style="{ background: item.color }"></span>
                <span class="legend-name">{{ item.reason }}</span>
                <span class="legend-value">{{ item.count }} ({{ item.percent }}%)</span>
              </div>
            </div>
          </div>
        </div>

        <div class="chart-section">
          <div class="section-header">
            <h3>缺料物料TOP10</h3>
          </div>
          <div class="top-list">
            <div class="top-item" v-for="(item, idx) in shortageData.top_materials" :key="item.code">
              <span class="rank" :class="{ 'top3': idx < 3 }">{{ idx + 1 }}</span>
              <div class="item-info">
                <span class="item-name">{{ item.name }}</span>
                <span class="item-code">{{ item.code }}</span>
              </div>
              <div class="item-stats">
                <span class="shortage-count">缺料 {{ item.count }} 次</span>
                <span class="shortage-qty">累计 {{ item.total_qty }} 件</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 缺料趋势 -->
      <div class="chart-section">
        <div class="section-header">
          <h3>缺料趋势</h3>
        </div>
        <div class="chart-container">
          <div class="trend-chart line">
            <div class="chart-bar" v-for="(item, idx) in shortageData.trend" :key="idx">
              <div class="bar-fill" :style="{ height: (item.count / 20 * 100) + '%' }">
                <span class="bar-value">{{ item.count }}</span>
              </div>
              <span class="bar-label">{{ item.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 供应商交期 -->
    <section class="report-content" v-if="activeTab === 'supplier'">
      <!-- 汇总指标 -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-value">{{ supplierData.summary.total_orders }}</div>
          <div class="card-label">采购订单</div>
        </div>
        <div class="summary-card success">
          <div class="card-value">{{ supplierData.summary.on_time_rate }}%</div>
          <div class="card-label">准时交付率</div>
        </div>
        <div class="summary-card warning">
          <div class="card-value">{{ supplierData.summary.delayed_orders }}</div>
          <div class="card-label">延迟订单</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ supplierData.summary.avg_delay_days }}天</div>
          <div class="card-label">平均延迟</div>
        </div>
      </div>

      <!-- 供应商排名 -->
      <div class="chart-section">
        <div class="section-header">
          <h3>供应商交期排名</h3>
          <div class="sort-options">
            <select v-model="supplierData.sortBy">
              <option value="on_time_rate">按准时率</option>
              <option value="total_orders">按订单量</option>
              <option value="delay_days">按延迟天数</option>
            </select>
          </div>
        </div>
        <div class="supplier-table">
          <div class="table-header">
            <span class="col-rank">排名</span>
            <span class="col-name">供应商</span>
            <span class="col-orders">订单数</span>
            <span class="col-ontime">准时</span>
            <span class="col-delayed">延迟</span>
            <span class="col-rate">准时率</span>
            <span class="col-avg">平均延迟</span>
            <span class="col-trend">趋势</span>
          </div>
          <div class="table-body">
            <div class="table-row" v-for="(supplier, idx) in supplierData.ranking" :key="supplier.id">
              <span class="col-rank">
                <span class="rank-badge" :class="{ gold: idx === 0, silver: idx === 1, bronze: idx === 2 }">
                  {{ idx + 1 }}
                </span>
              </span>
              <span class="col-name">{{ supplier.name }}</span>
              <span class="col-orders">{{ supplier.total_orders }}</span>
              <span class="col-ontime success">{{ supplier.on_time_orders }}</span>
              <span class="col-delayed danger">{{ supplier.delayed_orders }}</span>
              <span class="col-rate">
                <span class="rate-badge" :class="getRateClass(supplier.on_time_rate)">
                  {{ supplier.on_time_rate }}%
                </span>
              </span>
              <span class="col-avg">{{ supplier.avg_delay_days }}天</span>
              <span class="col-trend">
                <span class="trend-icon" :class="supplier.trend">
                  {{ supplier.trend === 'up' ? '↑' : supplier.trend === 'down' ? '↓' : '→' }}
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 交期趋势 -->
      <div class="chart-section">
        <div class="section-header">
          <h3>交期准时率趋势</h3>
        </div>
        <div class="chart-container">
          <div class="trend-chart">
            <div class="chart-bar" v-for="(item, idx) in supplierData.trend" :key="idx">
              <div class="bar-fill" :style="{ height: item.rate + '%' }"
                   :class="{ warning: item.rate < 85, danger: item.rate < 70 }">
                <span class="bar-value">{{ item.rate }}%</span>
              </div>
              <span class="bar-label">{{ item.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '@/utils/request'

const activeTab = ref('kit-rate')
const dateRange = reactive({
  start: '2024-12-01',
  end: '2025-01-03'
})

// 齐套率数据
const kitRateData = reactive({
  period: 'day',
  summary: { avg_rate: 87.5, total_orders: 156, complete_orders: 136, shortage_orders: 20 },
  trend: [
    { label: '12/28', rate: 82 },
    { label: '12/29', rate: 85 },
    { label: '12/30', rate: 88 },
    { label: '12/31', rate: 86 },
    { label: '1/1', rate: 90 },
    { label: '1/2', rate: 89 },
    { label: '1/3', rate: 92 }
  ],
  by_workshop: [
    { id: 1, name: '装配车间', rate: 92, complete: 45, shortage: 4 },
    { id: 2, name: '机加车间', rate: 88, complete: 38, shortage: 5 },
    { id: 3, name: '调试车间', rate: 85, complete: 28, shortage: 5 },
    { id: 4, name: '电气车间', rate: 78, complete: 25, shortage: 7 }
  ]
})

// 缺料数据
const shortageData = reactive({
  summary: { total_alerts: 45, avg_resolve_hours: 4.2, resolved_rate: 92, stoppage_hours: 18 },
  by_reason: [
    { reason: '供应商延迟', count: 18, percent: 40, color: '#EF4444' },
    { reason: '需求变更', count: 12, percent: 27, color: '#F59E0B' },
    { reason: '库存不准', count: 8, percent: 18, color: '#6366F1' },
    { reason: '质量问题', count: 5, percent: 11, color: '#10B981' },
    { reason: '其他', count: 2, percent: 4, color: '#94A3B8' }
  ],
  top_materials: [
    { code: 'M-0123', name: '传动轴', count: 8, total_qty: 15 },
    { code: 'M-0456', name: '伺服控制器', count: 6, total_qty: 12 },
    { code: 'M-0789', name: 'PLC模块', count: 5, total_qty: 10 },
    { code: 'M-0234', name: '联轴器', count: 4, total_qty: 20 },
    { code: 'M-0567', name: '直线导轨', count: 4, total_qty: 8 }
  ],
  trend: [
    { label: '12/28', count: 8 },
    { label: '12/29', count: 6 },
    { label: '12/30', count: 10 },
    { label: '12/31', count: 5 },
    { label: '1/1', count: 4 },
    { label: '1/2', count: 7 },
    { label: '1/3', count: 5 }
  ]
})

// 供应商数据
const supplierData = reactive({
  sortBy: 'on_time_rate',
  summary: { total_orders: 89, on_time_rate: 85, delayed_orders: 13, avg_delay_days: 2.3 },
  ranking: [
    { id: 1, name: '西门子代理', total_orders: 15, on_time_orders: 14, delayed_orders: 1, on_time_rate: 93, avg_delay_days: 0.5, trend: 'up' },
    { id: 2, name: 'ZZ自动化', total_orders: 22, on_time_orders: 20, delayed_orders: 2, on_time_rate: 91, avg_delay_days: 1.2, trend: 'stable' },
    { id: 3, name: 'YY机械', total_orders: 18, on_time_orders: 16, delayed_orders: 2, on_time_rate: 89, avg_delay_days: 1.5, trend: 'up' },
    { id: 4, name: 'AA电气', total_orders: 12, on_time_orders: 10, delayed_orders: 2, on_time_rate: 83, avg_delay_days: 2.0, trend: 'down' },
    { id: 5, name: 'BB五金', total_orders: 22, on_time_orders: 16, delayed_orders: 6, on_time_rate: 73, avg_delay_days: 3.5, trend: 'down' }
  ],
  trend: [
    { label: '12/28', rate: 82 },
    { label: '12/29', rate: 85 },
    { label: '12/30', rate: 80 },
    { label: '12/31', rate: 88 },
    { label: '1/1', rate: 86 },
    { label: '1/2', rate: 90 },
    { label: '1/3', rate: 88 }
  ]
})

const getRateClass = (rate) => {
  if (rate >= 90) return 'excellent'
  if (rate >= 80) return 'good'
  if (rate >= 70) return 'warning'
  return 'danger'
}

const exportReport = () => {
  alert('报表导出功能开发中...')
}

const loadData = async () => {
  try {
    // 实际项目中调用API
    // const res = await request.get('/api/v1/material/reports/kit-rate', { params: dateRange })
  } catch (e) {
    console.log('使用模拟数据')
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.material-reports-page { min-height: 100vh; background: #0f172a; color: white; padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.header-actions { display: flex; gap: 16px; align-items: center; }
.date-range { display: flex; align-items: center; gap: 8px; }
.date-range input { padding: 8px 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; }
.date-range span { color: #64748B; }
.btn-primary { padding: 10px 20px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; border-radius: 10px; color: white; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; }

.report-tabs { display: flex; gap: 8px; margin-bottom: 24px; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 12px; }
.report-tabs button { flex: 1; padding: 12px 20px; background: transparent; border: none; border-radius: 8px; color: #94A3B8; font-size: 14px; cursor: pointer; transition: all 0.2s; }
.report-tabs button.active { background: rgba(99,102,241,0.2); color: white; }
.report-tabs button:hover { background: rgba(255,255,255,0.05); }

.summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.summary-card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1); }
.summary-card.success { border-color: rgba(16,185,129,0.3); }
.summary-card.warning { border-color: rgba(245,158,11,0.3); }
.summary-card.danger { border-color: rgba(239,68,68,0.3); }
.card-value { font-size: 32px; font-weight: 700; }
.summary-card.success .card-value { color: #10B981; }
.summary-card.warning .card-value { color: #F59E0B; }
.summary-card.danger .card-value { color: #EF4444; }
.card-label { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.card-trend { font-size: 13px; margin-top: 8px; }
.card-trend.up { color: #10B981; }
.card-trend.down { color: #EF4444; }

.chart-section { background: rgba(255,255,255,0.03); border-radius: 16px; padding: 24px; margin-bottom: 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.section-header h3 { font-size: 16px; font-weight: 600; }
.chart-filter { display: flex; gap: 4px; }
.chart-filter button { padding: 6px 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #94A3B8; cursor: pointer; }
.chart-filter button.active { background: rgba(99,102,241,0.2); border-color: #6366F1; color: white; }

.chart-container { height: 200px; }
.trend-chart { display: flex; justify-content: space-around; align-items: flex-end; height: 100%; padding: 0 20px; }
.chart-bar { display: flex; flex-direction: column; align-items: center; flex: 1; }
.bar-fill { width: 40px; background: linear-gradient(180deg, #6366F1, #8B5CF6); border-radius: 4px 4px 0 0; display: flex; align-items: flex-start; justify-content: center; padding-top: 8px; min-height: 20px; transition: height 0.3s; }
.bar-fill.warning { background: linear-gradient(180deg, #F59E0B, #D97706); }
.bar-fill.danger { background: linear-gradient(180deg, #EF4444, #DC2626); }
.bar-value { font-size: 11px; font-weight: 600; }
.bar-label { font-size: 12px; color: #64748B; margin-top: 8px; }

.workshop-comparison { display: flex; flex-direction: column; gap: 16px; }
.workshop-item { display: flex; align-items: center; gap: 16px; }
.ws-info { width: 120px; display: flex; justify-content: space-between; }
.ws-name { font-size: 14px; }
.ws-rate { font-size: 14px; font-weight: 600; color: #6366F1; }
.ws-bar { flex: 1; height: 12px; background: rgba(255,255,255,0.1); border-radius: 6px; overflow: hidden; }
.ws-bar-fill { height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6); border-radius: 6px; transition: width 0.3s; }
.ws-bar-fill.warning { background: linear-gradient(90deg, #F59E0B, #D97706); }
.ws-bar-fill.danger { background: linear-gradient(90deg, #EF4444, #DC2626); }
.ws-detail { width: 140px; font-size: 12px; color: #64748B; display: flex; gap: 12px; }

.analysis-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.pie-legend { display: flex; flex-direction: column; gap: 12px; }
.legend-item { display: flex; align-items: center; gap: 12px; }
.legend-color { width: 16px; height: 16px; border-radius: 4px; }
.legend-name { flex: 1; font-size: 14px; }
.legend-value { font-size: 14px; color: #94A3B8; }

.top-list { display: flex; flex-direction: column; gap: 12px; }
.top-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(255,255,255,0.02); border-radius: 10px; }
.rank { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); border-radius: 6px; font-size: 14px; font-weight: 600; }
.rank.top3 { background: linear-gradient(135deg, #F59E0B, #D97706); }
.item-info { flex: 1; }
.item-name { display: block; font-size: 14px; }
.item-code { font-size: 12px; color: #64748B; }
.item-stats { text-align: right; }
.shortage-count { display: block; font-size: 14px; color: #EF4444; }
.shortage-qty { font-size: 12px; color: #64748B; }

.supplier-table { overflow-x: auto; }
.table-header { display: grid; grid-template-columns: 60px 1fr 80px 60px 60px 100px 80px 60px; gap: 12px; padding: 12px 16px; background: rgba(255,255,255,0.05); border-radius: 8px 8px 0 0; font-size: 13px; color: #94A3B8; }
.table-row { display: grid; grid-template-columns: 60px 1fr 80px 60px 60px 100px 80px 60px; gap: 12px; padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); align-items: center; }
.table-row:hover { background: rgba(255,255,255,0.02); }
.rank-badge { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); border-radius: 50%; font-size: 13px; font-weight: 600; }
.rank-badge.gold { background: linear-gradient(135deg, #F59E0B, #D97706); }
.rank-badge.silver { background: linear-gradient(135deg, #94A3B8, #64748B); }
.rank-badge.bronze { background: linear-gradient(135deg, #CD7F32, #A0522D); }
.col-ontime.success { color: #10B981; }
.col-delayed.danger { color: #EF4444; }
.rate-badge { padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; }
.rate-badge.excellent { background: rgba(16,185,129,0.2); color: #10B981; }
.rate-badge.good { background: rgba(59,130,246,0.2); color: #3B82F6; }
.rate-badge.warning { background: rgba(245,158,11,0.2); color: #F59E0B; }
.rate-badge.danger { background: rgba(239,68,68,0.2); color: #EF4444; }
.trend-icon { font-size: 16px; }
.trend-icon.up { color: #10B981; }
.trend-icon.down { color: #EF4444; }
.trend-icon.stable { color: #94A3B8; }

.sort-options select { padding: 6px 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; color: white; }
</style>
