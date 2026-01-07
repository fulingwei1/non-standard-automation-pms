<template>
  <div class="production-dashboard">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>生产管理驾驶舱</h1>
          <p class="subtitle">实时监控生产全局状态</p>
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
          <div class="stat-icon projects">🏭</div>
          <div class="stat-info">
            <span class="stat-value">{{ data.overview?.active_projects || 0 }}</span>
            <span class="stat-label">在产项目</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon tasks">📋</div>
          <div class="stat-info">
            <span class="stat-value">{{ data.overview?.today_tasks || 0 }}</span>
            <span class="stat-label">今日任务</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon completed">✅</div>
          <div class="stat-info">
            <span class="stat-value">{{ data.overview?.completed_today || 0 }}</span>
            <span class="stat-label">已完成</span>
          </div>
        </div>
        <div class="stat-card warning">
          <div class="stat-icon exception">⚠️</div>
          <div class="stat-info">
            <span class="stat-value">{{ data.overview?.exception_count || 0 }}</span>
            <span class="stat-label">异常数</span>
          </div>
        </div>
        <div class="stat-card efficiency">
          <div class="stat-icon">📈</div>
          <div class="stat-info">
            <span class="stat-value">{{ data.overview?.today_efficiency || 0 }}<span class="unit">%</span></span>
            <span class="stat-label">今日效率</span>
          </div>
          <div class="efficiency-bar">
            <div class="efficiency-fill" :style="{ width: (data.overview?.today_efficiency || 0) + '%' }"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 主体内容 -->
    <div class="dashboard-grid">
      <!-- 左侧 -->
      <div class="grid-left">
        <!-- 车间负荷 -->
        <div class="card">
          <div class="card-header">
            <h3>🏭 车间负荷</h3>
          </div>
          <div class="card-body">
            <div class="workshop-list">
              <div class="workshop-item" v-for="ws in data.workshop_workload" :key="ws.workshop"
                   :class="{ overload: ws.status === 'overload' }"
                   @click="goToWorkshop(ws)">
                <div class="workshop-info">
                  <span class="workshop-name">{{ ws.workshop }}</span>
                  <span class="workshop-stats">{{ ws.tasks }}任务 / {{ ws.workers }}人</span>
                </div>
                <div class="workshop-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: ws.workload + '%' }" :class="ws.status"></div>
                  </div>
                  <span class="progress-text" :class="ws.status">{{ ws.workload }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 重点项目进度 -->
        <div class="card">
          <div class="card-header">
            <h3>🎯 重点项目生产进度</h3>
          </div>
          <div class="card-body">
            <div class="project-progress-list">
              <div class="project-progress-item" v-for="project in data.key_projects" :key="project.id">
                <div class="project-header">
                  <span class="project-name">{{ project.name }}</span>
                  <span class="project-deadline" :class="project.status">
                    交期: {{ project.deadline }}
                    <span class="status-badge" :class="project.status">
                      {{ project.status === 'normal' ? '正常' : '有风险' }}
                    </span>
                  </span>
                </div>
                <div class="stage-progress">
                  <div class="stage">
                    <span class="stage-name">机加</span>
                    <div class="stage-bar">
                      <div class="stage-fill" :style="{ width: project.machining_progress + '%' }"></div>
                    </div>
                    <span class="stage-percent">{{ project.machining_progress }}%</span>
                  </div>
                  <div class="stage">
                    <span class="stage-name">装配</span>
                    <div class="stage-bar">
                      <div class="stage-fill assembly" :style="{ width: project.assembly_progress + '%' }"></div>
                    </div>
                    <span class="stage-percent">{{ project.assembly_progress }}%</span>
                  </div>
                  <div class="stage">
                    <span class="stage-name">调试</span>
                    <div class="stage-bar">
                      <div class="stage-fill debugging" :style="{ width: project.debugging_progress + '%' }"></div>
                    </div>
                    <span class="stage-percent">{{ project.debugging_progress }}%</span>
                  </div>
                </div>
                <div class="risk-reason" v-if="project.risk_reason">
                  ⚠️ {{ project.risk_reason }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧 -->
      <div class="grid-right">
        <!-- 今日异常 -->
        <div class="card exception-card">
          <div class="card-header">
            <h3>🚨 今日异常</h3>
            <span class="exception-count" v-if="data.today_exceptions?.length">{{ data.today_exceptions.length }}</span>
          </div>
          <div class="card-body">
            <div class="exception-list">
              <div class="exception-item" v-for="exc in data.today_exceptions" :key="exc.id" :class="exc.level">
                <span class="exception-icon">{{ exc.level === 'critical' ? '🔴' : exc.level === 'major' ? '🟠' : '🟡' }}</span>
                <div class="exception-content">
                  <span class="exception-project">{{ exc.project }}</span>
                  <span class="exception-desc">{{ exc.content }}</span>
                </div>
                <span class="exception-status" :class="exc.status">{{ exc.status === 'handling' ? '处理中' : '待处理' }}</span>
              </div>
              <div class="empty-exception" v-if="!data.today_exceptions?.length">
                ✅ 今日无异常，生产正常
              </div>
            </div>
          </div>
        </div>

        <!-- 人员出勤 -->
        <div class="card">
          <div class="card-header">
            <h3>👥 人员出勤</h3>
          </div>
          <div class="card-body">
            <div class="attendance-summary">
              <div class="attendance-item">
                <span class="att-value present">{{ data.attendance?.present || 0 }}</span>
                <span class="att-label">出勤</span>
              </div>
              <div class="attendance-item">
                <span class="att-value leave">{{ data.attendance?.leave || 0 }}</span>
                <span class="att-label">请假</span>
              </div>
              <div class="attendance-item">
                <span class="att-value overtime">{{ data.attendance?.overtime || 0 }}</span>
                <span class="att-label">加班</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 快捷入口 -->
        <div class="card">
          <div class="card-header">
            <h3>⚡ 快捷操作</h3>
          </div>
          <div class="card-body">
            <div class="quick-actions">
              <router-link to="/production/work-orders" class="action-btn">
                <span class="action-icon">📋</span>
                <span>工单管理</span>
              </router-link>
              <router-link to="/production/reports" class="action-btn">
                <span class="action-icon">⏱️</span>
                <span>报工审核</span>
              </router-link>
              <router-link to="/production/exceptions" class="action-btn">
                <span class="action-icon">⚠️</span>
                <span>异常处理</span>
              </router-link>
              <router-link to="/production/daily-report" class="action-btn">
                <span class="action-icon">📊</span>
                <span>生产日报</span>
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
  workshop_workload: [],
  today_exceptions: [],
  key_projects: [],
  attendance: {}
})

const currentDate = computed(() => {
  const d = new Date()
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
})

const goToWorkshop = (ws) => {
  router.push(`/production/workshop?name=${ws.workshop}`)
}

const refreshData = async () => {
  try {
    const res = await request.get('/api/v1/production/dashboard')
    if (res.code === 200) data.value = res.data
  } catch (e) {
    data.value = getMockData()
  }
}

const getMockData = () => ({
  overview: { active_projects: 12, today_tasks: 45, completed_today: 32, exception_count: 3, today_efficiency: 87 },
  workshop_workload: [
    { workshop: '机加车间', workload: 85, status: 'normal', tasks: 15, workers: 14 },
    { workshop: '装配车间', workload: 95, status: 'overload', tasks: 22, workers: 18 },
    { workshop: '调试车间', workload: 68, status: 'normal', tasks: 8, workers: 10 }
  ],
  today_exceptions: [
    { id: 1, level: 'critical', project: 'XX项目', content: '缺料，影响装配', status: 'handling' },
    { id: 2, level: 'major', project: '设备', content: 'CNC机床故障', status: 'handling' },
    { id: 3, level: 'minor', project: 'YY项目', content: '图纸有误', status: 'reported' }
  ],
  key_projects: [
    { id: 1, name: 'XX汽车传感器测试设备', machining_progress: 100, assembly_progress: 75, debugging_progress: 0, deadline: '2025-02-10', status: 'normal' },
    { id: 2, name: 'YY新能源电池检测线', machining_progress: 80, assembly_progress: 30, debugging_progress: 0, deadline: '2025-03-15', status: 'at_risk', risk_reason: '物料延迟' }
  ],
  attendance: { present: 42, leave: 2, overtime: 8 }
})

onMounted(() => refreshData())
</script>

<style scoped>
.production-dashboard { min-height: 100vh; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; }
.page-header { padding: 24px 32px; }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.header-content h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.date-info { font-size: 14px; color: #94A3B8; }
.btn-secondary { display: flex; align-items: center; gap: 8px; padding: 10px 20px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; color: white; cursor: pointer; }
.btn-secondary svg { width: 18px; height: 18px; }

/* 统计概览 */
.stats-overview { padding: 0 32px 24px; }
.stats-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; }
.stat-card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 16px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
.stat-card.warning { border-color: rgba(245,158,11,0.3); }
.stat-card.efficiency { flex-direction: column; align-items: stretch; }
.stat-icon { font-size: 32px; }
.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 32px; font-weight: 700; }
.stat-value .unit { font-size: 18px; font-weight: 400; color: #94A3B8; }
.stat-label { font-size: 13px; color: #94A3B8; }
.efficiency-bar { height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-top: 12px; overflow: hidden; }
.efficiency-fill { height: 100%; background: linear-gradient(90deg, #10B981, #34D399); border-radius: 4px; }

/* 主体布局 */
.dashboard-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 24px; padding: 0 32px 32px; }
.grid-left, .grid-right { display: flex; flex-direction: column; gap: 20px; }

/* 卡片 */
.card { background: rgba(255,255,255,0.05); border-radius: 20px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); overflow: hidden; }
.card-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.card-header h3 { font-size: 16px; font-weight: 600; }
.card-body { padding: 20px 24px; }

/* 车间负荷 */
.workshop-list { display: flex; flex-direction: column; gap: 16px; }
.workshop-item { display: flex; align-items: center; gap: 20px; padding: 16px; background: rgba(255,255,255,0.03); border-radius: 12px; cursor: pointer; transition: all 0.2s; }
.workshop-item:hover { background: rgba(255,255,255,0.08); }
.workshop-item.overload { border-left: 3px solid #EF4444; }
.workshop-info { flex: 1; }
.workshop-name { font-size: 15px; font-weight: 600; display: block; }
.workshop-stats { font-size: 12px; color: #94A3B8; }
.workshop-progress { display: flex; align-items: center; gap: 12px; width: 200px; }
.workshop-progress .progress-bar { flex: 1; height: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; overflow: hidden; }
.workshop-progress .progress-fill { height: 100%; border-radius: 5px; }
.workshop-progress .progress-fill.normal { background: linear-gradient(90deg, #10B981, #34D399); }
.workshop-progress .progress-fill.overload { background: linear-gradient(90deg, #EF4444, #F87171); }
.progress-text { font-size: 14px; font-weight: 600; min-width: 45px; }
.progress-text.overload { color: #EF4444; }

/* 项目进度 */
.project-progress-list { display: flex; flex-direction: column; gap: 20px; }
.project-progress-item { padding: 16px; background: rgba(255,255,255,0.03); border-radius: 12px; }
.project-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.project-name { font-size: 15px; font-weight: 600; }
.project-deadline { font-size: 13px; color: #94A3B8; }
.status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-left: 8px; }
.status-badge.normal { background: rgba(16,185,129,0.2); color: #10B981; }
.status-badge.at_risk { background: rgba(245,158,11,0.2); color: #F59E0B; }
.stage-progress { display: flex; flex-direction: column; gap: 10px; }
.stage { display: flex; align-items: center; gap: 12px; }
.stage-name { font-size: 13px; color: #94A3B8; min-width: 40px; }
.stage-bar { flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.stage-fill { height: 100%; background: #6366F1; border-radius: 4px; }
.stage-fill.assembly { background: #8B5CF6; }
.stage-fill.debugging { background: #10B981; }
.stage-percent { font-size: 12px; color: #CBD5E1; min-width: 40px; text-align: right; }
.risk-reason { margin-top: 12px; padding: 8px 12px; background: rgba(245,158,11,0.1); border-radius: 6px; font-size: 13px; color: #F59E0B; }

/* 异常 */
.exception-card .card-header { background: rgba(239,68,68,0.1); }
.exception-count { background: #EF4444; color: white; padding: 4px 10px; border-radius: 10px; font-size: 13px; font-weight: 600; }
.exception-list { display: flex; flex-direction: column; gap: 12px; }
.exception-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 10px; }
.exception-content { flex: 1; }
.exception-project { font-size: 13px; font-weight: 600; display: block; }
.exception-desc { font-size: 13px; color: #94A3B8; }
.exception-status { font-size: 12px; padding: 4px 8px; border-radius: 4px; }
.exception-status.handling { background: rgba(59,130,246,0.2); color: #3B82F6; }
.exception-status.reported { background: rgba(245,158,11,0.2); color: #F59E0B; }
.empty-exception { text-align: center; padding: 24px; color: #64748B; }

/* 出勤 */
.attendance-summary { display: flex; justify-content: space-around; }
.attendance-item { text-align: center; }
.att-value { font-size: 32px; font-weight: 700; display: block; }
.att-value.present { color: #10B981; }
.att-value.leave { color: #F59E0B; }
.att-value.overtime { color: #3B82F6; }
.att-label { font-size: 13px; color: #94A3B8; }

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
