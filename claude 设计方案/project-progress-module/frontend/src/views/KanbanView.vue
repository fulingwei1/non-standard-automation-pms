<template>
  <div class="kanban-view">
    <!-- 页面头部 -->
    <header class="kanban-header">
      <div class="header-left">
        <h1>任务看板</h1>
        <div class="view-toggle">
          <button class="toggle-btn" :class="{ active: viewMode === 'status' }" @click="viewMode = 'status'">按状态</button>
          <button class="toggle-btn" :class="{ active: viewMode === 'priority' }" @click="viewMode = 'priority'">按优先级</button>
          <button class="toggle-btn" :class="{ active: viewMode === 'project' }" @click="viewMode = 'project'">按项目</button>
        </div>
      </div>
      <div class="header-right">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" v-model="searchKeyword" placeholder="搜索任务...">
        </div>
        <select v-model="filterProject" class="filter-select">
          <option value="">全部项目</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <button class="btn-primary" @click="showCreateModal = true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          新建任务
        </button>
      </div>
    </header>

    <!-- 看板主体 -->
    <div class="kanban-board" ref="boardRef">
      <div class="kanban-column" v-for="column in columns" :key="column.id"
           @dragover.prevent="onDragOver($event, column)"
           @drop="onDrop($event, column)"
           @dragleave="onDragLeave($event, column)"
           :class="{ 'drag-over': dragOverColumn === column.id }">
        
        <!-- 列头 -->
        <div class="column-header" :style="{ borderColor: column.color }">
          <div class="column-title">
            <span class="column-icon">{{ column.icon }}</span>
            <span class="column-name">{{ column.name }}</span>
            <span class="column-count">{{ getColumnTasks(column.id).length }}</span>
          </div>
          <div class="column-actions">
            <button class="column-btn" @click="collapseColumn(column.id)" :title="column.collapsed ? '展开' : '折叠'">
              <svg v-if="!column.collapsed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </button>
            <button class="column-btn" @click="addTaskToColumn(column.id)" title="添加任务">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- 列内容 -->
        <div class="column-body" v-show="!column.collapsed">
          <transition-group name="card-move" tag="div" class="cards-container">
            <div class="task-card" v-for="task in getColumnTasks(column.id)" :key="task.id"
                 draggable="true"
                 @dragstart="onDragStart($event, task)"
                 @dragend="onDragEnd"
                 :class="{ 
                   dragging: draggingTask?.id === task.id,
                   urgent: task.is_urgent,
                   overdue: task.is_overdue
                 }"
                 @click="openTaskDetail(task)">
              
              <!-- 优先级指示条 -->
              <div class="priority-bar" :class="task.priority"></div>
              
              <!-- 任务标签 -->
              <div class="card-tags">
                <span class="tag type" :style="{ background: getTypeColor(task.task_type) }">
                  {{ task.type_label }}
                </span>
                <span class="tag urgent" v-if="task.is_urgent">🔥 紧急</span>
                <span class="tag overdue" v-if="task.is_overdue">⚠️ 逾期</span>
              </div>
              
              <!-- 任务标题 -->
              <h4 class="card-title">{{ task.title }}</h4>
              
              <!-- 任务元信息 -->
              <div class="card-meta">
                <span class="meta-item" v-if="task.project">
                  <span class="project-badge" :class="'level-' + (task.project.level || 'c').toLowerCase()">
                    {{ task.project.level }}
                  </span>
                  {{ task.project.name }}
                </span>
              </div>
              
              <!-- 进度条 -->
              <div class="card-progress" v-if="task.progress > 0">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
                </div>
                <span class="progress-text">{{ task.progress }}%</span>
              </div>
              
              <!-- 卡片底部 -->
              <div class="card-footer">
                <div class="card-deadline" v-if="task.schedule?.deadline" :class="{ urgent: isDeadlineSoon(task.schedule.deadline) }">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                  </svg>
                  {{ formatDeadline(task.schedule.deadline) }}
                </div>
                <div class="card-assignee" v-if="task.assigner">
                  <div class="avatar">{{ task.assigner.name.charAt(0) }}</div>
                </div>
              </div>
            </div>
          </transition-group>

          <!-- 空状态 -->
          <div class="column-empty" v-if="getColumnTasks(column.id).length === 0">
            <p>暂无任务</p>
            <button class="btn-add" @click="addTaskToColumn(column.id)">+ 添加任务</button>
          </div>
        </div>

        <!-- 折叠状态 -->
        <div class="column-collapsed" v-if="column.collapsed">
          <span class="collapsed-count">{{ getColumnTasks(column.id).length }}</span>
        </div>
      </div>
    </div>

    <!-- 任务详情抽屉 -->
    <transition name="drawer">
      <div class="drawer-overlay" v-if="selectedTask" @click="selectedTask = null">
        <div class="drawer" @click.stop>
          <div class="drawer-header">
            <div class="drawer-title">
              <span class="task-type-badge" :style="{ background: getTypeColor(selectedTask.task_type) }">
                {{ selectedTask.type_label }}
              </span>
              <h2>任务详情</h2>
            </div>
            <button class="drawer-close" @click="selectedTask = null">×</button>
          </div>
          
          <div class="drawer-body">
            <div class="detail-section">
              <h3 class="task-title-large">{{ selectedTask.title }}</h3>
              <p class="task-desc">{{ selectedTask.description || '暂无描述' }}</p>
            </div>

            <div class="detail-section">
              <h4>状态切换</h4>
              <div class="status-switcher">
                <button v-for="col in statusColumns" :key="col.id"
                        :class="{ active: selectedTask.status === col.id }"
                        :style="{ '--color': col.color }"
                        @click="changeTaskStatus(selectedTask, col.id)">
                  {{ col.icon }} {{ col.name }}
                </button>
              </div>
            </div>

            <div class="detail-section">
              <h4>基本信息</h4>
              <div class="info-grid">
                <div class="info-item">
                  <span class="label">优先级</span>
                  <select v-model="selectedTask.priority" @change="updateTask(selectedTask)" class="inline-select">
                    <option value="urgent">🔴 紧急</option>
                    <option value="high">🟠 高</option>
                    <option value="medium">🔵 中</option>
                    <option value="low">⚪ 低</option>
                  </select>
                </div>
                <div class="info-item">
                  <span class="label">进度</span>
                  <div class="progress-control">
                    <input type="range" min="0" max="100" step="5" v-model="selectedTask.progress" @change="updateTask(selectedTask)">
                    <span>{{ selectedTask.progress }}%</span>
                  </div>
                </div>
                <div class="info-item" v-if="selectedTask.project">
                  <span class="label">所属项目</span>
                  <span class="value">{{ selectedTask.project.name }}</span>
                </div>
                <div class="info-item" v-if="selectedTask.schedule?.deadline">
                  <span class="label">截止时间</span>
                  <span class="value" :class="{ overdue: selectedTask.is_overdue }">
                    {{ formatDateTime(selectedTask.schedule.deadline) }}
                  </span>
                </div>
                <div class="info-item" v-if="selectedTask.assigner">
                  <span class="label">指派人</span>
                  <span class="value">{{ selectedTask.assigner.name }}</span>
                </div>
              </div>
            </div>

            <div class="detail-actions">
              <button class="btn-primary" @click="completeTask(selectedTask)" v-if="selectedTask.status !== 'completed'">
                ✓ 完成任务
              </button>
              <button class="btn-secondary" @click="transferTask(selectedTask)">转办</button>
              <button class="btn-secondary" @click="logHours(selectedTask)">填工时</button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 快速新建任务弹窗 -->
    <div class="modal-overlay" v-if="showCreateModal" @click="showCreateModal = false">
      <div class="modal quick-create" @click.stop>
        <div class="modal-header">
          <h3>快速新建任务</h3>
          <button @click="showCreateModal = false">×</button>
        </div>
        <div class="modal-body">
          <input type="text" v-model="newTask.title" placeholder="任务标题" class="title-input" @keyup.enter="createTask">
          <textarea v-model="newTask.description" placeholder="任务描述（可选）"></textarea>
          <div class="form-row">
            <select v-model="newTask.priority">
              <option value="low">⚪ 低优先级</option>
              <option value="medium">🔵 中优先级</option>
              <option value="high">🟠 高优先级</option>
              <option value="urgent">🔴 紧急</option>
            </select>
            <select v-model="newTask.status">
              <option v-for="col in statusColumns" :key="col.id" :value="col.id">{{ col.icon }} {{ col.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <input type="datetime-local" v-model="newTask.deadline" placeholder="截止时间">
            <select v-model="newTask.project_id">
              <option value="">不关联项目</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn-primary" @click="createTask" :disabled="!newTask.title">创建</button>
        </div>
      </div>
    </div>

    <!-- 操作提示 -->
    <transition name="toast">
      <div class="toast" v-if="toastMessage" :class="toastType">
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import request from '@/utils/request'

// 视图模式
const viewMode = ref('status')

// 状态列配置
const statusColumns = ref([
  { id: 'pending', name: '待处理', icon: '📋', color: '#94A3B8', collapsed: false },
  { id: 'in_progress', name: '进行中', icon: '🚀', color: '#3B82F6', collapsed: false },
  { id: 'review', name: '待验收', icon: '👀', color: '#F59E0B', collapsed: false },
  { id: 'completed', name: '已完成', icon: '✅', color: '#10B981', collapsed: false }
])

// 优先级列配置
const priorityColumns = ref([
  { id: 'urgent', name: '紧急', icon: '🔴', color: '#EF4444', collapsed: false },
  { id: 'high', name: '高优先级', icon: '🟠', color: '#F59E0B', collapsed: false },
  { id: 'medium', name: '中优先级', icon: '🔵', color: '#3B82F6', collapsed: false },
  { id: 'low', name: '低优先级', icon: '⚪', color: '#94A3B8', collapsed: false }
])

// 项目列配置（动态生成）
const projectColumns = computed(() => {
  const cols = projects.value.map(p => ({
    id: `project_${p.id}`,
    projectId: p.id,
    name: p.name,
    icon: '📁',
    color: p.level === 'A' ? '#6366F1' : p.level === 'B' ? '#F59E0B' : '#10B981',
    collapsed: false
  }))
  cols.push({ id: 'no_project', name: '未关联项目', icon: '📄', color: '#94A3B8', collapsed: false })
  return cols
})

// 当前使用的列
const columns = computed(() => {
  if (viewMode.value === 'status') return statusColumns.value
  if (viewMode.value === 'priority') return priorityColumns.value
  return projectColumns.value
})

// 任务数据
const tasks = ref([])
const projects = ref([
  { id: 1, name: 'XX自动化测试设备', level: 'A' },
  { id: 2, name: 'YY产线改造', level: 'B' },
  { id: 3, name: 'ZZ检测系统', level: 'C' }
])

// 筛选
const searchKeyword = ref('')
const filterProject = ref('')

// 拖拽状态
const draggingTask = ref(null)
const dragOverColumn = ref(null)

// 选中任务
const selectedTask = ref(null)

// 新建任务
const showCreateModal = ref(false)
const newTask = ref({
  title: '',
  description: '',
  priority: 'medium',
  status: 'pending',
  deadline: '',
  project_id: ''
})

// 提示
const toastMessage = ref('')
const toastType = ref('success')

// 任务类型配置
const taskTypes = {
  project_wbs: { color: '#F59E0B' },
  job_duty: { color: '#6366F1' },
  workflow: { color: '#10B981' },
  transfer: { color: '#EC4899' },
  legacy: { color: '#8B5CF6' },
  assigned: { color: '#14B8A6' },
  personal: { color: '#64748B' }
}

// 计算属性
const filteredTasks = computed(() => {
  let result = tasks.value
  
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(t => t.title.toLowerCase().includes(kw))
  }
  
  if (filterProject.value) {
    result = result.filter(t => t.project?.id == filterProject.value)
  }
  
  return result
})

// 方法
const getColumnTasks = (columnId) => {
  const filtered = filteredTasks.value
  
  if (viewMode.value === 'status') {
    return filtered.filter(t => t.status === columnId)
  }
  
  if (viewMode.value === 'priority') {
    return filtered.filter(t => t.priority === columnId)
  }
  
  // 按项目
  if (columnId === 'no_project') {
    return filtered.filter(t => !t.project)
  }
  const projectId = parseInt(columnId.replace('project_', ''))
  return filtered.filter(t => t.project?.id === projectId)
}

const getTypeColor = (type) => taskTypes[type]?.color || '#64748B'

const formatDeadline = (deadline) => {
  if (!deadline) return ''
  const d = new Date(deadline)
  const now = new Date()
  const diff = d - now
  if (diff < 0) return '已逾期'
  if (diff < 86400000) return '今天'
  if (diff < 172800000) return '明天'
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

const formatDateTime = (dt) => dt ? new Date(dt).toLocaleString('zh-CN') : ''

const isDeadlineSoon = (deadline) => {
  if (!deadline) return false
  const d = new Date(deadline)
  const now = new Date()
  return d - now < 86400000 * 2 // 2天内
}

const showToast = (message, type = 'success') => {
  toastMessage.value = message
  toastType.value = type
  setTimeout(() => { toastMessage.value = '' }, 3000)
}

// 拖拽事件
const onDragStart = (event, task) => {
  draggingTask.value = task
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', task.id)
  
  // 添加拖拽样式
  setTimeout(() => {
    event.target.classList.add('dragging')
  }, 0)
}

const onDragEnd = (event) => {
  event.target.classList.remove('dragging')
  draggingTask.value = null
  dragOverColumn.value = null
}

const onDragOver = (event, column) => {
  event.preventDefault()
  dragOverColumn.value = column.id
}

const onDragLeave = (event, column) => {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    dragOverColumn.value = null
  }
}

const onDrop = async (event, column) => {
  event.preventDefault()
  dragOverColumn.value = null
  
  if (!draggingTask.value) return
  
  const task = draggingTask.value
  const oldValue = viewMode.value === 'status' ? task.status : 
                   viewMode.value === 'priority' ? task.priority : 
                   task.project?.id
  
  // 更新任务
  if (viewMode.value === 'status') {
    if (task.status === column.id) return
    task.status = column.id
    if (column.id === 'completed') task.progress = 100
  } else if (viewMode.value === 'priority') {
    if (task.priority === column.id) return
    task.priority = column.id
  } else {
    // 按项目视图
    const newProjectId = column.id === 'no_project' ? null : column.projectId
    if (task.project?.id === newProjectId) return
    if (newProjectId) {
      task.project = projects.value.find(p => p.id === newProjectId)
    } else {
      task.project = null
    }
  }
  
  // 调用API更新
  try {
    // await request.put(`/api/v1/task-center/task/${task.id}`, task)
    showToast(`任务已移动到"${column.name}"`)
  } catch (e) {
    showToast('更新失败', 'error')
  }
  
  draggingTask.value = null
}

// 列操作
const collapseColumn = (columnId) => {
  const col = columns.value.find(c => c.id === columnId)
  if (col) col.collapsed = !col.collapsed
}

const addTaskToColumn = (columnId) => {
  newTask.value = {
    title: '',
    description: '',
    priority: viewMode.value === 'priority' ? columnId : 'medium',
    status: viewMode.value === 'status' ? columnId : 'pending',
    deadline: '',
    project_id: viewMode.value === 'project' && columnId !== 'no_project' 
      ? parseInt(columnId.replace('project_', '')) 
      : ''
  }
  showCreateModal.value = true
}

// 任务操作
const openTaskDetail = (task) => {
  selectedTask.value = { ...task }
}

const changeTaskStatus = (task, newStatus) => {
  task.status = newStatus
  if (newStatus === 'completed') task.progress = 100
  updateTask(task)
}

const updateTask = async (task) => {
  try {
    // await request.put(`/api/v1/task-center/task/${task.id}`, task)
    // 更新本地数据
    const idx = tasks.value.findIndex(t => t.id === task.id)
    if (idx > -1) {
      tasks.value[idx] = { ...task }
    }
    showToast('任务已更新')
  } catch (e) {
    showToast('更新失败', 'error')
  }
}

const completeTask = (task) => {
  task.status = 'completed'
  task.progress = 100
  updateTask(task)
  selectedTask.value = null
  showToast('任务已完成 🎉')
}

const transferTask = (task) => {
  alert('转办功能开发中')
}

const logHours = (task) => {
  const hours = prompt('输入工时:', '')
  if (hours) showToast(`已记录 ${hours} 小时`)
}

const createTask = async () => {
  if (!newTask.value.title) return
  
  const task = {
    id: Date.now(),
    title: newTask.value.title,
    description: newTask.value.description,
    priority: newTask.value.priority,
    priority_label: { urgent: '紧急', high: '高', medium: '中', low: '低' }[newTask.value.priority],
    status: newTask.value.status,
    status_label: statusColumns.value.find(c => c.id === newTask.value.status)?.name,
    task_type: 'personal',
    type_label: '个人任务',
    progress: 0,
    schedule: newTask.value.deadline ? { deadline: newTask.value.deadline } : null,
    project: newTask.value.project_id ? projects.value.find(p => p.id == newTask.value.project_id) : null,
    is_urgent: newTask.value.priority === 'urgent',
    is_overdue: false
  }
  
  tasks.value.unshift(task)
  showCreateModal.value = false
  newTask.value = { title: '', description: '', priority: 'medium', status: 'pending', deadline: '', project_id: '' }
  showToast('任务创建成功')
}

// 加载数据
const loadTasks = async () => {
  try {
    const res = await request.get('/api/v1/task-center/my-tasks', { params: { page_size: 100 } })
    if (res.code === 200) tasks.value = res.data.tasks
  } catch (e) {
    tasks.value = getMockTasks()
  }
}

const getMockTasks = () => [
  { id: 1001, title: '机械结构3D建模', description: '完成XX设备主体结构的3D建模工作', task_type: 'project_wbs', type_label: '项目任务', project: { id: 1, name: 'XX自动化测试设备', level: 'A' }, schedule: { deadline: '2025-01-05T18:00:00' }, assigner: { id: 100, name: '张经理' }, status: 'in_progress', priority: 'high', priority_label: '高', progress: 60, is_urgent: false, is_overdue: false },
  { id: 1002, title: '提交本周周报', description: '总结本周工作内容', task_type: 'job_duty', type_label: '岗位职责', schedule: { deadline: '2025-01-03T18:00:00' }, status: 'pending', priority: 'medium', priority_label: '中', progress: 0, is_urgent: false, is_overdue: false },
  { id: 1003, title: '图纸评审签字', description: '评审机械图纸并签字确认', task_type: 'workflow', type_label: '流程待办', project: { id: 1, name: 'XX自动化测试设备', level: 'A' }, schedule: { deadline: '2025-01-04T18:00:00' }, assigner: { id: 102, name: '李工' }, status: 'pending', priority: 'high', priority_label: '高', progress: 0, is_urgent: true, is_overdue: false },
  { id: 1004, title: '协助调试设备', description: '帮助王工调试设备', task_type: 'transfer', type_label: '转办任务', project: { id: 1, name: 'XX自动化测试设备', level: 'A' }, schedule: { deadline: '2025-01-03T17:00:00' }, status: 'in_progress', priority: 'high', priority_label: '高', progress: 50, is_urgent: false, is_overdue: false },
  { id: 1005, title: 'YY项目进度汇报', description: '准备进度汇报材料', task_type: 'assigned', type_label: '临时指派', project: { id: 2, name: 'YY产线改造', level: 'B' }, status: 'pending', priority: 'urgent', priority_label: '紧急', progress: 0, is_urgent: true, is_overdue: false },
  { id: 1006, title: '整理ZZ项目文档', description: '归档技术文档', task_type: 'legacy', type_label: '遗留任务', project: { id: 3, name: 'ZZ检测系统', level: 'C' }, status: 'in_progress', priority: 'low', priority_label: '低', progress: 30, is_urgent: false, is_overdue: true },
  { id: 1007, title: '电气原理图设计', description: '完成电气原理图', task_type: 'project_wbs', type_label: '项目任务', project: { id: 1, name: 'XX自动化测试设备', level: 'A' }, schedule: { deadline: '2025-01-06T18:00:00' }, status: 'review', priority: 'high', priority_label: '高', progress: 100, is_urgent: false, is_overdue: false },
  { id: 1008, title: '学习Vue3新特性', description: '个人学习计划', task_type: 'personal', type_label: '个人任务', status: 'in_progress', priority: 'low', priority_label: '低', progress: 20, is_urgent: false, is_overdue: false }
]

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.kanban-view {
  min-height: 100vh;
  background: #F1F5F9;
  display: flex;
  flex-direction: column;
}

/* 头部 */
.kanban-header {
  background: white;
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #E2E8F0;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.header-left h1 {
  font-size: 24px;
  font-weight: 700;
  color: #0F172A;
}

.view-toggle {
  display: flex;
  background: #F1F5F9;
  border-radius: 10px;
  padding: 4px;
}

.toggle-btn {
  padding: 8px 16px;
  border: none;
  background: none;
  border-radius: 8px;
  font-size: 14px;
  color: #64748B;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn.active {
  background: white;
  color: #0F172A;
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
}

.search-box svg {
  width: 18px;
  height: 18px;
  color: #94A3B8;
}

.search-box input {
  border: none;
  background: none;
  outline: none;
  width: 180px;
  font-size: 14px;
}

.filter-select {
  padding: 10px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 14px;
  background: white;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #6366F1, #4F46E5);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

/* 看板主体 */
.kanban-board {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 24px;
  overflow-x: auto;
  align-items: flex-start;
}

/* 列 */
.kanban-column {
  flex: 0 0 320px;
  background: #F8FAFC;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 160px);
  transition: all 0.2s;
}

.kanban-column.drag-over {
  background: #EEF2FF;
  box-shadow: 0 0 0 2px #6366F1;
}

.column-header {
  padding: 16px;
  border-bottom: 3px solid;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.column-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.column-icon {
  font-size: 18px;
}

.column-name {
  font-size: 15px;
  font-weight: 600;
  color: #0F172A;
}

.column-count {
  background: #E2E8F0;
  color: #64748B;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}

.column-actions {
  display: flex;
  gap: 4px;
}

.column-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94A3B8;
  transition: all 0.2s;
}

.column-btn:hover {
  background: #E2E8F0;
  color: #64748B;
}

.column-btn svg {
  width: 16px;
  height: 16px;
}

.column-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.cards-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 任务卡片 */
.task-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  cursor: grab;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.task-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.task-card.dragging {
  opacity: 0.5;
  cursor: grabbing;
}

.task-card.urgent {
  box-shadow: 0 0 0 1px #FEE2E2;
}

.task-card.overdue {
  background: #FEF2F2;
}

.priority-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.priority-bar.urgent { background: #EF4444; }
.priority-bar.high { background: #F59E0B; }
.priority-bar.medium { background: #3B82F6; }
.priority-bar.low { background: #94A3B8; }

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.tag {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
}

.tag.type {
  color: white;
}

.tag.urgent {
  background: #FEE2E2;
  color: #991B1B;
}

.tag.overdue {
  background: #FEF3C7;
  color: #92400E;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 8px;
  line-height: 1.4;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748B;
}

.project-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  color: white;
}

.project-badge.level-a { background: #6366F1; }
.project-badge.level-b { background: #F59E0B; }
.project-badge.level-c { background: #10B981; }

.card-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: #E2E8F0;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366F1, #8B5CF6);
  border-radius: 2px;
}

.progress-text {
  font-size: 11px;
  font-weight: 600;
  color: #6366F1;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-deadline {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748B;
}

.card-deadline svg {
  width: 14px;
  height: 14px;
}

.card-deadline.urgent {
  color: #DC2626;
}

.card-assignee .avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

/* 空状态 */
.column-empty {
  text-align: center;
  padding: 32px 16px;
  color: #94A3B8;
}

.column-empty p {
  margin-bottom: 12px;
}

.btn-add {
  padding: 8px 16px;
  border: 1px dashed #CBD5E1;
  background: none;
  border-radius: 8px;
  color: #64748B;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add:hover {
  border-color: #6366F1;
  color: #6366F1;
}

/* 折叠状态 */
.column-collapsed {
  padding: 16px;
  text-align: center;
}

.collapsed-count {
  background: #E2E8F0;
  color: #64748B;
  font-size: 14px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 12px;
}

/* 抽屉 */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 100;
  display: flex;
  justify-content: flex-end;
}

.drawer {
  width: 480px;
  max-width: 100%;
  background: white;
  height: 100%;
  overflow-y: auto;
  box-shadow: -4px 0 20px rgba(0,0,0,0.1);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #E2E8F0;
}

.drawer-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.drawer-title h2 {
  font-size: 18px;
  font-weight: 600;
}

.task-type-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: white;
}

.drawer-close {
  width: 32px;
  height: 32px;
  border: none;
  background: #F1F5F9;
  border-radius: 8px;
  font-size: 20px;
  cursor: pointer;
}

.drawer-body {
  padding: 24px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: #64748B;
  margin-bottom: 12px;
}

.task-title-large {
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 8px;
}

.task-desc {
  font-size: 14px;
  color: #64748B;
  line-height: 1.6;
}

.status-switcher {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-switcher button {
  padding: 8px 16px;
  border: 1px solid #E2E8F0;
  background: white;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.status-switcher button:hover {
  border-color: var(--color);
}

.status-switcher button.active {
  background: var(--color);
  border-color: var(--color);
  color: white;
}

.info-grid {
  display: grid;
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item .label {
  font-size: 13px;
  color: #64748B;
}

.info-item .value {
  font-size: 14px;
  font-weight: 500;
  color: #0F172A;
}

.info-item .value.overdue {
  color: #DC2626;
}

.inline-select {
  padding: 6px 12px;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  font-size: 13px;
}

.progress-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-control input[type="range"] {
  width: 120px;
}

.progress-control span {
  font-weight: 600;
  color: #6366F1;
}

.detail-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #E2E8F0;
}

.btn-secondary {
  padding: 10px 20px;
  background: #F1F5F9;
  color: #374151;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal {
  background: white;
  border-radius: 20px;
  width: 480px;
  max-width: 90%;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #E2E8F0;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.modal-header button {
  width: 32px;
  height: 32px;
  border: none;
  background: #F1F5F9;
  border-radius: 8px;
  font-size: 20px;
  cursor: pointer;
}

.modal-body {
  padding: 24px;
}

.title-input {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
}

.modal-body textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 14px;
  min-height: 80px;
  resize: vertical;
  margin-bottom: 12px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.form-row select,
.form-row input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #E2E8F0;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  background: #10B981;
  color: white;
  border-radius: 10px;
  font-weight: 500;
  z-index: 2000;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.toast.error {
  background: #EF4444;
}

/* 动画 */
.drawer-enter-active,
.drawer-leave-active {
  transition: all 0.3s ease;
}

.drawer-enter-from .drawer,
.drawer-leave-to .drawer {
  transform: translateX(100%);
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.card-move-move {
  transition: transform 0.3s ease;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}

/* 响应式 */
@media (max-width: 768px) {
  .kanban-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-left,
  .header-right {
    flex-wrap: wrap;
  }
  
  .kanban-column {
    flex: 0 0 280px;
  }
  
  .drawer {
    width: 100%;
  }
}
</style>
VUEEOF
echo "Created KanbanView.vue"