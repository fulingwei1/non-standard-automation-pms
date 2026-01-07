<template>
  <div class="bom-detail" v-loading="loading">
    <!-- 顶部信息栏 -->
    <el-card shadow="never" class="header-card">
      <div class="header-content">
        <div class="bom-info">
          <div class="title-row">
            <h2>{{ bomData.machine_no }} - {{ bomData.machine_name }}</h2>
            <el-tag :type="getStatusType(bomData.status)" size="large">{{ bomData.status }}</el-tag>
          </div>
          <div class="meta-row">
            <span><el-icon><Folder /></el-icon> {{ bomData.project_code }}</span>
            <span><el-icon><Document /></el-icon> {{ bomData.bom_type }}</span>
            <span><el-icon><User /></el-icon> {{ bomData.designer_name }}</span>
            <span><el-icon><Clock /></el-icon> {{ formatDateTime(bomData.created_time) }}</span>
          </div>
        </div>
        <div class="action-buttons">
          <el-button @click="handleBack"><el-icon><Back /></el-icon> 返回</el-button>
          <el-button type="primary" @click="handleImport" v-if="bomData.status === '草稿'">
            <el-icon><Upload /></el-icon> 导入
          </el-button>
          <el-button @click="handleExport"><el-icon><Download /></el-icon> 导出</el-button>
          <el-button type="success" @click="handlePublish" v-if="bomData.status === '草稿'">
            <el-icon><Promotion /></el-icon> 发布
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 统计信息 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="物料总数" :value="bomData.total_items" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="预估成本" :value="bomData.total_cost" prefix="¥" :precision="2" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <template #default>
            <div class="kit-rate-stat">
              <div class="label">齐套率</div>
              <el-progress
                type="dashboard"
                :percentage="Number(bomData.kit_rate)"
                :color="getKitRateColor(bomData.kit_rate)"
                :width="80"
              />
            </div>
          </template>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="当前版本" :value="bomData.current_version" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 物料类别统计 -->
    <el-card shadow="never" class="category-card">
      <template #header>
        <span>物料类别分布</span>
      </template>
      <div class="category-stats">
        <div v-for="cat in categoryStats" :key="cat.category" class="category-item">
          <div class="category-label">{{ cat.category_name }}</div>
          <div class="category-value">{{ cat.count }}项</div>
          <div class="category-amount">¥{{ formatNumber(cat.amount) }}</div>
        </div>
      </div>
    </el-card>

    <!-- BOM明细表格 -->
    <el-card shadow="never" class="items-card">
      <template #header>
        <div class="card-header">
          <span>BOM明细 ({{ items.length }}项)</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索物料编码/名称"
              style="width: 200px"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select v-model="filterCategory" placeholder="物料类别" clearable style="width: 120px" @change="handleSearch">
              <el-option v-for="c in CATEGORY_OPTIONS" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
            <el-button type="primary" @click="handleAddItem" v-if="bomData.status === '草稿'">
              <el-icon><Plus /></el-icon> 添加物料
            </el-button>
            <el-button @click="handleBatchDelete" v-if="selectedItems.length > 0 && bomData.status === '草稿'">
              批量删除 ({{ selectedItems.length }})
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="filteredItems"
        stripe
        border
        max-height="500"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" v-if="bomData.status === '草稿'" />
        <el-table-column prop="line_no" label="行号" width="60" align="center" />
        <el-table-column prop="material_code" label="物料编码" width="120" />
        <el-table-column prop="material_name" label="物料名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="specification" label="规格型号" width="150" show-overflow-tooltip />
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column prop="category_name" label="类别" width="80" />
        <el-table-column prop="unit" label="单位" width="60" align="center" />
        <el-table-column prop="quantity" label="需求数量" width="90" align="right" />
        <el-table-column prop="unit_price" label="单价" width="90" align="right">
          <template #default="{ row }">
            {{ row.unit_price ? '¥' + row.unit_price : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="100" align="right">
          <template #default="{ row }">
            {{ row.amount ? '¥' + formatNumber(row.amount) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="到货进度" width="140">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress
                :percentage="getReceivedRate(row)"
                :stroke-width="8"
                :color="getReceivedColor(row)"
              />
              <span class="progress-text">{{ row.received_qty }}/{{ row.quantity }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="procurement_status" label="采购状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getProcurementStatusType(row.procurement_status)" size="small">
              {{ row.procurement_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="供应商" width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="120" fixed="right" v-if="bomData.status === '草稿'">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEditItem(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDeleteItem(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 版本历史 -->
    <el-card shadow="never" class="version-card">
      <template #header>
        <div class="card-header">
          <span>版本历史</span>
          <el-button link type="primary" @click="handleCompareVersions" v-if="versions.length >= 2">
            版本对比
          </el-button>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="v in versions"
          :key="v.version_id"
          :timestamp="formatDateTime(v.published_time)"
          placement="top"
        >
          <el-card shadow="hover">
            <div class="version-content">
              <div class="version-header">
                <el-tag>{{ v.version }}</el-tag>
                <span class="version-type">{{ v.version_type }}</span>
                <span class="version-user">{{ v.published_name }}</span>
              </div>
              <div class="version-summary" v-if="v.change_summary">{{ v.change_summary }}</div>
              <div class="version-stats">
                物料数: {{ v.total_items }} | 成本: ¥{{ formatNumber(v.total_cost) }}
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="versions.length === 0" description="暂无版本记录" :image-size="60" />
    </el-card>

    <!-- 添加/编辑物料对话框 -->
    <el-dialog
      v-model="itemDialogVisible"
      :title="editingItem ? '编辑物料' : '添加物料'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form ref="itemFormRef" :model="itemForm" :rules="itemRules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="物料编码" prop="material_code">
              <el-input v-model="itemForm.material_code" placeholder="输入物料编码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="物料名称" prop="material_name">
              <el-input v-model="itemForm.material_name" placeholder="输入物料名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="规格型号" prop="specification">
              <el-input v-model="itemForm.specification" placeholder="输入规格型号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品牌" prop="brand">
              <el-input v-model="itemForm.brand" placeholder="输入品牌" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="物料类别" prop="category">
              <el-select v-model="itemForm.category" style="width: 100%">
                <el-option v-for="c in CATEGORY_OPTIONS" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="单位" prop="unit">
              <el-input v-model="itemForm.unit" placeholder="pcs" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="需求数量" prop="quantity">
              <el-input-number v-model="itemForm.quantity" :min="1" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="单价" prop="unit_price">
              <el-input-number v-model="itemForm.unit_price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="供应商" prop="supplier_name">
              <el-input v-model="itemForm.supplier_name" placeholder="输入供应商" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="采购周期" prop="lead_time">
              <el-input-number v-model="itemForm.lead_time" :min="1" style="width: 100%">
                <template #suffix>天</template>
              </el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="图纸号" prop="drawing_no">
              <el-input v-model="itemForm.drawing_no" placeholder="输入图纸号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="位置号" prop="position_no">
              <el-input v-model="itemForm.position_no" placeholder="输入位置号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="itemForm.remark" type="textarea" :rows="2" placeholder="输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitItem" :loading="itemSubmitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Folder, Document, User, Clock, Back, Upload, Download, Promotion,
  Search, Plus
} from '@element-plus/icons-vue'
import {
  getBomDetail, addBomItem, updateBomItem, deleteBomItem, batchDeleteItems,
  getBomVersions, getCategoryStatistics, publishBom,
  BomHeader, BomItem, BomVersion, CategoryStatistics,
  BOM_STATUS_OPTIONS, CATEGORY_OPTIONS, PROCUREMENT_STATUS_OPTIONS
} from '@/api/bom'

const route = useRoute()
const router = useRouter()
const bomId = Number(route.params.id)

// 状态
const loading = ref(true)
const bomData = ref<BomHeader>({} as BomHeader)
const items = ref<BomItem[]>([])
const versions = ref<BomVersion[]>([])
const categoryStats = ref<CategoryStatistics[]>([])
const selectedItems = ref<BomItem[]>([])

// 搜索筛选
const searchKeyword = ref('')
const filterCategory = ref('')

// 物料表单
const itemDialogVisible = ref(false)
const editingItem = ref<BomItem | null>(null)
const itemFormRef = ref<FormInstance>()
const itemSubmitting = ref(false)
const itemForm = reactive({
  line_no: 0,
  material_code: '',
  material_name: '',
  specification: '',
  brand: '',
  category: 'ME',
  unit: 'pcs',
  quantity: 1,
  unit_price: undefined as number | undefined,
  supplier_name: '',
  lead_time: 7,
  drawing_no: '',
  position_no: '',
  remark: ''
})
const itemRules: FormRules = {
  material_code: [{ required: true, message: '请输入物料编码', trigger: 'blur' }],
  material_name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择物料类别', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入需求数量', trigger: 'blur' }]
}

// 过滤后的明细列表
const filteredItems = computed(() => {
  let result = items.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(item =>
      item.material_code.toLowerCase().includes(kw) ||
      item.material_name.toLowerCase().includes(kw)
    )
  }
  if (filterCategory.value) {
    result = result.filter(item => item.category === filterCategory.value)
  }
  return result
})

// 初始化
onMounted(() => {
  fetchBomDetail()
  fetchVersions()
  fetchCategoryStats()
})

// 获取BOM详情
async function fetchBomDetail() {
  loading.value = true
  try {
    const res = await getBomDetail(bomId)
    bomData.value = res.data
    items.value = res.data.items || []
  } catch (error) {
    console.error('获取BOM详情失败', error)
    ElMessage.error('获取BOM详情失败')
  } finally {
    loading.value = false
  }
}

// 获取版本历史
async function fetchVersions() {
  try {
    const res = await getBomVersions(bomId)
    versions.value = res.data.items
  } catch (error) {
    console.error('获取版本历史失败', error)
  }
}

// 获取类别统计
async function fetchCategoryStats() {
  try {
    const res = await getCategoryStatistics(bomId)
    categoryStats.value = res.data.items
  } catch (error) {
    console.error('获取类别统计失败', error)
  }
}

// 返回列表
function handleBack() {
  router.push({ name: 'BomList' })
}

// 搜索
function handleSearch() {
  // 触发computed重新计算
}

// 选择变化
function handleSelectionChange(rows: BomItem[]) {
  selectedItems.value = rows
}

// 添加物料
function handleAddItem() {
  editingItem.value = null
  const maxLineNo = items.value.reduce((max, item) => Math.max(max, item.line_no), 0)
  Object.assign(itemForm, {
    line_no: maxLineNo + 1,
    material_code: '',
    material_name: '',
    specification: '',
    brand: '',
    category: 'ME',
    unit: 'pcs',
    quantity: 1,
    unit_price: undefined,
    supplier_name: '',
    lead_time: 7,
    drawing_no: '',
    position_no: '',
    remark: ''
  })
  itemDialogVisible.value = true
}

// 编辑物料
function handleEditItem(row: BomItem) {
  editingItem.value = row
  Object.assign(itemForm, {
    line_no: row.line_no,
    material_code: row.material_code,
    material_name: row.material_name,
    specification: row.specification || '',
    brand: row.brand || '',
    category: row.category,
    unit: row.unit,
    quantity: row.quantity,
    unit_price: row.unit_price,
    supplier_name: row.supplier_name || '',
    lead_time: row.lead_time || 7,
    drawing_no: row.drawing_no || '',
    position_no: row.position_no || '',
    remark: row.remark || ''
  })
  itemDialogVisible.value = true
}

// 提交物料
async function handleSubmitItem() {
  const valid = await itemFormRef.value?.validate()
  if (!valid) return

  itemSubmitting.value = true
  try {
    if (editingItem.value) {
      await updateBomItem(editingItem.value.item_id, itemForm)
      ElMessage.success('更新成功')
    } else {
      await addBomItem(bomId, itemForm)
      ElMessage.success('添加成功')
    }
    itemDialogVisible.value = false
    fetchBomDetail()
    fetchCategoryStats()
  } catch (error) {
    console.error('保存失败', error)
    ElMessage.error('保存失败')
  } finally {
    itemSubmitting.value = false
  }
}

// 删除物料
async function handleDeleteItem(row: BomItem) {
  try {
    await ElMessageBox.confirm(`确定删除物料 "${row.material_name}"?`, '删除确认', { type: 'warning' })
    await deleteBomItem(row.item_id)
    ElMessage.success('删除成功')
    fetchBomDetail()
    fetchCategoryStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
    }
  }
}

// 批量删除
async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedItems.value.length} 项物料?`, '批量删除', { type: 'warning' })
    const ids = selectedItems.value.map(item => item.item_id)
    await batchDeleteItems(ids)
    ElMessage.success('删除成功')
    fetchBomDetail()
    fetchCategoryStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败', error)
    }
  }
}

// 导入
function handleImport() {
  ElMessage.info('导入功能开发中')
}

// 导出
function handleExport() {
  ElMessage.info('导出功能开发中')
}

// 发布
async function handlePublish() {
  try {
    await ElMessageBox.confirm('确定发布此BOM?发布后将生成新版本。', '发布确认', { type: 'info' })
    await publishBom(bomId, { version_type: '初始' })
    ElMessage.success('发布成功')
    fetchBomDetail()
    fetchVersions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('发布失败', error)
    }
  }
}

// 版本对比
function handleCompareVersions() {
  ElMessage.info('版本对比功能开发中')
}

// 工具函数
function getStatusType(status: string) {
  const option = BOM_STATUS_OPTIONS.find(s => s.value === status)
  return option?.type || 'info'
}

function getProcurementStatusType(status: string) {
  const option = PROCUREMENT_STATUS_OPTIONS.find(s => s.value === status)
  return option?.type || 'info'
}

function getKitRateColor(rate: number) {
  if (rate >= 100) return '#67C23A'
  if (rate >= 80) return '#E6A23C'
  return '#F56C6C'
}

function getReceivedRate(row: BomItem) {
  if (!row.quantity || row.quantity === 0) return 0
  return Math.min(100, (row.received_qty / row.quantity) * 100)
}

function getReceivedColor(row: BomItem) {
  const rate = getReceivedRate(row)
  if (rate >= 100) return '#67C23A'
  if (rate > 0) return '#E6A23C'
  return '#909399'
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
.bom-detail {
  padding: 16px;

  .header-card {
    margin-bottom: 16px;

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;

      .bom-info {
        .title-row {
          display: flex;
          align-items: center;
          gap: 12px;

          h2 {
            margin: 0;
            font-size: 20px;
          }
        }

        .meta-row {
          margin-top: 12px;
          display: flex;
          gap: 24px;
          color: #606266;
          font-size: 14px;

          span {
            display: flex;
            align-items: center;
            gap: 4px;
          }
        }
      }

      .action-buttons {
        display: flex;
        gap: 8px;
      }
    }
  }

  .stats-row {
    margin-bottom: 16px;

    .stat-card {
      .kit-rate-stat {
        display: flex;
        flex-direction: column;
        align-items: center;

        .label {
          font-size: 14px;
          color: #909399;
          margin-bottom: 8px;
        }
      }
    }
  }

  .category-card {
    margin-bottom: 16px;

    .category-stats {
      display: flex;
      gap: 24px;
      flex-wrap: wrap;

      .category-item {
        text-align: center;
        padding: 12px 24px;
        background: #f5f7fa;
        border-radius: 4px;

        .category-label {
          font-size: 14px;
          color: #606266;
        }

        .category-value {
          font-size: 20px;
          font-weight: 600;
          margin: 4px 0;
        }

        .category-amount {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }

  .items-card {
    margin-bottom: 16px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 8px;
      }
    }

    .progress-cell {
      .progress-text {
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .version-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .version-content {
      .version-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;

        .version-type {
          color: #606266;
        }

        .version-user {
          color: #909399;
          font-size: 13px;
        }
      }

      .version-summary {
        color: #606266;
        margin-bottom: 8px;
      }

      .version-stats {
        font-size: 13px;
        color: #909399;
      }
    }
  }
}
</style>
