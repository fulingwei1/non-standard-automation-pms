<template>
  <div class="material-dashboard">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>物料保障看板</h1>
          <p class="subtitle">实时监控物料齐套与缺料状态</p>
        </div>
        <div class="header-right">
          <div class="date-info">{{ currentDate }}</div>
          <button class="btn-secondary" @click="refreshData">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
            刷新
          </button>
        </div>
      </div>
    </header>

    <!-- 统计概览 -->
    <section class="stats-overview">
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon">📋</div>
          <div class="stat-info">
            <span class="stat-value">{{ data.overview?.today_work_orders || 0 }}</span>
            <span class="stat-label">今日工单</span>
          </div>
        </div>
        <div class="stat-card success">
          <div class="stat-icon">✅</div>
          <div class="stat-info">
            <span class="stat-value">{{ data.overview?.kit_complete || 0 }}</span>
            <span class="stat-label">齐套工单</span>
          </div>
        </div>
        <div class="stat-card warning">
          <div class="stat-icon">⚠️</div>
          <div class="stat-info">
            <span class="stat-value">{{ data.overview?.kit_partial || 0 }}</span>
            <span class="stat-label">部分齐套</span>
          </div>
        </div>
        <div class="stat-card danger">
          <div class="stat-icon">❌</div>
          <div class="stat-info">
            <span class="stat-value">{{ data.overview?.kit_shortage || 0 }}</span>
            <span class="stat-label">缺料工单</span>
          </div>
        </div>
        <div class="stat-card primary kit-rate-card">
          <div class="kit-rate-header">
            <span class="stat-label">整体齐套率</span>
            <span class="stat-value large">{{ data.overview?.kit_rate || 0 }}%</span>
          </div>
          <div class="kit-rate-bar">
            <div class="kit-rate-fill" :style="{ width: (data.overview?.kit_rate || 0) + '%' }"></div>
          </div>
          <div class="kit-rate-target">目标: 95%</div>
        </div>
      </div>
    </section>

    <!-- 预警级别统计 -->
    <section class="alert-summary">
      <div class="alert-levels">
        <div class="alert-level level1" @click="filterByLevel('level1')">
          <span class="level-icon">🟡</span>
          <span class="level-count">{{ data.alerts_summary?.level1 || 0 }}</span>
          <span class="level-name">一级预警</span>
        </div>
        <div class="alert-level level2" @click="filterByLevel('level2')">
          <span class="level-icon">🟠</span>
          <span class="level-count">{{ data.alerts_summary?.level2 || 0 }}</span>
          <span class="level-name">二级预警</span>
        </div>
        <div class="alert-level level3" @click="filterByLevel('level3')">
          <span class="level-icon">🔴</span>
          <span class="level-count">{{ data.alerts_summary?.level3 || 0 }}</span>
          <span class="level-name">三级预警</span>
        </div>
        <div class="alert-level level4" @click="filterByLevel('level4')">
          <span class="level-icon">⚫</span>
          <span class="level-count">{{ data.alerts_summary?.level4 || 0 }}</span>
          <span class="level-name">四级预警</span>
        </div>
      </div>
    </section>

    <!-- 主体内容 -->
    <div class="dashboard-grid">
      <!-- 左侧：紧急缺料 -->
      <div class="grid-left">
        <div class="card urgent-card">
          <div class="card-header">
            <h3>🚨 紧急缺料清单</h3>
            <router-link to="/material/alerts" class="view-all">查看全部 →</router-link>
          </div>
          <div class="card-body">
            <div class="shortage-list">
              <div class="shortage-item" v-for="item in data.urgent_shortages" :key="item.id"
                   :class="'level-' + item.alert_level"
                   @click="viewShortageDetail(item)">
                <div class="shortage-level">
                  <span class="level-badge" :class="item.alert_level">
                    {{ getLevelIcon(item.alert_level) }}
                  </span>
                </div>
                <div class="shortage-info">
                  <div class="shortage-header">
                    <span class="work-order">{{ item.work_order_no }}</span>
                    <span class="project-name">{{ item.project_name }}</span>
                  </div>
                  <div class="shortage-material">
                    <span class="material-name">{{ item.material_name }}</span>
                    <span class="material-code">({{ item.material_code }})</span>
                    <span class="shortage-qty">缺 {{ item.shortage_qty }} 件</span>
                  </div>
                  <div class="shortage-impact">
                    <span class="impact-label">影响:</span>
                    <span class="impact-text">{{ item.impact }}</span>
                  </div>
                </div>
                <div class="shortage-status">
                  <span class="status-badge" :class="item.status">
                    {{ getStatusLabel(item.status) }}
                  </span>
                  <span class="expected-time" v-if="item.expected_arrival">
                    预计: {{ item.expected_arrival }}
                  </span>
                </div>
              </div>
              <div class="empty-shortage" v-if="!data.urgent_shortages?.length">
                ✅ 暂无紧急缺料，物料保障正常
              </div>
            </div>
          </div>
        </div>

        <!-- 缺料原因分析 -->
        <div class="card">
          <div class="card-header">
            <h3>📊 缺料原因分析</h3>
          </div>
          <div class="card-body">
            <div class="reason-chart">
              <div class="reason-item" v-for="reason in data.shortage_by_reason" :key="reason.reason">
                <div class="reason-info">
                  <span class="reason-name">{{ reason.reason }}</span>
                  <span class="reason-count">{{ reason.count }}件</span>
                </div>
                <div class="reason-bar">
                  <div class="reason-fill" :style="{ width: reason.percent + '%' }"></div>
                </div>
                <span class="reason-percent">{{ reason.percent }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：到货跟踪 -->
      <div class="grid-right">
        <!-- 今日到货 -->
        <div class="card">
          <div class="card-header">
            <h3>🚚 今日待到货</h3>
            <span class="arrival-count">{{ data.today_arrivals?.length || 0 }} 项</span>
          </div>
          <div class="card-body">
            <div class="arrival-list">
              <div class="arrival-item" v-for="arrival in data.today_arrivals" :key="arrival.id">
                <div class="arrival-time">
                  <span class="time-icon">{{ getArrivalIcon(arrival.status) }}</span>
                  <span class="time-text">{{ arrival.expected_time }}</span>
                </div>
                <div class="arrival-info">
                  <span class="arrival-material">{{ arrival.material_name }}</span>
                  <span class="arrival-qty">x{{ arrival.qty }}</span>
                </div>
                <div class="arrival-supplier">{{ arrival.supplier }}</div>
                <div class="arrival-status" :class="arrival.status">
                  {{ getArrivalStatusLabel(arrival.status) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 齐套率趋势 -->
        <div class="card">
          <div class="card-header">
            <h3>📈 齐套率趋势</h3>
          </div>
          <div class="card-body">
            <div class="trend-chart">
              <div class="trend-bars">
                <div class="trend-bar" v-for="item in data.kit_trend" :key="item.date">
                  <div class="bar-fill" :style="{ height: item.rate + '%' }">
                    <span class="bar-value">{{ item.rate }}%</span>
                  </div>
                  <span class="bar-label">{{ item.date }}</span>
                </div>
              </div>
              <div class="trend-target">
                <div class="target-line" style="bottom: 95%"></div>
                <span class="target-label">目标95%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="card">
          <div class="card-header">
            <h3>⚡ 快捷操作</h3>
          </div>
          <div class="card-body">
            <div class="quick-actions">
              <router-link to="/material/kit-check" class="action-btn">
                <span class="action-icon">✅</span>
                <span>齐套检查</span>
              </router-link>
              <router-link to="/material/alerts" class="action-btn">
                <span class="action-icon">⚠️</span>
                <span>预警处理</span>
              </router-link>
              <router-link to="/material/arrivals" class="action-btn">
                <span class="action-icon">🚚</span>
                <span>到货跟踪</span>
              </router-link>
              <router-link to="/material/reports" class="action-btn">
                <span class="action-icon">📊</span>
                <span>统计分析</span>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request'

const router = useRouter()

const data = ref({
  overview: {},
  kit_trend: [],
  urgent_shortages: [],
  today_arrivals: [],
  shortage_by_reason: [],
  alerts_summary: {}
})

const currentDate = computed(() => {
  return new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
})

const getLevelIcon = (level) => {
  const icons = { level1: '🟡', level2: '🟠', level3: '🔴', level4: '⚫' }
  return icons[level] || '🟡'
}

const getStatusLabel = (status) => {
  const labels = { handling: '处理中', substituting: '替代中', pending: '待处理', resolved: '已解决' }
  return labels[status] || status
}

const getArrivalIcon = (status) => {
  const icons = { shipped: '🚚', confirmed: '📦', arrived: '✅' }
  return icons[status] || '📦'
}

const getArrivalStatusLabel = (status) => {
  const labels = { shipped: '运输中', confirmed: '已确认', arrived: '已到货' }
  return labels[status] || status
}

const filterByLevel = (level) => {
  router.push(`/material/alerts?level=${level}`)
}

const viewShortageDetail = (item) => {
  router.push(`/material/alerts/${item.id}`)
}

const refreshData = async () => {
  try {
    const res = await request.get('/api/v1/material/dashboard')
    if (res.code === 200) data.value = res.data
  } catch (e) {
    data.value = getMockData()
  }
}

const getMockData = () => ({
  overview: { today_work_orders: 45, kit_complete: 38, kit_partial: 4, kit_shortage: 3, kit_rate: 84.4, urgent_shortage: 3, pending_arrival: 12 },
  kit_trend: [
    { date: '01-01', rate: 82 },
    { date: '01-02', rate: 85 },
    { date: '01-03', rate: 84 }
  ],
  urgent_shortages: [
    { id: 1, work_order_no: 'WO-0103-001', project_name: 'XX汽车传感器测试设备', material_name: '传动轴', material_code: 'M-0123', shortage_qty: 1, impact: '装配停工', status: 'handling', expected_arrival: '今天14:00', alert_level: 'level3' },
    { id: 2, work_order_no: 'WO-0103-005', project_name: 'YY新能源电池检测线', material_name: '伺服控制器', material_code: 'M-0456', shortage_qty: 2, impact: '电气装配延后', status: 'handling', expected_arrival: '明天上午', alert_level: 'level2' },
    { id: 3, work_order_no: 'WO-0103-008', project_name: 'ZZ医疗器械测试系统', material_name: 'M8内六角螺丝', material_code: 'M-0789', shortage_qty: 50, impact: '可用替代料', status: 'substituting', alert_level: 'level1' }
  ],
  today_arrivals: [
    { id: 1, material_name: '伺服电机', qty: 2, supplier: 'XX电机', expected_time: '10:00', status: 'shipped' },
    { id: 2, material_name: '传动轴', qty: 1, supplier: 'YY机械', expected_time: '14:00', status: 'shipped' },
    { id: 3, material_name: 'PLC模块', qty: 3, supplier: 'ZZ自动化', expected_time: '16:00', status: 'confirmed' }
  ],
  shortage_by_reason: [
    { reason: '采购延迟', count: 5, percent: 42 },
    { reason: '供应商交期', count: 4, percent: 33 },
    { reason: '库存不准', count: 2, percent: 17 },
    { reason: '设计变更', count: 1, percent: 8 }
  ],
  alerts_summary: { level1: 5, level2: 3, level3: 2, level4: 0 }
})

onMounted(() => refreshData())
</script>

<style scoped>
.material-dashboard { min-height: 100vh; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; }
.page-header { padding: 24px 32px; }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.header-content h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.date-info { font-size: 14px; color: #94A3B8; }
.btn-secondary { display: flex; align-items: center; gap: 8px; padding: 10px 20px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; color: white; cursor: pointer; }
.btn-secondary svg { width: 18px; height: 18px; }

/* 统计概览 */
.stats-overview { padding: 0 32px 20px; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr) 1.5fr; gap: 16px; }
.stat-card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 16px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
.stat-card.success { border-color: rgba(16,185,129,0.3); }
.stat-card.warning { border-color: rgba(245,158,11,0.3); }
.stat-card.danger { border-color: rgba(239,68,68,0.3); }
.stat-card.primary { border-color: rgba(99,102,241,0.3); }
.stat-icon { font-size: 28px; }
.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-value.large { font-size: 36px; }
.stat-label { font-size: 13px; color: #94A3B8; }
.kit-rate-card { flex-direction: column; align-items: stretch; }
.kit-rate-header { display: flex; justify-content: space-between; align-items: center; }
.kit-rate-bar { height: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; margin: 12px 0 8px; overflow: hidden; }
.kit-rate-fill { height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6); border-radius: 5px; }
.kit-rate-target { font-size: 12px; color: #64748B; text-align: right; }

/* 预警级别 */
.alert-summary { padding: 0 32px 20px; }
.alert-levels { display: flex; gap: 16px; }
.alert-level { flex: 1; display: flex; align-items: center; gap: 12px; padding: 16px 20px; background: rgba(255,255,255,0.05); border-radius: 12px; cursor: pointer; transition: all 0.2s; }
.alert-level:hover { background: rgba(255,255,255,0.1); transform: translateY(-2px); }
.level-icon { font-size: 24px; }
.level-count { font-size: 28px; font-weight: 700; }
.level-name { font-size: 13px; color: #94A3B8; }

/* 主体布局 */
.dashboard-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 24px; padding: 0 32px 32px; }
.grid-left, .grid-right { display: flex; flex-direction: column; gap: 20px; }

/* 卡片 */
.card { background: rgba(255,255,255,0.05); border-radius: 20px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); overflow: hidden; }
.card-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.card-header h3 { font-size: 16px; font-weight: 600; }
.view-all { font-size: 13px; color: #6366F1; text-decoration: none; }
.card-body { padding: 20px 24px; }

/* 紧急缺料 */
.urgent-card .card-header { background: rgba(239,68,68,0.1); }
.shortage-list { display: flex; flex-direction: column; gap: 12px; }
.shortage-item { display: flex; align-items: flex-start; gap: 16px; padding: 16px; background: rgba(255,255,255,0.03); border-radius: 12px; cursor: pointer; transition: all 0.2s; border-left: 4px solid transparent; }
.shortage-item:hover { background: rgba(255,255,255,0.08); }
.shortage-item.level-level3 { border-left-color: #EF4444; }
.shortage-item.level-level2 { border-left-color: #F59E0B; }
.shortage-item.level-level1 { border-left-color: #FBBF24; }
.level-badge { font-size: 20px; }
.shortage-info { flex: 1; }
.shortage-header { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }
.work-order { font-size: 13px; font-weight: 600; color: #6366F1; }
.project-name { font-size: 13px; color: #94A3B8; }
.shortage-material { margin-bottom: 6px; }
.material-name { font-size: 15px; font-weight: 600; }
.material-code { font-size: 13px; color: #64748B; margin: 0 8px; }
.shortage-qty { font-size: 14px; color: #EF4444; font-weight: 600; }
.shortage-impact { font-size: 13px; }
.impact-label { color: #64748B; }
.impact-text { color: #F59E0B; }
.shortage-status { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.status-badge { padding: 4px 10px; border-radius: 6px; font-size: 12px; }
.status-badge.handling { background: rgba(59,130,246,0.2); color: #3B82F6; }
.status-badge.substituting { background: rgba(139,92,246,0.2); color: #8B5CF6; }
.status-badge.pending { background: rgba(245,158,11,0.2); color: #F59E0B; }
.expected-time { font-size: 12px; color: #94A3B8; }
.empty-shortage { text-align: center; padding: 32px; color: #64748B; }

/* 缺料原因 */
.reason-chart { display: flex; flex-direction: column; gap: 14px; }
.reason-item { display: flex; align-items: center; gap: 12px; }
.reason-info { width: 100px; display: flex; justify-content: space-between; }
.reason-name { font-size: 13px; }
.reason-count { font-size: 12px; color: #64748B; }
.reason-bar { flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.reason-fill { height: 100%; background: linear-gradient(90deg, #F59E0B, #FBBF24); border-radius: 4px; }
.reason-percent { font-size: 13px; font-weight: 600; width: 40px; text-align: right; }

/* 到货列表 */
.arrival-count { background: rgba(99,102,241,0.2); color: #A5B4FC; padding: 4px 10px; border-radius: 6px; font-size: 13px; }
.arrival-list { display: flex; flex-direction: column; gap: 12px; }
.arrival-item { display: grid; grid-template-columns: 80px 1fr 80px 70px; align-items: center; gap: 12px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 10px; }
.arrival-time { display: flex; align-items: center; gap: 6px; }
.time-icon { font-size: 18px; }
.time-text { font-size: 14px; font-weight: 600; }
.arrival-info { display: flex; align-items: center; gap: 8px; }
.arrival-material { font-size: 14px; }
.arrival-qty { font-size: 13px; color: #64748B; }
.arrival-supplier { font-size: 13px; color: #94A3B8; }
.arrival-status { font-size: 12px; padding: 4px 8px; border-radius: 4px; text-align: center; }
.arrival-status.shipped { background: rgba(59,130,246,0.2); color: #3B82F6; }
.arrival-status.confirmed { background: rgba(139,92,246,0.2); color: #8B5CF6; }

/* 趋势图 */
.trend-chart { position: relative; height: 150px; }
.trend-bars { display: flex; justify-content: space-around; align-items: flex-end; height: 120px; padding-bottom: 30px; }
.trend-bar { display: flex; flex-direction: column; align-items: center; width: 50px; }
.bar-fill { width: 40px; background: linear-gradient(180deg, #6366F1, #8B5CF6); border-radius: 6px 6px 0 0; display: flex; align-items: flex-start; justify-content: center; min-height: 20px; }
.bar-value { font-size: 11px; font-weight: 600; padding-top: 4px; }
.bar-label { font-size: 12px; color: #64748B; margin-top: 8px; }
.trend-target { position: absolute; bottom: 35px; left: 0; right: 0; }
.target-line { position: absolute; left: 0; right: 0; border-top: 2px dashed rgba(16,185,129,0.5); }
.target-label { position: absolute; right: 0; top: -20px; font-size: 11px; color: #10B981; }

/* 快捷操作 */
.quick-actions { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.action-btn { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 16px; background: rgba(255,255,255,0.05); border-radius: 12px; text-decoration: none; color: white; transition: all 0.2s; }
.action-btn:hover { background: rgba(255,255,255,0.1); transform: translateY(-2px); }
.action-icon { font-size: 24px; }
.action-btn span:last-child { font-size: 13px; color: #CBD5E1; }

@media (max-width: 1200px) {
  .stats-row { grid-template-columns: repeat(3, 1fr); }
  .dashboard-grid { grid-template-columns: 1fr; }
}
</style>
