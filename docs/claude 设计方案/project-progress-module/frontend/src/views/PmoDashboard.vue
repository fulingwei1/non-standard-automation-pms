<template>
  <div class="pmo-dashboard">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>项目管理驾驶舱</h1>
          <p class="subtitle">实时监控项目全景状态</p>
        </div>
        <div class="header-right">
          <div class="date-info">{{ currentDate }}</div>
          <button class="btn-secondary" @click="refreshData">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
            刷新
          </button>
          <button class="btn-primary" @click="showWeeklyReport = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            周报
          </button>
        </div>
      </div>
    </header>

    <!-- 统计概览 -->
    <section class="stats-overview">
      <div class="stats-row">
        <div class="stat-card large primary">
          <div class="stat-header">
            <span class="stat-icon">📊</span>
            <span class="stat-title">在建项目</span>
          </div>
          <div class="stat-value">{{ data.overview?.total_projects || 0 }}</div>
          <div class="stat-breakdown">
            <span class="breakdown-item a">A级 {{ data.overview?.level_a || 0 }}</span>
            <span class="breakdown-item b">B级 {{ data.overview?.level_b || 0 }}</span>
            <span class="breakdown-item c">C级 {{ data.overview?.level_c || 0 }}</span>
          </div>
        </div>
        <div class="stat-card delivery">
          <div class="stat-header">
            <span class="stat-icon">🚚</span>
            <span class="stat-title">本月交付</span>
          </div>
          <div class="stat-value">{{ data.overview?.this_month_delivery || 0 }}</div>
          <div class="stat-trend up">较上月 +2</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-header">
            <span class="stat-icon">⚠️</span>
            <span class="stat-title">预警项目</span>
          </div>
          <div class="stat-value">{{ data.overview?.warning_projects || 0 }}</div>
          <div class="stat-trend">需要关注</div>
        </div>
        <div class="stat-card health">
          <div class="stat-header">
            <span class="stat-icon">💚</span>
            <span class="stat-title">健康度</span>
          </div>
          <div class="stat-value">{{ data.overview?.avg_health_score || 0 }}<span class="unit">%</span></div>
          <div class="health-bar">
            <div class="health-fill" :style="{ width: (data.overview?.avg_health_score || 0) + '%' }"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 主体内容 -->
    <div class="dashboard-grid">
      <!-- 左侧：项目状态 -->
      <div class="grid-left">
        <!-- 项目阶段分布 -->
        <div class="card">
          <div class="card-header">
            <h3>项目阶段分布</h3>
          </div>
          <div class="card-body">
            <div class="phase-chart">
              <div class="phase-item" v-for="(count, phase) in data.status_distribution" :key="phase">
                <div class="phase-bar" :style="{ width: getPhaseWidth(count) + '%' }" :class="phase"></div>
                <div class="phase-info">
                  <span class="phase-name">{{ phaseLabels[phase] }}</span>
                  <span class="phase-count">{{ count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 重点项目进度 -->
        <div class="card">
          <div class="card-header">
            <h3>重点项目进度</h3>
            <router-link to="/pmo/projects" class="view-all">查看全部 →</router-link>
          </div>
          <div class="card-body">
            <div class="project-list">
              <div class="project-item" v-for="project in data.key_projects" :key="project.id"
                   @click="goToProject(project.id)">
                <div class="project-info">
                  <span class="project-level" :class="'level-' + project.level.toLowerCase()">{{ project.level }}</span>
                  <span class="project-name">{{ project.name }}</span>
                </div>
                <div class="project-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: project.progress + '%' }" :class="project.health"></div>
                  </div>
                  <span class="progress-text">{{ project.progress }}%</span>
                </div>
                <div class="project-health" :class="project.health">
                  <span class="health-dot"></span>
                  {{ healthLabels[project.health] }}
                </div>
                <div class="project-pm">{{ project.pm_name }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 健康状态分布 -->
        <div class="card small">
          <div class="card-header">
            <h3>健康状态分布</h3>
          </div>
          <div class="card-body">
            <div class="health-distribution">
              <div class="health-item green" @click="filterByHealth('green')">
                <div class="health-count">{{ data.health_distribution?.green || 0 }}</div>
                <div class="health-label">正常</div>
              </div>
              <div class="health-item yellow" @click="filterByHealth('yellow')">
                <div class="health-count">{{ data.health_distribution?.yellow || 0 }}</div>
                <div class="health-label">预警</div>
              </div>
              <div class="health-item red" @click="filterByHealth('red')">
                <div class="health-count">{{ data.health_distribution?.red || 0 }}</div>
                <div class="health-label">问题</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：预警和资源 -->
      <div class="grid-right">
        <!-- 预警事项 -->
        <div class="card warning-card">
          <div class="card-header">
            <h3>🚨 预警事项</h3>
            <span class="warning-count">{{ data.warnings?.length || 0 }}</span>
          </div>
          <div class="card-body">
            <div class="warning-list">
              <div class="warning-item" v-for="(warning, idx) in data.warnings" :key="idx" :class="warning.type">
                <span class="warning-icon">{{ warning.type === 'red' ? '🔴' : '🟡' }}</span>
                <span class="warning-project">{{ warning.project }}</span>
                <span class="warning-content">{{ warning.content }}</span>
              </div>
              <div class="empty-warning" v-if="!data.warnings?.length">
                <span>✅ 暂无预警，项目运行正常</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 即将到期里程碑 -->
        <div class="card">
          <div class="card-header">
            <h3>📅 即将到期里程碑</h3>
          </div>
          <div class="card-body">
            <div class="milestone-list">
              <div class="milestone-item" v-for="(ms, idx) in data.upcoming_milestones" :key="idx">
                <div class="milestone-date" :class="{ urgent: isUrgent(ms.date) }">
                  <span class="date-day">{{ formatDay(ms.date) }}</span>
                  <span class="date-month">{{ formatMonth(ms.date) }}</span>
                </div>
                <div class="milestone-info">
                  <span class="milestone-name">{{ ms.milestone }}</span>
                  <span class="milestone-project">{{ ms.project }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 部门资源负荷 -->
        <div class="card">
          <div class="card-header">
            <h3>📊 部门资源负荷</h3>
          </div>
          <div class="card-body">
            <div class="workload-list">
              <div class="workload-item" v-for="dept in data.department_workload" :key="dept.dept">
                <div class="workload-header">
                  <span class="dept-name">{{ dept.dept }}</span>
                  <span class="workload-percent" :class="dept.status">{{ dept.workload }}%</span>
                </div>
                <div class="workload-bar">
                  <div class="workload-fill" :style="{ width: dept.workload + '%' }" :class="dept.status"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 周报弹窗 -->
    <div class="modal-overlay" v-if="showWeeklyReport" @click="showWeeklyReport = false">
      <div class="modal weekly-report-modal" @click.stop>
        <div class="modal-header">
          <h3>📋 项目管理部周报</h3>
          <button @click="showWeeklyReport = false">×</button>
        </div>
        <div class="modal-body">
          <div class="report-section">
            <h4>一、项目总体情况</h4>
            <div class="report-stats">
              <span>在建项目: {{ data.overview?.total_projects }}个</span>
              <span>健康项目: {{ data.health_distribution?.green }}个</span>
              <span>预警项目: {{ data.overview?.warning_projects }}个</span>
            </div>
          </div>
          <div class="report-section">
            <h4>二、本周预警事项</h4>
            <ul class="report-list">
              <li v-for="(w, idx) in data.warnings" :key="idx">
                {{ w.type === 'red' ? '🔴' : '🟡' }} {{ w.project }}: {{ w.content }}
              </li>
            </ul>
          </div>
          <div class="report-section">
            <h4>三、下周重点里程碑</h4>
            <ul class="report-list">
              <li v-for="(ms, idx) in data.upcoming_milestones" :key="idx">
                {{ ms.date }} {{ ms.project }} - {{ ms.milestone }}
              </li>
            </ul>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="exportReport">导出报告</button>
          <button class="btn-primary" @click="showWeeklyReport = false">关闭</button>
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
  status_distribution: {},
  health_distribution: {},
  department_workload: [],
  key_projects: [],
  warnings: [],
  upcoming_milestones: []
})

const showWeeklyReport = ref(false)

const currentDate = computed(() => {
  const d = new Date()
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
})

const phaseLabels = {
  initiation: '立项中',
  design: '设计中',
  production: '生产中',
  delivery: '交付中',
  closure: '结项中'
}

const healthLabels = {
  green: '正常',
  yellow: '预警',
  red: '问题'
}

const getPhaseWidth = (count) => {
  const total = Object.values(data.value.status_distribution).reduce((a, b) => a + b, 0)
  return total > 0 ? (count / total) * 100 : 0
}

const formatDay = (dateStr) => new Date(dateStr).getDate()
const formatMonth = (dateStr) => (new Date(dateStr).getMonth() + 1) + '月'
const isUrgent = (dateStr) => {
  const d = new Date(dateStr)
  const now = new Date()
  return (d - now) < 3 * 24 * 60 * 60 * 1000
}

const goToProject = (id) => router.push(`/pmo/projects/${id}`)
const filterByHealth = (health) => router.push(`/pmo/projects?health=${health}`)

const refreshData = async () => {
  try {
    const res = await request.get('/api/v1/pmo/dashboard')
    if (res.code === 200) data.value = res.data
  } catch (e) {
    data.value = getMockData()
  }
}

const exportReport = () => alert('导出功能开发中')

const getMockData = () => ({
  overview: { total_projects: 45, level_a: 12, level_b: 20, level_c: 13, this_month_delivery: 5, warning_projects: 8, avg_health_score: 82 },
  status_distribution: { initiation: 3, design: 15, production: 18, delivery: 6, closure: 3 },
  health_distribution: { green: 35, yellow: 8, red: 2 },
  department_workload: [
    { dept: '机械部', workload: 85, status: 'normal' },
    { dept: '电气部', workload: 95, status: 'overload' },
    { dept: '软件部', workload: 72, status: 'normal' },
    { dept: '装配组', workload: 78, status: 'normal' }
  ],
  key_projects: [
    { id: 1, name: 'XX汽车传感器测试设备', level: 'A', progress: 78, health: 'green', pm_name: '王经理' },
    { id: 2, name: 'YY新能源电池检测线', level: 'A', progress: 55, health: 'yellow', pm_name: '李经理' },
    { id: 3, name: 'ZZ医疗器械测试系统', level: 'B', progress: 35, health: 'red', pm_name: '张经理' }
  ],
  warnings: [
    { type: 'red', project: 'ZZ项目', content: '机械设计延期3天' },
    { type: 'red', project: 'YY项目', content: '关键物料未到货' },
    { type: 'yellow', project: 'AA项目', content: '客户需求变更' },
    { type: 'yellow', project: 'BB项目', content: '电气工程师请假' }
  ],
  upcoming_milestones: [
    { project: 'XX项目', milestone: '电气设计评审', date: '2025-01-05' },
    { project: 'YY项目', milestone: '软件联调', date: '2025-01-08' },
    { project: 'BB项目', milestone: '出厂检验', date: '2025-01-10' }
  ]
})

onMounted(() => refreshData())
</script>

<style scoped>
.pmo-dashboard { min-height: 100vh; background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); color: white; }
.page-header { padding: 24px 32px; display: flex; justify-content: space-between; align-items: center; }
.header-content { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.header-content h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.date-info { font-size: 14px; color: #94A3B8; }
.btn-primary, .btn-secondary { display: flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 10px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: linear-gradient(135deg, #6366F1, #4F46E5); color: white; }
.btn-secondary { background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2); }
.btn-primary svg, .btn-secondary svg { width: 18px; height: 18px; }

/* 统计概览 */
.stats-overview { padding: 0 32px 24px; }
.stats-row { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 20px; }
.stat-card { background: rgba(255,255,255,0.05); border-radius: 20px; padding: 24px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
.stat-card.large { padding: 28px; }
.stat-card.primary { background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(79,70,229,0.2)); border-color: rgba(99,102,241,0.3); }
.stat-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.stat-icon { font-size: 24px; }
.stat-title { font-size: 14px; color: #94A3B8; }
.stat-value { font-size: 42px; font-weight: 700; }
.stat-value .unit { font-size: 24px; font-weight: 400; color: #94A3B8; }
.stat-breakdown { display: flex; gap: 16px; margin-top: 12px; }
.breakdown-item { font-size: 13px; padding: 4px 10px; border-radius: 6px; }
.breakdown-item.a { background: rgba(99,102,241,0.2); color: #A5B4FC; }
.breakdown-item.b { background: rgba(245,158,11,0.2); color: #FCD34D; }
.breakdown-item.c { background: rgba(16,185,129,0.2); color: #6EE7B7; }
.stat-trend { font-size: 13px; color: #94A3B8; margin-top: 8px; }
.stat-trend.up { color: #10B981; }
.health-bar { height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-top: 12px; overflow: hidden; }
.health-fill { height: 100%; background: linear-gradient(90deg, #10B981, #34D399); border-radius: 4px; }

/* 主体布局 */
.dashboard-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; padding: 0 32px 32px; }
.grid-left { display: flex; flex-direction: column; gap: 20px; }
.grid-right { display: flex; flex-direction: column; gap: 20px; }

/* 卡片 */
.card { background: rgba(255,255,255,0.05); border-radius: 20px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); overflow: hidden; }
.card-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.card-header h3 { font-size: 16px; font-weight: 600; }
.view-all { font-size: 13px; color: #6366F1; text-decoration: none; }
.card-body { padding: 20px 24px; }

/* 项目阶段图 */
.phase-chart { display: flex; flex-direction: column; gap: 12px; }
.phase-item { display: flex; align-items: center; gap: 16px; }
.phase-bar { height: 24px; border-radius: 6px; min-width: 8px; }
.phase-bar.initiation { background: linear-gradient(90deg, #6366F1, #818CF8); }
.phase-bar.design { background: linear-gradient(90deg, #8B5CF6, #A78BFA); }
.phase-bar.production { background: linear-gradient(90deg, #F59E0B, #FBBF24); }
.phase-bar.delivery { background: linear-gradient(90deg, #10B981, #34D399); }
.phase-bar.closure { background: linear-gradient(90deg, #64748B, #94A3B8); }
.phase-info { display: flex; justify-content: space-between; flex: 1; }
.phase-name { font-size: 14px; color: #CBD5E1; }
.phase-count { font-size: 14px; font-weight: 600; }

/* 项目列表 */
.project-list { display: flex; flex-direction: column; gap: 12px; }
.project-item { display: grid; grid-template-columns: 2fr 1.5fr 80px 80px; align-items: center; gap: 16px; padding: 16px; background: rgba(255,255,255,0.03); border-radius: 12px; cursor: pointer; transition: all 0.2s; }
.project-item:hover { background: rgba(255,255,255,0.08); }
.project-info { display: flex; align-items: center; gap: 12px; }
.project-level { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.project-level.level-a { background: rgba(99,102,241,0.2); color: #A5B4FC; }
.project-level.level-b { background: rgba(245,158,11,0.2); color: #FCD34D; }
.project-level.level-c { background: rgba(16,185,129,0.2); color: #6EE7B7; }
.project-name { font-size: 14px; font-weight: 500; }
.project-progress { display: flex; align-items: center; gap: 10px; }
.project-progress .progress-bar { flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.project-progress .progress-fill { height: 100%; border-radius: 4px; }
.project-progress .progress-fill.green { background: #10B981; }
.project-progress .progress-fill.yellow { background: #F59E0B; }
.project-progress .progress-fill.red { background: #EF4444; }
.progress-text { font-size: 13px; font-weight: 600; width: 40px; }
.project-health { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.health-dot { width: 8px; height: 8px; border-radius: 50%; }
.project-health.green .health-dot { background: #10B981; }
.project-health.yellow .health-dot { background: #F59E0B; }
.project-health.red .health-dot { background: #EF4444; }
.project-pm { font-size: 13px; color: #94A3B8; }

/* 健康分布 */
.health-distribution { display: flex; justify-content: space-around; }
.health-item { text-align: center; padding: 20px; border-radius: 16px; cursor: pointer; transition: all 0.2s; flex: 1; }
.health-item:hover { transform: scale(1.05); }
.health-item.green { background: rgba(16,185,129,0.1); }
.health-item.yellow { background: rgba(245,158,11,0.1); }
.health-item.red { background: rgba(239,68,68,0.1); }
.health-count { font-size: 36px; font-weight: 700; }
.health-item.green .health-count { color: #10B981; }
.health-item.yellow .health-count { color: #F59E0B; }
.health-item.red .health-count { color: #EF4444; }
.health-label { font-size: 14px; color: #94A3B8; margin-top: 4px; }

/* 预警卡片 */
.warning-card .card-header { background: rgba(239,68,68,0.1); }
.warning-count { background: #EF4444; color: white; padding: 4px 10px; border-radius: 10px; font-size: 13px; font-weight: 600; }
.warning-list { display: flex; flex-direction: column; gap: 12px; }
.warning-item { display: flex; align-items: center; gap: 10px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 10px; border-left: 3px solid; }
.warning-item.red { border-color: #EF4444; }
.warning-item.yellow { border-color: #F59E0B; }
.warning-project { font-size: 13px; font-weight: 600; color: #CBD5E1; min-width: 60px; }
.warning-content { font-size: 14px; color: #94A3B8; }
.empty-warning { text-align: center; padding: 24px; color: #64748B; }

/* 里程碑 */
.milestone-list { display: flex; flex-direction: column; gap: 12px; }
.milestone-item { display: flex; align-items: center; gap: 16px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 10px; }
.milestone-date { text-align: center; min-width: 50px; }
.milestone-date.urgent { color: #EF4444; }
.date-day { font-size: 24px; font-weight: 700; display: block; }
.date-month { font-size: 12px; color: #94A3B8; }
.milestone-info { flex: 1; }
.milestone-name { font-size: 14px; font-weight: 500; display: block; }
.milestone-project { font-size: 12px; color: #94A3B8; }

/* 资源负荷 */
.workload-list { display: flex; flex-direction: column; gap: 16px; }
.workload-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.dept-name { font-size: 14px; }
.workload-percent { font-size: 14px; font-weight: 600; }
.workload-percent.normal { color: #10B981; }
.workload-percent.overload { color: #EF4444; }
.workload-bar { height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.workload-fill { height: 100%; border-radius: 4px; }
.workload-fill.normal { background: linear-gradient(90deg, #10B981, #34D399); }
.workload-fill.overload { background: linear-gradient(90deg, #EF4444, #F87171); }

/* 弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 100; display: flex; align-items: center; justify-content: center; }
.modal { background: #1E293B; border-radius: 20px; max-width: 600px; width: 90%; max-height: 80vh; overflow: hidden; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.modal-header h3 { font-size: 18px; }
.modal-header button { width: 32px; height: 32px; border: none; background: rgba(255,255,255,0.1); border-radius: 8px; color: white; font-size: 20px; cursor: pointer; }
.modal-body { padding: 24px; max-height: 60vh; overflow-y: auto; }
.report-section { margin-bottom: 24px; }
.report-section h4 { font-size: 15px; font-weight: 600; margin-bottom: 12px; color: #CBD5E1; }
.report-stats { display: flex; gap: 20px; }
.report-stats span { padding: 8px 16px; background: rgba(255,255,255,0.05); border-radius: 8px; font-size: 14px; }
.report-list { list-style: none; padding: 0; }
.report-list li { padding: 8px 0; font-size: 14px; color: #94A3B8; border-bottom: 1px solid rgba(255,255,255,0.05); }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 24px; border-top: 1px solid rgba(255,255,255,0.1); }

@media (max-width: 1200px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .dashboard-grid { grid-template-columns: 1fr; }
}
</style>
