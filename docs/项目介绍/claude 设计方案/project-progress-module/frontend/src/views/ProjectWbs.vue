<template>
  <div class="project-wbs-page">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h2>{{ project.project_name }} - WBS任务分解</h2>
      </div>
      <div class="header-right">
        <el-button @click="expandAll">全部展开</el-button>
        <el-button @click="collapseAll">全部折叠</el-button>
        <el-button type="primary" @click="showAddTask = true"><el-icon><Plus /></el-icon> 添加任务</el-button>
      </div>
    </div>
    
    <el-card class="wbs-card">
      <el-table :data="wbsTree" row-key="task_id" :tree-props="{ children: 'children' }" default-expand-all v-loading="loading">
        <el-table-column prop="wbs_code" label="WBS编码" width="120" />
        <el-table-column prop="task_name" label="任务名称" min-width="220">
          <template #default="{ row }">
            <span :style="{ paddingLeft: (row.level - 1) * 16 + 'px' }">
              <el-icon v-if="row.type === 'milestone'" style="color: #faad14"><Star /></el-icon>
              {{ row.task_name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="phase" label="阶段" width="100" />
        <el-table-column label="进度" width="140">
          <template #default="{ row }">
            <el-progress :percentage="row.progress_rate" :stroke-width="8" :color="getProgressColor(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="owner_name" label="负责人" width="90" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }"><el-tag :type="getStatusType(row.status)" size="small">{{ row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column label="计划周期" width="180">
          <template #default="{ row }">{{ row.plan_start_date }} ~ {{ row.plan_end_date }}</template>
        </el-table-column>
        <el-table-column label="工时" width="100">
          <template #default="{ row }">{{ row.actual_manhours || 0 }} / {{ row.plan_manhours || 0 }}h</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="editTask(row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="addSubTask(row)">添加子任务</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 添加/编辑任务对话框 -->
    <el-dialog v-model="showAddTask" :title="editingTask ? '编辑任务' : '添加任务'" width="550px">
      <el-form :model="taskForm" label-width="90px">
        <el-form-item label="任务名称"><el-input v-model="taskForm.task_name" /></el-form-item>
        <el-form-item label="所属阶段">
          <el-select v-model="taskForm.phase" style="width: 100%">
            <el-option v-for="p in phases" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务类型">
          <el-radio-group v-model="taskForm.type">
            <el-radio label="task">普通任务</el-radio>
            <el-radio label="milestone">里程碑</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="开始日期"><el-date-picker v-model="taskForm.start_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="结束日期"><el-date-picker v-model="taskForm.end_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="计划工时"><el-input-number v-model="taskForm.plan_hours" :min="0" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="负责人"><el-select v-model="taskForm.owner_id" style="width: 100%"><el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" /></el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="交付物"><el-input v-model="taskForm.deliverable" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddTask = false">取消</el-button>
        <el-button type="primary" @click="saveTask" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Star } from '@element-plus/icons-vue'
import { getProjectDetail, getWbsTasks, createTask, updateTask } from '@/api/task'

const props = defineProps({ projectId: { type: Number, required: true } })
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const project = ref({})
const wbsTree = ref([])
const showAddTask = ref(false)
const editingTask = ref(null)
const parentTask = ref(null)

const phases = ['立项启动', '方案设计', '结构设计', '电气设计', '采购制造', '装配调试', '验收交付']
const users = ref([{ id: 1, name: '张工' }, { id: 2, name: '李工' }, { id: 3, name: '王工' }, { id: 4, name: '赵工' }])

const taskForm = reactive({ task_name: '', phase: '', type: 'task', start_date: '', end_date: '', plan_hours: null, owner_id: null, deliverable: '' })

async function loadData() {
  loading.value = true
  try {
    const [projRes, wbsRes] = await Promise.all([getProjectDetail(props.projectId), getWbsTasks(props.projectId)])
    if (projRes.code === 200) project.value = projRes.data
    if (wbsRes.code === 200) wbsTree.value = buildTree(wbsRes.data || [])
  } finally { loading.value = false }
}

function buildTree(tasks) {
  const map = new Map()
  const roots = []
  tasks.forEach(t => map.set(t.task_id, { ...t, children: [] }))
  tasks.forEach(t => {
    const node = map.get(t.task_id)
    if (t.parent_id && map.has(t.parent_id)) map.get(t.parent_id).children.push(node)
    else roots.push(node)
  })
  return roots
}

function getProgressColor(task) { if (task.status === '阻塞') return '#ff4d4f'; if (task.progress_rate >= 100) return '#52c41a'; return '#1890ff' }
function getStatusType(s) { return { '未开始': 'info', '进行中': 'primary', '已完成': 'success', '阻塞': 'danger' }[s] || 'info' }

function goBack() { router.back() }
function expandAll() { /* TODO */ }
function collapseAll() { /* TODO */ }

function editTask(task) {
  editingTask.value = task
  Object.assign(taskForm, { task_name: task.task_name, phase: task.phase, type: task.type || 'task', start_date: task.plan_start_date, end_date: task.plan_end_date, plan_hours: task.plan_manhours, owner_id: task.owner_id, deliverable: task.deliverable })
  showAddTask.value = true
}

function addSubTask(task) {
  editingTask.value = null
  parentTask.value = task
  Object.assign(taskForm, { task_name: '', phase: task.phase, type: 'task', start_date: '', end_date: '', plan_hours: null, owner_id: null, deliverable: '' })
  showAddTask.value = true
}

async function saveTask() {
  saving.value = true
  try {
    if (editingTask.value) {
      await updateTask(editingTask.value.task_id, taskForm)
      ElMessage.success('更新成功')
    } else {
      await createTask({ project_id: props.projectId, parent_id: parentTask.value?.task_id, ...taskForm })
      ElMessage.success('添加成功')
    }
    showAddTask.value = false
    loadData()
  } finally { saving.value = false }
}

onMounted(() => {
  // 模拟数据
  wbsTree.value = [
    { task_id: 1, wbs_code: '1', task_name: '立项启动', phase: '立项启动', level: 1, progress_rate: 100, status: '已完成', owner_name: '张经理', plan_start_date: '2025-01-01', plan_end_date: '2025-01-05', plan_manhours: 40, actual_manhours: 38, children: [
      { task_id: 11, wbs_code: '1.1', task_name: '项目启动会', phase: '立项启动', level: 2, progress_rate: 100, status: '已完成', owner_name: '张经理', plan_start_date: '2025-01-01', plan_end_date: '2025-01-02', plan_manhours: 8, actual_manhours: 8, children: [] },
      { task_id: 12, wbs_code: '1.2', task_name: '需求确认', phase: '立项启动', level: 2, progress_rate: 100, status: '已完成', owner_name: '李工', plan_start_date: '2025-01-02', plan_end_date: '2025-01-05', plan_manhours: 32, actual_manhours: 30, children: [] }
    ]},
    { task_id: 2, wbs_code: '2', task_name: '方案设计', phase: '方案设计', level: 1, progress_rate: 80, status: '进行中', owner_name: '李工', plan_start_date: '2025-01-06', plan_end_date: '2025-01-15', plan_manhours: 80, actual_manhours: 64, children: [
      { task_id: 21, wbs_code: '2.1', task_name: '总体方案设计', phase: '方案设计', level: 2, progress_rate: 100, status: '已完成', owner_name: '李工', plan_start_date: '2025-01-06', plan_end_date: '2025-01-10', plan_manhours: 40, actual_manhours: 38, children: [] },
      { task_id: 22, wbs_code: '2.2', task_name: '方案评审', phase: '方案设计', level: 2, type: 'milestone', progress_rate: 50, status: '进行中', owner_name: '张经理', plan_start_date: '2025-01-12', plan_end_date: '2025-01-15', plan_manhours: 16, actual_manhours: 8, children: [] }
    ]},
    { task_id: 3, wbs_code: '3', task_name: '结构设计', phase: '结构设计', level: 1, progress_rate: 30, status: '进行中', owner_name: '王工', plan_start_date: '2025-01-16', plan_end_date: '2025-02-10', plan_manhours: 160, actual_manhours: 48, children: [] }
  ]
})
</script>

<style lang="scss" scoped>
.project-wbs-page { padding: 20px; background: #f0f2f5; min-height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; .header-left { display: flex; align-items: center; gap: 16px; h2 { margin: 0; font-size: 18px; } } .header-right { display: flex; gap: 12px; } }
.wbs-card { }
</style>
