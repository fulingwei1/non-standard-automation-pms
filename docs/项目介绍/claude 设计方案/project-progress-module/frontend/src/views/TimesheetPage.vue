<template>
  <div class="timesheet-page">
    <!-- 头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>工时填报</h2>
        <div class="date-nav">
          <el-button :icon="ArrowLeft" circle size="small" @click="prevWeek" />
          <span class="current-week">{{ weekRange }}</span>
          <el-button :icon="ArrowRight" circle size="small" @click="nextWeek" />
          <el-button size="small" @click="goToday">今天</el-button>
        </div>
      </div>
      <div class="header-right">
        <div class="week-summary">
          <span class="label">本周已填报:</span>
          <span class="value">{{ weekTotal }}小时</span>
          <span class="label" style="margin-left: 16px">本周标准:</span>
          <span class="value">40小时</span>
        </div>
        <el-button type="primary" @click="submitWeek" :loading="submitting">
          提交本周工时
        </el-button>
      </div>
    </div>
    
    <!-- 工时表格 -->
    <div class="timesheet-grid">
      <table class="timesheet-table">
        <thead>
          <tr>
            <th class="col-project">项目/任务</th>
            <th 
              v-for="day in weekDays" 
              :key="day.date"
              class="col-day"
              :class="{ 'is-today': day.isToday, 'is-weekend': day.isWeekend }"
            >
              <div class="day-header">
                <span class="day-name">{{ day.dayName }}</span>
                <span class="day-date">{{ day.dateStr }}</span>
              </div>
            </th>
            <th class="col-total">合计</th>
          </tr>
        </thead>
        <tbody>
          <!-- 任务行 -->
          <tr v-for="task in myTasks" :key="task.assign_id" class="task-row">
            <td class="col-project">
              <div class="project-info">
                <span class="project-code">{{ task.project_code }}</span>
                <span class="task-name">{{ task.task_name }}</span>
              </div>
              <div class="task-meta">
                <el-progress 
                  :percentage="task.progress_rate" 
                  :stroke-width="4"
                  :show-text="false"
                  style="width: 100px"
                />
                <span class="progress-text">{{ task.progress_rate }}%</span>
              </div>
            </td>
            <td 
              v-for="day in weekDays" 
              :key="task.assign_id + '-' + day.date"
              class="col-day"
              :class="{ 'is-today': day.isToday, 'is-weekend': day.isWeekend }"
            >
              <el-input-number
                v-model="timesheetData[task.assign_id][day.date]"
                :min="0"
                :max="24"
                :step="0.5"
                :precision="1"
                size="small"
                controls-position="right"
                :disabled="day.isWeekend && !allowWeekend"
                @change="onHoursChange(task, day.date)"
              />
            </td>
            <td class="col-total">
              <span class="row-total">{{ getRowTotal(task.assign_id) }}</span>
            </td>
          </tr>
          
          <!-- 添加任务行 -->
          <tr class="add-row">
            <td colspan="9">
              <el-button type="primary" link @click="showAddTask = true">
                <el-icon><Plus /></el-icon> 添加工时条目
              </el-button>
            </td>
          </tr>
          
          <!-- 日合计行 -->
          <tr class="total-row">
            <td class="col-project"><strong>日合计</strong></td>
            <td 
              v-for="day in weekDays" 
              :key="'total-' + day.date"
              class="col-day"
              :class="{ 
                'is-today': day.isToday, 
                'is-weekend': day.isWeekend,
                'is-full': getDayTotal(day.date) >= 8,
                'is-over': getDayTotal(day.date) > 8
              }"
            >
              <span class="day-total">{{ getDayTotal(day.date) }}</span>
            </td>
            <td class="col-total">
              <span class="week-total">{{ weekTotal }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 工作内容填写 -->
    <el-card class="work-content-card" v-if="selectedEntry">
      <template #header>
        <span>工作内容描述 - {{ selectedEntry.task_name }} ({{ selectedEntry.date }})</span>
      </template>
      <el-input
        v-model="selectedEntry.work_content"
        type="textarea"
        :rows="3"
        placeholder="请输入当日工作内容..."
        @blur="saveWorkContent"
      />
    </el-card>
    
    <!-- 本周工时统计 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="8">
        <el-card>
          <template #header><span>项目工时分布</span></template>
          <div ref="projectPieChart" style="height: 200px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>本周工时趋势</span></template>
          <div ref="weekBarChart" style="height: 200px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>月度工时汇总</span></template>
          <div class="month-stats">
            <div class="stat-item">
              <span class="stat-label">本月已填报</span>
              <span class="stat-value">{{ monthTotal }}小时</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">本月标准工时</span>
              <span class="stat-value">{{ monthStandard }}小时</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">加班工时</span>
              <span class="stat-value">{{ overtimeTotal }}小时</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 添加任务对话框 -->
    <el-dialog v-model="showAddTask" title="添加工时条目" width="500px">
      <el-form label-width="80px">
        <el-form-item label="选择项目">
          <el-select v-model="newEntry.project_id" placeholder="请选择项目" style="width: 100%" @change="onProjectChange">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择任务">
          <el-select v-model="newEntry.task_id" placeholder="请选择任务" style="width: 100%">
            <el-option v-for="t in taskOptions" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddTask = false">取消</el-button>
        <el-button type="primary" @click="addTaskEntry">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import isoWeek from 'dayjs/plugin/isoWeek'
import { getMyTasks, submitTimesheet } from '@/api/task'

dayjs.extend(isoWeek)

// 状态
const currentWeekStart = ref(dayjs().startOf('isoWeek'))
const myTasks = ref([])
const timesheetData = reactive({})
const submitting = ref(false)
const showAddTask = ref(false)
const selectedEntry = ref(null)
const allowWeekend = ref(false)

const newEntry = reactive({ project_id: null, task_id: null })
const projectOptions = ref([])
const taskOptions = ref([])

// 图表
const projectPieChart = ref(null)
const weekBarChart = ref(null)

// 计算属性
const weekDays = computed(() => {
  const days = []
  const weekNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  
  for (let i = 0; i < 7; i++) {
    const date = currentWeekStart.value.add(i, 'day')
    days.push({
      date: date.format('YYYY-MM-DD'),
      dateStr: date.format('MM/DD'),
      dayName: weekNames[i],
      isToday: date.isSame(dayjs(), 'day'),
      isWeekend: i >= 5
    })
  }
  return days
})

const weekRange = computed(() => {
  const start = currentWeekStart.value.format('MM月DD日')
  const end = currentWeekStart.value.add(6, 'day').format('MM月DD日')
  return `${start} - ${end}`
})

const weekTotal = computed(() => {
  let total = 0
  for (const taskId in timesheetData) {
    for (const date in timesheetData[taskId]) {
      total += timesheetData[taskId][date] || 0
    }
  }
  return total
})

const monthTotal = ref(120)
const monthStandard = ref(176)
const overtimeTotal = ref(8)

// 方法
function loadMyTasks() {
  // 模拟数据
  myTasks.value = [
    { assign_id: 1, project_id: 1, project_code: 'PRJ-001', task_id: 101, task_name: '方案设计', progress_rate: 60, plan_manhours: 40 },
    { assign_id: 2, project_id: 1, project_code: 'PRJ-001', task_id: 102, task_name: '结构设计', progress_rate: 30, plan_manhours: 80 },
    { assign_id: 3, project_id: 2, project_code: 'PRJ-002', task_id: 201, task_name: '电气设计', progress_rate: 20, plan_manhours: 60 }
  ]
  
  // 初始化工时数据
  myTasks.value.forEach(task => {
    if (!timesheetData[task.assign_id]) {
      timesheetData[task.assign_id] = {}
    }
    weekDays.value.forEach(day => {
      if (timesheetData[task.assign_id][day.date] === undefined) {
        timesheetData[task.assign_id][day.date] = 0
      }
    })
  })
  
  // 模拟已填报数据
  timesheetData[1]['2025-01-02'] = 4
  timesheetData[2]['2025-01-02'] = 4
  timesheetData[1]['2025-01-03'] = 6
  timesheetData[3]['2025-01-03'] = 2
}

function getRowTotal(taskId) {
  let total = 0
  weekDays.value.forEach(day => {
    total += timesheetData[taskId]?.[day.date] || 0
  })
  return total
}

function getDayTotal(date) {
  let total = 0
  for (const taskId in timesheetData) {
    total += timesheetData[taskId][date] || 0
  }
  return total
}

function onHoursChange(task, date) {
  // 选中当前条目用于填写工作内容
  selectedEntry.value = {
    assign_id: task.assign_id,
    task_name: task.task_name,
    date: date,
    work_content: ''
  }
  
  // 自动保存
  autoSave(task.assign_id, date)
}

function autoSave(assignId, date) {
  // TODO: 调用API自动保存
  console.log('自动保存:', assignId, date, timesheetData[assignId][date])
}

function saveWorkContent() {
  if (!selectedEntry.value) return
  // TODO: 保存工作内容
  console.log('保存工作内容:', selectedEntry.value)
}

function prevWeek() {
  currentWeekStart.value = currentWeekStart.value.subtract(1, 'week')
  loadMyTasks()
}

function nextWeek() {
  currentWeekStart.value = currentWeekStart.value.add(1, 'week')
  loadMyTasks()
}

function goToday() {
  currentWeekStart.value = dayjs().startOf('isoWeek')
  loadMyTasks()
}

async function submitWeek() {
  try {
    await ElMessageBox.confirm(
      `确定要提交本周(${weekRange.value})的工时吗？提交后将进入审核流程。`,
      '确认提交',
      { type: 'warning' }
    )
    
    submitting.value = true
    
    // 构建提交数据
    const entries = []
    for (const taskId in timesheetData) {
      const task = myTasks.value.find(t => t.assign_id === parseInt(taskId))
      if (!task) continue
      
      weekDays.value.forEach(day => {
        const hours = timesheetData[taskId][day.date]
        if (hours > 0) {
          entries.push({
            project_id: task.project_id,
            task_id: task.task_id,
            assign_id: task.assign_id,
            work_date: day.date,
            hours: hours,
            work_content: ''
          })
        }
      })
    }
    
    // TODO: 调用API提交
    console.log('提交工时:', entries)
    
    ElMessage.success('工时提交成功，等待审核')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('提交失败')
    }
  } finally {
    submitting.value = false
  }
}

function onProjectChange(projectId) {
  // TODO: 根据项目加载任务列表
  taskOptions.value = [
    { id: 301, name: '新任务1' },
    { id: 302, name: '新任务2' }
  ]
}

function addTaskEntry() {
  if (!newEntry.project_id || !newEntry.task_id) {
    ElMessage.warning('请选择项目和任务')
    return
  }
  
  // TODO: 添加新条目
  ElMessage.success('添加成功')
  showAddTask.value = false
}

function renderCharts() {
  // 项目饼图
  if (projectPieChart.value) {
    const chart1 = echarts.init(projectPieChart.value)
    chart1.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: '70%',
        data: [
          { name: 'PRJ-001', value: 26 },
          { name: 'PRJ-002', value: 14 }
        ]
      }]
    })
  }
  
  // 周趋势柱状图
  if (weekBarChart.value) {
    const chart2 = echarts.init(weekBarChart.value)
    chart2.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] },
      yAxis: { type: 'value', max: 12 },
      series: [{
        type: 'bar',
        data: [8, 8, 8, 0, 0, 0, 0],
        itemStyle: { color: '#1890ff' }
      }]
    })
  }
}

onMounted(() => {
  loadMyTasks()
  projectOptions.value = [
    { id: 1, name: 'PRJ-001 某客户设备项目' },
    { id: 2, name: 'PRJ-002 另一个项目' }
  ]
  nextTick(() => renderCharts())
})

watch(currentWeekStart, () => {
  loadMyTasks()
})
</script>

<style lang="scss" scoped>
.timesheet-page { padding: 20px; background: #f5f5f5; min-height: 100vh; }

.page-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; background: #fff; border-radius: 8px; margin-bottom: 16px;
  
  .header-left { display: flex; align-items: center; gap: 24px; h2 { margin: 0; font-size: 18px; } }
  .date-nav { display: flex; align-items: center; gap: 12px; .current-week { font-size: 15px; font-weight: 500; min-width: 180px; text-align: center; } }
  .header-right { display: flex; align-items: center; gap: 24px; }
  .week-summary { .label { color: #999; margin-right: 4px; } .value { font-weight: 600; color: #1890ff; } }
}

.timesheet-grid { background: #fff; border-radius: 8px; overflow: hidden; margin-bottom: 16px; }

.timesheet-table {
  width: 100%; border-collapse: collapse;
  
  th, td { padding: 12px; text-align: center; border: 1px solid #f0f0f0; }
  th { background: #fafafa; font-weight: 600; font-size: 13px; }
  
  .col-project { width: 280px; text-align: left; }
  .col-day { width: 100px; &.is-today { background: #e6f7ff; } &.is-weekend { background: #fafafa; } }
  .col-total { width: 80px; background: #fafafa; font-weight: 600; }
  
  .day-header { .day-name { display: block; font-size: 13px; } .day-date { display: block; font-size: 12px; color: #999; } }
  
  .project-info { margin-bottom: 4px; .project-code { font-size: 12px; color: #1890ff; margin-right: 8px; } .task-name { font-size: 13px; } }
  .task-meta { display: flex; align-items: center; gap: 8px; .progress-text { font-size: 12px; color: #999; } }
  
  .add-row td { background: #fafafa; }
  
  .total-row {
    td { background: #f5f5f5; font-weight: 600; }
    .is-full { color: #52c41a; }
    .is-over { color: #ff4d4f; }
  }
  
  .row-total, .day-total, .week-total { font-size: 14px; }
}

.work-content-card { margin-bottom: 16px; }
.stats-row { margin-bottom: 16px; }

.month-stats {
  .stat-item { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #f0f0f0; &:last-child { border-bottom: none; } }
  .stat-label { color: #666; }
  .stat-value { font-weight: 600; font-size: 16px; color: #1890ff; }
}
</style>
