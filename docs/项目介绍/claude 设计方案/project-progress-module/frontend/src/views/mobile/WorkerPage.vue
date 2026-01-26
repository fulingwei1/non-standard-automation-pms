<template>
  <div class="mobile-worker-page">
    <!-- 顶部状态栏 -->
    <header class="mobile-header">
      <div class="user-info">
        <div class="avatar">{{ user.name.charAt(0) }}</div>
        <div class="user-detail">
          <span class="user-name">{{ user.name }}</span>
          <span class="user-role">{{ user.role }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="notification-btn" @click="showNotifications = true">
          <span class="icon">🔔</span>
          <span class="badge" v-if="notifications.length">{{ notifications.length }}</span>
        </button>
      </div>
    </header>

    <!-- 今日任务概览 -->
    <section class="today-summary">
      <h2>今日任务</h2>
      <div class="summary-cards">
        <div class="summary-card">
          <span class="card-value">{{ todaySummary.pending }}</span>
          <span class="card-label">待处理</span>
        </div>
        <div class="summary-card in-progress">
          <span class="card-value">{{ todaySummary.inProgress }}</span>
          <span class="card-label">进行中</span>
        </div>
        <div class="summary-card completed">
          <span class="card-value">{{ todaySummary.completed }}</span>
          <span class="card-label">已完成</span>
        </div>
      </div>
    </section>

    <!-- 快捷操作 -->
    <section class="quick-actions">
      <button class="action-btn" @click="scanQRCode">
        <span class="action-icon">📷</span>
        <span class="action-text">扫码报工</span>
      </button>
      <button class="action-btn" @click="reportIssue">
        <span class="action-icon">⚠️</span>
        <span class="action-text">问题上报</span>
      </button>
      <button class="action-btn" @click="pickMaterial">
        <span class="action-icon">📦</span>
        <span class="action-text">领料申请</span>
      </button>
      <button class="action-btn" @click="checkWorkOrder">
        <span class="action-icon">📋</span>
        <span class="action-text">工单查询</span>
      </button>
    </section>

    <!-- 当前任务列表 -->
    <section class="task-list">
      <div class="section-header">
        <h3>我的任务</h3>
        <div class="filter-tabs">
          <button :class="{ active: taskFilter === 'all' }" @click="taskFilter = 'all'">全部</button>
          <button :class="{ active: taskFilter === 'urgent' }" @click="taskFilter = 'urgent'">紧急</button>
          <button :class="{ active: taskFilter === 'today' }" @click="taskFilter = 'today'">今日</button>
        </div>
      </div>

      <div class="tasks">
        <div class="task-card" v-for="task in filteredTasks" :key="task.id" @click="openTaskDetail(task)">
          <div class="task-header">
            <span class="task-priority" :class="task.priority">{{ task.priority === 'urgent' ? '紧急' : '普通' }}</span>
            <span class="task-status" :class="task.status">{{ task.status_label }}</span>
          </div>
          <h4 class="task-name">{{ task.name }}</h4>
          <p class="task-desc">{{ task.description }}</p>
          <div class="task-meta">
            <span class="meta-item">
              <span class="icon">📍</span>
              {{ task.workstation }}
            </span>
            <span class="meta-item">
              <span class="icon">🕐</span>
              {{ task.deadline }}
            </span>
          </div>
          <div class="task-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
            </div>
            <span class="progress-text">{{ task.progress }}%</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 底部导航 -->
    <nav class="bottom-nav">
      <button :class="{ active: activeTab === 'home' }" @click="activeTab = 'home'">
        <span class="nav-icon">🏠</span>
        <span class="nav-text">首页</span>
      </button>
      <button :class="{ active: activeTab === 'tasks' }" @click="activeTab = 'tasks'">
        <span class="nav-icon">📋</span>
        <span class="nav-text">任务</span>
      </button>
      <button class="main-action" @click="scanQRCode">
        <span class="nav-icon">📷</span>
      </button>
      <button :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">
        <span class="nav-icon">📊</span>
        <span class="nav-text">记录</span>
      </button>
      <button :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">
        <span class="nav-icon">👤</span>
        <span class="nav-text">我的</span>
      </button>
    </nav>

    <!-- 任务详情弹窗 -->
    <div class="modal-overlay" v-if="showTaskDetail" @click.self="showTaskDetail = false">
      <div class="modal-sheet">
        <div class="sheet-handle"></div>
        <div class="sheet-content">
          <div class="task-detail-header">
            <span class="task-priority" :class="currentTask?.priority">{{ currentTask?.priority === 'urgent' ? '紧急' : '普通' }}</span>
            <h3>{{ currentTask?.name }}</h3>
          </div>
          
          <div class="detail-section">
            <div class="detail-row">
              <span class="detail-label">工单号</span>
              <span class="detail-value">{{ currentTask?.work_order_no }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">设备</span>
              <span class="detail-value">{{ currentTask?.equipment_name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">工位</span>
              <span class="detail-value">{{ currentTask?.workstation }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">计划工时</span>
              <span class="detail-value">{{ currentTask?.plan_hours }}小时</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">截止时间</span>
              <span class="detail-value">{{ currentTask?.deadline }}</span>
            </div>
          </div>

          <div class="detail-section">
            <h4>任务描述</h4>
            <p>{{ currentTask?.description }}</p>
          </div>

          <div class="detail-section">
            <h4>操作说明</h4>
            <ol class="instruction-list">
              <li v-for="(inst, idx) in currentTask?.instructions" :key="idx">{{ inst }}</li>
            </ol>
          </div>

          <div class="detail-section">
            <h4>相关图纸</h4>
            <div class="drawing-list">
              <div class="drawing-item" v-for="d in currentTask?.drawings" :key="d.id">
                <span class="icon">📐</span>
                <span class="name">{{ d.name }}</span>
                <button class="view-btn">查看</button>
              </div>
            </div>
          </div>

          <div class="action-buttons">
            <button class="btn-secondary" @click="showTaskDetail = false">关闭</button>
            <button class="btn-primary" v-if="currentTask?.status === 'pending'" @click="startTask">
              开始任务
            </button>
            <button class="btn-primary" v-else-if="currentTask?.status === 'in_progress'" @click="showReportModal = true">
              报工完成
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 报工弹窗 -->
    <div class="modal-overlay" v-if="showReportModal" @click.self="showReportModal = false">
      <div class="modal-sheet">
        <div class="sheet-handle"></div>
        <div class="sheet-content">
          <h3>报工</h3>
          
          <div class="form-group">
            <label>完成数量</label>
            <div class="quantity-input">
              <button @click="reportForm.quantity > 0 && reportForm.quantity--">-</button>
              <input type="number" v-model="reportForm.quantity" />
              <button @click="reportForm.quantity++">+</button>
            </div>
          </div>

          <div class="form-group">
            <label>实际工时（小时）</label>
            <input type="number" v-model="reportForm.hours" step="0.5" />
          </div>

          <div class="form-group">
            <label>完成状态</label>
            <div class="radio-group">
              <label class="radio-item">
                <input type="radio" v-model="reportForm.status" value="completed" />
                <span>全部完成</span>
              </label>
              <label class="radio-item">
                <input type="radio" v-model="reportForm.status" value="partial" />
                <span>部分完成</span>
              </label>
              <label class="radio-item">
                <input type="radio" v-model="reportForm.status" value="issue" />
                <span>有问题</span>
              </label>
            </div>
          </div>

          <div class="form-group" v-if="reportForm.status === 'issue'">
            <label>问题描述</label>
            <textarea v-model="reportForm.issueDesc" placeholder="请描述遇到的问题..."></textarea>
          </div>

          <div class="form-group">
            <label>拍照（可选）</label>
            <div class="photo-upload">
              <div class="photo-item" v-for="(photo, idx) in reportForm.photos" :key="idx">
                <img :src="photo" alt="" />
                <button class="remove-btn" @click="reportForm.photos.splice(idx, 1)">×</button>
              </div>
              <button class="add-photo-btn" @click="takePhoto">
                <span>📷</span>
                <span>拍照</span>
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>备注</label>
            <textarea v-model="reportForm.remark" placeholder="其他说明..."></textarea>
          </div>

          <div class="action-buttons">
            <button class="btn-secondary" @click="showReportModal = false">取消</button>
            <button class="btn-primary" @click="submitReport">提交报工</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 问题上报弹窗 -->
    <div class="modal-overlay" v-if="showIssueModal" @click.self="showIssueModal = false">
      <div class="modal-sheet">
        <div class="sheet-handle"></div>
        <div class="sheet-content">
          <h3>问题上报</h3>
          
          <div class="form-group">
            <label>问题类型</label>
            <select v-model="issueForm.type">
              <option value="quality">质量问题</option>
              <option value="material">物料问题</option>
              <option value="equipment">设备故障</option>
              <option value="drawing">图纸问题</option>
              <option value="other">其他</option>
            </select>
          </div>

          <div class="form-group">
            <label>紧急程度</label>
            <div class="radio-group inline">
              <label class="radio-item">
                <input type="radio" v-model="issueForm.level" value="low" />
                <span>一般</span>
              </label>
              <label class="radio-item">
                <input type="radio" v-model="issueForm.level" value="medium" />
                <span>较急</span>
              </label>
              <label class="radio-item">
                <input type="radio" v-model="issueForm.level" value="high" />
                <span>紧急</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>关联工单（可选）</label>
            <select v-model="issueForm.workOrderId">
              <option value="">请选择</option>
              <option v-for="wo in workOrders" :key="wo.id" :value="wo.id">{{ wo.no }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>问题描述</label>
            <textarea v-model="issueForm.description" placeholder="请详细描述问题..." rows="4"></textarea>
          </div>

          <div class="form-group">
            <label>拍照（建议上传）</label>
            <div class="photo-upload">
              <div class="photo-item" v-for="(photo, idx) in issueForm.photos" :key="idx">
                <img :src="photo" alt="" />
                <button class="remove-btn" @click="issueForm.photos.splice(idx, 1)">×</button>
              </div>
              <button class="add-photo-btn" @click="takeIssuePhoto">
                <span>📷</span>
                <span>拍照</span>
              </button>
            </div>
          </div>

          <div class="action-buttons">
            <button class="btn-secondary" @click="showIssueModal = false">取消</button>
            <button class="btn-primary" @click="submitIssue">提交</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

// 用户信息
const user = reactive({
  name: '张师傅',
  role: '装配工'
})

// 今日汇总
const todaySummary = reactive({
  pending: 3,
  inProgress: 2,
  completed: 5
})

// 状态
const activeTab = ref('home')
const taskFilter = ref('all')
const showTaskDetail = ref(false)
const showReportModal = ref(false)
const showIssueModal = ref(false)
const showNotifications = ref(false)
const currentTask = ref(null)

// 通知
const notifications = ref([
  { id: 1, type: 'urgent', message: '紧急任务：机架装配需要今日完成', time: '10分钟前' }
])

// 任务列表
const tasks = ref([
  {
    id: 1,
    name: '机架总成装配',
    description: '完成设备主机架的组装工作，包括底座、立柱、横梁的安装',
    work_order_no: 'WO-2025-0103-001',
    equipment_name: 'XX汽车传感器自动测试设备',
    workstation: '装配区-A3工位',
    priority: 'urgent',
    status: 'in_progress',
    status_label: '进行中',
    progress: 60,
    plan_hours: 8,
    deadline: '今天 18:00',
    instructions: [
      '按图纸要求组装底座框架',
      '安装4根立柱，确保垂直度在0.1mm以内',
      '安装横梁，使用力矩扳手拧紧螺栓',
      '完成后进行水平度检测'
    ],
    drawings: [
      { id: 1, name: '机架装配图.dwg' },
      { id: 2, name: '底座详图.dwg' }
    ]
  },
  {
    id: 2,
    name: '电气柜走线',
    description: '电气柜内部走线及接线工作',
    work_order_no: 'WO-2025-0103-002',
    equipment_name: 'XX汽车传感器自动测试设备',
    workstation: '电气区-B1工位',
    priority: 'normal',
    status: 'pending',
    status_label: '待开始',
    progress: 0,
    plan_hours: 6,
    deadline: '明天 12:00',
    instructions: [
      '按照电气图纸进行线缆布置',
      '使用线号管标识每根线缆',
      '确保接线牢固，使用端子压接工具'
    ],
    drawings: [
      { id: 3, name: '电气接线图.dwg' }
    ]
  },
  {
    id: 3,
    name: '传动系统安装',
    description: '安装伺服电机、减速机、联轴器等传动部件',
    work_order_no: 'WO-2025-0103-003',
    equipment_name: 'XX汽车传感器自动测试设备',
    workstation: '装配区-A3工位',
    priority: 'normal',
    status: 'pending',
    status_label: '待开始',
    progress: 0,
    plan_hours: 4,
    deadline: '明天 18:00',
    instructions: [],
    drawings: []
  }
])

// 工单列表
const workOrders = ref([
  { id: 1, no: 'WO-2025-0103-001' },
  { id: 2, no: 'WO-2025-0103-002' }
])

// 报工表单
const reportForm = reactive({
  quantity: 1,
  hours: 0,
  status: 'completed',
  issueDesc: '',
  photos: [],
  remark: ''
})

// 问题上报表单
const issueForm = reactive({
  type: 'quality',
  level: 'medium',
  workOrderId: '',
  description: '',
  photos: []
})

// 筛选后的任务
const filteredTasks = computed(() => {
  if (taskFilter.value === 'urgent') {
    return tasks.value.filter(t => t.priority === 'urgent')
  }
  if (taskFilter.value === 'today') {
    return tasks.value.filter(t => t.deadline.includes('今天'))
  }
  return tasks.value
})

// 方法
const scanQRCode = () => {
  alert('打开扫码功能')
}

const reportIssue = () => {
  showIssueModal.value = true
}

const pickMaterial = () => {
  alert('打开领料申请')
}

const checkWorkOrder = () => {
  alert('打开工单查询')
}

const openTaskDetail = (task) => {
  currentTask.value = task
  showTaskDetail.value = true
}

const startTask = () => {
  if (currentTask.value) {
    currentTask.value.status = 'in_progress'
    currentTask.value.status_label = '进行中'
    alert('任务已开始')
  }
}

const takePhoto = () => {
  // 模拟拍照
  reportForm.photos.push('https://via.placeholder.com/100')
}

const takeIssuePhoto = () => {
  issueForm.photos.push('https://via.placeholder.com/100')
}

const submitReport = () => {
  alert('报工提交成功！')
  showReportModal.value = false
  showTaskDetail.value = false
  if (currentTask.value) {
    currentTask.value.status = 'completed'
    currentTask.value.status_label = '已完成'
    currentTask.value.progress = 100
    todaySummary.completed++
    todaySummary.inProgress--
  }
}

const submitIssue = () => {
  alert('问题已上报，已通知相关负责人！')
  showIssueModal.value = false
}
</script>

<style scoped>
.mobile-worker-page {
  min-height: 100vh;
  background: #0f172a;
  color: white;
  padding-bottom: 80px;
}

/* 顶部 */
.mobile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.user-info { display: flex; align-items: center; gap: 12px; }
.avatar {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
}
.user-detail { display: flex; flex-direction: column; }
.user-name { font-size: 16px; font-weight: 600; }
.user-role { font-size: 13px; color: #94A3B8; }

.notification-btn {
  position: relative;
  width: 44px;
  height: 44px;
  background: rgba(255,255,255,0.05);
  border: none;
  border-radius: 12px;
  cursor: pointer;
}
.notification-btn .icon { font-size: 20px; }
.notification-btn .badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 18px;
  height: 18px;
  background: #EF4444;
  border-radius: 50%;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

/* 今日汇总 */
.today-summary { padding: 20px; }
.today-summary h2 { font-size: 18px; margin-bottom: 16px; }
.summary-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.summary-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}
.card-value { font-size: 28px; font-weight: 700; display: block; }
.card-label { font-size: 12px; color: #94A3B8; }
.summary-card.in-progress { border-color: rgba(245,158,11,0.3); }
.summary-card.in-progress .card-value { color: #F59E0B; }
.summary-card.completed { border-color: rgba(16,185,129,0.3); }
.summary-card.completed .card-value { color: #10B981; }

/* 快捷操作 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 0 20px;
  margin-bottom: 20px;
}
.action-btn {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.action-icon { font-size: 24px; }
.action-text { font-size: 12px; color: #94A3B8; }

/* 任务列表 */
.task-list { padding: 0 20px; }
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-header h3 { font-size: 16px; }
.filter-tabs { display: flex; gap: 8px; }
.filter-tabs button {
  padding: 6px 12px;
  background: rgba(255,255,255,0.05);
  border: none;
  border-radius: 6px;
  color: #94A3B8;
  font-size: 12px;
  cursor: pointer;
}
.filter-tabs button.active { background: rgba(99,102,241,0.2); color: white; }

.tasks { display: flex; flex-direction: column; gap: 12px; }
.task-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
}
.task-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.task-priority, .task-status { font-size: 11px; padding: 4px 8px; border-radius: 4px; }
.task-priority.urgent { background: rgba(239,68,68,0.2); color: #F87171; }
.task-priority.normal { background: rgba(100,116,139,0.2); color: #94A3B8; }
.task-status.in_progress { background: rgba(245,158,11,0.2); color: #F59E0B; }
.task-status.pending { background: rgba(100,116,139,0.2); color: #94A3B8; }
.task-status.completed { background: rgba(16,185,129,0.2); color: #10B981; }
.task-name { font-size: 15px; margin-bottom: 6px; }
.task-desc { font-size: 13px; color: #94A3B8; margin-bottom: 12px; line-height: 1.4; }
.task-meta { display: flex; gap: 16px; margin-bottom: 12px; }
.meta-item { font-size: 12px; color: #64748B; display: flex; align-items: center; gap: 4px; }
.task-progress { display: flex; align-items: center; gap: 8px; }
.progress-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6); }
.progress-text { font-size: 12px; color: #94A3B8; }

/* 底部导航 */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #1E293B;
  border-top: 1px solid rgba(255,255,255,0.1);
  display: flex;
  justify-content: space-around;
  padding: 8px 0 20px;
}
.bottom-nav button {
  background: transparent;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 8px 16px;
}
.nav-icon { font-size: 20px; }
.nav-text { font-size: 11px; color: #64748B; }
.bottom-nav button.active .nav-text { color: #6366F1; }
.main-action {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border-radius: 50% !important;
  margin-top: -20px;
  box-shadow: 0 4px 12px rgba(99,102,241,0.4);
}
.main-action .nav-icon { font-size: 24px; color: white; }

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: flex-end;
  z-index: 1000;
}
.modal-sheet {
  width: 100%;
  max-height: 90vh;
  background: #1E293B;
  border-radius: 20px 20px 0 0;
  overflow: hidden;
}
.sheet-handle {
  width: 40px;
  height: 4px;
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
  margin: 12px auto;
}
.sheet-content { padding: 0 20px 30px; max-height: 85vh; overflow-y: auto; }
.sheet-content h3 { font-size: 18px; margin-bottom: 20px; }

/* 任务详情 */
.task-detail-header { margin-bottom: 20px; }
.task-detail-header .task-priority { margin-bottom: 8px; display: inline-block; }
.task-detail-header h3 { font-size: 18px; }

.detail-section { margin-bottom: 20px; }
.detail-section h4 { font-size: 14px; color: #94A3B8; margin-bottom: 12px; }
.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  font-size: 14px;
}
.detail-label { color: #64748B; }
.instruction-list { padding-left: 20px; font-size: 14px; line-height: 1.8; color: #94A3B8; }
.drawing-list { display: flex; flex-direction: column; gap: 8px; }
.drawing-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
}
.drawing-item .name { flex: 1; font-size: 14px; }
.view-btn {
  padding: 6px 12px;
  background: rgba(99,102,241,0.2);
  border: none;
  border-radius: 6px;
  color: #A5B4FC;
  font-size: 12px;
  cursor: pointer;
}

.action-buttons { display: flex; gap: 12px; margin-top: 24px; }
.btn-primary, .btn-secondary { flex: 1; padding: 14px; border: none; border-radius: 10px; font-size: 15px; cursor: pointer; }
.btn-primary { background: linear-gradient(135deg, #6366F1, #8B5CF6); color: white; }
.btn-secondary { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); color: white; }

/* 表单 */
.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 14px; color: #94A3B8; margin-bottom: 8px; }
.form-group input, .form-group select, .form-group textarea {
  width: 100%;
  padding: 12px 14px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px;
  color: white;
  font-size: 14px;
}
.form-group textarea { min-height: 80px; resize: vertical; }

.quantity-input {
  display: flex;
  align-items: center;
  gap: 12px;
}
.quantity-input button {
  width: 44px;
  height: 44px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px;
  color: white;
  font-size: 20px;
  cursor: pointer;
}
.quantity-input input { text-align: center; width: 80px; }

.radio-group { display: flex; flex-direction: column; gap: 12px; }
.radio-group.inline { flex-direction: row; gap: 16px; }
.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  cursor: pointer;
}
.radio-item input { width: 18px; height: 18px; }

.photo-upload { display: flex; gap: 12px; flex-wrap: wrap; }
.photo-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
}
.photo-item img { width: 100%; height: 100%; object-fit: cover; }
.photo-item .remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: rgba(0,0,0,0.6);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
}
.add-photo-btn {
  width: 80px;
  height: 80px;
  background: rgba(255,255,255,0.02);
  border: 2px dashed rgba(255,255,255,0.2);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  color: #64748B;
  font-size: 12px;
}
.add-photo-btn span:first-child { font-size: 24px; }
</style>
