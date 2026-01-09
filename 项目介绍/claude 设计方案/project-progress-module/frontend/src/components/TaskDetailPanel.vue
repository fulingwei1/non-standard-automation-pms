<template>
  <div class="task-detail-panel">
    <!-- 基本信息 -->
    <el-form :model="formData" label-width="80px" size="default">
      <el-form-item label="任务名称">
        <el-input v-model="formData.task_name" />
      </el-form-item>
      
      <el-form-item label="WBS编码">
        <el-input v-model="formData.wbs_code" disabled />
      </el-form-item>
      
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="开始日期">
            <el-date-picker 
              v-model="formData.plan_start_date" 
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="结束日期">
            <el-date-picker 
              v-model="formData.plan_end_date" 
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="计划工期">
            <el-input-number v-model="formData.plan_duration" :min="1" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="计划工时">
            <el-input-number v-model="formData.plan_manhours" :min="0" :precision="1" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-form-item label="负责人">
        <el-select v-model="formData.owner_id" placeholder="选择负责人" style="width: 100%">
          <el-option 
            v-for="user in userOptions" 
            :key="user.id" 
            :label="user.name" 
            :value="user.id"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="任务状态">
        <el-select v-model="formData.status" style="width: 100%">
          <el-option label="未开始" value="未开始" />
          <el-option label="进行中" value="进行中" />
          <el-option label="已完成" value="已完成" />
          <el-option label="阻塞" value="阻塞" />
          <el-option label="暂停" value="暂停" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="完成进度">
        <div class="progress-input">
          <el-slider v-model="formData.progress_rate" :max="100" :show-tooltip="false" />
          <el-input-number 
            v-model="formData.progress_rate" 
            :min="0" 
            :max="100" 
            :precision="0"
            size="small"
            style="width: 80px; margin-left: 12px"
          />
          <span style="margin-left: 4px">%</span>
        </div>
      </el-form-item>
      
      <el-form-item label="优先级">
        <el-rate 
          v-model="formData.priority" 
          :max="5"
          :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
        />
      </el-form-item>
      
      <el-form-item label="交付物">
        <el-input v-model="formData.deliverable" type="textarea" :rows="2" />
      </el-form-item>
      
      <!-- 阻塞信息 -->
      <template v-if="formData.status === '阻塞'">
        <el-divider content-position="left">阻塞信息</el-divider>
        
        <el-form-item label="阻塞类型">
          <el-select v-model="formData.block_type" style="width: 100%">
            <el-option label="技术问题" value="技术问题" />
            <el-option label="资源不足" value="资源不足" />
            <el-option label="外部依赖" value="外部依赖" />
            <el-option label="需求变更" value="需求变更" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="阻塞原因">
          <el-input v-model="formData.block_reason" type="textarea" :rows="2" />
        </el-form-item>
      </template>
    </el-form>
    
    <!-- 统计信息 -->
    <el-divider content-position="left">统计信息</el-divider>
    
    <el-descriptions :column="2" size="small" border>
      <el-descriptions-item label="实际工时">
        {{ task.actual_manhours || 0 }} 小时
      </el-descriptions-item>
      <el-descriptions-item label="剩余工时">
        {{ Math.max(0, (formData.plan_manhours || 0) - (task.actual_manhours || 0)).toFixed(1) }} 小时
      </el-descriptions-item>
      <el-descriptions-item label="是否关键">
        <el-tag :type="task.is_critical ? 'danger' : 'info'" size="small">
          {{ task.is_critical ? '是' : '否' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="浮动时间">
        {{ task.float_days || 0 }} 天
      </el-descriptions-item>
    </el-descriptions>
    
    <!-- 依赖关系 -->
    <el-divider content-position="left">依赖关系</el-divider>
    
    <div class="dependencies-section">
      <div class="dep-header">
        <span>前置任务</span>
        <el-button type="primary" link size="small" @click="showAddDependency = true">
          <el-icon><Plus /></el-icon> 添加
        </el-button>
      </div>
      <div class="dep-list" v-if="predecessors.length > 0">
        <div v-for="dep in predecessors" :key="dep.id" class="dep-item">
          <span class="dep-name">{{ dep.task_name }}</span>
          <el-tag size="small">{{ dep.depend_type }}</el-tag>
          <el-button type="danger" link size="small" @click="removeDependency(dep.depend_id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
      <el-empty v-else description="暂无前置任务" :image-size="60" />
    </div>
    
    <!-- 操作日志 -->
    <el-divider content-position="left">操作日志</el-divider>
    
    <el-timeline>
      <el-timeline-item
        v-for="log in taskLogs"
        :key="log.id"
        :timestamp="log.created_time"
        placement="top"
      >
        <div class="log-content">
          <span class="log-user">{{ log.operator_name }}</span>
          <span class="log-action">{{ log.action }}</span>
          <span v-if="log.old_value">
            {{ log.field_name }}: {{ log.old_value }} → {{ log.new_value }}
          </span>
        </div>
      </el-timeline-item>
    </el-timeline>
    
    <!-- 底部按钮 -->
    <div class="panel-footer">
      <el-button @click="$emit('close')">取消</el-button>
      <el-button type="primary" @click="saveTask" :loading="saving">保存</el-button>
    </div>
    
    <!-- 添加依赖对话框 -->
    <el-dialog v-model="showAddDependency" title="添加前置任务" width="400px">
      <el-form label-width="80px">
        <el-form-item label="前置任务">
          <el-select v-model="newDependency.predecessor_id" style="width: 100%">
            <el-option
              v-for="t in availableTasks"
              :key="t.id"
              :label="`${t.wbs_code} ${t.label}`"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="依赖类型">
          <el-select v-model="newDependency.depend_type" style="width: 100%">
            <el-option label="完成-开始 (FS)" value="FS" />
            <el-option label="开始-开始 (SS)" value="SS" />
            <el-option label="完成-完成 (FF)" value="FF" />
            <el-option label="开始-完成 (SF)" value="SF" />
          </el-select>
        </el-form-item>
        <el-form-item label="延迟天数">
          <el-input-number v-model="newDependency.lag_days" :min="0" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDependency = false">取消</el-button>
        <el-button type="primary" @click="addDependency">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { updateTask, updateTaskProgress, createDependency, deleteDependency as delDep } from '@/api/task'

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  projectId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update', 'delete', 'close'])

// 表单数据
const formData = reactive({
  task_name: '',
  wbs_code: '',
  plan_start_date: '',
  plan_end_date: '',
  plan_duration: 1,
  plan_manhours: 0,
  owner_id: null,
  status: '未开始',
  progress_rate: 0,
  priority: 3,
  deliverable: '',
  block_type: '',
  block_reason: ''
})

const saving = ref(false)
const showAddDependency = ref(false)
const newDependency = reactive({
  predecessor_id: null,
  depend_type: 'FS',
  lag_days: 0
})

// 模拟数据
const userOptions = ref([
  { id: 1, name: '张工' },
  { id: 2, name: '李工' },
  { id: 3, name: '王工' },
  { id: 4, name: '赵工' },
])

const predecessors = ref([])
const taskLogs = ref([])
const availableTasks = ref([])

// 初始化表单数据
function initFormData() {
  Object.assign(formData, {
    task_name: props.task.label || '',
    wbs_code: props.task.wbs_code || '',
    plan_start_date: props.task.start || '',
    plan_end_date: props.task.end || '',
    plan_duration: props.task.duration || 1,
    plan_manhours: props.task.plan_manhours || 0,
    owner_id: props.task.owner_id || null,
    status: props.task.status || '未开始',
    progress_rate: props.task.progress || 0,
    priority: props.task.priority || 3,
    deliverable: props.task.deliverable || '',
    block_type: props.task.block_type || '',
    block_reason: props.task.block_reason || ''
  })
}

// 保存任务
async function saveTask() {
  saving.value = true
  try {
    // 更新基本信息
    await updateTask(props.task.id, {
      task_name: formData.task_name,
      plan_start_date: formData.plan_start_date,
      plan_end_date: formData.plan_end_date,
      plan_duration: formData.plan_duration,
      plan_manhours: formData.plan_manhours,
      owner_id: formData.owner_id,
      status: formData.status,
      priority: formData.priority,
      deliverable: formData.deliverable,
      block_type: formData.block_type,
      block_reason: formData.block_reason
    })
    
    // 如果进度有变化，单独更新进度
    if (formData.progress_rate !== props.task.progress) {
      await updateTaskProgress(props.task.id, {
        progress_rate: formData.progress_rate
      })
    }
    
    ElMessage.success('保存成功')
    emit('update', { ...props.task, ...formData, progress: formData.progress_rate })
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 添加依赖
async function addDependency() {
  if (!newDependency.predecessor_id) {
    ElMessage.warning('请选择前置任务')
    return
  }
  
  try {
    await createDependency({
      task_id: props.task.id,
      predecessor_id: newDependency.predecessor_id,
      depend_type: newDependency.depend_type,
      lag_days: newDependency.lag_days
    })
    
    ElMessage.success('添加成功')
    showAddDependency.value = false
    // 刷新依赖列表
    loadDependencies()
  } catch (error) {
    console.error('添加依赖失败:', error)
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

// 删除依赖
async function removeDependency(dependId) {
  try {
    await ElMessageBox.confirm('确定要删除这个依赖关系吗？', '确认删除')
    await delDep(dependId)
    ElMessage.success('删除成功')
    loadDependencies()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 加载依赖关系
function loadDependencies() {
  // TODO: 调用API获取依赖关系
  predecessors.value = []
}

// 加载操作日志
function loadTaskLogs() {
  // TODO: 调用API获取日志
  taskLogs.value = [
    { id: 1, operator_name: '张工', action: '更新进度', field_name: '进度', old_value: '30%', new_value: '50%', created_time: '2025-01-02 14:30' },
    { id: 2, operator_name: '系统', action: '创建任务', created_time: '2025-01-01 09:00' }
  ]
}

// 加载可选任务列表
function loadAvailableTasks() {
  // TODO: 调用API获取
  availableTasks.value = []
}

watch(() => props.task, () => {
  initFormData()
  loadDependencies()
  loadTaskLogs()
}, { immediate: true })

onMounted(() => {
  loadAvailableTasks()
})
</script>

<style lang="scss" scoped>
.task-detail-panel {
  padding: 16px;
  
  .progress-input {
    display: flex;
    align-items: center;
    
    .el-slider {
      flex: 1;
    }
  }
  
  .dependencies-section {
    .dep-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    
    .dep-list {
      .dep-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: #f5f5f5;
        border-radius: 4px;
        margin-bottom: 8px;
        
        .dep-name {
          flex: 1;
        }
      }
    }
  }
  
  .log-content {
    font-size: 13px;
    
    .log-user {
      font-weight: 600;
      margin-right: 8px;
    }
    
    .log-action {
      color: #1890ff;
      margin-right: 8px;
    }
  }
  
  .panel-footer {
    position: sticky;
    bottom: 0;
    background: #fff;
    padding: 16px 0;
    margin-top: 24px;
    border-top: 1px solid #f0f0f0;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>
