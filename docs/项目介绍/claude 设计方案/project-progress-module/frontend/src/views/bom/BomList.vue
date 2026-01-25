<template>
  <div class="bom-list">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.total_bom }}</div>
            <div class="stat-label">BOM总数</div>
          </div>
          <el-icon class="stat-icon"><Document /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card draft">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.draft_count }}</div>
            <div class="stat-label">草稿</div>
          </div>
          <el-icon class="stat-icon"><Edit /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card reviewing">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.reviewing_count }}</div>
            <div class="stat-label">评审中</div>
          </div>
          <el-icon class="stat-icon"><Timer /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card published">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.published_count }}</div>
            <div class="stat-label">已发布</div>
          </div>
          <el-icon class="stat-icon"><CircleCheck /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索筛选 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="queryParams" class="filter-form">
        <el-form-item label="项目">
          <el-select v-model="queryParams.project_id" placeholder="选择项目" clearable style="width: 180px">
            <el-option v-for="p in projectOptions" :key="p.project_id" :label="p.project_code" :value="p.project_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="机台号">
          <el-input v-model="queryParams.machine_no" placeholder="输入机台号" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="选择状态" clearable style="width: 120px">
            <el-option v-for="s in BOM_STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 查询</el-button>
          <el-button @click="handleReset"><el-icon><Refresh /></el-icon> 重置</el-button>
        </el-form-item>
      </el-form>
      <div class="action-buttons">
        <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 新建BOM</el-button>
        <el-button @click="handleExportAll"><el-icon><Download /></el-icon> 批量导出</el-button>
      </div>
    </el-card>

    <!-- BOM列表 -->
    <el-card shadow="never" class="table-card">
      <el-table
        v-loading="loading"
        :data="bomList"
        stripe
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="project_code" label="项目编号" width="120" />
        <el-table-column prop="machine_no" label="机台号" width="120">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.machine_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="machine_name" label="机台名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="bom_type" label="类型" width="80" />
        <el-table-column prop="current_version" label="版本" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_items" label="物料数" width="80" align="center" />
        <el-table-column prop="total_cost" label="预估成本" width="120" align="right">
          <template #default="{ row }">
            ¥{{ formatNumber(row.total_cost) }}
          </template>
        </el-table-column>
        <el-table-column prop="kit_rate" label="齐套率" width="100" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="Number(row.kit_rate)"
              :stroke-width="12"
              :color="getKitRateColor(row.kit_rate)"
              :format="(p: number) => p.toFixed(1) + '%'"
            />
          </template>
        </el-table-column>
        <el-table-column prop="designer_name" label="设计人" width="100" />
        <el-table-column prop="created_time" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">查看</el-button>
            <el-button link type="primary" @click="handleEdit(row)" v-if="row.status === '草稿'">编辑</el-button>
            <el-button link type="success" @click="handlePublish(row)" v-if="row.status === '草稿'">发布</el-button>
            <el-button link type="danger" @click="handleDelete(row)" v-if="row.status === '草稿'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :page-sizes="[20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="项目" prop="project_id">
          <el-select v-model="formData.project_id" placeholder="选择项目" style="width: 100%">
            <el-option v-for="p in projectOptions" :key="p.project_id" :label="`${p.project_code} - ${p.project_name}`" :value="p.project_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="机台号" prop="machine_no">
          <el-input v-model="formData.machine_no" placeholder="输入机台号" />
        </el-form-item>
        <el-form-item label="机台名称" prop="machine_name">
          <el-input v-model="formData.machine_name" placeholder="输入机台名称" />
        </el-form-item>
        <el-form-item label="BOM类型" prop="bom_type">
          <el-select v-model="formData.bom_type" style="width: 100%">
            <el-option v-for="t in BOM_TYPE_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="3" placeholder="输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 发布对话框 -->
    <el-dialog v-model="publishDialogVisible" title="发布BOM" width="500px">
      <el-form :model="publishForm" label-width="100px">
        <el-form-item label="版本类型">
          <el-select v-model="publishForm.version_type" style="width: 100%">
            <el-option label="初始版本" value="初始" />
            <el-option label="设计变更" value="变更" />
            <el-option label="修订更新" value="修订" />
          </el-select>
        </el-form-item>
        <el-form-item label="变更说明">
          <el-input v-model="publishForm.change_summary" type="textarea" :rows="3" placeholder="输入变更说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmPublish" :loading="publishing">确认发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Document, Edit, Timer, CircleCheck, Search, Refresh, Plus, Download
} from '@element-plus/icons-vue'
import {
  getBomList, createBom, updateBom, deleteBom, publishBom, getBomStatistics,
  BomHeader, BomStatistics, BOM_STATUS_OPTIONS, BOM_TYPE_OPTIONS
} from '@/api/bom'

const router = useRouter()

// 状态
const loading = ref(false)
const bomList = ref<BomHeader[]>([])
const total = ref(0)
const selectedRows = ref<BomHeader[]>([])
const statistics = ref<BomStatistics>({
  total_bom: 0,
  draft_count: 0,
  reviewing_count: 0,
  published_count: 0,
  frozen_count: 0
})

// 查询参数
const queryParams = reactive({
  project_id: undefined as number | undefined,
  machine_no: '',
  status: '',
  page: 1,
  page_size: 20
})

// 项目选项（模拟数据）
const projectOptions = ref([
  { project_id: 1, project_code: 'PRJ-2026-001', project_name: '某汽车零部件自动化产线' },
  { project_id: 2, project_code: 'PRJ-2026-002', project_name: '电子元器件组装线' }
])

// 表单相关
const dialogVisible = ref(false)
const dialogTitle = computed(() => formData.bom_id ? '编辑BOM' : '新建BOM')
const formRef = ref<FormInstance>()
const submitting = ref(false)
const formData = reactive({
  bom_id: 0,
  project_id: undefined as number | undefined,
  project_code: '',
  machine_no: '',
  machine_name: '',
  bom_type: '整机',
  designer_id: 1,
  designer_name: '当前用户',
  remark: ''
})
const formRules: FormRules = {
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  machine_no: [{ required: true, message: '请输入机台号', trigger: 'blur' }],
  bom_type: [{ required: true, message: '请选择BOM类型', trigger: 'change' }]
}

// 发布相关
const publishDialogVisible = ref(false)
const publishing = ref(false)
const currentBomId = ref(0)
const publishForm = reactive({
  version_type: '初始',
  change_summary: ''
})

// 初始化
onMounted(() => {
  fetchStatistics()
  fetchBomList()
})

// 获取统计数据
async function fetchStatistics() {
  try {
    const res = await getBomStatistics()
    statistics.value = res.data
  } catch (error) {
    console.error('获取统计数据失败', error)
  }
}

// 获取BOM列表
async function fetchBomList() {
  loading.value = true
  try {
    const res = await getBomList(queryParams)
    bomList.value = res.data.items
    total.value = res.data.total
  } catch (error) {
    console.error('获取BOM列表失败', error)
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  queryParams.page = 1
  fetchBomList()
}

// 重置
function handleReset() {
  queryParams.project_id = undefined
  queryParams.machine_no = ''
  queryParams.status = ''
  handleSearch()
}

// 新建
function handleCreate() {
  Object.assign(formData, {
    bom_id: 0,
    project_id: undefined,
    project_code: '',
    machine_no: '',
    machine_name: '',
    bom_type: '整机',
    remark: ''
  })
  dialogVisible.value = true
}

// 编辑
function handleEdit(row: BomHeader) {
  Object.assign(formData, {
    bom_id: row.bom_id,
    project_id: row.project_id,
    project_code: row.project_code,
    machine_no: row.machine_no,
    machine_name: row.machine_name,
    bom_type: row.bom_type,
    remark: row.remark
  })
  dialogVisible.value = true
}

// 查看
function handleView(row: BomHeader) {
  router.push({ name: 'BomDetail', params: { id: row.bom_id } })
}

// 提交表单
async function handleSubmit() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  submitting.value = true
  try {
    // 设置项目编号
    const project = projectOptions.value.find(p => p.project_id === formData.project_id)
    formData.project_code = project?.project_code || ''

    if (formData.bom_id) {
      await updateBom(formData.bom_id, formData)
      ElMessage.success('更新成功')
    } else {
      await createBom(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchBomList()
  } catch (error) {
    console.error('保存失败', error)
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

// 删除
async function handleDelete(row: BomHeader) {
  try {
    await ElMessageBox.confirm(`确定删除BOM "${row.machine_no}"?`, '删除确认', { type: 'warning' })
    await deleteBom(row.bom_id)
    ElMessage.success('删除成功')
    fetchBomList()
    fetchStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
    }
  }
}

// 发布
function handlePublish(row: BomHeader) {
  currentBomId.value = row.bom_id
  publishForm.version_type = '初始'
  publishForm.change_summary = ''
  publishDialogVisible.value = true
}

async function confirmPublish() {
  publishing.value = true
  try {
    await publishBom(currentBomId.value, publishForm)
    ElMessage.success('发布成功')
    publishDialogVisible.value = false
    fetchBomList()
    fetchStatistics()
  } catch (error) {
    console.error('发布失败', error)
    ElMessage.error('发布失败')
  } finally {
    publishing.value = false
  }
}

// 导出
function handleExportAll() {
  ElMessage.info('批量导出功能开发中')
}

// 选择变化
function handleSelectionChange(rows: BomHeader[]) {
  selectedRows.value = rows
}

// 工具函数
function getStatusType(status: string) {
  const option = BOM_STATUS_OPTIONS.find(s => s.value === status)
  return option?.type || 'info'
}

function getKitRateColor(rate: number) {
  if (rate >= 100) return '#67C23A'
  if (rate >= 80) return '#E6A23C'
  return '#F56C6C'
}

function formatNumber(num: number) {
  return num?.toLocaleString() || '0'
}

function formatDateTime(dt: string) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped lang="scss">
.bom-list {
  padding: 16px;

  .stats-row {
    margin-bottom: 16px;
  }

  .stat-card {
    position: relative;
    overflow: hidden;

    :deep(.el-card__body) {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px;
    }

    .stat-content {
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #303133;
      }
      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-top: 4px;
      }
    }

    .stat-icon {
      font-size: 48px;
      color: #409EFF;
      opacity: 0.3;
    }

    &.draft .stat-icon { color: #909399; }
    &.reviewing .stat-icon { color: #E6A23C; }
    &.published .stat-icon { color: #67C23A; }
  }

  .filter-card {
    margin-bottom: 16px;

    :deep(.el-card__body) {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
    }

    .filter-form {
      flex: 1;
    }

    .action-buttons {
      display: flex;
      gap: 8px;
    }
  }

  .table-card {
    .pagination-wrapper {
      margin-top: 16px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>
