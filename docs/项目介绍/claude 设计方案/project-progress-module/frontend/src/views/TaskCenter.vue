<template>
  <div class="task-center">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>我的任务</h1>
          <p class="header-subtitle">统一管理所有工作任务</p>
        </div>
        <div class="header-right">
          <button class="btn-secondary" @click="toggleBatchMode" :class="{ active: batchMode }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12l2 2 4-4"/>
            </svg>
            {{ batchMode ? '退出批量' : '批量操作' }}
          </button>
          <button class="btn-secondary" @click="refreshTasks">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            刷新
          </button>
          <button class="btn-primary" @click="showCreateModal = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            新建任务
          </button>
        </div>
      </div>
    </header>

    <!-- 批量操作工具栏 -->
    <transition name="slide-down">
      <div class="batch-toolbar" v-if="batchMode">
        <div class="batch-info">
          <button class="btn-check-all" @click="toggleSelectAll">
            <svg v-if="isAllSelected" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <svg v-else-if="selectedTasks.length > 0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="8" y1="12" x2="16" y2="12"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
            </svg>
          </button>
          <span class="selected-count" v-if="selectedTasks.length > 0">
            已选择 <strong>{{ selectedTasks.length }}</strong> 个任务
          </span>
          <span class="selected-count hint" v-else>点击任务卡片进行选择</span>
          <button class="btn-text" @click="clearSelection" v-if="selectedTasks.length > 0">取消选择</button>
        </div>
        <div class="batch-actions" v-if="selectedTasks.length > 0">
          <button class="batch-btn complete" @click="batchComplete" title="批量完成">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <span>完成</span>
          </button>
          <button class="batch-btn transfer" @click="showBatchTransfer = true" title="批量转办">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>
            </svg>
            <span>转办</span>
          </button>
          <div class="batch-dropdown" @click.stop>
            <button class="batch-btn priority" @click="showPriorityMenu = !showPriorityMenu">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
              <span>优先级</span>
              <svg class="arrow" :class="{ open: showPriorityMenu }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            <transition name="fade">
              <div class="dropdown-menu" v-if="showPriorityMenu">
                <button @click="batchSetPriority('urgent')"><span class="dot urgent"></span>紧急</button>
                <button @click="batchSetPriority('high')"><span class="dot high"></span>高</button>
                <button @click="batchSetPriority('medium')"><span class="dot medium"></span>中</button>
                <button @click="batchSetPriority('low')"><span class="dot low"></span>低</button>
              </div>
            </transition>
          </div>
          <button class="batch-btn progress" @click="showBatchProgress = true" title="批量更新进度">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            <span>进度</span>
          </button>
          <button class="batch-btn urge" @click="batchUrge" title="批量催办">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/>
              <line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span>催办</span>
          </button>
          <button class="batch-btn delete" @click="batchDelete" title="批量删除">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
            <span>删除</span>
          </button>
        </div>
      </div>
    </transition>

    <!-- 统计卡片 -->
    <section class="stats-section">
      <div class="stats-grid">
        <div class="stat-card" @click="filterByStatus('all')">
          <div class="stat-icon all"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.total }}</span><span class="stat-label">全部任务</span></div>
        </div>
        <div class="stat-card urgent" @click="filterByUrgent">
          <div class="stat-icon urgent"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.urgent + stats.overdue }}</span><span class="stat-label">紧急/逾期</span></div>
        </div>
        <div class="stat-card today" @click="filterByToday">
          <div class="stat-icon today"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.due_today }}</span><span class="stat-label">今日到期</span></div>
        </div>
        <div class="stat-card week" @click="filterByWeek">
          <div class="stat-icon week"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.due_this_week }}</span><span class="stat-label">本周到期</span></div>
        </div>
        <div class="stat-card progress" @click="filterByStatus('in_progress')">
          <div class="stat-icon progress"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div>
          <div class="stat-info"><span class="stat-value">{{ stats.in_progress }}</span><span class="stat-label">进行中</span></div>
        </div>
      </div>
    </section>

    <!-- 任务类型Tab -->
    <section class="tasks-section">
      <div class="section-header">
        <div class="tabs">
          <button class="tab" :class="{ active: activeType === 'all' }" @click="activeType = 'all'">
            全部 <span class="tab-count">{{ stats.total }}</span>
          </button>
          <button class="tab" v-for="t in taskTypes" :key="t.code" 
                  :class="{ active: activeType === t.code }" @click="activeType = t.code">
            <span class="tab-icon">{{ t.icon }}</span>
            {{ t.name }}
            <span class="tab-count" v-if="stats.by_type[t.code]">{{ stats.by_type[t.code] }}</span>
          </button>
        </div>
        <div class="filters">
          <select v-model="filterPriority">
            <option value="">优先级</option>
            <option value="urgent">紧急</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
          <select v-model="filterProject">
            <option value="">所有项目</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
          <div class="search-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input type="text" v-model="searchKeyword" placeholder="搜索任务...">
          </div>
        </div>
      </div>

      <!-- 紧急任务提醒 -->
      <div class="urgent-banner" v-if="urgentTasks.length > 0 && !batchMode">
        <div class="banner-icon">🔥</div>
        <div class="banner-content">
          <strong>{{ urgentTasks.length }}个紧急/逾期任务需要处理</strong>
          <span>请优先处理以下任务</span>
        </div>
        <button class="banner-btn" @click="selectUrgentTasks">批量处理</button>
      </div>

      <!-- 任务列表 -->
      <div class="task-list">
        <div class="task-card" v-for="task in filteredTasks" :key="task.id" 
             :class="{ urgent: task.is_urgent, overdue: task.is_overdue, selected: isSelected(task.id), 'batch-mode': batchMode }"
             @click="handleTaskClick(task)">
          
          <!-- 批量选择复选框 -->
          <div class="task-select" v-if="batchMode" @click.stop="toggleSelect(task.id)">
            <svg v-if="isSelected(task.id)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
            </svg>
          </div>
          
          <!-- 普通模式复选框 -->
          <div class="task-checkbox" v-else @click.stop="toggleComplete(task)">
            <svg v-if="task.status === 'completed'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          
          <div class="task-content">
            <div class="task-header">
              <span class="task-type" :style="{ background: getTypeColor(task.task_type) }">
                {{ getTypeIcon(task.task_type) }} {{ task.type_label }}
              </span>
              <span class="task-priority" :class="task.priority">{{ task.priority_label }}</span>
              <span class="task-urgent-tag" v-if="task.is_urgent">🔥 紧急</span>
              <span class="task-overdue-tag" v-if="task.is_overdue">⚠️ 逾期</span>
            </div>
            
            <h3 class="task-title">{{ task.title }}</h3>
            
            <div class="task-meta">
              <span class="meta-item" v-if="task.project">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                <span class="project-level" :class="'level-' + (task.project.level || 'c').toLowerCase()">{{ task.project.level }}</span>
                {{ task.project.name }}
              </span>
              <span class="meta-item" v-if="task.schedule?.deadline">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                </svg>
                {{ formatDeadline(task.schedule.deadline) }}
              </span>
              <span class="meta-item" v-if="task.assigner">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
                {{ task.assigner.name }}指派
              </span>
              <span class="meta-item" v-if="task.transfer?.is_transferred">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>
                </svg>
                {{ task.transfer.from_name }}转办
              </span>
            </div>
            
            <div class="task-progress" v-if="task.progress > 0">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
              </div>
              <span class="progress-text">{{ task.progress }}%</span>
            </div>
          </div>
          
          <div class="task-actions" v-if="!batchMode">
            <button class="action-btn" @click.stop="updateProgress(task)" title="更新进度">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
            </button>
            <button class="action-btn" @click.stop="logHours(task)" title="填报工时">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
            </button>
            <button class="action-btn" @click.stop="transferTask(task)" title="转办">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="empty-state" v-if="filteredTasks.length === 0">
          <div class="empty-icon">📋</div>
          <h3>暂无任务</h3>
          <p>当前筛选条件下没有任务</p>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination" v-if="totalPages > 1">
        <button @click="page--" :disabled="page <= 1">上一页</button>
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button @click="page++" :disabled="page >= totalPages">下一页</button>
      </div>
    </section>

    <!-- 任务详情抽屉 -->
    <div class="drawer-overlay" v-if="selectedTask && !batchMode" @click="selectedTask = null">
      <div class="drawer" @click.stop>
        <div class="drawer-header">
          <h2>任务详情</h2>
          <button class="drawer-close" @click="selectedTask = null">×</button>
        </div>
        <div class="drawer-body">
          <div class="detail-section">
            <div class="detail-type" :style="{ background: getTypeColor(selectedTask.task_type) }">
              {{ getTypeIcon(selectedTask.task_type) }} {{ selectedTask.type_label }}
            </div>
            <h1 class="detail-title">{{ selectedTask.title }}</h1>
            <p class="detail-desc">{{ selectedTask.description }}</p>
          </div>

          <div class="detail-section">
            <h3>基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item"><span class="label">状态</span><span class="value status" :class="selectedTask.status">{{ selectedTask.status_label }}</span></div>
              <div class="detail-item"><span class="label">优先级</span><span class="value priority" :class="selectedTask.priority">{{ selectedTask.priority_label }}</span></div>
              <div class="detail-item" v-if="selectedTask.project"><span class="label">所属项目</span><span class="value">{{ selectedTask.project.name }}</span></div>
              <div class="detail-item" v-if="selectedTask.schedule?.deadline"><span class="label">截止时间</span><span class="value">{{ formatDateTime(selectedTask.schedule.deadline) }}</span></div>
              <div class="detail-item" v-if="selectedTask.assigner"><span class="label">指派人</span><span class="value">{{ selectedTask.assigner.name }}</span></div>
              <div class="detail-item"><span class="label">进度</span><span class="value">{{ selectedTask.progress }}%</span></div>
              <div class="detail-item" v-if="selectedTask.hours"><span class="label">工时</span><span class="value">{{ selectedTask.hours.actual }}h / {{ selectedTask.hours.estimated }}h</span></div>
            </div>
          </div>

          <div class="detail-section" v-if="selectedTask.transfer?.is_transferred">
            <h3>转办信息</h3>
            <div class="transfer-info">
              <p><strong>{{ selectedTask.transfer.from_name }}</strong> 于 {{ formatDateTime(selectedTask.transfer.time) }} 转办</p>
              <p class="transfer-reason">原因：{{ selectedTask.transfer.reason }}</p>
            </div>
          </div>

          <div class="detail-actions">
            <button class="btn-primary" @click="completeTask(selectedTask)" v-if="selectedTask.status !== 'completed'">完成任务</button>
            <button class="btn-secondary" @click="updateProgress(selectedTask)">更新进度</button>
            <button class="btn-secondary" @click="logHours(selectedTask)">填报工时</button>
            <button class="btn-secondary" @click="transferTask(selectedTask)">转办</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量转办弹窗 -->
    <div class="modal-overlay" v-if="showBatchTransfer" @click="showBatchTransfer = false">
      <div class="modal" @click.stop>
        <div class="modal-header"><h3>批量转办 ({{ selectedTasks.length }}个任务)</h3><button @click="showBatchTransfer = false">×</button></div>
        <div class="modal-body">
          <div class="selected-tasks-preview">
            <div class="preview-item" v-for="id in selectedTasks.slice(0, 3)" :key="id">
              {{ getTaskById(id)?.title }}
            </div>
            <div class="preview-more" v-if="selectedTasks.length > 3">等{{ selectedTasks.length - 3 }}个任务...</div>
          </div>
          <div class="form-group">
            <label>转办给</label>
            <select v-model="transferTo">
              <option value="">请选择</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.name }} - {{ u.department }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>转办原因</label>
            <textarea v-model="transferReason" placeholder="请填写转办原因"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showBatchTransfer = false">取消</button>
          <button class="btn-primary" @click="confirmBatchTransfer" :disabled="!transferTo">确认转办</button>
        </div>
      </div>
    </div>

    <!-- 批量更新进度弹窗 -->
    <div class="modal-overlay" v-if="showBatchProgress" @click="showBatchProgress = false">
      <div class="modal" @click.stop>
        <div class="modal-header"><h3>批量更新进度 ({{ selectedTasks.length }}个任务)</h3><button @click="showBatchProgress = false">×</button></div>
        <div class="modal-body">
          <div class="progress-slider">
            <input type="range" min="0" max="100" step="5" v-model="batchProgressValue">
            <div class="progress-value">{{ batchProgressValue }}%</div>
          </div>
          <div class="progress-presets">
            <button v-for="v in [0, 25, 50, 75, 100]" :key="v" @click="batchProgressValue = v" :class="{ active: batchProgressValue == v }">{{ v }}%</button>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showBatchProgress = false">取消</button>
          <button class="btn-primary" @click="confirmBatchProgress">确认更新</button>
        </div>
      </div>
    </div>

    <!-- 新建任务弹窗 -->
    <div class="modal-overlay" v-if="showCreateModal" @click="showCreateModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header"><h3>新建个人任务</h3><button @click="showCreateModal = false">×</button></div>
        <div class="modal-body">
          <div class="form-group"><label>任务标题</label><input type="text" v-model="newTask.title" placeholder="输入任务标题"></div>
          <div class="form-group"><label>描述</label><textarea v-model="newTask.description" placeholder="任务描述"></textarea></div>
          <div class="form-row">
            <div class="form-group"><label>优先级</label>
              <select v-model="newTask.priority"><option value="low">低</option><option value="medium">中</option><option value="high">高</option><option value="urgent">紧急</option></select>
            </div>
            <div class="form-group"><label>截止时间</label><input type="datetime-local" v-model="newTask.deadline"></div>
          </div>
          <div class="form-group"><label>关联项目</label>
            <select v-model="newTask.project_id"><option value="">不关联</option><option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option></select>
          </div>
        </div>
        <div class="modal-footer"><button class="btn-secondary" @click="showCreateModal = false">取消</button><button class="btn-primary" @click="createTask">创建</button></div>
      </div>
    </div>

    <!-- 操作结果提示 -->
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

// 状态
const loading = ref(false)
const tasks = ref([])
const stats = ref({ total: 0, pending: 0, in_progress: 0, overdue: 0, due_today: 0, due_this_week: 0, urgent: 0, by_type: {}, by_project: {} })
const page = ref(1)
const pageSize = ref(20)
const totalPages = ref(1)

const activeType = ref('all')
const filterPriority = ref('')
const filterProject = ref('')
const filterStatus = ref('')
const filterOverdue = ref(false)
const filterDueToday = ref(false)
const searchKeyword = ref('')

const selectedTask = ref(null)
const showCreateModal = ref(false)
const newTask = ref({ title: '', description: '', priority: 'medium', deadline: '', project_id: '' })

// 批量操作状态
const batchMode = ref(false)
const selectedTasks = ref([])
const showPriorityMenu = ref(false)
const showBatchTransfer = ref(false)
const showBatchProgress = ref(false)
const transferTo = ref('')
const transferReason = ref('')
const batchProgressValue = ref(50)

// 提示消息
const toastMessage = ref('')
const toastType = ref('success')

const users = ref([
  { id: 101, name: '张三', department: '机械组' },
  { id: 102, name: '李四', department: '电气组' },
  { id: 103, name: '王五', department: '软件组' },
  { id: 104, name: '赵六', department: '测试组' }
])

const taskTypes = ref([
  { code: 'project_wbs', name: '项目任务', icon: '📁', color: '#F59E0B' },
  { code: 'job_duty', name: '岗位职责', icon: '📋', color: '#6366F1' },
  { code: 'workflow', name: '流程待办', icon: '🔄', color: '#10B981' },
  { code: 'transfer', name: '转办任务', icon: '📨', color: '#EC4899' },
  { code: 'legacy', name: '遗留任务', icon: '⏰', color: '#8B5CF6' },
  { code: 'assigned', name: '临时指派', icon: '🎯', color: '#14B8A6' }
])

const projects = ref([
  { id: 1, name: 'XX自动化测试设备' },
  { id: 2, name: 'YY产线改造' },
  { id: 3, name: 'ZZ检测系统' }
])

// 计算属性
const filteredTasks = computed(() => {
  let result = tasks.value
  if (activeType.value !== 'all') result = result.filter(t => t.task_type === activeType.value)
  if (filterPriority.value) result = result.filter(t => t.priority === filterPriority.value)
  if (filterProject.value) result = result.filter(t => t.project?.id == filterProject.value)
  if (filterStatus.value) result = result.filter(t => t.status === filterStatus.value)
  if (filterOverdue.value) result = result.filter(t => t.is_overdue)
  if (filterDueToday.value) result = result.filter(t => t.is_due_today)
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(t => t.title.toLowerCase().includes(kw) || t.project?.name?.toLowerCase().includes(kw))
  }
  return result
})

const urgentTasks = computed(() => tasks.value.filter(t => t.is_urgent || t.is_overdue))
const isAllSelected = computed(() => filteredTasks.value.length > 0 && selectedTasks.value.length === filteredTasks.value.length)

// 方法
const getTypeIcon = (type) => taskTypes.value.find(t => t.code === type)?.icon || '📋'
const getTypeColor = (type) => taskTypes.value.find(t => t.code === type)?.color || '#6B7280'
const getTaskById = (id) => tasks.value.find(t => t.id === id)
const isSelected = (id) => selectedTasks.value.includes(id)

const formatDeadline = (deadline) => {
  if (!deadline) return ''
  const d = new Date(deadline)
  const now = new Date()
  const diff = d - now
  if (diff < 0) return '已逾期'
  if (diff < 86400000) return '今天 ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  if (diff < 172800000) return '明天'
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

const formatDateTime = (dt) => dt ? new Date(dt).toLocaleString('zh-CN') : ''

const showToast = (message, type = 'success') => {
  toastMessage.value = message
  toastType.value = type
  setTimeout(() => { toastMessage.value = '' }, 3000)
}

// 批量操作
const toggleBatchMode = () => {
  batchMode.value = !batchMode.value
  if (!batchMode.value) clearSelection()
}

const toggleSelect = (id) => {
  const idx = selectedTasks.value.indexOf(id)
  if (idx > -1) selectedTasks.value.splice(idx, 1)
  else selectedTasks.value.push(id)
}

const toggleSelectAll = () => {
  if (isAllSelected.value) clearSelection()
  else selectedTasks.value = filteredTasks.value.map(t => t.id)
}

const clearSelection = () => { selectedTasks.value = [] }

const selectUrgentTasks = () => {
  batchMode.value = true
  selectedTasks.value = urgentTasks.value.map(t => t.id)
}

const handleTaskClick = (task) => {
  if (batchMode.value) toggleSelect(task.id)
  else selectedTask.value = task
}

const batchComplete = async () => {
  if (!confirm(`确定完成选中的 ${selectedTasks.value.length} 个任务？`)) return
  
  try {
    // 实际调用API
    // await request.post('/api/v1/task-center/batch/complete', { task_ids: selectedTasks.value })
    
    selectedTasks.value.forEach(id => {
      const task = getTaskById(id)
      if (task) { task.status = 'completed'; task.progress = 100 }
    })
    showToast(`成功完成 ${selectedTasks.value.length} 个任务`)
    clearSelection()
    batchMode.value = false
  } catch (e) {
    showToast('操作失败', 'error')
  }
}

const batchSetPriority = async (priority) => {
  showPriorityMenu.value = false
  const labels = { urgent: '紧急', high: '高', medium: '中', low: '低' }
  
  try {
    // await request.post('/api/v1/task-center/batch/priority', { task_ids: selectedTasks.value, priority })
    
    selectedTasks.value.forEach(id => {
      const task = getTaskById(id)
      if (task) { task.priority = priority; task.priority_label = labels[priority] }
    })
    showToast(`已将 ${selectedTasks.value.length} 个任务优先级设为"${labels[priority]}"`)
  } catch (e) {
    showToast('操作失败', 'error')
  }
}

const confirmBatchTransfer = async () => {
  if (!transferTo.value) return
  
  try {
    // await request.post('/api/v1/task-center/batch/transfer', { task_ids: selectedTasks.value, to_user_id: transferTo.value, reason: transferReason.value })
    
    const user = users.value.find(u => u.id == transferTo.value)
    showToast(`已将 ${selectedTasks.value.length} 个任务转办给 ${user?.name}`)
    showBatchTransfer.value = false
    clearSelection()
    batchMode.value = false
    transferTo.value = ''
    transferReason.value = ''
  } catch (e) {
    showToast('转办失败', 'error')
  }
}

const confirmBatchProgress = async () => {
  try {
    // await request.post('/api/v1/task-center/batch/progress', { task_ids: selectedTasks.value, progress: batchProgressValue.value })
    
    selectedTasks.value.forEach(id => {
      const task = getTaskById(id)
      if (task) task.progress = parseInt(batchProgressValue.value)
    })
    showToast(`已更新 ${selectedTasks.value.length} 个任务进度为 ${batchProgressValue.value}%`)
    showBatchProgress.value = false
  } catch (e) {
    showToast('更新失败', 'error')
  }
}

const batchUrge = async () => {
  const remark = prompt('请输入催办备注（可选）:', '')
  if (remark === null) return
  
  try {
    // await request.post('/api/v1/task-center/batch/urge', { task_ids: selectedTasks.value, remark })
    showToast(`已对 ${selectedTasks.value.length} 个任务发送催办`)
  } catch (e) {
    showToast('催办失败', 'error')
  }
}

const batchDelete = async () => {
  if (!confirm(`确定删除选中的 ${selectedTasks.value.length} 个任务？此操作不可恢复！`)) return
  
  try {
    // await request.post('/api/v1/task-center/batch/delete', { task_ids: selectedTasks.value })
    
    tasks.value = tasks.value.filter(t => !selectedTasks.value.includes(t.id))
    showToast(`已删除 ${selectedTasks.value.length} 个任务`)
    clearSelection()
    batchMode.value = false
  } catch (e) {
    showToast('删除失败', 'error')
  }
}

// 单个任务操作
const filterByStatus = (status) => { filterStatus.value = status === 'all' ? '' : status; filterOverdue.value = false; filterDueToday.value = false }
const filterByUrgent = () => { filterOverdue.value = true; filterDueToday.value = false; filterStatus.value = '' }
const filterByToday = () => { filterDueToday.value = true; filterOverdue.value = false; filterStatus.value = '' }
const filterByWeek = () => { filterDueToday.value = false; filterOverdue.value = false; filterStatus.value = '' }

const toggleComplete = (task) => { task.status = task.status === 'completed' ? 'in_progress' : 'completed' }
const updateProgress = (task) => { const p = prompt('输入进度(0-100):', task.progress); if (p !== null) task.progress = parseInt(p) || 0 }
const logHours = (task) => { const h = prompt('输入工时:', ''); if (h) showToast(`已记录 ${h} 小时`) }
const transferTask = (task) => { showBatchTransfer.value = true; selectedTasks.value = [task.id] }
const completeTask = (task) => { task.status = 'completed'; task.progress = 100; selectedTask.value = null; showToast('任务已完成') }
const createTask = () => { showToast('任务创建成功'); showCreateModal.value = false; newTask.value = { title: '', description: '', priority: 'medium', deadline: '', project_id: '' } }
const refreshTasks = () => { loadTasks(); loadStats() }

const loadTasks = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/v1/task-center/my-tasks', { params: { page: page.value, page_size: pageSize.value } })
    if (res.code === 200) { tasks.value = res.data.tasks; totalPages.value = res.data.total_pages }
  } catch (e) { tasks.value = getMockTasks() }
  loading.value = false
}

const loadStats = async () => {
  try {
    const res = await request.get('/api/v1/task-center/statistics')
    if (res.code === 200) stats.value = res.data
  } catch (e) { stats.value = getMockStats() }
}

const getMockTasks = () => [
  { id: 1001, task_code: 'T001', title: '机械结构3D建模', description: '完成XX设备建模', task_type: 'project_wbs', type_label: '项目任务', source: { type: 'project', name: 'XX设备' }, project: { id: 1, name: 'XX自动化测试设备', level: 'A' }, schedule: { deadline: '2025-01-05T18:00:00' }, assigner: { id: 100, name: '张经理' }, status: 'in_progress', status_label: '进行中', progress: 60, priority: 'high', priority_label: '高', is_urgent: false, is_overdue: false, is_due_today: false, hours: { estimated: 40, actual: 24 } },
  { id: 1002, task_code: 'T002', title: '提交本周周报', description: '总结本周工作', task_type: 'job_duty', type_label: '岗位职责', source: { type: 'job_duty', name: '岗位职责' }, schedule: { deadline: '2025-01-03T18:00:00' }, status: 'pending', status_label: '待处理', progress: 0, priority: 'medium', priority_label: '中', is_urgent: false, is_overdue: false, is_due_today: true },
  { id: 1003, task_code: 'T003', title: '图纸评审签字', description: '评审机械图纸', task_type: 'workflow', type_label: '流程待办', source: { type: 'workflow', name: '评审流程' }, project: { id: 1, name: 'XX自动化测试设备', level: 'A' }, schedule: { deadline: '2025-01-04T18:00:00' }, assigner: { id: 102, name: '李工' }, status: 'pending', status_label: '待处理', progress: 0, priority: 'high', priority_label: '高', is_urgent: true, is_overdue: false },
  { id: 1004, task_code: 'T004', title: '协助调试设备', description: '帮老王调试', task_type: 'transfer', type_label: '转办任务', source: { type: 'transfer', name: '王工转办' }, project: { id: 1, name: 'XX自动化测试设备', level: 'A' }, schedule: { deadline: '2025-01-03T17:00:00' }, status: 'in_progress', status_label: '进行中', progress: 50, priority: 'high', priority_label: '高', is_transferred: true, transfer: { is_transferred: true, from_id: 103, from_name: '王工', reason: '出差无法处理', time: '2025-01-02T14:00:00' } },
  { id: 1005, task_code: 'T005', title: 'YY项目进度预警处理', description: '进度落后15%', task_type: 'assigned', type_label: '临时指派', source: { type: 'alert', name: '进度预警' }, project: { id: 2, name: 'YY产线改造', level: 'B' }, status: 'in_progress', status_label: '进行中', progress: 0, priority: 'urgent', priority_label: '紧急', is_urgent: true, is_overdue: false },
  { id: 1006, task_code: 'T006', title: '整理ZZ项目文档', description: '归档技术文档', task_type: 'legacy', type_label: '遗留任务', source: { type: 'project', name: 'ZZ项目' }, project: { id: 3, name: 'ZZ检测系统', level: 'C' }, status: 'in_progress', status_label: '进行中', progress: 30, priority: 'low', priority_label: '低', is_overdue: true }
]

const getMockStats = () => ({ total: 12, pending: 4, in_progress: 6, overdue: 2, due_today: 3, due_this_week: 5, urgent: 2, by_type: { project_wbs: 5, job_duty: 2, workflow: 2, transfer: 1, legacy: 1, assigned: 1 }, by_project: { 'XX自动化测试设备': 4, 'YY产线改造': 2, 'ZZ检测系统': 1 } })

// 点击外部关闭下拉菜单
const handleClickOutside = () => { showPriorityMenu.value = false }

onMounted(() => { 
  loadTasks(); loadStats()
  document.addEventListener('click', handleClickOutside)
})

watch([activeType, filterPriority, filterProject], () => { page.value = 1 })
</script>

<style scoped>
.task-center { min-height: 100vh; background: #F8FAFC; }
.page-header { background: white; border-bottom: 1px solid #E2E8F0; padding: 24px 32px; }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.header-content h1 { font-size: 24px; font-weight: 700; color: #0F172A; }
.header-subtitle { font-size: 14px; color: #64748B; margin-top: 4px; }
.header-right { display: flex; gap: 12px; }
.btn-primary, .btn-secondary { display: flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 10px; font-weight: 600; cursor: pointer; border: none; transition: all 0.2s; }
.btn-primary { background: linear-gradient(135deg, #6366F1, #4F46E5); color: white; }
.btn-secondary { background: white; color: #374151; border: 1px solid #E2E8F0; }
.btn-secondary.active { background: #6366F1; color: white; border-color: #6366F1; }
.btn-primary svg, .btn-secondary svg { width: 18px; height: 18px; }

/* 批量操作工具栏 */
.batch-toolbar { background: linear-gradient(135deg, #6366F1, #4F46E5); padding: 16px 32px; display: flex; justify-content: space-between; align-items: center; }
.batch-info { display: flex; align-items: center; gap: 16px; color: white; }
.btn-check-all { width: 24px; height: 24px; background: white; border: none; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.btn-check-all svg { width: 16px; height: 16px; color: #6366F1; }
.selected-count { font-size: 14px; }
.selected-count.hint { opacity: 0.8; }
.selected-count strong { font-weight: 700; }
.btn-text { background: none; border: none; color: white; opacity: 0.8; cursor: pointer; font-size: 14px; }
.btn-text:hover { opacity: 1; }

.batch-actions { display: flex; gap: 8px; }
.batch-btn { display: flex; align-items: center; gap: 6px; padding: 8px 16px; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; color: white; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
.batch-btn:hover { background: rgba(255,255,255,0.25); }
.batch-btn svg { width: 16px; height: 16px; }
.batch-btn.delete:hover { background: #EF4444; border-color: #EF4444; }

.batch-dropdown { position: relative; }
.batch-btn .arrow { width: 14px; height: 14px; transition: transform 0.2s; }
.batch-btn .arrow.open { transform: rotate(180deg); }
.dropdown-menu { position: absolute; top: 100%; left: 0; margin-top: 4px; background: white; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); min-width: 120px; z-index: 100; overflow: hidden; }
.dropdown-menu button { display: flex; align-items: center; gap: 8px; width: 100%; padding: 10px 16px; background: none; border: none; font-size: 14px; color: #374151; cursor: pointer; text-align: left; }
.dropdown-menu button:hover { background: #F1F5F9; }
.dropdown-menu .dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.urgent { background: #EF4444; }
.dot.high { background: #F59E0B; }
.dot.medium { background: #3B82F6; }
.dot.low { background: #94A3B8; }

.stats-section { padding: 24px 32px; }
.stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.stat-card { background: white; border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 16px; cursor: pointer; transition: all 0.2s; border: 2px solid transparent; }
.stat-card:hover { border-color: #6366F1; transform: translateY(-2px); }
.stat-card.urgent { background: linear-gradient(135deg, #FEF2F2, #FEE2E2); }
.stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-icon svg { width: 24px; height: 24px; color: white; }
.stat-icon.all { background: linear-gradient(135deg, #6366F1, #4F46E5); }
.stat-icon.urgent { background: linear-gradient(135deg, #EF4444, #DC2626); }
.stat-icon.today { background: linear-gradient(135deg, #F59E0B, #D97706); }
.stat-icon.week { background: linear-gradient(135deg, #3B82F6, #2563EB); }
.stat-icon.progress { background: linear-gradient(135deg, #10B981, #059669); }
.stat-value { font-size: 28px; font-weight: 700; color: #0F172A; display: block; }
.stat-label { font-size: 13px; color: #64748B; }

.tasks-section { padding: 0 32px 32px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 16px; }
.tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.tab { display: flex; align-items: center; gap: 6px; padding: 10px 16px; background: white; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 14px; color: #64748B; cursor: pointer; transition: all 0.2s; }
.tab:hover { border-color: #6366F1; }
.tab.active { background: #6366F1; color: white; border-color: #6366F1; }
.tab-icon { font-size: 16px; }
.tab-count { background: rgba(0,0,0,0.1); padding: 2px 8px; border-radius: 10px; font-size: 12px; }
.tab.active .tab-count { background: rgba(255,255,255,0.2); }
.filters { display: flex; gap: 12px; align-items: center; }
.filters select { padding: 10px 16px; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 14px; background: white; }
.search-box { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: white; border: 1px solid #E2E8F0; border-radius: 8px; }
.search-box svg { width: 18px; height: 18px; color: #94A3B8; }
.search-box input { border: none; outline: none; font-size: 14px; width: 160px; }

.urgent-banner { display: flex; align-items: center; gap: 16px; padding: 16px 20px; background: linear-gradient(135deg, #FEF2F2, #FEE2E2); border: 1px solid #FECACA; border-radius: 12px; margin-bottom: 20px; }
.banner-icon { font-size: 24px; }
.banner-content { flex: 1; }
.banner-content strong { display: block; color: #991B1B; }
.banner-content span { font-size: 13px; color: #B91C1C; }
.banner-btn { padding: 8px 16px; background: #EF4444; color: white; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }

.task-list { display: flex; flex-direction: column; gap: 12px; }
.task-card { display: flex; align-items: flex-start; gap: 16px; padding: 20px; background: white; border-radius: 16px; cursor: pointer; transition: all 0.2s; border: 2px solid transparent; }
.task-card:hover { border-color: #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.task-card.urgent { border-left: 4px solid #EF4444; }
.task-card.overdue { background: #FEF2F2; border-left: 4px solid #EF4444; }
.task-card.selected { border-color: #6366F1; background: #EEF2FF; }
.task-card.batch-mode { cursor: pointer; }

.task-select, .task-checkbox { width: 28px; height: 28px; border: 2px solid #D1D5DB; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; margin-top: 4px; transition: all 0.2s; }
.task-select svg, .task-checkbox svg { width: 18px; height: 18px; color: #10B981; }
.task-card.selected .task-select { background: #6366F1; border-color: #6366F1; }
.task-card.selected .task-select svg { color: white; }

.task-content { flex: 1; min-width: 0; }
.task-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.task-type { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; color: white; }
.task-priority { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; }
.task-priority.urgent { background: #FEE2E2; color: #991B1B; }
.task-priority.high { background: #FEF3C7; color: #92400E; }
.task-priority.medium { background: #E0E7FF; color: #3730A3; }
.task-priority.low { background: #F1F5F9; color: #475569; }
.task-urgent-tag, .task-overdue-tag { font-size: 12px; font-weight: 600; }
.task-urgent-tag { color: #DC2626; }
.task-overdue-tag { color: #EA580C; }
.task-title { font-size: 16px; font-weight: 600; color: #0F172A; margin-bottom: 8px; }
.task-meta { display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #64748B; }
.meta-item { display: flex; align-items: center; gap: 6px; }
.meta-item svg { width: 14px; height: 14px; }
.project-level { padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; color: white; margin-right: 4px; }
.project-level.level-a { background: #6366F1; }
.project-level.level-b { background: #F59E0B; }
.project-level.level-c { background: #10B981; }
.task-progress { display: flex; align-items: center; gap: 12px; margin-top: 12px; }
.progress-bar { flex: 1; height: 6px; background: #E2E8F0; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6); border-radius: 3px; }
.progress-text { font-size: 13px; font-weight: 600; color: #6366F1; }
.task-actions { display: flex; gap: 8px; }
.action-btn { width: 36px; height: 36px; border: none; background: #F1F5F9; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.action-btn:hover { background: #E2E8F0; }
.action-btn svg { width: 18px; height: 18px; color: #64748B; }

.empty-state { text-align: center; padding: 60px; color: #64748B; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }

.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 24px; }
.pagination button { padding: 10px 20px; border: 1px solid #E2E8F0; border-radius: 8px; background: white; cursor: pointer; }
.pagination button:disabled { opacity: 0.5; cursor: not-allowed; }

/* 抽屉和弹窗 */
.drawer-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; justify-content: flex-end; }
.drawer { width: 500px; max-width: 100%; background: white; height: 100%; overflow-y: auto; }
.drawer-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #E2E8F0; }
.drawer-header h2 { font-size: 18px; font-weight: 600; }
.drawer-close { width: 32px; height: 32px; border: none; background: #F1F5F9; border-radius: 8px; font-size: 20px; cursor: pointer; }
.drawer-body { padding: 24px; }
.detail-section { margin-bottom: 24px; }
.detail-section h3 { font-size: 14px; font-weight: 600; color: #64748B; margin-bottom: 12px; }
.detail-type { display: inline-block; padding: 6px 12px; border-radius: 8px; font-size: 13px; color: white; margin-bottom: 12px; }
.detail-title { font-size: 20px; font-weight: 700; color: #0F172A; margin-bottom: 8px; }
.detail-desc { font-size: 14px; color: #64748B; line-height: 1.6; }
.detail-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item .label { font-size: 12px; color: #94A3B8; }
.detail-item .value { font-size: 14px; font-weight: 500; color: #0F172A; }
.detail-item .value.status, .detail-item .value.priority { padding: 4px 10px; border-radius: 6px; display: inline-block; width: fit-content; }
.transfer-info { padding: 16px; background: #F8FAFC; border-radius: 12px; }
.transfer-reason { margin-top: 8px; color: #64748B; }
.detail-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 24px; padding-top: 24px; border-top: 1px solid #E2E8F0; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: center; justify-content: center; }
.modal { background: white; border-radius: 20px; width: 500px; max-width: 90%; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid #E2E8F0; }
.modal-header h3 { font-size: 18px; font-weight: 600; }
.modal-header button { width: 32px; height: 32px; border: none; background: #F1F5F9; border-radius: 8px; font-size: 20px; cursor: pointer; }
.modal-body { padding: 24px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 12px 16px; border: 1px solid #E2E8F0; border-radius: 10px; font-size: 14px; }
.form-group textarea { min-height: 80px; resize: vertical; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 24px; border-top: 1px solid #E2E8F0; }

.selected-tasks-preview { background: #F8FAFC; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; }
.preview-item { font-size: 13px; color: #374151; padding: 4px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.preview-more { font-size: 12px; color: #64748B; margin-top: 4px; }

.progress-slider { text-align: center; padding: 20px 0; }
.progress-slider input[type="range"] { width: 100%; height: 8px; border-radius: 4px; appearance: none; background: #E2E8F0; }
.progress-slider input[type="range"]::-webkit-slider-thumb { appearance: none; width: 24px; height: 24px; border-radius: 50%; background: #6366F1; cursor: pointer; }
.progress-value { font-size: 36px; font-weight: 700; color: #6366F1; margin-top: 16px; }
.progress-presets { display: flex; justify-content: center; gap: 8px; margin-top: 16px; }
.progress-presets button { padding: 8px 16px; border: 1px solid #E2E8F0; border-radius: 8px; background: white; cursor: pointer; }
.progress-presets button.active { background: #6366F1; color: white; border-color: #6366F1; }

/* Toast提示 */
.toast { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); padding: 12px 24px; background: #10B981; color: white; border-radius: 10px; font-weight: 500; z-index: 2000; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
.toast.error { background: #EF4444; }

/* 动画 */
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.3s ease; }
.slide-down-enter-from, .slide-down-leave-to { transform: translateY(-100%); opacity: 0; }
.fade-enter-active, .fade-leave-active { transition: all 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-10px); }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 20px); }

@media (max-width: 1024px) { .stats-grid { grid-template-columns: repeat(3, 1fr); } .batch-btn span { display: none; } }
@media (max-width: 768px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } .section-header { flex-direction: column; align-items: stretch; } .filters { flex-wrap: wrap; } .batch-toolbar { flex-direction: column; gap: 12px; } }
</style>
