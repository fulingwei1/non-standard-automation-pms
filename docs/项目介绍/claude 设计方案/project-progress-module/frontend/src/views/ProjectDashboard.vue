<template>
  <div class="project-dashboard">
    <!-- 头部信息 -->
    <div class="dashboard-header">
      <div class="project-info">
        <h2>{{ project.project_name }}</h2>
        <div class="project-meta">
          <el-tag>{{ project.project_code }}</el-tag>
          <el-tag :type="getLevelType(project.project_level)">{{ project.project_level }}级</el-tag>
          <el-tag :type="getStatusType(project.status)">{{ project.status }}</el-tag>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="refreshData"><el-icon><Refresh /></el-icon> 刷新</el-button>
        <el-button type="primary" @click="goToGantt"><el-icon><DataLine /></el-icon> 甘特图</el-button>
      </div>
    </div>
    
    <!-- 核心指标卡片 -->
    <el-row :gutter="16" class="kpi-cards">
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-icon" style="background: #1890ff"><el-icon><TrendCharts /></el-icon></div>
          <div class="kpi-content">
            <div class="kpi-label">项目进度</div>
            <div class="kpi-value">{{ progress.progress_rate }}%</div>
            <el-progress :percentage="progress.progress_rate" :stroke-width="6" :show-text="false" />
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-icon" :style="{ background: getSpiColor(progress.spi) }"><el-icon><Odometer /></el-icon></div>
          <div class="kpi-content">
            <div class="kpi-label">SPI指数</div>
            <div class="kpi-value" :style="{ color: getSpiColor(progress.spi) }">{{ progress.spi?.toFixed(2) || '-' }}</div>
            <div class="kpi-sub">计划进度: {{ progress.plan_progress_rate }}%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-icon" style="background: #722ed1"><el-icon><Clock /></el-icon></div>
          <div class="kpi-content">
            <div class="kpi-label">工时消耗</div>
            <div class="kpi-value">{{ project.actual_manhours || 0 }}h</div>
            <div class="kpi-sub">计划: {{ project.plan_manhours || 0 }}h</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-icon" :style="{ background: getHealthColor(progress.health_status) }"><el-icon><CircleCheck /></el-icon></div>
          <div class="kpi-content">
            <div class="kpi-label">健康状态</div>
            <div class="kpi-value"><span class="health-dot" :style="{ background: getHealthColor(progress.health_status) }"></span> {{ getHealthText(progress.health_status) }}</div>
            <div class="kpi-sub">当前阶段: {{ progress.current_phase }}</div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 阶段进度和任务状态 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span>阶段进度</span></template>
          <div class="phase-progress">
            <div v-for="phase in progress.phase_progress" :key="phase.phase" class="phase-item">
              <div class="phase-name">{{ phase.phase }}</div>
              <div class="phase-bar"><el-progress :percentage="phase.progress" :stroke-width="16" :color="getPhaseColor(phase)" /></div>
              <div class="phase-status"><el-tag :type="getStatusType(phase.status)" size="small">{{ phase.status }}</el-tag></div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span>任务状态分布</span></template>
          <div ref="taskStatusChart" class="chart-container" style="height: 280px"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 进度趋势和团队负荷 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>进度趋势（S曲线）</span>
              <el-radio-group v-model="trendRange" size="small">
                <el-radio-button label="week">本周</el-radio-button>
                <el-radio-button label="month">本月</el-radio-button>
                <el-radio-button label="all">全部</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="progressTrendChart" class="chart-container" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header><span>团队成员负荷</span></template>
          <div class="workload-list">
            <div v-for="member in teamWorkload" :key="member.user_id" class="workload-item">
              <div class="member-info">
                <el-avatar :size="32">{{ member.user_name?.charAt(0) }}</el-avatar>
                <span class="member-name">{{ member.user_name }}</span>
              </div>
              <div class="workload-bar">
                <el-progress :percentage="Math.min(member.allocation_rate, 100)" :stroke-width="10" :color="getWorkloadColor(member.allocation_rate)" :show-text="false" />
              </div>
              <div class="workload-value" :class="{ 'is-overload': member.allocation_rate > 100 }">{{ member.allocation_rate }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 预警和任务 -->
    <el-row :gutter="16" class="list-row">
      <el-col :span="12">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Warning /></el-icon> 预警信息</span>
              <el-button link size="small" @click="goToAlerts">查看全部</el-button>
            </div>
          </template>
          <div class="alert-list" v-if="alerts.length > 0">
            <div v-for="alert in alerts.slice(0, 5)" :key="alert.alert_id" class="alert-item" :class="'level-' + alert.alert_level">
              <div class="alert-level"><span class="level-dot"></span></div>
              <div class="alert-content">
                <div class="alert-title">{{ alert.alert_title }}</div>
                <div class="alert-time">{{ alert.created_time }}</div>
              </div>
              <el-button size="small" @click="handleAlert(alert)">处理</el-button>
            </div>
          </div>
          <el-empty v-else description="暂无预警" :image-size="80" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Calendar /></el-icon> 近期到期任务</span>
              <el-button link size="small" @click="goToTasks">查看全部</el-button>
            </div>
          </template>
          <div class="task-list" v-if="upcomingTasks.length > 0">
            <div v-for="task in upcomingTasks.slice(0, 5)" :key="task.task_id" class="task-item" :class="{ 'is-overdue': isOverdue(task) }">
              <div class="task-info">
                <div class="task-name">{{ task.task_name }}</div>
                <div class="task-owner">{{ task.owner_name || '未分配' }}</div>
              </div>
              <el-progress type="circle" :percentage="task.progress_rate" :width="40" :stroke-width="4" />
              <div class="task-deadline">
                <div class="deadline-date">{{ formatDate(task.plan_end_date) }}</div>
                <div class="deadline-days" :class="{ 'is-urgent': getDaysLeft(task) <= 3 }">{{ getDaysText(task) }}</div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无近期任务" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, DataLine, TrendCharts, Odometer, Clock, CircleCheck, Warning, Calendar } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

const props = defineProps({ projectId: { type: Number, required: true } })
const router = useRouter()

const project = ref({})
const progress = ref({ progress_rate: 0, plan_progress_rate: 0, spi: 1, health_status: '绿', current_phase: '', phase_progress: [], task_status_count: {} })
const alerts = ref([])
const upcomingTasks = ref([])
const teamWorkload = ref([])
const trendRange = ref('month')

const taskStatusChart = ref(null)
const progressTrendChart = ref(null)
let statusChartInstance = null
let trendChartInstance = null

async function loadData() {
  // 模拟数据加载
  project.value = { project_code: 'PRJ-2025-001', project_name: '某客户自动化测试设备', project_level: 'A', status: '进行中', plan_manhours: 800, actual_manhours: 320 }
  progress.value = {
    progress_rate: 45, plan_progress_rate: 50, spi: 0.9, health_status: '黄', current_phase: '结构设计',
    phase_progress: [
      { phase: '立项启动', progress: 100, status: '已完成' },
      { phase: '方案设计', progress: 100, status: '已完成' },
      { phase: '结构设计', progress: 60, status: '进行中' },
      { phase: '电气设计', progress: 40, status: '进行中' },
      { phase: '采购制造', progress: 0, status: '未开始' },
      { phase: '装配调试', progress: 0, status: '未开始' },
      { phase: '验收交付', progress: 0, status: '未开始' }
    ],
    task_status_count: { '未开始': 15, '进行中': 8, '已完成': 12, '阻塞': 2 }
  }
  alerts.value = [
    { alert_id: 1, alert_title: '任务"电气设计"已逾期3天', alert_level: '红', created_time: '2025-01-02 10:00' },
    { alert_id: 2, alert_title: '任务"BOM清单"即将到期', alert_level: '黄', created_time: '2025-01-02 09:30' }
  ]
  upcomingTasks.value = [
    { task_id: 1, task_name: '总体方案设计', owner_name: '张工', progress_rate: 80, plan_end_date: '2025-01-05' },
    { task_id: 2, task_name: '机械结构设计', owner_name: '李工', progress_rate: 30, plan_end_date: '2025-01-10' },
    { task_id: 3, task_name: 'BOM清单编制', owner_name: '王工', progress_rate: 50, plan_end_date: '2025-01-03' }
  ]
  teamWorkload.value = [
    { user_id: 1, user_name: '张工', allocation_rate: 120 },
    { user_id: 2, user_name: '李工', allocation_rate: 95 },
    { user_id: 3, user_name: '王工', allocation_rate: 80 },
    { user_id: 4, user_name: '赵工', allocation_rate: 60 }
  ]
  nextTick(() => { renderStatusChart(); renderTrendChart() })
}

function renderStatusChart() {
  if (!taskStatusChart.value) return
  if (statusChartInstance) statusChartInstance.dispose()
  statusChartInstance = echarts.init(taskStatusChart.value)
  const statusData = progress.value.task_status_count || {}
  const data = [
    { name: '未开始', value: statusData['未开始'] || 0, itemStyle: { color: '#d9d9d9' } },
    { name: '进行中', value: statusData['进行中'] || 0, itemStyle: { color: '#1890ff' } },
    { name: '已完成', value: statusData['已完成'] || 0, itemStyle: { color: '#52c41a' } },
    { name: '阻塞', value: statusData['阻塞'] || 0, itemStyle: { color: '#ff4d4f' } }
  ].filter(d => d.value > 0)
  statusChartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center' },
    series: [{ type: 'pie', radius: ['50%', '70%'], center: ['40%', '50%'], label: { show: false }, data }]
  })
}

function renderTrendChart() {
  if (!progressTrendChart.value) return
  if (trendChartInstance) trendChartInstance.dispose()
  trendChartInstance = echarts.init(progressTrendChart.value)
  const dates = [], planData = [], actualData = []
  for (let i = 0; i < 30; i++) {
    dates.push(dayjs().subtract(30 - i, 'day').format('MM-DD'))
    planData.push(Math.min(100, i * 3.3))
    actualData.push(Math.min(100, Math.max(0, i * 3 + Math.random() * 5 - 2)))
  }
  trendChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['计划进度', '实际进度'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { interval: 4 } },
    yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    series: [
      { name: '计划进度', type: 'line', data: planData, smooth: true, lineStyle: { type: 'dashed' }, itemStyle: { color: '#999' } },
      { name: '实际进度', type: 'line', data: actualData, smooth: true, areaStyle: { opacity: 0.2 }, itemStyle: { color: '#1890ff' } }
    ]
  })
}

function getLevelType(level) { return { A: 'danger', B: 'warning', C: 'success', D: 'info' }[level] || 'info' }
function getStatusType(status) { return { '未启动': 'info', '进行中': 'primary', '已完成': 'success', '阻塞': 'danger', '未开始': 'info' }[status] || 'info' }
function getSpiColor(spi) { if (spi >= 0.95) return '#52c41a'; if (spi >= 0.85) return '#faad14'; return '#ff4d4f' }
function getHealthColor(status) { return { '绿': '#52c41a', '黄': '#faad14', '红': '#ff4d4f' }[status] || '#52c41a' }
function getHealthText(status) { return { '绿': '正常', '黄': '关注', '红': '预警' }[status] || '正常' }
function getPhaseColor(phase) { if (phase.progress >= 100) return '#52c41a'; if (phase.progress > 0) return '#1890ff'; return '#d9d9d9' }
function getWorkloadColor(rate) { if (rate > 100) return '#ff4d4f'; if (rate > 80) return '#faad14'; return '#52c41a' }
function formatDate(date) { return dayjs(date).format('MM-DD') }
function isOverdue(task) { return dayjs(task.plan_end_date).isBefore(dayjs(), 'day') && task.progress_rate < 100 }
function getDaysLeft(task) { return dayjs(task.plan_end_date).diff(dayjs(), 'day') }
function getDaysText(task) {
  const days = getDaysLeft(task)
  if (days < 0) return `逾期${-days}天`
  if (days === 0) return '今日到期'
  return `剩余${days}天`
}

function refreshData() { loadData(); ElMessage.success('刷新成功') }
function goToGantt() { router.push(`/project/${props.projectId}/gantt`) }
function goToAlerts() { router.push(`/project/${props.projectId}/alerts`) }
function goToTasks() { router.push(`/project/${props.projectId}/tasks`) }
function handleAlert(alert) { ElMessage.info('处理预警: ' + alert.alert_title) }

onMounted(() => { loadData() })
</script>

<style lang="scss" scoped>
.project-dashboard { padding: 20px; background: #f5f5f5; min-height: 100vh; }

.dashboard-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px; padding: 20px; background: #fff; border-radius: 8px;
  h2 { margin: 0 0 8px 0; font-size: 20px; }
  .project-meta { display: flex; gap: 8px; }
  .header-actions { display: flex; gap: 8px; }
}

.kpi-cards { margin-bottom: 16px; }
.kpi-card {
  display: flex; align-items: center; gap: 16px;
  padding: 20px; background: #fff; border-radius: 8px;
  .kpi-icon {
    width: 48px; height: 48px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 24px;
  }
  .kpi-content { flex: 1; }
  .kpi-label { font-size: 13px; color: #999; margin-bottom: 4px; }
  .kpi-value { font-size: 24px; font-weight: 600; margin-bottom: 4px; }
  .kpi-sub { font-size: 12px; color: #999; }
  .health-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
}

.chart-row, .list-row { margin-bottom: 16px; }
.chart-card, .list-card { height: 100%; }
.chart-container { width: 100%; height: 280px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }

.phase-progress {
  .phase-item { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .phase-name { width: 80px; font-size: 13px; }
  .phase-bar { flex: 1; }
  .phase-status { width: 70px; }
}

.workload-list {
  .workload-item { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  .member-info { display: flex; align-items: center; gap: 8px; width: 100px; }
  .member-name { font-size: 13px; overflow: hidden; text-overflow: ellipsis; }
  .workload-bar { flex: 1; }
  .workload-value { width: 50px; text-align: right; font-weight: 600; &.is-overload { color: #ff4d4f; } }
}

.alert-list {
  .alert-item {
    display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 6px; margin-bottom: 8px; background: #fafafa;
    &.level-红 { background: #fff2f0; .level-dot { background: #ff4d4f; } }
    &.level-橙 { background: #fff7e6; .level-dot { background: #fa8c16; } }
    &.level-黄 { background: #fffbe6; .level-dot { background: #faad14; } }
    .alert-level { .level-dot { width: 8px; height: 8px; border-radius: 50%; } }
    .alert-content { flex: 1; .alert-title { font-size: 13px; margin-bottom: 4px; } .alert-time { font-size: 12px; color: #999; } }
  }
}

.task-list {
  .task-item {
    display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 6px; margin-bottom: 8px; background: #fafafa;
    &.is-overdue { background: #fff2f0; }
    .task-info { flex: 1; .task-name { font-size: 13px; margin-bottom: 4px; } .task-owner { font-size: 12px; color: #999; } }
    .task-deadline { text-align: right; .deadline-date { font-size: 13px; } .deadline-days { font-size: 12px; color: #999; &.is-urgent { color: #ff4d4f; font-weight: 600; } } }
  }
}
</style>
