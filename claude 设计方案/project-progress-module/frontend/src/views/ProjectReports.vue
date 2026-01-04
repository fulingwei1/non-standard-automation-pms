<template>
  <div class="project-reports-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-left">
        <h1>项目统计报表</h1>
        <p class="subtitle">项目进度、工时、成本综合分析</p>
      </div>
      <div class="header-actions">
        <select v-model="filter.year">
          <option value="2025">2025年</option>
          <option value="2024">2024年</option>
        </select>
        <button class="btn-primary" @click="exportReport">
          <span>📥</span> 导出报表
        </button>
      </div>
    </header>

    <!-- 报表标签页 -->
    <section class="report-tabs">
      <button :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'">
        📊 项目总览
      </button>
      <button :class="{ active: activeTab === 'progress' }" @click="activeTab = 'progress'">
        📈 进度分析
      </button>
      <button :class="{ active: activeTab === 'workload' }" @click="activeTab = 'workload'">
        ⏱️ 工时分析
      </button>
      <button :class="{ active: activeTab === 'efficiency' }" @click="activeTab = 'efficiency'">
        🎯 效率分析
      </button>
    </section>

    <!-- 项目总览 -->
    <section class="report-content" v-if="activeTab === 'overview'">
      <!-- 汇总指标 -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-icon">📁</div>
          <div class="card-body">
            <div class="card-value">{{ overview.total_projects }}</div>
            <div class="card-label">项目总数</div>
          </div>
        </div>
        <div class="summary-card active">
          <div class="card-icon">🔄</div>
          <div class="card-body">
            <div class="card-value">{{ overview.active_projects }}</div>
            <div class="card-label">进行中</div>
          </div>
        </div>
        <div class="summary-card success">
          <div class="card-icon">✅</div>
          <div class="card-body">
            <div class="card-value">{{ overview.completed_projects }}</div>
            <div class="card-label">已完成</div>
          </div>
        </div>
        <div class="summary-card warning">
          <div class="card-icon">⚠️</div>
          <div class="card-body">
            <div class="card-value">{{ overview.delayed_projects }}</div>
            <div class="card-label">延期项目</div>
          </div>
        </div>
      </div>

      <!-- 项目状态分布 -->
      <div class="charts-grid">
        <div class="chart-section">
          <div class="section-header">
            <h3>项目状态分布</h3>
          </div>
          <div class="status-distribution">
            <div class="status-item" v-for="item in overview.status_distribution" :key="item.status">
              <div class="status-bar">
                <div class="status-fill" :style="{ width: item.percent + '%', background: item.color }"></div>
              </div>
              <div class="status-info">
                <span class="status-name">{{ item.name }}</span>
                <span class="status-count">{{ item.count }} ({{ item.percent }}%)</span>
              </div>
            </div>
          </div>
        </div>

        <div class="chart-section">
          <div class="section-header">
            <h3>月度项目趋势</h3>
          </div>
          <div class="trend-chart-container">
            <div class="trend-chart">
              <div class="chart-bar" v-for="item in overview.monthly_trend" :key="item.month">
                <div class="bar-group">
                  <div class="bar new" :style="{ height: item.new * 8 + 'px' }" :title="'新增: ' + item.new"></div>
                  <div class="bar completed" :style="{ height: item.completed * 8 + 'px' }" :title="'完成: ' + item.completed"></div>
                </div>
                <span class="bar-label">{{ item.month }}</span>
              </div>
            </div>
            <div class="chart-legend">
              <span class="legend-item"><span class="dot new"></span>新增</span>
              <span class="legend-item"><span class="dot completed"></span>完成</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 项目列表 -->
      <div class="chart-section">
        <div class="section-header">
          <h3>项目进度概览</h3>
          <input type="text" v-model="filter.keyword" placeholder="搜索项目..." class="search-input" />
        </div>
        <div class="project-table">
          <div class="table-header">
            <span class="col-name">项目名称</span>
            <span class="col-pm">项目经理</span>
            <span class="col-progress">进度</span>
            <span class="col-date">计划完成</span>
            <span class="col-status">状态</span>
            <span class="col-health">健康度</span>
          </div>
          <div class="table-body">
            <div class="table-row" v-for="project in overview.project_list" :key="project.id">
              <span class="col-name">
                <span class="project-name">{{ project.name }}</span>
                <span class="project-code">{{ project.code }}</span>
              </span>
              <span class="col-pm">{{ project.pm }}</span>
              <span class="col-progress">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: project.progress + '%' }"></div>
                </div>
                <span class="progress-text">{{ project.progress }}%</span>
              </span>
              <span class="col-date">{{ project.plan_end_date }}</span>
              <span class="col-status">
                <span class="status-badge" :class="project.status">{{ project.status_label }}</span>
              </span>
              <span class="col-health">
                <span class="health-indicator" :class="project.health"></span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 进度分析 -->
    <section class="report-content" v-if="activeTab === 'progress'">
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-value">{{ progressData.avg_progress }}%</div>
          <div class="card-label">平均进度</div>
        </div>
        <div class="summary-card success">
          <div class="card-value">{{ progressData.on_schedule }}</div>
          <div class="card-label">按计划进行</div>
        </div>
        <div class="summary-card warning">
          <div class="card-value">{{ progressData.behind_schedule }}</div>
          <div class="card-label">进度落后</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ progressData.avg_deviation }}%</div>
          <div class="card-label">平均偏差</div>
        </div>
      </div>

      <!-- 进度对比 -->
      <div class="chart-section">
        <div class="section-header">
          <h3>计划vs实际进度对比</h3>
        </div>
        <div class="comparison-list">
          <div class="comparison-item" v-for="project in progressData.comparison" :key="project.id">
            <div class="project-info">
              <span class="project-name">{{ project.name }}</span>
            </div>
            <div class="comparison-bars">
              <div class="bar-row">
                <span class="bar-label">计划</span>
                <div class="bar-track">
                  <div class="bar-fill plan" :style="{ width: project.plan_progress + '%' }"></div>
                </div>
                <span class="bar-value">{{ project.plan_progress }}%</span>
              </div>
              <div class="bar-row">
                <span class="bar-label">实际</span>
                <div class="bar-track">
                  <div class="bar-fill actual" :style="{ width: project.actual_progress + '%' }"
                       :class="{ behind: project.actual_progress < project.plan_progress }"></div>
                </div>
                <span class="bar-value">{{ project.actual_progress }}%</span>
              </div>
            </div>
            <div class="deviation" :class="{ negative: project.deviation < 0 }">
              {{ project.deviation > 0 ? '+' : '' }}{{ project.deviation }}%
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 工时分析 -->
    <section class="report-content" v-if="activeTab === 'workload'">
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-value">{{ workloadData.total_hours }}</div>
          <div class="card-label">总工时(小时)</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ workloadData.plan_hours }}</div>
          <div class="card-label">计划工时</div>
        </div>
        <div class="summary-card" :class="workloadData.overtime_rate > 10 ? 'warning' : ''">
          <div class="card-value">{{ workloadData.overtime_rate }}%</div>
          <div class="card-label">加班比例</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ workloadData.avg_utilization }}%</div>
          <div class="card-label">平均利用率</div>
        </div>
      </div>

      <!-- 部门工时分布 -->
      <div class="charts-grid">
        <div class="chart-section">
          <div class="section-header">
            <h3>部门工时分布</h3>
          </div>
          <div class="dept-workload">
            <div class="dept-item" v-for="dept in workloadData.by_department" :key="dept.id">
              <div class="dept-info">
                <span class="dept-name">{{ dept.name }}</span>
                <span class="dept-hours">{{ dept.hours }}h</span>
              </div>
              <div class="dept-bar">
                <div class="dept-bar-fill" :style="{ width: dept.percent + '%' }"></div>
              </div>
              <span class="dept-percent">{{ dept.percent }}%</span>
            </div>
          </div>
        </div>

        <div class="chart-section">
          <div class="section-header">
            <h3>工时趋势</h3>
          </div>
          <div class="trend-chart">
            <div class="chart-bar" v-for="item in workloadData.trend" :key="item.week">
              <div class="bar-fill" :style="{ height: (item.hours / 500 * 100) + '%' }">
                <span class="bar-value">{{ item.hours }}h</span>
              </div>
              <span class="bar-label">{{ item.week }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 人员工时排名 -->
      <div class="chart-section">
        <div class="section-header">
          <h3>人员工时排名 TOP10</h3>
        </div>
        <div class="ranking-list">
          <div class="ranking-item" v-for="(person, idx) in workloadData.top_workers" :key="person.id">
            <span class="rank" :class="{ top3: idx < 3 }">{{ idx + 1 }}</span>
            <span class="person-name">{{ person.name }}</span>
            <span class="person-dept">{{ person.department }}</span>
            <div class="hours-bar">
              <div class="hours-fill" :style="{ width: (person.hours / 200 * 100) + '%' }"></div>
            </div>
            <span class="person-hours">{{ person.hours }}h</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 效率分析 -->
    <section class="report-content" v-if="activeTab === 'efficiency'">
      <div class="summary-cards">
        <div class="summary-card success">
          <div class="card-value">{{ efficiencyData.on_time_rate }}%</div>
          <div class="card-label">按时完成率</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ efficiencyData.first_pass_rate }}%</div>
          <div class="card-label">一次通过率</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ efficiencyData.rework_rate }}%</div>
          <div class="card-label">返工率</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ efficiencyData.efficiency_index }}</div>
          <div class="card-label">效率指数</div>
        </div>
      </div>

      <!-- 项目效率对比 -->
      <div class="chart-section">
        <div class="section-header">
          <h3>项目效率对比</h3>
        </div>
        <div class="efficiency-table">
          <div class="table-header">
            <span>项目</span>
            <span>按时率</span>
            <span>一次通过</span>
            <span>返工率</span>
            <span>工时效率</span>
            <span>综合评分</span>
          </div>
          <div class="table-body">
            <div class="table-row" v-for="project in efficiencyData.by_project" :key="project.id">
              <span>{{ project.name }}</span>
              <span :class="getScoreClass(project.on_time_rate)">{{ project.on_time_rate }}%</span>
              <span :class="getScoreClass(project.first_pass_rate)">{{ project.first_pass_rate }}%</span>
              <span :class="getScoreClass(100 - project.rework_rate, true)">{{ project.rework_rate }}%</span>
              <span :class="getScoreClass(project.hour_efficiency)">{{ project.hour_efficiency }}%</span>
              <span class="score-badge" :class="getScoreClass(project.score)">{{ project.score }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const activeTab = ref('overview')
const filter = reactive({ year: '2025', keyword: '' })

const overview = reactive({
  total_projects: 45,
  active_projects: 18,
  completed_projects: 22,
  delayed_projects: 5,
  status_distribution: [
    { status: 'active', name: '进行中', count: 18, percent: 40, color: '#6366F1' },
    { status: 'completed', name: '已完成', count: 22, percent: 49, color: '#10B981' },
    { status: 'delayed', name: '延期', count: 5, percent: 11, color: '#EF4444' }
  ],
  monthly_trend: [
    { month: '1月', new: 5, completed: 3 },
    { month: '2月', new: 4, completed: 4 },
    { month: '3月', new: 6, completed: 5 },
    { month: '4月', new: 3, completed: 4 },
    { month: '5月', new: 5, completed: 6 },
    { month: '6月', new: 4, completed: 3 }
  ],
  project_list: [
    { id: 1, code: 'PRJ-2025-001', name: 'XX汽车传感器测试设备', pm: '张工', progress: 75, plan_end_date: '2025-02-28', status: 'active', status_label: '进行中', health: 'good' },
    { id: 2, code: 'PRJ-2025-002', name: 'YY新能源电池检测线', pm: '李工', progress: 45, plan_end_date: '2025-03-15', status: 'delayed', status_label: '延期风险', health: 'warning' },
    { id: 3, code: 'PRJ-2025-003', name: 'ZZ医疗器械测试系统', pm: '王工', progress: 90, plan_end_date: '2025-01-20', status: 'active', status_label: '进行中', health: 'good' }
  ]
})

const progressData = reactive({
  avg_progress: 68,
  on_schedule: 12,
  behind_schedule: 6,
  avg_deviation: -5.2,
  comparison: [
    { id: 1, name: 'XX汽车传感器测试设备', plan_progress: 80, actual_progress: 75, deviation: -5 },
    { id: 2, name: 'YY新能源电池检测线', plan_progress: 60, actual_progress: 45, deviation: -15 },
    { id: 3, name: 'ZZ医疗器械测试系统', plan_progress: 85, actual_progress: 90, deviation: 5 }
  ]
})

const workloadData = reactive({
  total_hours: 12580,
  plan_hours: 11500,
  overtime_rate: 8.5,
  avg_utilization: 85,
  by_department: [
    { id: 1, name: '机械部', hours: 4200, percent: 33 },
    { id: 2, name: '电气部', hours: 3800, percent: 30 },
    { id: 3, name: '软件部', hours: 2500, percent: 20 },
    { id: 4, name: '调试部', hours: 2080, percent: 17 }
  ],
  trend: [
    { week: 'W1', hours: 420 },
    { week: 'W2', hours: 385 },
    { week: 'W3', hours: 450 },
    { week: 'W4', hours: 410 }
  ],
  top_workers: [
    { id: 1, name: '张三', department: '机械部', hours: 185 },
    { id: 2, name: '李四', department: '电气部', hours: 172 },
    { id: 3, name: '王五', department: '软件部', hours: 168 },
    { id: 4, name: '赵六', department: '调试部', hours: 155 },
    { id: 5, name: '钱七', department: '机械部', hours: 148 }
  ]
})

const efficiencyData = reactive({
  on_time_rate: 85,
  first_pass_rate: 78,
  rework_rate: 12,
  efficiency_index: 0.82,
  by_project: [
    { id: 1, name: 'XX汽车传感器测试设备', on_time_rate: 88, first_pass_rate: 82, rework_rate: 8, hour_efficiency: 92, score: 88 },
    { id: 2, name: 'YY新能源电池检测线', on_time_rate: 72, first_pass_rate: 70, rework_rate: 18, hour_efficiency: 78, score: 72 },
    { id: 3, name: 'ZZ医疗器械测试系统', on_time_rate: 95, first_pass_rate: 88, rework_rate: 5, hour_efficiency: 95, score: 93 }
  ]
})

const getScoreClass = (score, inverse = false) => {
  const val = inverse ? 100 - score : score
  if (val >= 85) return 'excellent'
  if (val >= 70) return 'good'
  if (val >= 60) return 'warning'
  return 'danger'
}

const exportReport = () => alert('报表导出功能开发中...')
</script>

<style scoped>
.project-reports-page { min-height: 100vh; background: #0f172a; color: white; padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.header-actions { display: flex; gap: 16px; align-items: center; }
.header-actions select { padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; }
.btn-primary { padding: 10px 20px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; border-radius: 10px; color: white; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; }

.report-tabs { display: flex; gap: 8px; margin-bottom: 24px; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 12px; }
.report-tabs button { flex: 1; padding: 12px 20px; background: transparent; border: none; border-radius: 8px; color: #94A3B8; font-size: 14px; cursor: pointer; }
.report-tabs button.active { background: rgba(99,102,241,0.2); color: white; }

.summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.summary-card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 16px; border: 1px solid rgba(255,255,255,0.1); }
.summary-card.active { border-color: rgba(99,102,241,0.3); }
.summary-card.success { border-color: rgba(16,185,129,0.3); }
.summary-card.warning { border-color: rgba(245,158,11,0.3); }
.card-icon { font-size: 28px; }
.card-value { font-size: 28px; font-weight: 700; }
.summary-card.success .card-value { color: #10B981; }
.summary-card.warning .card-value { color: #F59E0B; }
.card-label { font-size: 13px; color: #94A3B8; margin-top: 4px; }

.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.chart-section { background: rgba(255,255,255,0.03); border-radius: 16px; padding: 24px; margin-bottom: 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.section-header h3 { font-size: 16px; font-weight: 600; }
.search-input { padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; width: 200px; }

.status-distribution { display: flex; flex-direction: column; gap: 16px; }
.status-item { display: flex; align-items: center; gap: 12px; }
.status-bar { flex: 1; height: 24px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.status-fill { height: 100%; border-radius: 4px; }
.status-info { width: 160px; display: flex; justify-content: space-between; font-size: 13px; }

.trend-chart-container { display: flex; flex-direction: column; }
.trend-chart { display: flex; justify-content: space-around; align-items: flex-end; height: 160px; }
.chart-bar { display: flex; flex-direction: column; align-items: center; }
.bar-group { display: flex; gap: 4px; align-items: flex-end; }
.bar { width: 20px; border-radius: 3px 3px 0 0; }
.bar.new { background: #6366F1; }
.bar.completed { background: #10B981; }
.bar-label { font-size: 12px; color: #64748B; margin-top: 8px; }
.chart-legend { display: flex; justify-content: center; gap: 20px; margin-top: 16px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #94A3B8; }
.dot { width: 10px; height: 10px; border-radius: 2px; }
.dot.new { background: #6366F1; }
.dot.completed { background: #10B981; }

.project-table, .efficiency-table { overflow-x: auto; }
.table-header { display: grid; grid-template-columns: 1.5fr 100px 150px 100px 100px 80px; gap: 12px; padding: 12px 16px; background: rgba(255,255,255,0.05); border-radius: 8px 8px 0 0; font-size: 13px; color: #94A3B8; }
.table-row { display: grid; grid-template-columns: 1.5fr 100px 150px 100px 100px 80px; gap: 12px; padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); align-items: center; font-size: 14px; }
.col-name .project-name { display: block; }
.col-name .project-code { font-size: 12px; color: #64748B; }
.progress-bar { width: 80px; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; display: inline-block; vertical-align: middle; }
.progress-fill { height: 100%; background: #6366F1; border-radius: 4px; }
.progress-text { font-size: 13px; margin-left: 8px; }
.status-badge { padding: 4px 10px; border-radius: 6px; font-size: 12px; }
.status-badge.active { background: rgba(99,102,241,0.2); color: #A5B4FC; }
.status-badge.delayed { background: rgba(239,68,68,0.2); color: #EF4444; }
.health-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.health-indicator.good { background: #10B981; }
.health-indicator.warning { background: #F59E0B; }
.health-indicator.danger { background: #EF4444; }

.comparison-list { display: flex; flex-direction: column; gap: 20px; }
.comparison-item { display: grid; grid-template-columns: 200px 1fr 60px; gap: 16px; align-items: center; }
.comparison-bars { display: flex; flex-direction: column; gap: 8px; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-row .bar-label { width: 40px; font-size: 12px; color: #64748B; }
.bar-track { flex: 1; height: 16px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.bar-fill.plan { background: rgba(99,102,241,0.5); }
.bar-fill.actual { background: #10B981; }
.bar-fill.actual.behind { background: #EF4444; }
.bar-row .bar-value { width: 50px; font-size: 13px; text-align: right; }
.deviation { font-size: 14px; font-weight: 600; color: #10B981; }
.deviation.negative { color: #EF4444; }

.dept-workload { display: flex; flex-direction: column; gap: 16px; }
.dept-item { display: flex; align-items: center; gap: 12px; }
.dept-info { width: 100px; display: flex; justify-content: space-between; }
.dept-name { font-size: 14px; }
.dept-hours { font-size: 13px; color: #64748B; }
.dept-bar { flex: 1; height: 12px; background: rgba(255,255,255,0.1); border-radius: 6px; overflow: hidden; }
.dept-bar-fill { height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6); border-radius: 6px; }
.dept-percent { width: 40px; font-size: 13px; color: #94A3B8; }

.ranking-list { display: flex; flex-direction: column; gap: 12px; }
.ranking-item { display: flex; align-items: center; gap: 16px; padding: 12px; background: rgba(255,255,255,0.02); border-radius: 10px; }
.rank { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); border-radius: 6px; font-size: 14px; font-weight: 600; }
.rank.top3 { background: linear-gradient(135deg, #F59E0B, #D97706); }
.person-name { width: 80px; font-size: 14px; }
.person-dept { width: 80px; font-size: 13px; color: #64748B; }
.hours-bar { flex: 1; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.hours-fill { height: 100%; background: #6366F1; border-radius: 4px; }
.person-hours { width: 60px; font-size: 14px; font-weight: 600; text-align: right; }

.efficiency-table .table-header { grid-template-columns: 1.5fr repeat(5, 1fr); }
.efficiency-table .table-row { grid-template-columns: 1.5fr repeat(5, 1fr); }
.excellent { color: #10B981; }
.good { color: #6366F1; }
.warning { color: #F59E0B; }
.danger { color: #EF4444; }
.score-badge { padding: 4px 12px; border-radius: 6px; font-weight: 600; }
.score-badge.excellent { background: rgba(16,185,129,0.2); }
.score-badge.good { background: rgba(99,102,241,0.2); }
.score-badge.warning { background: rgba(245,158,11,0.2); }
.score-badge.danger { background: rgba(239,68,68,0.2); }

.bar-fill { width: 40px; background: linear-gradient(180deg, #6366F1, #8B5CF6); border-radius: 4px 4px 0 0; display: flex; align-items: flex-start; justify-content: center; padding-top: 8px; min-height: 20px; }
.bar-value { font-size: 11px; font-weight: 600; }
</style>
