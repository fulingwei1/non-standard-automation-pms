<template>
  <div class="project-list-page">
    <div class="page-header">
      <h2>项目列表</h2>
      <el-button type="primary" @click="showCreateDialog = true"><el-icon><Plus /></el-icon> 新建项目</el-button>
    </div>
    
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 100px">
            <el-option label="进行中" value="进行中" /><el-option label="已完成" value="已完成" /><el-option label="已暂停" value="已暂停" />
          </el-select>
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="filterForm.level" placeholder="全部" clearable style="width: 80px">
            <el-option label="A" value="A" /><el-option label="B" value="B" /><el-option label="C" value="C" />
          </el-select>
        </el-form-item>
        <el-form-item label="健康">
          <el-select v-model="filterForm.health" placeholder="全部" clearable style="width: 80px">
            <el-option label="正常" value="绿" /><el-option label="关注" value="黄" /><el-option label="预警" value="红" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filterForm.keyword" placeholder="项目编号/名称" clearable style="width: 160px" @keyup.enter="loadProjects" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadProjects">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6"><div class="stat-card"><div class="stat-icon" style="background:#1890ff"><el-icon><Folder /></el-icon></div><div class="stat-info"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">全部项目</div></div></div></el-col>
      <el-col :span="6"><div class="stat-card"><div class="stat-icon" style="background:#52c41a"><el-icon><VideoPlay /></el-icon></div><div class="stat-info"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">进行中</div></div></div></el-col>
      <el-col :span="6"><div class="stat-card"><div class="stat-icon" style="background:#faad14"><el-icon><Warning /></el-icon></div><div class="stat-info"><div class="stat-value">{{ stats.warning }}</div><div class="stat-label">需关注</div></div></div></el-col>
      <el-col :span="6"><div class="stat-card"><div class="stat-icon" style="background:#ff4d4f"><el-icon><CircleClose /></el-icon></div><div class="stat-info"><div class="stat-value">{{ stats.critical }}</div><div class="stat-label">预警</div></div></div></el-col>
    </el-row>
    
    <div class="view-switch">
      <el-radio-group v-model="viewMode" size="small">
        <el-radio-button label="table">表格</el-radio-button>
        <el-radio-button label="card">卡片</el-radio-button>
      </el-radio-group>
    </div>
    
    <el-card v-if="viewMode === 'table'" class="table-card">
      <el-table :data="projectList" v-loading="loading" @row-click="goToProject" style="cursor: pointer">
        <el-table-column prop="project_code" label="项目编号" width="130"><template #default="{ row }"><span class="project-code">{{ row.project_code }}</span></template></el-table-column>
        <el-table-column prop="project_name" label="项目名称" min-width="200" />
        <el-table-column prop="customer_name" label="客户" width="120" />
        <el-table-column prop="project_level" label="级别" width="70" align="center"><template #default="{ row }"><el-tag :type="getLevelType(row.project_level)" size="small">{{ row.project_level }}</el-tag></template></el-table-column>
        <el-table-column prop="pm_name" label="项目经理" width="90" />
        <el-table-column label="进度" width="150"><template #default="{ row }"><div class="progress-cell"><el-progress :percentage="row.progress_rate" :stroke-width="8" :color="getProgressColor(row)" /><span class="progress-text">{{ row.progress_rate }}%</span></div></template></el-table-column>
        <el-table-column prop="status" label="状态" width="80"><template #default="{ row }"><el-tag :type="getStatusType(row.status)" size="small">{{ row.status }}</el-tag></template></el-table-column>
        <el-table-column label="健康" width="60" align="center"><template #default="{ row }"><span class="health-dot" :style="{ background: getHealthColor(row.health_status) }"></span></template></el-table-column>
        <el-table-column prop="current_phase" label="阶段" width="90" />
        <el-table-column label="计划完成" width="100"><template #default="{ row }">{{ formatDate(row.plan_end_date) }}</template></el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="goToProject(row)">查看</el-button>
            <el-button link type="primary" size="small" @click.stop="goToGantt(row)">甘特图</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination"><el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="loadProjects" /></div>
    </el-card>
    
    <div v-else class="card-view">
      <el-row :gutter="16">
        <el-col :span="6" v-for="p in projectList" :key="p.project_id">
          <el-card class="project-card" @click="goToProject(p)">
            <div class="card-header"><span class="code">{{ p.project_code }}</span><el-tag :type="getLevelType(p.project_level)" size="small">{{ p.project_level }}</el-tag><span class="health-dot" :style="{ background: getHealthColor(p.health_status) }"></span></div>
            <div class="card-name">{{ p.project_name }}</div>
            <div class="card-customer">{{ p.customer_name }}</div>
            <div class="card-progress"><div class="progress-label"><span>进度</span><span>{{ p.progress_rate }}%</span></div><el-progress :percentage="p.progress_rate" :stroke-width="8" :show-text="false" /></div>
            <div class="card-info"><span><el-icon><User /></el-icon> {{ p.pm_name }}</span><span><el-icon><Calendar /></el-icon> {{ formatDate(p.plan_end_date) }}</span></div>
            <div class="card-footer"><el-tag :type="getStatusType(p.status)" size="small">{{ p.status }}</el-tag><span class="phase">{{ p.current_phase }}</span></div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <el-dialog v-model="showCreateDialog" title="新建项目" width="560px">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="项目编号"><el-input v-model="createForm.project_code" placeholder="PRJ-2025-XXX"><template #append><el-button @click="generateCode">生成</el-button></template></el-input></el-form-item>
        <el-form-item label="项目名称"><el-input v-model="createForm.project_name" placeholder="请输入项目名称" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="客户"><el-select v-model="createForm.customer_id" placeholder="选择客户" style="width:100%"><el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="项目级别"><el-select v-model="createForm.project_level" style="width:100%"><el-option label="A级" value="A" /><el-option label="B级" value="B" /><el-option label="C级" value="C" /></el-select></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="项目经理"><el-select v-model="createForm.pm_id" placeholder="选择PM" style="width:100%"><el-option v-for="pm in pmList" :key="pm.id" :label="pm.name" :value="pm.id" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="技术负责人"><el-select v-model="createForm.te_id" placeholder="选择TE" style="width:100%"><el-option v-for="te in teList" :key="te.id" :label="te.name" :value="te.id" /></el-select></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="计划开始"><el-date-picker v-model="createForm.plan_start_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计划结束"><el-date-picker v-model="createForm.plan_end_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="项目描述"><el-input v-model="createForm.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showCreateDialog = false">取消</el-button><el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getProjectList, createProject } from '@/api/task'

const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const projectList = ref([])
const viewMode = ref('table')
const showCreateDialog = ref(false)
const page = ref(1)
const total = ref(0)

const filterForm = reactive({ status: '', level: '', health: '', keyword: '' })
const stats = reactive({ total: 0, active: 0, warning: 0, critical: 0 })
const createForm = reactive({ project_code: '', project_name: '', customer_id: null, project_level: 'C', pm_id: null, te_id: null, plan_start_date: '', plan_end_date: '', description: '' })

const pmList = ref([{ id: 1, name: '张经理' }, { id: 2, name: '李经理' }, { id: 3, name: '王经理' }])
const teList = ref([{ id: 1, name: '赵工' }, { id: 2, name: '钱工' }, { id: 3, name: '孙工' }])
const customers = ref([{ id: 1, name: '深圳XX科技' }, { id: 2, name: '东莞YY电池' }, { id: 3, name: '广州ZZ半导体' }])

async function loadProjects() {
  loading.value = true
  try {
    const res = await getProjectList({ page: page.value, page_size: 20, status: filterForm.status || undefined, level: filterForm.level || undefined, keyword: filterForm.keyword || undefined })
    if (res.code === 200) {
      projectList.value = res.data.list || []
      total.value = res.data.total || 0
      stats.total = total.value
      stats.active = projectList.value.filter(p => p.status === '进行中').length
      stats.warning = projectList.value.filter(p => p.health_status === '黄').length
      stats.critical = projectList.value.filter(p => p.health_status === '红').length
    }
  } finally { loading.value = false }
}

function getLevelType(l) { return { A: 'danger', B: 'warning', C: 'success' }[l] || 'info' }
function getStatusType(s) { return { '进行中': 'primary', '已完成': 'success', '已暂停': 'warning' }[s] || 'info' }
function getHealthColor(s) { return { '绿': '#52c41a', '黄': '#faad14', '红': '#ff4d4f' }[s] || '#d9d9d9' }
function getProgressColor(p) { if (p.health_status === '红') return '#ff4d4f'; return '#1890ff' }
function formatDate(d) { return d ? dayjs(d).format('MM-DD') : '-' }
function resetFilter() { Object.assign(filterForm, { status: '', level: '', health: '', keyword: '' }); loadProjects() }
function goToProject(p) { router.push(`/project/${p.project_id}`) }
function goToGantt(p) { router.push(`/project/${p.project_id}/gantt`) }
function generateCode() { createForm.project_code = `PRJ-${dayjs().format('YYYY')}-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}` }
async function handleCreate() {
  creating.value = true
  try {
    const res = await createProject(createForm)
    if (res.code === 200) { ElMessage.success('创建成功'); showCreateDialog.value = false; loadProjects() }
  } finally { creating.value = false }
}

onMounted(() => { loadProjects() })
</script>

<style lang="scss" scoped>
.project-list-page { padding: 20px; background: #f0f2f5; min-height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; h2 { margin: 0; } }
.filter-card { margin-bottom: 16px; }
.stats-row { margin-bottom: 16px; }
.stat-card { display: flex; align-items: center; gap: 16px; padding: 20px; background: #fff; border-radius: 8px; .stat-icon { width: 48px; height: 48px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 24px; } .stat-info { .stat-value { font-size: 28px; font-weight: 600; } .stat-label { font-size: 13px; color: #999; } } }
.view-switch { margin-bottom: 16px; }
.table-card { .project-code { color: #1890ff; font-weight: 500; } .progress-cell { display: flex; align-items: center; gap: 8px; .progress-text { width: 40px; text-align: right; font-size: 12px; } } .health-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; } }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.card-view { .project-card { margin-bottom: 16px; cursor: pointer; transition: all 0.3s; &:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); } .card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; .code { font-size: 12px; color: #1890ff; } .health-dot { margin-left: auto; width: 10px; height: 10px; border-radius: 50%; } } .card-name { font-size: 15px; font-weight: 500; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; } .card-customer { font-size: 13px; color: #999; margin-bottom: 12px; } .card-progress { margin-bottom: 12px; .progress-label { display: flex; justify-content: space-between; font-size: 12px; color: #666; margin-bottom: 4px; } } .card-info { display: flex; justify-content: space-between; font-size: 12px; color: #999; margin-bottom: 12px; } .card-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid #f0f0f0; .phase { font-size: 12px; color: #666; } } } }
</style>
