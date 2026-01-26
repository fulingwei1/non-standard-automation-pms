<template>
  <div class="gantt-container">
    <!-- 工具栏 -->
    <div class="gantt-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button size="small" @click="zoomIn">
            <el-icon><ZoomIn /></el-icon> 放大
          </el-button>
          <el-button size="small" @click="zoomOut">
            <el-icon><ZoomOut /></el-icon> 缩小
          </el-button>
          <el-button size="small" @click="fitToScreen">
            <el-icon><FullScreen /></el-icon> 适应
          </el-button>
          <el-button size="small" @click="scrollToToday">
            <el-icon><Aim /></el-icon> 今日
          </el-button>
        </el-button-group>
        
        <el-radio-group v-model="viewMode" size="small" @change="changeViewMode">
          <el-radio-button label="day">日视图</el-radio-button>
          <el-radio-button label="week">周视图</el-radio-button>
          <el-radio-button label="month">月视图</el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="toolbar-right">
        <el-checkbox v-model="showCriticalPath">关键路径</el-checkbox>
        <el-checkbox v-model="showDependencies">依赖线</el-checkbox>
        <el-checkbox v-model="showBaseline">基线对比</el-checkbox>
        
        <el-button type="primary" size="small" @click="calculateCPM" :loading="calculating">
          <el-icon><DataAnalysis /></el-icon> 计算关键路径
        </el-button>
        
        <el-button size="small" @click="exportImage">
          <el-icon><Download /></el-icon> 导出
        </el-button>
      </div>
    </div>
    
    <!-- 甘特图主体 -->
    <div class="gantt-main" ref="ganttMain">
      <!-- 左侧任务列表 -->
      <div class="task-list" :style="{ width: listWidth + 'px' }">
        <!-- 列表头部 -->
        <div class="task-list-header">
          <div class="header-row">
            <div class="col col-wbs" style="width: 70px">WBS</div>
            <div class="col col-name" style="flex: 1">任务名称</div>
            <div class="col col-owner" style="width: 70px">负责人</div>
            <div class="col col-start" style="width: 90px">开始日期</div>
            <div class="col col-end" style="width: 90px">结束日期</div>
            <div class="col col-duration" style="width: 50px">工期</div>
            <div class="col col-progress" style="width: 80px">进度</div>
          </div>
        </div>
        
        <!-- 列表内容 -->
        <div class="task-list-body" ref="taskListBody" @scroll="onListScroll">
          <div 
            v-for="(task, index) in visibleTasks" 
            :key="task.id"
            class="task-row"
            :class="getRowClass(task)"
            :style="{ height: rowHeight + 'px' }"
            @click="selectTask(task)"
            @dblclick="openTaskDetail(task)"
          >
            <div class="col col-wbs" style="width: 70px">
              <span class="wbs-code">{{ task.wbs_code }}</span>
            </div>
            <div class="col col-name" style="flex: 1" :style="{ paddingLeft: getIndent(task) + 'px' }">
              <span 
                v-if="hasChildren(task)" 
                class="expand-btn"
                @click.stop="toggleExpand(task.id)"
              >
                <el-icon v-if="isExpanded(task.id)"><ArrowDown /></el-icon>
                <el-icon v-else><ArrowRight /></el-icon>
              </span>
              <span class="task-name" :title="task.label">{{ task.label }}</span>
              <el-tag v-if="task.type === 'milestone'" size="small" type="warning" class="milestone-tag">
                <el-icon><Flag /></el-icon>
              </el-tag>
              <el-tag v-if="task.is_critical && showCriticalPath" size="small" type="danger" class="critical-tag">
                关键
              </el-tag>
            </div>
            <div class="col col-owner" style="width: 70px">
              <el-avatar v-if="task.owner" :size="20">{{ task.owner?.charAt(0) }}</el-avatar>
              <span class="owner-name">{{ task.owner || '-' }}</span>
            </div>
            <div class="col col-start" style="width: 90px">{{ formatDate(task.start) }}</div>
            <div class="col col-end" style="width: 90px">{{ formatDate(task.end) }}</div>
            <div class="col col-duration" style="width: 50px">{{ task.duration }}天</div>
            <div class="col col-progress" style="width: 80px">
              <el-progress 
                :percentage="task.progress" 
                :stroke-width="8"
                :color="getProgressColor(task)"
                :show-text="false"
              />
              <span class="progress-text">{{ task.progress }}%</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 分隔条 -->
      <div class="splitter" @mousedown="startResize">
        <div class="splitter-line"></div>
      </div>
      
      <!-- 右侧甘特图 -->
      <div class="chart-area" ref="chartArea">
        <!-- 时间轴头部 -->
        <div class="timeline-header" ref="timelineHeader">
          <!-- 第一行：月份/年份 -->
          <div class="timeline-row timeline-months">
            <div 
              v-for="period in timelinePeriods" 
              :key="period.key"
              class="period-cell"
              :style="{ width: period.width + 'px' }"
            >
              {{ period.label }}
            </div>
          </div>
          <!-- 第二行：日期 -->
          <div class="timeline-row timeline-days">
            <div 
              v-for="day in timelineDays" 
              :key="day.key"
              class="day-cell"
              :class="{ 
                'is-weekend': day.isWeekend, 
                'is-today': day.isToday,
                'is-holiday': day.isHoliday
              }"
              :style="{ width: cellWidth + 'px' }"
            >
              <span class="day-number">{{ day.dayNum }}</span>
              <span v-if="viewMode === 'day'" class="day-week">{{ day.weekDay }}</span>
            </div>
          </div>
        </div>
        
        <!-- 甘特图画布 -->
        <div class="chart-canvas" ref="chartCanvas" @scroll="onChartScroll">
          <!-- 网格背景 -->
          <div class="grid-layer" :style="{ width: chartWidth + 'px', height: chartHeight + 'px' }">
            <div 
              v-for="day in timelineDays" 
              :key="'grid-' + day.key"
              class="grid-column"
              :class="{ 'is-weekend': day.isWeekend, 'is-today': day.isToday }"
              :style="{ width: cellWidth + 'px' }"
            ></div>
          </div>
          
          <!-- 今日标线 -->
          <div 
            v-if="todayPosition >= 0"
            class="today-marker" 
            :style="{ left: todayPosition + 'px' }"
          >
            <div class="today-label">今日</div>
            <div class="today-line"></div>
          </div>
          
          <!-- 依赖线SVG层 -->
          <svg 
            v-if="showDependencies"
            class="dependency-layer" 
            :width="chartWidth" 
            :height="chartHeight"
          >
            <defs>
              <marker 
                id="arrow" 
                markerWidth="10" 
                markerHeight="10" 
                refX="9" 
                refY="3"
                orient="auto" 
                markerUnits="strokeWidth"
              >
                <path d="M0,0 L0,6 L9,3 z" fill="#999" />
              </marker>
              <marker 
                id="arrow-critical" 
                markerWidth="10" 
                markerHeight="10" 
                refX="9" 
                refY="3"
                orient="auto" 
                markerUnits="strokeWidth"
              >
                <path d="M0,0 L0,6 L9,3 z" fill="#ff4d4f" />
              </marker>
            </defs>
            <g class="dependencies">
              <path 
                v-for="dep in dependencyPaths" 
                :key="dep.id"
                :d="dep.path"
                class="dep-line"
                :class="{ 'is-critical': dep.isCritical && showCriticalPath }"
                :marker-end="dep.isCritical && showCriticalPath ? 'url(#arrow-critical)' : 'url(#arrow)'"
              />
            </g>
          </svg>
          
          <!-- 任务条层 -->
          <div class="bars-layer" :style="{ width: chartWidth + 'px' }">
            <div 
              v-for="(task, index) in visibleTasks" 
              :key="'bar-' + task.id"
              class="bar-row"
              :style="{ height: rowHeight + 'px' }"
            >
              <!-- 基线条（虚线） -->
              <div 
                v-if="showBaseline && task.baseline_start && task.baseline_end"
                class="baseline-bar"
                :style="getBaselineStyle(task)"
              ></div>
              
              <!-- 里程碑菱形 -->
              <div 
                v-if="task.type === 'milestone'"
                class="milestone-diamond"
                :class="{ 'is-critical': task.is_critical && showCriticalPath }"
                :style="getMilestoneStyle(task)"
                @click.stop="selectTask(task)"
                @mousedown="startDragMilestone($event, task)"
              >
                <el-icon><Star /></el-icon>
              </div>
              
              <!-- 任务条 -->
              <div 
                v-else
                class="task-bar"
                :class="getBarClass(task)"
                :style="getBarStyle(task)"
                @click.stop="selectTask(task)"
                @mousedown="startDragBar($event, task)"
              >
                <!-- 进度填充 -->
                <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
                
                <!-- 任务名称标签 -->
                <span class="bar-label" :class="{ 'outside': getBarWidth(task) < 100 }">
                  {{ task.label }}
                </span>
                
                <!-- 左侧拖拽手柄 -->
                <div 
                  class="resize-handle left"
                  @mousedown.stop="startResizeBar($event, task, 'left')"
                ></div>
                
                <!-- 右侧拖拽手柄 -->
                <div 
                  class="resize-handle right"
                  @mousedown.stop="startResizeBar($event, task, 'right')"
                ></div>
                
                <!-- 连接点（用于创建依赖） -->
                <div 
                  class="connector left"
                  @mousedown.stop="startCreateDependency($event, task, 'start')"
                ></div>
                <div 
                  class="connector right"
                  @mousedown.stop="startCreateDependency($event, task, 'end')"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 任务详情抽屉 -->
    <el-drawer 
      v-model="showDetailDrawer" 
      title="任务详情" 
      size="480px"
      :destroy-on-close="true"
    >
      <TaskDetailPanel 
        v-if="selectedTask"
        :task="selectedTask"
        :project-id="projectId"
        @update="handleTaskUpdate"
        @delete="handleTaskDelete"
        @close="showDetailDrawer = false"
      />
    </el-drawer>
    
    <!-- 右键菜单 -->
    <div 
      v-show="showContextMenu"
      class="context-menu"
      :style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }"
    >
      <div class="menu-item" @click="addSubTask">
        <el-icon><Plus /></el-icon> 添加子任务
      </div>
      <div class="menu-item" @click="editTask">
        <el-icon><Edit /></el-icon> 编辑任务
      </div>
      <div class="menu-divider"></div>
      <div class="menu-item" @click="setBaseline">
        <el-icon><Calendar /></el-icon> 设为基线
      </div>
      <div class="menu-item danger" @click="deleteTask">
        <el-icon><Delete /></el-icon> 删除任务
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ZoomIn, ZoomOut, FullScreen, Aim, ArrowDown, ArrowRight,
  Flag, DataAnalysis, Download, Star, Plus, Edit, Calendar, Delete
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import TaskDetailPanel from './TaskDetailPanel.vue'
import { 
  getGanttData, 
  updateTaskDates, 
  calculateCriticalPath as calcCPM,
  createDependency,
  deleteDependency 
} from '@/api/task'

// ============== Props ==============
const props = defineProps({
  projectId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['task-updated', 'task-selected', 'task-deleted'])

// ============== 响应式数据 ==============
const tasks = ref([])
const dependencies = ref([])
const expandedIds = ref(new Set())
const selectedTaskId = ref(null)
const showDetailDrawer = ref(false)
const calculating = ref(false)

// 视图配置
const viewMode = ref('day')
const cellWidth = ref(40)
const rowHeight = ref(40)
const listWidth = ref(600)
const showCriticalPath = ref(true)
const showDependencies = ref(true)
const showBaseline = ref(false)

// 时间范围
const startDate = ref(dayjs())
const endDate = ref(dayjs().add(3, 'month'))

// 右键菜单
const showContextMenu = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextTask = ref(null)

// DOM引用
const ganttMain = ref(null)
const taskListBody = ref(null)
const chartCanvas = ref(null)
const timelineHeader = ref(null)

// ============== 计算属性 ==============

// 构建可见任务列表（考虑展开折叠）
const visibleTasks = computed(() => {
  const result = []
  const taskTree = buildTaskTree(tasks.value)
  
  const traverse = (nodes, parentExpanded = true) => {
    for (const node of nodes) {
      if (parentExpanded) {
        result.push(node)
      }
      if (node.children?.length > 0) {
        const expanded = expandedIds.value.has(node.id)
        traverse(node.children, parentExpanded && expanded)
      }
    }
  }
  
  traverse(taskTree)
  return result
})

// 选中的任务对象
const selectedTask = computed(() => {
  return tasks.value.find(t => t.id === selectedTaskId.value)
})

// 时间轴周期（月/周）
const timelinePeriods = computed(() => {
  const periods = []
  let current = startDate.value.startOf('month')
  
  while (current.isBefore(endDate.value)) {
    const periodEnd = current.endOf('month')
    const end = periodEnd.isAfter(endDate.value) ? endDate.value : periodEnd
    const start = current.isBefore(startDate.value) ? startDate.value : current
    const days = end.diff(start, 'day') + 1
    
    periods.push({
      key: current.format('YYYY-MM'),
      label: current.format('YYYY年M月'),
      width: days * cellWidth.value
    })
    
    current = current.add(1, 'month').startOf('month')
  }
  
  return periods
})

// 时间轴天数
const timelineDays = computed(() => {
  const days = []
  let current = startDate.value.clone()
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']
  
  while (current.isBefore(endDate.value) || current.isSame(endDate.value, 'day')) {
    const dayOfWeek = current.day()
    days.push({
      key: current.format('YYYY-MM-DD'),
      date: current.clone(),
      dayNum: current.date(),
      weekDay: weekDays[dayOfWeek],
      isWeekend: dayOfWeek === 0 || dayOfWeek === 6,
      isToday: current.isSame(dayjs(), 'day'),
      isHoliday: false // TODO: 接入节假日数据
    })
    current = current.add(1, 'day')
  }
  
  return days
})

// 图表尺寸
const chartWidth = computed(() => timelineDays.value.length * cellWidth.value)
const chartHeight = computed(() => visibleTasks.value.length * rowHeight.value)

// 今日标线位置
const todayPosition = computed(() => {
  const today = dayjs()
  if (today.isBefore(startDate.value) || today.isAfter(endDate.value)) {
    return -1
  }
  return today.diff(startDate.value, 'day') * cellWidth.value + cellWidth.value / 2
})

// 依赖线路径
const dependencyPaths = computed(() => {
  const paths = []
  const taskIndexMap = new Map()
  
  visibleTasks.value.forEach((task, index) => {
    taskIndexMap.set(task.id, index)
  })
  
  for (const dep of dependencies.value) {
    const fromIndex = taskIndexMap.get(dep.from)
    const toIndex = taskIndexMap.get(dep.to)
    
    if (fromIndex === undefined || toIndex === undefined) continue
    
    const fromTask = visibleTasks.value[fromIndex]
    const toTask = visibleTasks.value[toIndex]
    
    // 计算起点和终点坐标
    const fromX = getTaskEndX(fromTask) + 4
    const fromY = fromIndex * rowHeight.value + rowHeight.value / 2
    const toX = getTaskStartX(toTask) - 4
    const toY = toIndex * rowHeight.value + rowHeight.value / 2
    
    // 生成贝塞尔曲线路径
    let path
    if (toX > fromX + 20) {
      // 正常情况：终点在起点右侧
      const midX = (fromX + toX) / 2
      path = `M ${fromX} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`
    } else {
      // 特殊情况：终点在起点左侧或很近，需要绕行
      const offset = 30
      path = `M ${fromX} ${fromY} 
              L ${fromX + offset} ${fromY}
              L ${fromX + offset} ${fromY + (toY > fromY ? offset : -offset)}
              L ${toX - offset} ${toY + (toY > fromY ? -offset : offset)}
              L ${toX - offset} ${toY}
              L ${toX} ${toY}`
    }
    
    paths.push({
      id: dep.id,
      path,
      from: dep.from,
      to: dep.to,
      isCritical: fromTask.is_critical && toTask.is_critical
    })
  }
  
  return paths
})

// ============== 方法 ==============

// 加载数据
async function loadGanttData() {
  try {
    const res = await getGanttData(props.projectId)
    if (res.code === 200) {
      tasks.value = res.data.tasks || []
      dependencies.value = res.data.dependencies || []
      
      // 更新时间范围
      updateTimeRange()
      
      // 默认展开所有一级任务
      tasks.value
        .filter(t => t.level === 1)
        .forEach(t => expandedIds.value.add(t.id))
    }
  } catch (error) {
    console.error('加载甘特图数据失败:', error)
    ElMessage.error('加载甘特图数据失败')
  }
}

// 更新时间范围
function updateTimeRange() {
  if (tasks.value.length === 0) {
    startDate.value = dayjs().subtract(7, 'day')
    endDate.value = dayjs().add(3, 'month')
    return
  }
  
  let minDate = dayjs()
  let maxDate = dayjs()
  
  tasks.value.forEach(task => {
    const start = dayjs(task.start)
    const end = dayjs(task.end)
    if (start.isValid() && start.isBefore(minDate)) minDate = start
    if (end.isValid() && end.isAfter(maxDate)) maxDate = end
  })
  
  startDate.value = minDate.subtract(14, 'day').startOf('week')
  endDate.value = maxDate.add(30, 'day').endOf('week')
}

// 构建任务树
function buildTaskTree(taskList) {
  const taskMap = new Map()
  const roots = []
  
  // 先创建所有节点
  taskList.forEach(task => {
    taskMap.set(task.id, { ...task, children: [] })
  })
  
  // 建立父子关系
  taskList.forEach(task => {
    const node = taskMap.get(task.id)
    if (task.parent_id && taskMap.has(task.parent_id)) {
      taskMap.get(task.parent_id).children.push(node)
    } else {
      roots.push(node)
    }
  })
  
  return roots
}

// 判断是否有子任务
function hasChildren(task) {
  return tasks.value.some(t => t.parent_id === task.id)
}

// 判断是否展开
function isExpanded(taskId) {
  return expandedIds.value.has(taskId)
}

// 切换展开/折叠
function toggleExpand(taskId) {
  if (expandedIds.value.has(taskId)) {
    expandedIds.value.delete(taskId)
  } else {
    expandedIds.value.add(taskId)
  }
}

// 获取缩进
function getIndent(task) {
  return (task.level - 1) * 20 + (hasChildren(task) ? 0 : 20)
}

// 选择任务
function selectTask(task) {
  selectedTaskId.value = task.id
  emit('task-selected', task)
}

// 打开任务详情
function openTaskDetail(task) {
  selectedTaskId.value = task.id
  showDetailDrawer.value = true
}

// 格式化日期
function formatDate(dateStr) {
  return dayjs(dateStr).format('MM-DD')
}

// 获取进度条颜色
function getProgressColor(task) {
  if (task.is_critical) return '#ff4d4f'
  if (task.progress >= 100) return '#52c41a'
  if (task.progress >= 50) return '#1890ff'
  if (task.progress > 0) return '#faad14'
  return '#d9d9d9'
}

// 获取行样式类
function getRowClass(task) {
  return {
    'is-selected': selectedTaskId.value === task.id,
    'is-critical': task.is_critical && showCriticalPath.value,
    'is-milestone': task.type === 'milestone',
    'is-parent': hasChildren(task),
    'is-overdue': isOverdue(task)
  }
}

// 获取任务条样式类
function getBarClass(task) {
  return {
    'is-selected': selectedTaskId.value === task.id,
    'is-critical': task.is_critical && showCriticalPath.value,
    'is-parent': hasChildren(task),
    'is-completed': task.progress >= 100,
    'is-overdue': isOverdue(task)
  }
}

// 判断是否逾期
function isOverdue(task) {
  return dayjs(task.end).isBefore(dayjs(), 'day') && task.progress < 100
}

// 获取任务条样式
function getBarStyle(task) {
  const left = getTaskStartX(task)
  const width = getBarWidth(task)
  
  return {
    left: left + 'px',
    width: Math.max(width, 20) + 'px'
  }
}

// 获取基线条样式
function getBaselineStyle(task) {
  if (!task.baseline_start || !task.baseline_end) return { display: 'none' }
  
  const start = dayjs(task.baseline_start)
  const end = dayjs(task.baseline_end)
  const left = start.diff(startDate.value, 'day') * cellWidth.value
  const width = (end.diff(start, 'day') + 1) * cellWidth.value
  
  return {
    left: left + 'px',
    width: width + 'px'
  }
}

// 获取里程碑样式
function getMilestoneStyle(task) {
  const x = getTaskStartX(task) + getBarWidth(task) / 2
  return {
    left: (x - 12) + 'px'
  }
}

// 计算任务起始X坐标
function getTaskStartX(task) {
  const taskStart = dayjs(task.start)
  if (!taskStart.isValid()) return 0
  return taskStart.diff(startDate.value, 'day') * cellWidth.value
}

// 计算任务结束X坐标
function getTaskEndX(task) {
  const taskEnd = dayjs(task.end)
  if (!taskEnd.isValid()) return 0
  return (taskEnd.diff(startDate.value, 'day') + 1) * cellWidth.value
}

// 计算任务条宽度
function getBarWidth(task) {
  const start = dayjs(task.start)
  const end = dayjs(task.end)
  if (!start.isValid() || !end.isValid()) return 0
  return (end.diff(start, 'day') + 1) * cellWidth.value
}

// 缩放操作
function zoomIn() {
  cellWidth.value = Math.min(cellWidth.value + 10, 100)
}

function zoomOut() {
  cellWidth.value = Math.max(cellWidth.value - 10, 15)
}

function fitToScreen() {
  if (chartCanvas.value) {
    const containerWidth = chartCanvas.value.clientWidth - 20
    const totalDays = timelineDays.value.length
    cellWidth.value = Math.max(Math.floor(containerWidth / totalDays), 15)
  }
}

// 滚动到今日
function scrollToToday() {
  if (chartCanvas.value && todayPosition.value >= 0) {
    const scrollLeft = todayPosition.value - chartCanvas.value.clientWidth / 2
    chartCanvas.value.scrollLeft = Math.max(0, scrollLeft)
  }
}

// 切换视图模式
function changeViewMode(mode) {
  switch (mode) {
    case 'day':
      cellWidth.value = 40
      break
    case 'week':
      cellWidth.value = 24
      break
    case 'month':
      cellWidth.value = 10
      break
  }
}

// 计算关键路径
async function calculateCPM() {
  calculating.value = true
  try {
    const res = await calcCPM(props.projectId)
    if (res.code === 200) {
      ElMessage.success(`关键路径计算完成，共${res.data.critical_path?.length || 0}个关键任务`)
      await loadGanttData()
    }
  } catch (error) {
    console.error('计算关键路径失败:', error)
    ElMessage.error('计算关键路径失败')
  } finally {
    calculating.value = false
  }
}

// 导出图片
function exportImage() {
  ElMessage.info('导出功能开发中...')
}

// 同步滚动
function onListScroll(e) {
  if (chartCanvas.value) {
    chartCanvas.value.scrollTop = e.target.scrollTop
  }
}

function onChartScroll(e) {
  if (taskListBody.value) {
    taskListBody.value.scrollTop = e.target.scrollTop
  }
  if (timelineHeader.value) {
    timelineHeader.value.scrollLeft = e.target.scrollLeft
  }
}

// 列宽调整
let isResizing = false
let startX = 0
let startWidth = 0

function startResize(e) {
  isResizing = true
  startX = e.clientX
  startWidth = listWidth.value
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResize(e) {
  if (!isResizing) return
  const delta = e.clientX - startX
  listWidth.value = Math.max(400, Math.min(900, startWidth + delta))
}

function stopResize() {
  isResizing = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// 任务条拖拽
let dragTask = null
let dragStartX = 0
let dragOriginalStart = null
let dragOriginalEnd = null

function startDragBar(e, task) {
  if (e.target.classList.contains('resize-handle') || 
      e.target.classList.contains('connector')) return
  
  dragTask = task
  dragStartX = e.clientX
  dragOriginalStart = dayjs(task.start)
  dragOriginalEnd = dayjs(task.end)
  
  document.addEventListener('mousemove', onDragBar)
  document.addEventListener('mouseup', stopDragBar)
}

function onDragBar(e) {
  if (!dragTask) return
  
  const deltaX = e.clientX - dragStartX
  const deltaDays = Math.round(deltaX / cellWidth.value)
  
  if (deltaDays === 0) return
  
  const newStart = dragOriginalStart.add(deltaDays, 'day')
  const newEnd = dragOriginalEnd.add(deltaDays, 'day')
  
  // 更新任务数据（临时）
  const task = tasks.value.find(t => t.id === dragTask.id)
  if (task) {
    task.start = newStart.format('YYYY-MM-DD')
    task.end = newEnd.format('YYYY-MM-DD')
  }
}

async function stopDragBar() {
  if (dragTask) {
    const task = tasks.value.find(t => t.id === dragTask.id)
    if (task && (task.start !== dragOriginalStart.format('YYYY-MM-DD') ||
                 task.end !== dragOriginalEnd.format('YYYY-MM-DD'))) {
      try {
        await updateTaskDates(task.id, {
          plan_start_date: task.start,
          plan_end_date: task.end
        })
        emit('task-updated', task)
        ElMessage.success('日期已更新')
      } catch (error) {
        // 回滚
        task.start = dragOriginalStart.format('YYYY-MM-DD')
        task.end = dragOriginalEnd.format('YYYY-MM-DD')
        ElMessage.error('更新失败')
      }
    }
  }
  
  dragTask = null
  document.removeEventListener('mousemove', onDragBar)
  document.removeEventListener('mouseup', stopDragBar)
}

// 任务条缩放
let resizeTask = null
let resizeType = null
let resizeStartX = 0
let resizeOriginalDate = null

function startResizeBar(e, task, type) {
  resizeTask = task
  resizeType = type
  resizeStartX = e.clientX
  resizeOriginalDate = dayjs(type === 'left' ? task.start : task.end)
  
  document.addEventListener('mousemove', onResizeBar)
  document.addEventListener('mouseup', stopResizeBar)
}

function onResizeBar(e) {
  if (!resizeTask) return
  
  const deltaX = e.clientX - resizeStartX
  const deltaDays = Math.round(deltaX / cellWidth.value)
  
  if (deltaDays === 0) return
  
  const task = tasks.value.find(t => t.id === resizeTask.id)
  if (!task) return
  
  if (resizeType === 'left') {
    const newStart = resizeOriginalDate.add(deltaDays, 'day')
    if (newStart.isBefore(dayjs(task.end))) {
      task.start = newStart.format('YYYY-MM-DD')
      task.duration = dayjs(task.end).diff(newStart, 'day') + 1
    }
  } else {
    const newEnd = resizeOriginalDate.add(deltaDays, 'day')
    if (newEnd.isAfter(dayjs(task.start))) {
      task.end = newEnd.format('YYYY-MM-DD')
      task.duration = newEnd.diff(dayjs(task.start), 'day') + 1
    }
  }
}

async function stopResizeBar() {
  if (resizeTask) {
    const task = tasks.value.find(t => t.id === resizeTask.id)
    if (task) {
      try {
        await updateTaskDates(task.id, {
          plan_start_date: task.start,
          plan_end_date: task.end
        })
        emit('task-updated', task)
        ElMessage.success('日期已更新')
      } catch (error) {
        ElMessage.error('更新失败')
        await loadGanttData()
      }
    }
  }
  
  resizeTask = null
  document.removeEventListener('mousemove', onResizeBar)
  document.removeEventListener('mouseup', stopResizeBar)
}

// 创建依赖关系
function startCreateDependency(e, task, point) {
  // TODO: 实现依赖线创建的拖拽逻辑
  console.log('Create dependency from', task.id, point)
}

// 里程碑拖拽
function startDragMilestone(e, task) {
  startDragBar(e, task)
}

// 右键菜单
function onContextMenu(e, task) {
  e.preventDefault()
  contextTask.value = task
  contextMenuX.value = e.clientX
  contextMenuY.value = e.clientY
  showContextMenu.value = true
}

function hideContextMenu() {
  showContextMenu.value = false
}

function addSubTask() {
  hideContextMenu()
  // TODO: 打开添加子任务对话框
}

function editTask() {
  hideContextMenu()
  if (contextTask.value) {
    openTaskDetail(contextTask.value)
  }
}

function setBaseline() {
  hideContextMenu()
  ElMessage.info('设置基线功能开发中...')
}

async function deleteTask() {
  hideContextMenu()
  if (!contextTask.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除任务"${contextTask.value.label}"吗？`,
      '确认删除',
      { type: 'warning' }
    )
    // TODO: 调用删除API
    emit('task-deleted', contextTask.value)
  } catch {
    // 取消
  }
}

// 处理任务更新
function handleTaskUpdate(updatedTask) {
  const index = tasks.value.findIndex(t => t.id === updatedTask.id)
  if (index !== -1) {
    tasks.value[index] = { ...tasks.value[index], ...updatedTask }
  }
  emit('task-updated', updatedTask)
}

// 处理任务删除
function handleTaskDelete(taskId) {
  tasks.value = tasks.value.filter(t => t.id !== taskId)
  emit('task-deleted', { id: taskId })
}

// ============== 生命周期 ==============
onMounted(() => {
  loadGanttData()
  document.addEventListener('click', hideContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', hideContextMenu)
})

watch(() => props.projectId, () => {
  loadGanttData()
})

// 暴露方法
defineExpose({
  refresh: loadGanttData,
  calculateCPM
})
</script>

<style lang="scss" scoped>
.gantt-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
}

// 工具栏
.gantt-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  
  .toolbar-left, .toolbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

// 主体区域
.gantt-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

// 左侧任务列表
.task-list {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  min-width: 400px;
}

.task-list-header {
  flex-shrink: 0;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  
  .header-row {
    display: flex;
    height: 60px;
    
    .col {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 8px;
      font-weight: 600;
      font-size: 13px;
      color: #333;
      border-right: 1px solid #f0f0f0;
      
      &:last-child {
        border-right: none;
      }
    }
  }
}

.task-list-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.task-row {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background: #f5f5f5;
  }
  
  &.is-selected {
    background: #e6f7ff;
  }
  
  &.is-critical {
    background: #fff1f0;
    
    &:hover {
      background: #ffccc7;
    }
  }
  
  &.is-overdue {
    .col-end {
      color: #ff4d4f;
    }
  }
  
  .col {
    display: flex;
    align-items: center;
    padding: 0 8px;
    font-size: 13px;
    overflow: hidden;
    
    &.col-name {
      gap: 4px;
    }
  }
  
  .expand-btn {
    cursor: pointer;
    color: #999;
    font-size: 12px;
    
    &:hover {
      color: #1890ff;
    }
  }
  
  .task-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .milestone-tag, .critical-tag {
    margin-left: 4px;
    flex-shrink: 0;
  }
  
  .owner-name {
    margin-left: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .progress-text {
    margin-left: 8px;
    font-size: 12px;
    color: #999;
    width: 32px;
    text-align: right;
  }
}

// 分隔条
.splitter {
  width: 6px;
  background: #f0f0f0;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    background: #d9d9d9;
  }
  
  .splitter-line {
    width: 2px;
    height: 30px;
    background: #bfbfbf;
    border-radius: 1px;
  }
}

// 右侧图表区
.chart-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 300px;
}

// 时间轴
.timeline-header {
  flex-shrink: 0;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  overflow: hidden;
}

.timeline-row {
  display: flex;
}

.timeline-months {
  height: 30px;
  border-bottom: 1px solid #f0f0f0;
  
  .period-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 600;
    color: #333;
    border-right: 1px solid #e8e8e8;
    box-sizing: border-box;
  }
}

.timeline-days {
  height: 30px;
  
  .day-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    color: #666;
    border-right: 1px solid #f5f5f5;
    box-sizing: border-box;
    
    &.is-weekend {
      background: #fafafa;
      color: #999;
    }
    
    &.is-today {
      background: #e6f7ff;
      color: #1890ff;
      font-weight: 600;
    }
    
    .day-number {
      line-height: 1;
    }
    
    .day-week {
      font-size: 10px;
      color: #999;
    }
  }
}

// 图表画布
.chart-canvas {
  flex: 1;
  position: relative;
  overflow: auto;
}

// 网格层
.grid-layer {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  
  .grid-column {
    height: 100%;
    border-right: 1px solid #f5f5f5;
    box-sizing: border-box;
    
    &.is-weekend {
      background: rgba(0, 0, 0, 0.02);
    }
    
    &.is-today {
      background: rgba(24, 144, 255, 0.05);
    }
  }
}

// 今日标线
.today-marker {
  position: absolute;
  top: 0;
  bottom: 0;
  z-index: 10;
  pointer-events: none;
  
  .today-label {
    position: absolute;
    top: -25px;
    left: 50%;
    transform: translateX(-50%);
    background: #1890ff;
    color: #fff;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 11px;
    white-space: nowrap;
  }
  
  .today-line {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 50%;
    width: 2px;
    background: #1890ff;
    transform: translateX(-50%);
  }
}

// 依赖线层
.dependency-layer {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  z-index: 5;
  
  .dep-line {
    fill: none;
    stroke: #999;
    stroke-width: 1.5;
    
    &.is-critical {
      stroke: #ff4d4f;
      stroke-width: 2;
    }
  }
}

// 任务条层
.bars-layer {
  position: relative;
  z-index: 6;
}

.bar-row {
  position: relative;
}

// 基线条
.baseline-bar {
  position: absolute;
  top: 50%;
  height: 6px;
  transform: translateY(-50%);
  background: transparent;
  border: 2px dashed #999;
  border-radius: 3px;
  opacity: 0.6;
}

// 任务条
.task-bar {
  position: absolute;
  top: 8px;
  height: calc(100% - 16px);
  min-height: 24px;
  background: #1890ff;
  border-radius: 4px;
  cursor: pointer;
  transition: box-shadow 0.2s;
  overflow: hidden;
  
  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    
    .resize-handle, .connector {
      opacity: 1;
    }
  }
  
  &.is-selected {
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.5);
  }
  
  &.is-critical {
    background: #ff4d4f;
  }
  
  &.is-parent {
    background: #722ed1;
  }
  
  &.is-completed {
    background: #52c41a;
  }
  
  &.is-overdue:not(.is-completed) {
    background: #faad14;
  }
  
  .progress-fill {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: rgba(255, 255, 255, 0.3);
    transition: width 0.3s;
  }
  
  .bar-label {
    position: absolute;
    top: 50%;
    left: 8px;
    transform: translateY(-50%);
    color: #fff;
    font-size: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: calc(100% - 16px);
    
    &.outside {
      left: 100%;
      margin-left: 8px;
      color: #333;
    }
  }
  
  .resize-handle {
    position: absolute;
    top: 0;
    width: 8px;
    height: 100%;
    cursor: ew-resize;
    opacity: 0;
    transition: opacity 0.2s;
    
    &.left {
      left: 0;
      background: linear-gradient(to right, rgba(0,0,0,0.2), transparent);
    }
    
    &.right {
      right: 0;
      background: linear-gradient(to left, rgba(0,0,0,0.2), transparent);
    }
  }
  
  .connector {
    position: absolute;
    top: 50%;
    width: 10px;
    height: 10px;
    background: #fff;
    border: 2px solid #1890ff;
    border-radius: 50%;
    transform: translateY(-50%);
    opacity: 0;
    cursor: crosshair;
    transition: opacity 0.2s;
    
    &.left {
      left: -5px;
    }
    
    &.right {
      right: -5px;
    }
  }
}

// 里程碑
.milestone-diamond {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #faad14;
  font-size: 20px;
  cursor: pointer;
  
  &.is-critical {
    color: #ff4d4f;
  }
  
  &:hover {
    transform: translateY(-50%) scale(1.2);
  }
}

// 右键菜单
.context-menu {
  position: fixed;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  padding: 4px 0;
  min-width: 150px;
  z-index: 1000;
  
  .menu-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    font-size: 13px;
    cursor: pointer;
    
    &:hover {
      background: #f5f5f5;
    }
    
    &.danger {
      color: #ff4d4f;
    }
  }
  
  .menu-divider {
    height: 1px;
    background: #f0f0f0;
    margin: 4px 0;
  }
}
</style>
