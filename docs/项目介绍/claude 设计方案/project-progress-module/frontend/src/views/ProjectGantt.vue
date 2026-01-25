<template>
  <div class="project-gantt-page">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h2>{{ project.project_name }} - 甘特图</h2>
        <el-tag>{{ project.project_code }}</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="$refs.gantt?.refresh()"><el-icon><Refresh /></el-icon> 刷新</el-button>
        <el-button type="primary" @click="showAddTask = true"><el-icon><Plus /></el-icon> 添加任务</el-button>
      </div>
    </div>
    
    <div class="gantt-wrapper">
      <GanttChart ref="gantt" :project-id="projectId" @task-selected="onTaskSelected" @task-updated="onTaskUpdated" />
    </div>
    
    <!-- 添加任务对话框 -->
    <el-dialog v-model="showAddTask" title="添加任务" width="500px">
      <el-form :model="taskForm" label-width="90px">
        <el-form-item label="任务名称"><el-input v-model="taskForm.task_name" placeholder="请输入任务名称" /></el-form-item>
        <el-form-item label="所属阶段">
          <el-select v-model="taskForm.phase" style="width: 100%">
            <el-option label="立项启动" value="立项启动" /><el-option label="方案设计" value="方案设计" /><el-option label="结构设计" value="结构设计" /><el-option label="电气设计" value="电气设计" /><el-option label="采购制造" value="采购制造" /><el-option label="装配调试" value="装配调试" /><el-option label="验收交付" value="验收交付" />
          </el-select>
        </el-form-item>
        <el-form-item label="父任务">
          <el-select v-model="taskForm.parent_id" placeholder="无（顶级任务）" clearable style="width: 100%">
            <el-option v-for="t in parentTasks" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="开始日期"><el-date-picker v-model="taskForm.start_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="结束日期"><el-date-picker v-model="taskForm.end_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="计划工时"><el-input-number v-model="taskForm.plan_hours" :min="0" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="负责人"><el-select v-model="taskForm.owner_id" placeholder="选择负责人" style="width: 100%"><el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" /></el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="交付物"><el-input v-model="taskForm.deliverable" placeholder="请输入交付物描述" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddTask = false">取消</el-button>
        <el-button type="primary" @click="handleAddTask" :loading="adding">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import GanttChart from '@/components/GanttChart.vue'
import { getProjectDetail, createTask } from '@/api/task'

const props = defineProps({ projectId: { type: Number, required: true } })
const router = useRouter()
const gantt = ref(null)
const project = ref({})
const showAddTask = ref(false)
const adding = ref(false)

const taskForm = reactive({ task_name: '', phase: '', parent_id: null, start_date: '', end_date: '', plan_hours: null, owner_id: null, deliverable: '' })
const parentTasks = ref([])
const users = ref([{ id: 1, name: '张工' }, { id: 2, name: '李工' }, { id: 3, name: '王工' }])

async function loadProject() {
  const res = await getProjectDetail(props.projectId)
  if (res.code === 200) project.value = res.data
}

function goBack() { router.back() }
function onTaskSelected(task) { console.log('选中任务:', task) }
function onTaskUpdated(task) { ElMessage.success('任务已更新') }

async function handleAddTask() {
  adding.value = true
  try {
    await createTask({ project_id: props.projectId, ...taskForm })
    ElMessage.success('任务添加成功')
    showAddTask.value = false
    gantt.value?.refresh()
  } finally { adding.value = false }
}

onMounted(() => { loadProject() })
</script>

<style lang="scss" scoped>
.project-gantt-page { display: flex; flex-direction: column; height: 100%; background: #f0f2f5; }
.page-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #fff; border-bottom: 1px solid #e8e8e8; .header-left { display: flex; align-items: center; gap: 16px; h2 { margin: 0; font-size: 18px; } } .header-right { display: flex; gap: 12px; } }
.gantt-wrapper { flex: 1; padding: 16px; overflow: hidden; }
</style>
