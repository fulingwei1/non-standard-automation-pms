<template>
  <div class="dashboard" :class="{ loaded: isLoaded }">
    <!-- 顶部欢迎区 -->
    <header class="dash-header">
      <div class="header-bg">
        <div class="bg-pattern"></div>
        <div class="bg-gradient"></div>
      </div>
      <div class="header-content">
        <div class="welcome-area">
          <div class="greeting-row">
            <h1>
              <span class="greeting-text">{{ greeting }}，</span>
              <span class="user-name">{{ userName }}</span>
              <span class="wave">👋</span>
            </h1>
          </div>
          <p class="welcome-sub">{{ todayInfo }}</p>
        </div>
        <div class="header-actions">
          <button class="header-btn secondary" @click="showQuickActions = !showQuickActions">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            快捷操作
          </button>
          <button class="header-btn primary" @click="$router.push('/projects/new')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            新建项目
          </button>
        </div>
      </div>
    </header>

    <!-- 核心指标卡片 -->
    <section class="stats-section">
      <div class="stats-grid">
        <div 
          class="stat-card" 
          v-for="(stat, index) in stats" 
          :key="stat.id"
          :class="[stat.type, { animate: isLoaded }]"
          :style="{ '--delay': index * 0.1 + 's' }"
        >
          <div class="stat-glow" :style="{ background: stat.glowColor }"></div>
          <div class="stat-icon" :style="{ background: stat.iconBg }">
            <div v-html="stat.icon"></div>
          </div>
          <div class="stat-body">
            <div class="stat-value-row">
              <span class="stat-value" ref="statValues">{{ stat.displayValue }}</span>
              <span class="stat-unit">{{ stat.unit }}</span>
            </div>
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-trend" :class="stat.trendDir" v-if="stat.trend !== null">
              <svg v-if="stat.trendDir === 'up'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="18 15 12 9 6 15"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
              <span>{{ Math.abs(stat.trend) }}%</span>
            </div>
          </div>
          <div class="stat-chart">
            <svg viewBox="0 0 100 40" preserveAspectRatio="none">
              <defs>
                <linearGradient :id="'grad-' + stat.id" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" :stop-color="stat.chartColor" stop-opacity="0.3"/>
                  <stop offset="100%" :stop-color="stat.chartColor" stop-opacity="0"/>
                </linearGradient>
              </defs>
              <path :d="stat.areaPath" :fill="'url(#grad-' + stat.id + ')'" />
              <path :d="stat.linePath" fill="none" :stroke="stat.chartColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
        </div>
      </div>
    </section>

    <!-- 主内容区 -->
    <div class="dash-content">
      <!-- 左侧主区域 -->
      <div class="content-main">
        <!-- 进行中的项目 -->
        <section class="content-card projects-section">
          <div class="card-header">
            <div class="header-left">
              <h2>进行中的项目</h2>
              <span class="count-badge">{{ activeProjects.length }}</span>
            </div>
            <button class="view-all" @click="$router.push('/projects')">
              查看全部
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </button>
          </div>
          
          <div class="projects-grid">
            <div 
              class="project-card" 
              v-for="project in activeProjects" 
              :key="project.id"
              @click="$router.push(`/projects/${project.id}`)"
            >
              <div class="project-top">
                <div class="project-level" :class="'level-' + project.level.toLowerCase()">
                  {{ project.level }}
                </div>
                <div class="project-health" :class="project.health">
                  <span class="health-dot"></span>
                  <span class="health-text">{{ getHealthText(project.health) }}</span>
                </div>
              </div>
              
              <h3 class="project-name">{{ project.name }}</h3>
              <p class="project-customer">{{ project.customer }}</p>
              
              <div class="project-progress-section">
                <div class="progress-header">
                  <span>整体进度</span>
                  <span class="progress-percent">{{ project.progress }}%</span>
                </div>
                <div class="progress-track">
                  <div 
                    class="progress-fill" 
                    :style="{ 
                      width: project.progress + '%',
                      background: getProgressGradient(project.progress)
                    }"
                  >
                    <div class="progress-glow"></div>
                  </div>
                </div>
              </div>
              
              <div class="project-footer">
                <div class="footer-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2"/>
                    <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
                    <line x1="3" y1="10" x2="21" y2="10"/>
                  </svg>
                  <span>{{ project.deadline }}</span>
                </div>
                <div class="team-avatars">
                  <div 
                    class="avatar" 
                    v-for="(member, i) in project.team.slice(0, 3)" 
                    :key="i"
                    :style="{ background: member.color, zIndex: 3 - i }"
                  >{{ member.name[0] }}</div>
                  <div class="avatar more" v-if="project.team.length > 3">
                    +{{ project.team.length - 3 }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 我的任务 -->
        <section class="content-card tasks-section">
          <div class="card-header">
            <div class="header-left">
              <h2>我的任务</h2>
            </div>
            <div class="tabs">
              <button 
                class="tab" 
                :class="{ active: taskTab === 'pending' }" 
                @click="taskTab = 'pending'"
              >
                待处理
                <span class="tab-count" v-if="pendingCount">{{ pendingCount }}</span>
              </button>
              <button 
                class="tab" 
                :class="{ active: taskTab === 'today' }" 
                @click="taskTab = 'today'"
              >
                今日到期
              </button>
              <button 
                class="tab" 
                :class="{ active: taskTab === 'overdue' }" 
                @click="taskTab = 'overdue'"
              >
                已逾期
                <span class="tab-count danger" v-if="overdueCount">{{ overdueCount }}</span>
              </button>
            </div>
          </div>
          
          <div class="tasks-list">
            <TransitionGroup name="task-list">
              <div 
                class="task-item" 
                v-for="task in displayedTasks" 
                :key="task.id"
                :class="{ completed: task.completed }"
              >
                <button 
                  class="task-check" 
                  :class="{ checked: task.completed }"
                  @click.stop="toggleTask(task)"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </button>
                
                <div class="task-content">
                  <div class="task-title">{{ task.title }}</div>
                  <div class="task-meta">
                    <span class="task-project">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                      </svg>
                      {{ task.projectName }}
                    </span>
                    <span class="task-due" :class="{ overdue: task.isOverdue }">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                      </svg>
                      {{ task.dueText }}
                    </span>
                  </div>
                </div>
                
                <div class="task-priority" :class="task.priority">
                  {{ task.priorityLabel }}
                </div>
              </div>
            </TransitionGroup>
            
            <div class="empty-tasks" v-if="displayedTasks.length === 0">
              <div class="empty-icon">🎉</div>
              <p>太棒了！暂无{{ taskTabLabel }}任务</p>
            </div>
          </div>
        </section>
      </div>

      <!-- 右侧边栏 -->
      <aside class="content-sidebar">
        <!-- 今日安排 -->
        <section class="sidebar-card schedule-card">
          <div class="sidebar-header">
            <h3>今日安排</h3>
            <span class="today-date">{{ todayDate }}</span>
          </div>
          <div class="schedule-list">
            <div class="schedule-item" v-for="item in todaySchedule" :key="item.id">
              <div class="schedule-time">{{ item.time }}</div>
              <div class="schedule-content">
                <div class="schedule-indicator" :style="{ background: item.color }"></div>
                <div class="schedule-info">
                  <div class="schedule-title">{{ item.title }}</div>
                  <div class="schedule-location" v-if="item.location">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                      <circle cx="12" cy="10" r="3"/>
                    </svg>
                    {{ item.location }}
                  </div>
                </div>
              </div>
            </div>
            <div class="empty-schedule" v-if="todaySchedule.length === 0">
              <p>今日暂无安排</p>
            </div>
          </div>
        </section>

        <!-- 团队动态 -->
        <section class="sidebar-card activity-card">
          <div class="sidebar-header">
            <h3>团队动态</h3>
            <button class="refresh-btn" @click="refreshActivities">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
            </button>
          </div>
          <div class="activity-list">
            <div class="activity-item" v-for="activity in teamActivities" :key="activity.id">
              <div class="activity-avatar" :style="{ background: activity.color }">
                {{ activity.user[0] }}
              </div>
              <div class="activity-content">
                <p>
                  <strong>{{ activity.user }}</strong>
                  <span>{{ activity.action }}</span>
                </p>
                <span class="activity-time">{{ activity.time }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 快捷入口 -->
        <section class="sidebar-card shortcuts-card">
          <div class="sidebar-header">
            <h3>快捷入口</h3>
          </div>
          <div class="shortcuts-grid">
            <button class="shortcut-btn" @click="$router.push('/timesheet')">
              <span class="shortcut-icon">⏱️</span>
              <span>填报工时</span>
            </button>
            <button class="shortcut-btn" @click="$router.push('/my-tasks')">
              <span class="shortcut-icon">📋</span>
              <span>我的任务</span>
            </button>
            <button class="shortcut-btn" @click="$router.push('/alerts')">
              <span class="shortcut-icon">🔔</span>
              <span>预警中心</span>
            </button>
            <button class="shortcut-btn" @click="$router.push('/reports')">
              <span class="shortcut-icon">📊</span>
              <span>报表中心</span>
            </button>
          </div>
        </section>
      </aside>
    </div>

    <!-- 快捷操作面板 -->
    <Transition name="panel">
      <div class="quick-panel" v-if="showQuickActions" @click.self="showQuickActions = false">
        <div class="panel-content">
          <div class="panel-header">
            <h3>快捷操作</h3>
            <button class="panel-close" @click="showQuickActions = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div class="panel-grid">
            <button class="panel-btn" @click="quickAction('project')">
              <div class="btn-icon" style="background: linear-gradient(135deg, #6366F1, #4F46E5)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <span>新建项目</span>
            </button>
            <button class="panel-btn" @click="quickAction('task')">
              <div class="btn-icon" style="background: linear-gradient(135deg, #F59E0B, #D97706)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                </svg>
              </div>
              <span>新建任务</span>
            </button>
            <button class="panel-btn" @click="quickAction('timesheet')">
              <div class="btn-icon" style="background: linear-gradient(135deg, #10B981, #059669)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                </svg>
              </div>
              <span>填报工时</span>
            </button>
            <button class="panel-btn" @click="quickAction('report')">
              <div class="btn-icon" style="background: linear-gradient(135deg, #8B5CF6, #7C3AED)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
                  <line x1="6" y1="20" x2="6" y2="14"/>
                </svg>
              </div>
              <span>生成报表</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores'

const userStore = useUserStore()
const isLoaded = ref(false)
const taskTab = ref('pending')
const showQuickActions = ref(false)

// 用户信息
const userName = computed(() => userStore.userInfo?.name || '用户')

// 问候语
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了'
})

// 今日信息
const todayInfo = computed(() => {
  const now = new Date()
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${now.getMonth() + 1}月${now.getDate()}日 ${weekdays[now.getDay()]} · 您有 ${pendingCount.value} 个待办任务`
})

const todayDate = computed(() => {
  const now = new Date()
  return `${now.getMonth() + 1}月${now.getDate()}日`
})

// 生成迷你图数据
const generateSparkline = (data) => {
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * 100
    const y = 40 - ((v - min) / range) * 35
    return `${x},${y}`
  })
  const linePath = 'M' + points.join(' L')
  const areaPath = linePath + ` L100,40 L0,40 Z`
  return { linePath, areaPath }
}

// 统计数据
const stats = computed(() => [
  {
    id: 'projects',
    label: '进行中项目',
    value: 12,
    displayValue: '12',
    unit: '个',
    trend: 8.2,
    trendDir: 'up',
    type: 'primary',
    iconBg: 'linear-gradient(135deg, #6366F1, #4F46E5)',
    chartColor: '#6366F1',
    glowColor: 'rgba(99, 102, 241, 0.15)',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
    ...generateSparkline([8, 9, 11, 10, 12, 11, 12])
  },
  {
    id: 'tasks',
    label: '待处理任务',
    value: 28,
    displayValue: '28',
    unit: '项',
    trend: -5.1,
    trendDir: 'down',
    type: 'warning',
    iconBg: 'linear-gradient(135deg, #F59E0B, #D97706)',
    chartColor: '#F59E0B',
    glowColor: 'rgba(245, 158, 11, 0.15)',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    ...generateSparkline([35, 32, 30, 28, 29, 27, 28])
  },
  {
    id: 'hours',
    label: '本月工时',
    value: 156,
    displayValue: '156',
    unit: 'h',
    trend: 12.5,
    trendDir: 'up',
    type: 'success',
    iconBg: 'linear-gradient(135deg, #10B981, #059669)',
    chartColor: '#10B981',
    glowColor: 'rgba(16, 185, 129, 0.15)',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    ...generateSparkline([80, 95, 110, 125, 140, 150, 156])
  },
  {
    id: 'alerts',
    label: '预警事项',
    value: 3,
    displayValue: '3',
    unit: '项',
    trend: null,
    trendDir: null,
    type: 'danger',
    iconBg: 'linear-gradient(135deg, #EF4444, #DC2626)',
    chartColor: '#EF4444',
    glowColor: 'rgba(239, 68, 68, 0.15)',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    ...generateSparkline([5, 4, 6, 3, 4, 2, 3])
  }
])

// 项目数据
const activeProjects = ref([
  { 
    id: 1, 
    name: 'XX公司自动化测试设备', 
    customer: 'XX科技有限公司', 
    level: 'A', 
    progress: 68, 
    health: 'good', 
    deadline: '03-15',
    team: [
      { name: '张三', color: '#6366F1' },
      { name: '李四', color: '#F59E0B' },
      { name: '王五', color: '#10B981' },
      { name: '赵六', color: '#EC4899' }
    ]
  },
  { 
    id: 2, 
    name: 'YY产线改造项目', 
    customer: 'YY电子科技', 
    level: 'B', 
    progress: 45, 
    health: 'warning', 
    deadline: '02-28',
    team: [
      { name: '张三', color: '#6366F1' },
      { name: '李四', color: '#F59E0B' }
    ]
  },
  { 
    id: 3, 
    name: 'ZZ检测系统开发', 
    customer: 'ZZ精密制造', 
    level: 'C', 
    progress: 82, 
    health: 'good', 
    deadline: '01-20',
    team: [
      { name: '王五', color: '#10B981' },
      { name: '赵六', color: '#EC4899' },
      { name: '钱七', color: '#8B5CF6' }
    ]
  }
])

// 任务数据
const tasks = ref([
  { id: 1, title: '完成机械结构3D建模', projectName: 'XX自动化测试设备', dueText: '今天', priority: 'high', priorityLabel: '紧急', completed: false, isOverdue: false, tab: 'today' },
  { id: 2, title: '电气原理图评审', projectName: 'YY产线改造', dueText: '明天', priority: 'medium', priorityLabel: '中等', completed: false, isOverdue: false, tab: 'pending' },
  { id: 3, title: '编写PLC程序框架', projectName: 'ZZ检测系统', dueText: '逾期2天', priority: 'high', priorityLabel: '紧急', completed: false, isOverdue: true, tab: 'overdue' },
  { id: 4, title: '采购清单确认', projectName: 'XX自动化测试设备', dueText: '后天', priority: 'low', priorityLabel: '普通', completed: false, isOverdue: false, tab: 'pending' },
  { id: 5, title: '客户需求确认会议', projectName: 'YY产线改造', dueText: '今天 14:00', priority: 'high', priorityLabel: '紧急', completed: false, isOverdue: false, tab: 'today' },
])

const pendingCount = computed(() => tasks.value.filter(t => !t.completed && t.tab === 'pending').length)
const overdueCount = computed(() => tasks.value.filter(t => !t.completed && t.tab === 'overdue').length)

const displayedTasks = computed(() => {
  return tasks.value.filter(t => t.tab === taskTab.value).slice(0, 5)
})

const taskTabLabel = computed(() => {
  const labels = { pending: '待处理', today: '今日到期', overdue: '逾期' }
  return labels[taskTab.value]
})

const toggleTask = (task) => {
  task.completed = !task.completed
}

// 今日安排
const todaySchedule = ref([
  { id: 1, time: '09:00', title: '项目晨会', location: '会议室A', color: '#6366F1' },
  { id: 2, time: '10:30', title: '设计评审会', location: '会议室B', color: '#F59E0B' },
  { id: 3, time: '14:00', title: '客户远程沟通', location: null, color: '#10B981' },
  { id: 4, time: '16:00', title: '周报撰写', location: null, color: '#8B5CF6' },
])

// 团队动态
const teamActivities = ref([
  { id: 1, user: '张三', action: '完成了任务「机械结构设计」', time: '10分钟前', color: '#6366F1' },
  { id: 2, user: '李四', action: '上传了文件「电气图纸v2.pdf」', time: '25分钟前', color: '#F59E0B' },
  { id: 3, user: '王五', action: '创建了新任务「调试程序」', time: '1小时前', color: '#10B981' },
  { id: 4, user: '赵六', action: '更新了项目进度至68%', time: '2小时前', color: '#EC4899' },
])

// 辅助函数
const getHealthText = (health) => {
  const map = { good: '健康', warning: '关注', critical: '异常' }
  return map[health] || health
}

const getProgressGradient = (progress) => {
  if (progress >= 80) return 'linear-gradient(90deg, #10B981, #34D399)'
  if (progress >= 50) return 'linear-gradient(90deg, #6366F1, #818CF8)'
  if (progress >= 30) return 'linear-gradient(90deg, #F59E0B, #FBBF24)'
  return 'linear-gradient(90deg, #EF4444, #F87171)'
}

const refreshActivities = () => {
  // 模拟刷新
}

const quickAction = (type) => {
  showQuickActions.value = false
  // 处理快捷操作
}

onMounted(() => {
  setTimeout(() => {
    isLoaded.value = true
  }, 100)
})
</script>

<style scoped>
/* ================================================
   Dashboard - World-Class Design System
   Inspired by: Stripe, Linear, Notion, Vercel
   ================================================ */

/* === Base Layout === */
.dashboard {
  min-height: 100vh;
  background: #F8FAFC;
}

/* === Header === */
.dash-header {
  position: relative;
  padding: 40px 48px 32px;
  overflow: hidden;
}

.header-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.bg-pattern {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle at 1px 1px, rgba(99, 102, 241, 0.08) 1px, transparent 0);
  background-size: 24px 24px;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.03) 50%, transparent 100%);
}

.header-content {
  position: relative;
  z-index: 1;
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.welcome-area h1 {
  font-size: 32px;
  font-weight: 700;
  color: #0F172A;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}

.user-name {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.wave {
  display: inline-block;
  animation: wave 1.8s ease-in-out infinite;
  transform-origin: 70% 70%;
  margin-left: 4px;
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  20% { transform: rotate(20deg); }
  40% { transform: rotate(-10deg); }
  60% { transform: rotate(10deg); }
  80% { transform: rotate(-5deg); }
}

.welcome-sub {
  font-size: 15px;
  color: #64748B;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.header-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.header-btn svg {
  width: 18px;
  height: 18px;
}

.header-btn.secondary {
  background: white;
  color: #475569;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
}

.header-btn.secondary:hover {
  background: #F8FAFC;
  box-shadow: 0 4px 6px rgba(0,0,0,0.07);
  transform: translateY(-1px);
}

.header-btn.primary {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  color: white;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.header-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
}

/* === Stats Section === */
.stats-section {
  padding: 0 48px 32px;
  max-width: 1536px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  position: relative;
  background: white;
  border-radius: 20px;
  padding: 24px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.04);
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card.animate {
  opacity: 1;
  transform: translateY(0);
  transition-delay: var(--delay);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.08);
}

.stat-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.6;
  pointer-events: none;
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  position: relative;
  z-index: 1;
}

.stat-icon :deep(svg) {
  width: 24px;
  height: 24px;
  color: white;
}

.stat-body {
  position: relative;
  z-index: 1;
}

.stat-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #0F172A;
  letter-spacing: -1px;
}

.stat-unit {
  font-size: 14px;
  color: #64748B;
  font-weight: 500;
}

.stat-label {
  font-size: 14px;
  color: #64748B;
  margin-bottom: 8px;
}

.stat-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 8px;
}

.stat-trend.up {
  color: #059669;
  background: rgba(16, 185, 129, 0.1);
}

.stat-trend.down {
  color: #DC2626;
  background: rgba(239, 68, 68, 0.1);
}

.stat-trend svg {
  width: 14px;
  height: 14px;
}

.stat-chart {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  opacity: 0.8;
}

.stat-chart svg {
  width: 100%;
  height: 100%;
}

/* === Content Layout === */
.dash-content {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  padding: 0 48px 48px;
  max-width: 1536px;
  margin: 0 auto;
}

.content-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* === Content Card === */
.content-card {
  background: white;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #0F172A;
}

.count-badge {
  background: #EEF2FF;
  color: #6366F1;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 8px;
}

.view-all {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #6366F1;
  background: none;
  border: none;
  cursor: pointer;
  transition: gap 0.2s;
}

.view-all:hover {
  gap: 8px;
}

.view-all svg {
  width: 16px;
  height: 16px;
}

/* === Projects Grid === */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.project-card {
  background: #FAFBFC;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 1px solid transparent;
}

.project-card:hover {
  background: white;
  border-color: #E2E8F0;
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
  transform: translateY(-2px);
}

.project-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.project-level {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
}

.project-level.level-a {
  background: linear-gradient(135deg, #6366F1, #4F46E5);
  color: white;
}

.project-level.level-b {
  background: linear-gradient(135deg, #F59E0B, #D97706);
  color: white;
}

.project-level.level-c {
  background: linear-gradient(135deg, #10B981, #059669);
  color: white;
}

.project-health {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.project-health.good .health-dot { background: #10B981; }
.project-health.good .health-text { color: #059669; }
.project-health.warning .health-dot { background: #F59E0B; }
.project-health.warning .health-text { color: #D97706; }
.project-health.critical .health-dot { background: #EF4444; }
.project-health.critical .health-text { color: #DC2626; }

.project-name {
  font-size: 15px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 4px;
  line-height: 1.4;
}

.project-customer {
  font-size: 13px;
  color: #64748B;
  margin-bottom: 16px;
}

.project-progress-section {
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #64748B;
}

.progress-percent {
  font-weight: 600;
  color: #0F172A;
}

.progress-track {
  height: 6px;
  background: #E2E8F0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  position: relative;
  transition: width 0.6s ease;
}

.progress-glow {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 20px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6));
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}

.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748B;
}

.footer-item svg {
  width: 14px;
  height: 14px;
}

.team-avatars {
  display: flex;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: white;
  border: 2px solid white;
  margin-left: -8px;
}

.avatar:first-child {
  margin-left: 0;
}

.avatar.more {
  background: #E2E8F0;
  color: #64748B;
  font-size: 10px;
}

/* === Tasks Section === */
.tabs {
  display: flex;
  gap: 4px;
  background: #F1F5F9;
  padding: 4px;
  border-radius: 10px;
}

.tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab.active {
  background: white;
  color: #0F172A;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.tab-count {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: #E2E8F0;
  color: #475569;
}

.tab-count.danger {
  background: #FEE2E2;
  color: #DC2626;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  background: #FAFBFC;
  border-radius: 12px;
  transition: all 0.2s;
}

.task-item:hover {
  background: #F1F5F9;
}

.task-item.completed {
  opacity: 0.5;
}

.task-item.completed .task-title {
  text-decoration: line-through;
}

.task-check {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: 2px solid #CBD5E1;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  margin-top: 2px;
}

.task-check svg {
  width: 12px;
  height: 12px;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.task-check:hover {
  border-color: #6366F1;
}

.task-check.checked {
  background: #6366F1;
  border-color: #6366F1;
}

.task-check.checked svg {
  opacity: 1;
}

.task-content {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-size: 14px;
  font-weight: 500;
  color: #0F172A;
  margin-bottom: 6px;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #64748B;
}

.task-project, .task-due {
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-meta svg {
  width: 12px;
  height: 12px;
}

.task-due.overdue {
  color: #DC2626;
}

.task-priority {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
  flex-shrink: 0;
}

.task-priority.high {
  background: #FEE2E2;
  color: #DC2626;
}

.task-priority.medium {
  background: #FEF3C7;
  color: #D97706;
}

.task-priority.low {
  background: #F1F5F9;
  color: #64748B;
}

.empty-tasks {
  text-align: center;
  padding: 40px;
  color: #64748B;
}

.empty-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

/* Transition animations */
.task-list-enter-active,
.task-list-leave-active {
  transition: all 0.3s ease;
}

.task-list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.task-list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* === Sidebar === */
.content-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sidebar-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.04);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sidebar-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
}

.today-date {
  font-size: 13px;
  color: #64748B;
}

.refresh-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: #F1F5F9;
  color: #64748B;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: #E2E8F0;
  color: #475569;
}

.refresh-btn svg {
  width: 16px;
  height: 16px;
}

/* === Schedule === */
.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.schedule-item {
  display: flex;
  gap: 14px;
}

.schedule-time {
  font-size: 13px;
  font-weight: 600;
  color: #64748B;
  width: 50px;
  flex-shrink: 0;
  padding-top: 2px;
}

.schedule-content {
  display: flex;
  gap: 12px;
  flex: 1;
}

.schedule-indicator {
  width: 4px;
  border-radius: 2px;
  flex-shrink: 0;
}

.schedule-info {
  flex: 1;
}

.schedule-title {
  font-size: 14px;
  font-weight: 500;
  color: #0F172A;
  margin-bottom: 4px;
}

.schedule-location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748B;
}

.schedule-location svg {
  width: 12px;
  height: 12px;
}

.empty-schedule {
  text-align: center;
  padding: 20px;
  color: #64748B;
  font-size: 14px;
}

/* === Activity === */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  gap: 12px;
}

.activity-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-content p {
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 4px;
}

.activity-content strong {
  color: #0F172A;
  font-weight: 600;
}

.activity-time {
  font-size: 11px;
  color: #94A3B8;
}

/* === Shortcuts === */
.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.shortcut-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #FAFBFC;
  border: 1px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.shortcut-btn:hover {
  background: white;
  border-color: #E2E8F0;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.shortcut-icon {
  font-size: 24px;
}

.shortcut-btn span:last-child {
  font-size: 13px;
  font-weight: 500;
  color: #475569;
}

/* === Quick Panel === */
.quick-panel {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-content {
  background: white;
  border-radius: 24px;
  padding: 32px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 25px 50px rgba(0,0,0,0.25);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.panel-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #0F172A;
}

.panel-close {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background: #F1F5F9;
  color: #64748B;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.panel-close:hover {
  background: #E2E8F0;
  color: #475569;
}

.panel-close svg {
  width: 18px;
  height: 18px;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.panel-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  background: #FAFBFC;
  border: 1px solid transparent;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.panel-btn:hover {
  background: white;
  border-color: #E2E8F0;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.btn-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.panel-btn span:last-child {
  font-size: 14px;
  font-weight: 500;
  color: #0F172A;
}

/* Panel Transition */
.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.3s ease;
}

.panel-enter-active .panel-content,
.panel-leave-active .panel-content {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}

.panel-enter-from .panel-content {
  transform: scale(0.9);
}

.panel-leave-to .panel-content {
  transform: scale(0.9);
}

/* === Responsive === */
@media (max-width: 1280px) {
  .dash-content {
    grid-template-columns: 1fr 340px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .dash-header {
    padding: 32px;
  }
  
  .stats-section,
  .dash-content {
    padding: 0 32px 32px;
  }
  
  .dash-content {
    grid-template-columns: 1fr;
  }
  
  .content-sidebar {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }
  
  .shortcuts-card {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .dash-header {
    padding: 24px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 20px;
  }
  
  .welcome-area h1 {
    font-size: 26px;
  }
  
  .stats-section,
  .dash-content {
    padding: 0 24px 24px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .content-sidebar {
    grid-template-columns: 1fr;
  }
  
  .shortcuts-card {
    grid-column: span 1;
  }
  
  .projects-grid {
    grid-template-columns: 1fr;
  }
  
  .content-card {
    padding: 20px;
  }
}
</style>
