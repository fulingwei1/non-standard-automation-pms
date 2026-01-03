<template>
  <div class="alerts-page">
    <div class="page-header">
      <h2>预警中心</h2>
      <el-button @click="triggerCheck" :loading="checking"><el-icon><Refresh /></el-icon> 立即检查</el-button>
    </div>
    
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6"><div class="stat-card critical" @click="filterLevel = '红'"><div class="stat-icon"><el-icon><Warning /></el-icon></div><div class="stat-info"><div class="stat-value">{{ stats.critical }}</div><div class="stat-label">严重预警</div></div></div></el-col>
      <el-col :span="6"><div class="stat-card warning" @click="filterLevel = '橙'"><div class="stat-icon"><el-icon><Bell /></el-icon></div><div class="stat-info"><div class="stat-value">{{ stats.warning }}</div><div class="stat-label">重要预警</div></div></div></el-col>
      <el-col :span="6"><div class="stat-card info" @click="filterLevel = '黄'"><div class="stat-icon"><el-icon><InfoFilled /></el-icon></div><div class="stat-info"><div class="stat-value">{{ stats.info }}</div><div class="stat-label">一般预警</div></div></div></el-col>
      <el-col :span="6"><div class="stat-card resolved" @click="filterStatus = '已处理'"><div class="stat-icon"><el-icon><CircleCheck /></el-icon></div><div class="stat-info"><div class="stat-value">{{ stats.resolved }}</div><div class="stat-label">今日已处理</div></div></div></el-col>
    </el-row>
    
    <el-card>
      <div class="filter-bar">
        <el-select v-model="filterLevel" placeholder="预警级别" clearable style="width: 120px">
          <el-option label="严重(红)" value="红" /><el-option label="重要(橙)" value="橙" /><el-option label="一般(黄)" value="黄" />
        </el-select>
        <el-select v-model="filterType" placeholder="预警类型" clearable style="width: 140px">
          <el-option label="任务逾期" value="任务逾期" /><el-option label="进度滞后" value="进度滞后" /><el-option label="任务即将到期" value="任务即将到期" /><el-option label="负荷过高" value="负荷过高" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="处理状态" clearable style="width: 120px">
          <el-option label="待处理" value="待处理" /><el-option label="处理中" value="处理中" /><el-option label="已处理" value="已处理" /><el-option label="已忽略" value="已忽略" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索预警内容" prefix-icon="Search" clearable style="width: 200px" />
      </div>
      
      <el-table :data="filteredAlerts" v-loading="loading">
        <el-table-column label="级别" width="70" align="center">
          <template #default="{ row }"><el-tag :type="getLevelType(row.alert_level)" size="small" effect="dark">{{ row.alert_level }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="alert_type" label="类型" width="120" />
        <el-table-column prop="alert_title" label="预警内容" min-width="280">
          <template #default="{ row }">
            <div class="alert-content-cell">
              <div class="alert-title">{{ row.alert_title }}</div>
              <div class="alert-meta"><span v-if="row.project_code" class="project-tag">{{ row.project_code }}</span><span v-if="row.task_name">{{ row.task_name }}</span></div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="owner_name" label="责任人" width="90" />
        <el-table-column prop="status" label="状态" width="90"><template #default="{ row }"><el-tag :type="getStatusType(row.status)" size="small">{{ row.status }}</el-tag></template></el-table-column>
        <el-table-column prop="created_time" label="创建时间" width="140" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">详情</el-button>
            <el-button v-if="row.status === '待处理'" link type="success" size="small" @click="handleAlert(row, '处理中')">处理</el-button>
            <el-button v-if="row.status === '处理中'" link type="success" size="small" @click="handleAlert(row, '已处理')">完成</el-button>
            <el-button v-if="row.status === '待处理'" link type="info" size="small" @click="handleAlert(row, '已忽略')">忽略</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination"><el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next" /></div>
    </el-card>
    
    <el-dialog v-model="showDetail" title="预警详情" width="600px">
      <el-descriptions v-if="currentAlert" :column="2" border>
        <el-descriptions-item label="预警级别"><el-tag :type="getLevelType(currentAlert.alert_level)" effect="dark">{{ currentAlert.alert_level }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="预警类型">{{ currentAlert.alert_type }}</el-descriptions-item>
        <el-descriptions-item label="预警标题" :span="2">{{ currentAlert.alert_title }}</el-descriptions-item>
        <el-descriptions-item label="关联项目">{{ currentAlert.project_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="关联任务">{{ currentAlert.task_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="责任人">{{ currentAlert.owner_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态"><el-tag :type="getStatusType(currentAlert.status)">{{ currentAlert.status }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentAlert.created_time }}</el-descriptions-item>
      </el-descriptions>
      <div v-if="currentAlert && currentAlert.status !== '已处理'" class="handle-section">
        <h4>处理操作</h4>
        <el-form label-width="80px">
          <el-form-item label="处理方式"><el-radio-group v-model="handleAction"><el-radio label="处理中">标记处理中</el-radio><el-radio label="已处理">标记已解决</el-radio><el-radio label="已忽略">忽略</el-radio></el-radio-group></el-form-item>
          <el-form-item label="处理备注"><el-input v-model="handleComment" type="textarea" :rows="2" placeholder="请输入处理说明..." /></el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
        <el-button v-if="currentAlert && currentAlert.status !== '已处理'" type="primary" @click="submitHandle" :loading="handling">确认处理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const checking = ref(false)
const handling = ref(false)
const alerts = ref([])
const page = ref(1)
const total = ref(0)
const filterLevel = ref('')
const filterType = ref('')
const filterStatus = ref('待处理')
const keyword = ref('')
const showDetail = ref(false)
const currentAlert = ref(null)
const handleAction = ref('处理中')
const handleComment = ref('')

const stats = computed(() => ({
  critical: alerts.value.filter(a => a.alert_level === '红' && a.status === '待处理').length,
  warning: alerts.value.filter(a => a.alert_level === '橙' && a.status === '待处理').length,
  info: alerts.value.filter(a => a.alert_level === '黄' && a.status === '待处理').length,
  resolved: alerts.value.filter(a => a.status === '已处理').length
}))

const filteredAlerts = computed(() => {
  let result = [...alerts.value]
  if (filterLevel.value) result = result.filter(a => a.alert_level === filterLevel.value)
  if (filterType.value) result = result.filter(a => a.alert_type === filterType.value)
  if (filterStatus.value) result = result.filter(a => a.status === filterStatus.value)
  if (keyword.value) result = result.filter(a => a.alert_title.includes(keyword.value))
  return result
})

function getLevelType(level) { return { '红': 'danger', '橙': 'warning', '黄': 'info' }[level] || 'info' }
function getStatusType(status) { return { '待处理': 'danger', '处理中': 'warning', '已处理': 'success', '已忽略': 'info' }[status] || 'info' }
function viewDetail(alert) { currentAlert.value = alert; handleAction.value = '处理中'; handleComment.value = ''; showDetail.value = true }
function handleAlert(alert, action) { alert.status = action; ElMessage.success(`预警已${action === '已忽略' ? '忽略' : '更新为' + action}`) }
async function submitHandle() { handling.value = true; try { currentAlert.value.status = handleAction.value; ElMessage.success('处理成功'); showDetail.value = false } finally { handling.value = false } }
async function triggerCheck() { checking.value = true; try { await new Promise(r => setTimeout(r, 1000)); ElMessage.success('预警检查完成') } finally { checking.value = false } }

onMounted(() => {
  alerts.value = [
    { alert_id: 1, alert_type: '任务逾期', alert_level: '红', alert_title: '任务"电气设计"已逾期3天', project_code: 'PRJ-001', project_name: '某客户设备', task_name: '电气设计', owner_name: '王工', status: '待处理', created_time: '2025-01-02 10:00' },
    { alert_id: 2, alert_type: '进度滞后', alert_level: '橙', alert_title: '项目PRJ-003进度滞后10%', project_code: 'PRJ-003', project_name: '芯片测试平台', task_name: null, owner_name: '李经理', status: '待处理', created_time: '2025-01-02 09:00' },
    { alert_id: 3, alert_type: '任务即将到期', alert_level: '黄', alert_title: '任务"BOM清单"将于3天后到期', project_code: 'PRJ-001', project_name: '某客户设备', task_name: 'BOM清单', owner_name: '张工', status: '待处理', created_time: '2025-01-02 08:00' },
    { alert_id: 4, alert_type: '负荷过高', alert_level: '黄', alert_title: '王工本周负荷达到130%', project_code: null, project_name: null, task_name: null, owner_name: '王工', status: '已处理', created_time: '2025-01-01 09:00' },
    { alert_id: 5, alert_type: '任务逾期', alert_level: '红', alert_title: '任务"采购跟进"已逾期5天', project_code: 'PRJ-002', project_name: '电池检测设备', task_name: '采购跟进', owner_name: '赵工', status: '处理中', created_time: '2024-12-28 14:00' }
  ]
  total.value = alerts.value.length
})
</script>

<style lang="scss" scoped>
.alerts-page { padding: 20px; background: #f0f2f5; min-height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; h2 { margin: 0; } }
.stats-row { margin-bottom: 16px; }
.stat-card { display: flex; align-items: center; gap: 16px; padding: 20px; background: #fff; border-radius: 8px; cursor: pointer; transition: all 0.3s; &:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); } .stat-icon { width: 48px; height: 48px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 24px; } .stat-info { .stat-value { font-size: 28px; font-weight: 600; } .stat-label { font-size: 13px; color: #999; } } &.critical .stat-icon { background: #ff4d4f; } &.warning .stat-icon { background: #fa8c16; } &.info .stat-icon { background: #faad14; } &.resolved .stat-icon { background: #52c41a; } }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.alert-content-cell { .alert-title { font-size: 14px; margin-bottom: 4px; } .alert-meta { font-size: 12px; color: #999; .project-tag { background: #e6f7ff; color: #1890ff; padding: 2px 6px; border-radius: 2px; margin-right: 8px; } } }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.handle-section { margin-top: 20px; padding-top: 20px; border-top: 1px solid #f0f0f0; h4 { margin: 0 0 16px 0; font-size: 14px; } }
</style>
