<template>
  <div class="my-tasks-page">
    <div class="page-header">
      <h2>我的任务</h2>
      <div class="header-actions">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button label="list">列表</el-radio-button>
          <el-radio-button label="kanban">看板</el-radio-button>
          <el-radio-button label="calendar">日历</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="4"><div class="stat-card" :class="{ active: filterStatus === '' }" @click="filterStatus = ''"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">全部任务</div></div></el-col>
      <el-col :span="4"><div class="stat-card" :class="{ active: filterStatus === '进行中' }" @click="filterStatus = '进行中'"><div class="stat-value text-primary">{{ stats.inProgress }}</div><div class="stat-label">进行中</div></div></el-col>
      <el-col :span="4"><div class="stat-card" :class="{ active: filterStatus === '未开始' }" @click="filterStatus = '未开始'"><div class="stat-value text-info">{{ stats.pending }}</div><div class="stat-label">待开始</div></div></el-col>
      <el-col :span="4"><div class="stat-card" :class="{ active: filterStatus === '已完成' }" @click="filterStatus = '已完成'"><div class="stat-value text-success">{{ stats.completed }}</div><div class="stat-label">已完成</div></div></el-col>
      <el-col :span="4"><div class="stat-card overdue" :class="{ active: filterStatus === 'overdue' }" @click="filterStatus = 'overdue'"><div class="stat-value text-danger">{{ stats.overdue }}</div><div class="stat-label">已逾期</div></div></el-col>
      <el-col :span="4"><div class="stat-card" :class="{ active: filterStatus === '阻塞' }" @click="filterStatus = '阻塞'"><div class="stat-value text-warning">{{ stats.blocked }}</div><div class="stat-label">阻塞中</div></div></el-col>
    </el-row>
    
    <!-- 列表视图 -->
    <el-card v-if="viewMode === 'list'" class="task-list-card">
      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="搜索任务名称" prefix-icon="Search" clearable style="width: 200px" />
        <el-select v-model="filterProject" placeholder="全部项目" clearable style="width: 150px">
          <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-select v-model="sortBy" style="width: 120px">
          <el-option label="截止日期" value="deadline" />
          <el-option label="优先级" value="priority" />
          <el-option label="进度" value="progress" />
        </el-select>
      </div>
      
      <el-table :data="filteredTasks" v-loading="loading" @row-click="openTask">
        <el-table-column label="任务" min-width="280">
          <template #default="{ row }">
            <div class="task-cell">
              <el-checkbox :model-value="row.status === '已完成'" @change="toggleComplete(row)" @click.stop />
              <div class="task-info">
                <div class="task-name" :class="{ completed: row.status === '已完成' }">
                  {{ row.task_name }}
                  <el-tag v-if="row.is_critical" type="danger" size="small">关键</el-tag>
                </div>
                <div class="task-meta">
                  <span class="project-tag">{{ row.project_code }}</span>
                  <span class="phase">{{ row.phase }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="140">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress :percentage="row.progress_rate" :stroke-width="8" :color="getProgressColor(row)" :show-text="false" />
              <span>{{ row.progress_rate }}%</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-rate v-model="row.priority" :max="3" disabled size="small" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="110">
          <template #default="{ row }">
            <span :class="{ 'text-danger': isOverdue(row), 'text-warning': isUrgent(row) }">
              {{ formatDate(row.plan_end_date) }}
              <span v-if="isOverdue(row)" class="overdue-days">(逾期{{ getOverdueDays(row) }}天)</span>
              <span v-else-if="isUrgent(row)" class="urgent-days">({{ getDaysLeft(row) }}天)</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="工时" width="100">
          <template #default="{ row }">
            {{ row.actual_manhours || 0 }} / {{ row.plan_manhours || 0 }}h
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="updateProgress(row)">更新进度</el-button>
            <el-button link type="primary" size="small" @click.stop="openTask(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 看板视图 -->
    <div v-else-if="viewMode === 'kanban'" class="kanban-view">
      <div class="kanban-column" v-for="col in kanbanColumns" :key="col.status">
        <div class="column-header" :style="{ borderColor: col.color }">
          <span class="column-title">{{ col.title }}</span>
          <el-badge :value="getColumnTasks(col.status).length" type="info" />
        </div>
        <div class="column-body">
          <div v-for="task in getColumnTasks(col.status)" :key="task.task_id" class="kanban-card" @click="openTask(task)" draggable="true">
            <div class="card-header">
              <span class="project-code">{{ task.project_code }}</span>
              <el-tag v-if="task.is_critical" type="danger" size="small">关键</el-tag>
            </div>
            <div class="card-name">{{ task.task_name }}</div>
            <div class="card-progress">
              <el-progress :percentage="task.progress_rate" :stroke-width="6" :show-text="false" />
              <span>{{ task.progress_rate }}%</span>
            </div>
            <div class="card-footer">
              <span class="deadline" :class="{ overdue: isOverdue(task) }">
                <el-icon><Calendar /></el-icon> {{ formatDate(task.plan_end_date) }}
              </span>
              <el-rate v-model="task.priority" :max="3" disabled size="small" />
            </div>
          </div>
          <div v-if="getColumnTasks(col.status).length === 0" class="empty-column">暂无任务</div>
        </div>
      </div>
    </div>
    
    <!-- 日历视图 -->
    <el-card v-else class="calendar-card">
      <div class="calendar-header">
        <el-button :icon="ArrowLeft" circle size="small" @click="prevMonth" />
        <span class="current-month">{{ currentMonth }}</span>
        <el-button :icon="ArrowRight" circle size="small" @click="nextMonth" />
        <el-button size="small" @click="goToday">今天</el-button>
      </div>
      <div class="calendar-grid">
        <div class="weekday-header">
          <div v-for="d in ['日', '一', '二', '三', '四', '五', '六']" :key="d" class="weekday">{{ d }}</div>
        </div>
        <div class="days-grid">
          <div v-for="day in calendarDays" :key="day.key" class="day-cell" :class="{ 'other-month': !day.isCurrentMonth, 'is-today': day.isToday, 'has-tasks': day.tasks.length > 0 }">
            <div class="day-number">{{ day.dayNum }}</div>
            <div class="day-tasks">
              <div v-for="task in day.tasks.slice(0, 3)" :key="task.task_id" class="task-dot" :class="getStatusClass(task)" @click="openTask(task)" :title="task.task_name"></div>
              <span v-if="day.tasks.length > 3" class="more-tasks">+{{ day.tasks.length - 3 }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 更新进度对话框 -->
    <el-dialog v-model="showProgressDialog" title="更新任务进度" width="400px">
      <el-form v-if="currentTask" label-width="80px">
        <el-form-item label="任务名称">{{ currentTask.task_name }}</el-form-item>
        <el-form-item label="当前进度">
          <div class="progress-input">
            <el-slider v-model="progressValue" :max="100" show-input />
          </div>
        </el-form-item>
        <el-form-item label="工作内容">
          <el-input v-model="progressContent" type="textarea" :rows="3" placeholder="请描述今日工作内容..." />
        </el-form-item>
        <el-form-item label="状态变更">
          <el-select v-model="progressStatus" style="width: 100%">
            <el-option label="进行中" value="进行中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="阻塞" value="阻塞" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProgressDialog = false">取消</el-button>
        <el-button type="primary" @click="submitProgress" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 任务详情抽屉 -->
    <el-drawer v-model="showTaskDrawer" title="任务详情" size="500px">
      <TaskDetailPanel v-if="currentTask" :task="currentTask" :project-id="currentTask.project_id" @update="handleTaskUpdate" @close="showTaskDrawer = false" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import TaskDetailPanel from '@/components/TaskDetailPanel.vue'
import { getMyTasks, updateTaskProgress } from '@/api/task'

const loading = ref(false)
const submitting = ref(false)
const tasks = ref([])
const viewMode = ref('list')
const filterStatus = ref('')
const filterProject = ref('')
const keyword = ref('')
const sortBy = ref('deadline')

const showProgressDialog = ref(false)
const showTaskDrawer = ref(false)
const currentTask = ref(null)
const progressValue = ref(0)
const progressContent = ref('')
const progressStatus = ref('进行中')

const calendarDate = ref(dayjs())

const projects = ref([
  { id: 1, name: 'PRJ-001 某客户设备' },
  { id: 2, name: 'PRJ-002 电池检测设备' },
  { id: 3, name: 'PRJ-003 芯片测试平台' }
])

const kanbanColumns = [
  { status: '未开始', title: '待开始', color: '#d9d9d9' },
  { status: '进行中', title: '进行中', color: '#1890ff' },
  { status: '阻塞', title: '阻塞', color: '#faad14' },
  { status: '已完成', title: '已完成', color: '#52c41a' }
]

const stats = computed(() => ({
  total: tasks.value.length,
  inProgress: tasks.value.filter(t => t.status === '进行中').length,
  pending: tasks.value.filter(t => t.status === '未开始').length,
  completed: tasks.value.filter(t => t.status === '已完成').length,
  overdue: tasks.value.filter(t => isOverdue(t)).length,
  blocked: tasks.value.filter(t => t.status === '阻塞').length
}))

const filteredTasks = computed(() => {
  let result = [...tasks.value]
  if (filterStatus.value === 'overdue') result = result.filter(t => isOverdue(t))
  else if (filterStatus.value) result = result.filter(t => t.status === filterStatus.value)
  if (filterProject.value) result = result.filter(t => t.project_id === filterProject.value)
  if (keyword.value) result = result.filter(t => t.task_name.includes(keyword.value))
  if (sortBy.value === 'deadline') result.sort((a, b) => dayjs(a.plan_end_date).diff(dayjs(b.plan_end_date)))
  else if (sortBy.value === 'priority') result.sort((a, b) => b.priority - a.priority)
  else if (sortBy.value === 'progress') result.sort((a, b) => a.progress_rate - b.progress_rate)
  return result
})

const currentMonth = computed(() => calendarDate.value.format('YYYY年M月'))

const calendarDays = computed(() => {
  const days = []
  const start = calendarDate.value.startOf('month').startOf('week')
  const end = calendarDate.value.endOf('month').endOf('week')
  let current = start
  while (current.isBefore(end) || current.isSame(end, 'day')) {
    const dateStr = current.format('YYYY-MM-DD')
    days.push({
      key: dateStr,
      dayNum: current.date(),
      isCurrentMonth: current.month() === calendarDate.value.month(),
      isToday: current.isSame(dayjs(), 'day'),
      tasks: tasks.value.filter(t => t.plan_end_date === dateStr)
    })
    current = current.add(1, 'day')
  }
  return days
})

async function loadTasks() {
  loading.value = true
  try {
    const res = await getMyTasks()
    if (res.code === 200) tasks.value = res.data.list || []
  } finally { loading.value = false }
}

function getColumnTasks(status) { return tasks.value.filter(t => t.status === status) }
function isOverdue(task) { return task.status !== '已完成' && dayjs(task.plan_end_date).isBefore(dayjs(), 'day') }
function isUrgent(task) { const days = dayjs(task.plan_end_date).diff(dayjs(), 'day'); return days >= 0 && days <= 3 }
function getOverdueDays(task) { return dayjs().diff(dayjs(task.plan_end_date), 'day') }
function getDaysLeft(task) { return dayjs(task.plan_end_date).diff(dayjs(), 'day') }
function formatDate(d) { return d ? dayjs(d).format('MM-DD') : '-' }
function getStatusType(s) { return { '未开始': 'info', '进行中': 'primary', '已完成': 'success', '阻塞': 'warning' }[s] || 'info' }
function getStatusClass(task) { if (isOverdue(task)) return 'overdue'; return task.status === '已完成' ? 'completed' : 'active' }
function getProgressColor(task) { if (isOverdue(task)) return '#ff4d4f'; if (task.progress_rate >= 80) return '#52c41a'; return '#1890ff' }

function toggleComplete(task) { task.status = task.status === '已完成' ? '进行中' : '已完成'; task.progress_rate = task.status === '已完成' ? 100 : task.progress_rate }
function openTask(task) { currentTask.value = task; showTaskDrawer.value = true }
function updateProgress(task) { currentTask.value = task; progressValue.value = task.progress_rate; progressStatus.value = task.status; progressContent.value = ''; showProgressDialog.value = true }

async function submitProgress() {
  submitting.value = true
  try {
    await updateTaskProgress(currentTask.value.task_id, { progress_rate: progressValue.value, status: progressStatus.value, content: progressContent.value })
    currentTask.value.progress_rate = progressValue.value
    currentTask.value.status = progressStatus.value
    ElMessage.success('进度更新成功')
    showProgressDialog.value = false
  } finally { submitting.value = false }
}

function handleTaskUpdate(task) { const idx = tasks.value.findIndex(t => t.task_id === task.task_id); if (idx !== -1) tasks.value[idx] = { ...tasks.value[idx], ...task } }
function prevMonth() { calendarDate.value = calendarDate.value.subtract(1, 'month') }
function nextMonth() { calendarDate.value = calendarDate.value.add(1, 'month') }
function goToday() { calendarDate.value = dayjs() }

onMounted(() => {
  tasks.value = [
    { task_id: 1, project_id: 1, project_code: 'PRJ-001', task_name: '总体方案设计', phase: '方案设计', progress_rate: 80, status: '进行中', priority: 3, plan_manhours: 40, actual_manhours: 32, plan_end_date: '2025-01-05', is_critical: true },
    { task_id: 2, project_id: 1, project_code: 'PRJ-001', task_name: '机械结构设计', phase: '结构设计', progress_rate: 30, status: '进行中', priority: 2, plan_manhours: 80, actual_manhours: 24, plan_end_date: '2025-01-15', is_critical: false },
    { task_id: 3, project_id: 1, project_code: 'PRJ-001', task_name: 'BOM清单编制', phase: '结构设计', progress_rate: 50, status: '进行中', priority: 2, plan_manhours: 16, actual_manhours: 8, plan_end_date: '2025-01-03', is_critical: true },
    { task_id: 4, project_id: 2, project_code: 'PRJ-002', task_name: '电气原理图设计', phase: '电气设计', progress_rate: 60, status: '阻塞', priority: 3, plan_manhours: 40, actual_manhours: 24, plan_end_date: '2024-12-30', is_critical: true },
    { task_id: 5, project_id: 2, project_code: 'PRJ-002', task_name: 'PLC程序编写', phase: '电气设计', progress_rate: 0, status: '未开始', priority: 2, plan_manhours: 60, actual_manhours: 0, plan_end_date: '2025-01-20', is_critical: false },
    { task_id: 6, project_id: 1, project_code: 'PRJ-001', task_name: '技术评审', phase: '方案设计', progress_rate: 100, status: '已完成', priority: 3, plan_manhours: 8, actual_manhours: 8, plan_end_date: '2024-12-25', is_critical: false }
  ]
})
</script>

<style lang="scss" scoped>
.my-tasks-page { padding: 20px; background: #f0f2f5; min-height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; h2 { margin: 0; } }
.stats-row { margin-bottom: 16px; }
.stat-card { padding: 16px; background: #fff; border-radius: 8px; text-align: center; cursor: pointer; transition: all 0.3s; border: 2px solid transparent; &:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); } &.active { border-color: #1890ff; background: #e6f7ff; } .stat-value { font-size: 28px; font-weight: 600; } .stat-label { font-size: 13px; color: #999; margin-top: 4px; } &.overdue .stat-value { color: #ff4d4f; } }
.text-primary { color: #1890ff; } .text-success { color: #52c41a; } .text-warning { color: #faad14; } .text-danger { color: #ff4d4f; } .text-info { color: #909399; }

.task-list-card { .filter-bar { display: flex; gap: 12px; margin-bottom: 16px; } .task-cell { display: flex; align-items: center; gap: 12px; .task-info { flex: 1; .task-name { font-size: 14px; &.completed { text-decoration: line-through; color: #999; } } .task-meta { font-size: 12px; color: #999; margin-top: 4px; .project-tag { background: #e6f7ff; color: #1890ff; padding: 2px 6px; border-radius: 2px; margin-right: 8px; } } } } .progress-cell { display: flex; align-items: center; gap: 8px; } .overdue-days { font-size: 12px; } .urgent-days { font-size: 12px; color: #faad14; } }

.kanban-view { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 16px; .kanban-column { flex: 0 0 280px; background: #f5f5f5; border-radius: 8px; display: flex; flex-direction: column; max-height: calc(100vh - 300px); .column-header { padding: 12px 16px; border-bottom: 3px solid; display: flex; justify-content: space-between; align-items: center; .column-title { font-weight: 600; } } .column-body { flex: 1; overflow-y: auto; padding: 12px; .kanban-card { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 8px; cursor: pointer; transition: box-shadow 0.3s; &:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.15); } .card-header { display: flex; justify-content: space-between; margin-bottom: 8px; .project-code { font-size: 12px; color: #1890ff; } } .card-name { font-size: 14px; margin-bottom: 8px; } .card-progress { display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 8px; } .card-footer { display: flex; justify-content: space-between; align-items: center; .deadline { font-size: 12px; color: #999; display: flex; align-items: center; gap: 4px; &.overdue { color: #ff4d4f; } } } } .empty-column { text-align: center; color: #999; padding: 20px; } } } }

.calendar-card { .calendar-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; .current-month { font-size: 18px; font-weight: 600; min-width: 120px; text-align: center; } } .weekday-header { display: grid; grid-template-columns: repeat(7, 1fr); .weekday { padding: 8px; text-align: center; font-weight: 600; color: #666; } } .days-grid { display: grid; grid-template-columns: repeat(7, 1fr); border: 1px solid #f0f0f0; .day-cell { min-height: 80px; padding: 8px; border: 1px solid #f0f0f0; &.other-month { background: #fafafa; .day-number { color: #ccc; } } &.is-today { background: #e6f7ff; .day-number { color: #1890ff; font-weight: 600; } } .day-number { font-size: 14px; margin-bottom: 4px; } .day-tasks { display: flex; flex-wrap: wrap; gap: 4px; .task-dot { width: 8px; height: 8px; border-radius: 50%; cursor: pointer; &.active { background: #1890ff; } &.completed { background: #52c41a; } &.overdue { background: #ff4d4f; } } .more-tasks { font-size: 10px; color: #999; } } } } }
</style>
