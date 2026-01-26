<template>
  <div class="shortage-list">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card danger">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.critical_count }}</div>
            <div class="stat-label">紧急缺料</div>
          </div>
          <el-icon class="stat-icon"><Warning /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card warning">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.warning_count }}</div>
            <div class="stat-label">预警物料</div>
          </div>
          <el-icon class="stat-icon"><Bell /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.total_shortage }}</div>
            <div class="stat-label">缺料总数</div>
          </div>
          <el-icon class="stat-icon"><Box /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.affected_bom }}</div>
            <div class="stat-label">影响BOM数</div>
          </div>
          <el-icon class="stat-icon"><Document /></el-icon>
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
        <el-form-item label="物料类别">
          <el-select v-model="queryParams.category" placeholder="选择类别" clearable style="width: 120px">
            <el-option v-for="c in CATEGORY_OPTIONS" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="紧急程度">
          <el-select v-model="queryParams.urgency" placeholder="选择紧急程度" clearable style="width: 120px">
            <el-option label="紧急" value="critical" />
            <el-option label="预警" value="warning" />
            <el-option label="一般" value="normal" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 查询</el-button>
          <el-button @click="handleReset"><el-icon><Refresh /></el-icon> 重置</el-button>
        </el-form-item>
      </el-form>
      <div class="action-buttons">
        <el-button @click="handleExport"><el-icon><Download /></el-icon> 导出缺料清单</el-button>
        <el-button type="primary" @click="handleGeneratePR">生成采购申请</el-button>
      </div>
    </el-card>

    <!-- 缺料列表 -->
    <el-card shadow="never" class="table-card">
      <el-table
        v-loading="loading"
        :data="shortageList"
        stripe
        border
        :row-class-name="getRowClassName"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column label="紧急" width="60" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.urgency === 'critical'" class="urgent-icon critical"><Warning /></el-icon>
            <el-icon v-else-if="row.urgency === 'warning'" class="urgent-icon warning"><Bell /></el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="project_code" label="项目编号" width="120" />
        <el-table-column prop="machine_no" label="机台号" width="100">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewBom(row)">{{ row.machine_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="material_code" label="物料编码" width="120" />
        <el-table-column prop="material_name" label="物料名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="specification" label="规格型号" width="150" show-overflow-tooltip />
        <el-table-column label="类别" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ getCategoryName(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="需求" width="80" align="right" />
        <el-table-column prop="received_qty" label="已到" width="80" align="right" />
        <el-table-column prop="shortage_qty" label="缺口" width="80" align="right">
          <template #default="{ row }">
            <span class="shortage-qty">{{ row.shortage_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="required_date" label="需求日期" width="110">
          <template #default="{ row }">
            <span :class="{ 'overdue': isOverdue(row.required_date) }">
              {{ row.required_date || '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="lead_time" label="采购周期" width="90" align="center">
          <template #default="{ row }">
            {{ row.lead_time ? row.lead_time + '天' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="供应商" width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleCreatePR(row)">创建采购</el-button>
            <el-button link type="info" @click="handleViewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :page-sizes="[50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailDrawerVisible" title="缺料详情" size="500px">
      <el-descriptions :column="1" border v-if="currentItem">
        <el-descriptions-item label="项目编号">{{ currentItem.project_code }}</el-descriptions-item>
        <el-descriptions-item label="机台号">{{ currentItem.machine_no }}</el-descriptions-item>
        <el-descriptions-item label="物料编码">{{ currentItem.material_code }}</el-descriptions-item>
        <el-descriptions-item label="物料名称">{{ currentItem.material_name }}</el-descriptions-item>
        <el-descriptions-item label="规格型号">{{ currentItem.specification || '-' }}</el-descriptions-item>
        <el-descriptions-item label="物料类别">{{ getCategoryName(currentItem.category) }}</el-descriptions-item>
        <el-descriptions-item label="需求数量">{{ currentItem.quantity }}</el-descriptions-item>
        <el-descriptions-item label="已到货">{{ currentItem.received_qty }}</el-descriptions-item>
        <el-descriptions-item label="缺口数量">
          <span class="shortage-qty">{{ currentItem.shortage_qty }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="需求日期">
          <span :class="{ 'overdue': isOverdue(currentItem.required_date) }">
            {{ currentItem.required_date || '-' }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="采购周期">{{ currentItem.lead_time ? currentItem.lead_time + '天' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="供应商">{{ currentItem.supplier_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="关键件">{{ currentItem.is_key_part ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="长周期">{{ currentItem.is_long_lead ? '是' : '否' }}</el-descriptions-item>
      </el-descriptions>
      <div class="drawer-actions">
        <el-button type="primary" @click="handleCreatePR(currentItem!)">创建采购申请</el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, Bell, Box, Document, Search, Refresh, Download } from '@element-plus/icons-vue'
import { getShortageList, ShortageItem, CATEGORY_OPTIONS } from '@/api/bom'

const router = useRouter()

// 状态
const loading = ref(false)
const shortageList = ref<(ShortageItem & { urgency?: string; project_code?: string })[]>([])
const total = ref(0)
const selectedItems = ref<ShortageItem[]>([])

// 统计数据
const statistics = reactive({
  critical_count: 0,
  warning_count: 0,
  total_shortage: 0,
  affected_bom: 0
})

// 查询参数
const queryParams = reactive({
  project_id: undefined as number | undefined,
  bom_id: undefined as number | undefined,
  category: '',
  urgency: '',
  page: 1,
  page_size: 50
})

// 项目选项（模拟数据）
const projectOptions = ref([
  { project_id: 1, project_code: 'PRJ-2026-001' },
  { project_id: 2, project_code: 'PRJ-2026-002' }
])

// 详情抽屉
const detailDrawerVisible = ref(false)
const currentItem = ref<ShortageItem & { urgency?: string; project_code?: string } | null>(null)

// 初始化
onMounted(() => {
  fetchShortageList()
})

// 获取缺料列表
async function fetchShortageList() {
  loading.value = true
  try {
    const res = await getShortageList(queryParams)
    // 添加紧急程度标记
    shortageList.value = res.data.items.map((item: ShortageItem) => ({
      ...item,
      urgency: calculateUrgency(item),
      project_code: 'PRJ-2026-001' // 模拟数据
    }))
    total.value = res.data.total
    calculateStatistics()
  } catch (error) {
    console.error('获取缺料列表失败', error)
  } finally {
    loading.value = false
  }
}

// 计算紧急程度
function calculateUrgency(item: ShortageItem): string {
  if (!item.required_date) return 'normal'
  const today = new Date()
  const required = new Date(item.required_date)
  const daysLeft = Math.ceil((required.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  const leadTime = item.lead_time || 7

  if (daysLeft < 0) return 'critical' // 已逾期
  if (daysLeft < leadTime) return 'critical' // 来不及采购
  if (daysLeft < leadTime * 1.5) return 'warning' // 预警
  return 'normal'
}

// 计算统计数据
function calculateStatistics() {
  statistics.critical_count = shortageList.value.filter(i => i.urgency === 'critical').length
  statistics.warning_count = shortageList.value.filter(i => i.urgency === 'warning').length
  statistics.total_shortage = total.value
  statistics.affected_bom = new Set(shortageList.value.map(i => i.bom_id)).size
}

// 搜索
function handleSearch() {
  queryParams.page = 1
  fetchShortageList()
}

// 重置
function handleReset() {
  queryParams.project_id = undefined
  queryParams.category = ''
  queryParams.urgency = ''
  handleSearch()
}

// 选择变化
function handleSelectionChange(rows: ShortageItem[]) {
  selectedItems.value = rows
}

// 查看BOM
function handleViewBom(row: ShortageItem) {
  router.push({ name: 'BomDetail', params: { id: row.bom_id } })
}

// 查看详情
function handleViewDetail(row: ShortageItem & { urgency?: string; project_code?: string }) {
  currentItem.value = row
  detailDrawerVisible.value = true
}

// 创建采购申请
function handleCreatePR(row: ShortageItem) {
  ElMessage.info(`创建采购申请: ${row.material_name}, 数量: ${row.shortage_qty}`)
}

// 批量生成采购申请
function handleGeneratePR() {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('请选择需要采购的物料')
    return
  }
  ElMessage.info(`生成采购申请: ${selectedItems.value.length}项物料`)
}

// 导出
function handleExport() {
  ElMessage.info('导出缺料清单')
}

// 获取行样式
function getRowClassName({ row }: { row: ShortageItem & { urgency?: string } }) {
  if (row.urgency === 'critical') return 'row-critical'
  if (row.urgency === 'warning') return 'row-warning'
  return ''
}

// 判断是否逾期
function isOverdue(date?: string) {
  if (!date) return false
  return new Date(date) < new Date()
}

// 工具函数
function getCategoryName(code: string) {
  const category = CATEGORY_OPTIONS.find(c => c.value === code)
  return category?.label || code
}
</script>

<style scoped lang="scss">
.shortage-list {
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

    &.danger {
      border-left: 4px solid #F56C6C;
      .stat-icon { color: #F56C6C; }
      .stat-value { color: #F56C6C; }
    }

    &.warning {
      border-left: 4px solid #E6A23C;
      .stat-icon { color: #E6A23C; }
      .stat-value { color: #E6A23C; }
    }
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
    :deep(.row-critical) {
      background-color: #FEF0F0 !important;
    }

    :deep(.row-warning) {
      background-color: #FDF6EC !important;
    }

    .urgent-icon {
      font-size: 20px;
      &.critical { color: #F56C6C; }
      &.warning { color: #E6A23C; }
    }

    .shortage-qty {
      color: #F56C6C;
      font-weight: 600;
    }

    .overdue {
      color: #F56C6C;
    }

    .pagination-wrapper {
      margin-top: 16px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .drawer-actions {
    margin-top: 24px;
    text-align: center;
  }
}
</style>
