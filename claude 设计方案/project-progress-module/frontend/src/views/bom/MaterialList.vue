<template>
  <div class="material-list">
    <!-- 搜索筛选 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="queryParams" class="filter-form">
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="编码/名称/规格" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="物料类别">
          <el-select v-model="queryParams.category" placeholder="选择类别" clearable style="width: 120px">
            <el-option v-for="c in CATEGORY_OPTIONS" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="选择状态" clearable style="width: 100px">
            <el-option label="启用" value="启用" />
            <el-option label="停用" value="停用" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 查询</el-button>
          <el-button @click="handleReset"><el-icon><Refresh /></el-icon> 重置</el-button>
        </el-form-item>
      </el-form>
      <div class="action-buttons">
        <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 新建物料</el-button>
        <el-button @click="handleImport"><el-icon><Upload /></el-icon> 批量导入</el-button>
        <el-button @click="handleExport"><el-icon><Download /></el-icon> 导出</el-button>
      </div>
    </el-card>

    <!-- 物料列表 -->
    <el-card shadow="never" class="table-card">
      <el-table v-loading="loading" :data="materialList" stripe border>
        <el-table-column prop="material_code" label="物料编码" width="130">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">{{ row.material_code }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="material_name" label="物料名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="specification" label="规格型号" width="150" show-overflow-tooltip />
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column label="类别" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ getCategoryName(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="60" align="center" />
        <el-table-column prop="reference_price" label="参考价" width="90" align="right">
          <template #default="{ row }">
            {{ row.reference_price ? '¥' + row.reference_price : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="default_supplier_name" label="默认供应商" width="120" show-overflow-tooltip />
        <el-table-column prop="lead_time" label="采购周期" width="90" align="center">
          <template #default="{ row }">
            {{ row.lead_time }}天
          </template>
        </el-table-column>
        <el-table-column prop="is_standard" label="标准件" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_standard ? 'success' : 'info'" size="small">
              {{ row.is_standard ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === '启用' ? 'success' : 'danger'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link :type="row.status === '启用' ? 'warning' : 'success'" @click="handleToggleStatus(row)">
              {{ row.status === '启用' ? '停用' : '启用' }}
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="物料编码" prop="material_code">
              <el-input v-model="formData.material_code" placeholder="输入物料编码" :disabled="!!formData.material_id" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="物料名称" prop="material_name">
              <el-input v-model="formData.material_name" placeholder="输入物料名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="规格型号" prop="specification">
              <el-input v-model="formData.specification" placeholder="输入规格型号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品牌" prop="brand">
              <el-input v-model="formData.brand" placeholder="输入品牌" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="物料类别" prop="category">
              <el-select v-model="formData.category" style="width: 100%">
                <el-option v-for="c in CATEGORY_OPTIONS" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="子类别" prop="sub_category">
              <el-input v-model="formData.sub_category" placeholder="子类别" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="单位" prop="unit">
              <el-input v-model="formData.unit" placeholder="pcs" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="参考单价" prop="reference_price">
              <el-input-number v-model="formData.reference_price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="采购周期" prop="lead_time">
              <el-input-number v-model="formData.lead_time" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最小起订量" prop="min_order_qty">
              <el-input-number v-model="formData.min_order_qty" :min="1" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="默认供应商" prop="default_supplier_name">
              <el-input v-model="formData.default_supplier_name" placeholder="输入默认供应商" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否标准件" prop="is_standard">
              <el-switch v-model="formData.is_standard" :active-value="1" :inactive-value="0" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="2" placeholder="输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情抽屉 -->
    <el-drawer v-model="detailDrawerVisible" title="物料详情" size="500px">
      <el-descriptions :column="1" border v-if="currentMaterial">
        <el-descriptions-item label="物料编码">{{ currentMaterial.material_code }}</el-descriptions-item>
        <el-descriptions-item label="物料名称">{{ currentMaterial.material_name }}</el-descriptions-item>
        <el-descriptions-item label="规格型号">{{ currentMaterial.specification || '-' }}</el-descriptions-item>
        <el-descriptions-item label="品牌">{{ currentMaterial.brand || '-' }}</el-descriptions-item>
        <el-descriptions-item label="物料类别">{{ getCategoryName(currentMaterial.category) }}</el-descriptions-item>
        <el-descriptions-item label="单位">{{ currentMaterial.unit }}</el-descriptions-item>
        <el-descriptions-item label="参考单价">{{ currentMaterial.reference_price ? '¥' + currentMaterial.reference_price : '-' }}</el-descriptions-item>
        <el-descriptions-item label="默认供应商">{{ currentMaterial.default_supplier_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="采购周期">{{ currentMaterial.lead_time }}天</el-descriptions-item>
        <el-descriptions-item label="最小起订量">{{ currentMaterial.min_order_qty }}</el-descriptions-item>
        <el-descriptions-item label="标准件">{{ currentMaterial.is_standard ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentMaterial.status === '启用' ? 'success' : 'danger'">{{ currentMaterial.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="备注">{{ currentMaterial.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(currentMaterial.created_time) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search, Refresh, Plus, Upload, Download } from '@element-plus/icons-vue'
import {
  getMaterialList, createMaterial, updateMaterial, deleteMaterial,
  Material, CATEGORY_OPTIONS
} from '@/api/bom'

// 状态
const loading = ref(false)
const materialList = ref<Material[]>([])
const total = ref(0)

// 查询参数
const queryParams = reactive({
  keyword: '',
  category: '',
  status: '',
  page: 1,
  page_size: 20
})

// 表单相关
const dialogVisible = ref(false)
const dialogTitle = computed(() => formData.material_id ? '编辑物料' : '新建物料')
const formRef = ref<FormInstance>()
const submitting = ref(false)
const formData = reactive({
  material_id: 0,
  material_code: '',
  material_name: '',
  specification: '',
  brand: '',
  category: 'ME',
  sub_category: '',
  unit: 'pcs',
  reference_price: undefined as number | undefined,
  default_supplier_id: undefined as number | undefined,
  default_supplier_name: '',
  lead_time: 7,
  min_order_qty: 1,
  is_standard: 0,
  remark: ''
})
const formRules: FormRules = {
  material_code: [{ required: true, message: '请输入物料编码', trigger: 'blur' }],
  material_name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择物料类别', trigger: 'change' }]
}

// 详情抽屉
const detailDrawerVisible = ref(false)
const currentMaterial = ref<Material | null>(null)

// 初始化
onMounted(() => {
  fetchMaterialList()
})

// 获取物料列表
async function fetchMaterialList() {
  loading.value = true
  try {
    const res = await getMaterialList(queryParams)
    materialList.value = res.data.items
    total.value = res.data.total
  } catch (error) {
    console.error('获取物料列表失败', error)
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  queryParams.page = 1
  fetchMaterialList()
}

// 重置
function handleReset() {
  queryParams.keyword = ''
  queryParams.category = ''
  queryParams.status = ''
  handleSearch()
}

// 新建
function handleCreate() {
  Object.assign(formData, {
    material_id: 0,
    material_code: '',
    material_name: '',
    specification: '',
    brand: '',
    category: 'ME',
    sub_category: '',
    unit: 'pcs',
    reference_price: undefined,
    default_supplier_name: '',
    lead_time: 7,
    min_order_qty: 1,
    is_standard: 0,
    remark: ''
  })
  dialogVisible.value = true
}

// 编辑
function handleEdit(row: Material) {
  Object.assign(formData, {
    material_id: row.material_id,
    material_code: row.material_code,
    material_name: row.material_name,
    specification: row.specification || '',
    brand: row.brand || '',
    category: row.category,
    sub_category: row.sub_category || '',
    unit: row.unit,
    reference_price: row.reference_price,
    default_supplier_name: row.default_supplier_name || '',
    lead_time: row.lead_time,
    min_order_qty: row.min_order_qty,
    is_standard: row.is_standard,
    remark: row.remark || ''
  })
  dialogVisible.value = true
}

// 查看
function handleView(row: Material) {
  currentMaterial.value = row
  detailDrawerVisible.value = true
}

// 提交表单
async function handleSubmit() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  submitting.value = true
  try {
    if (formData.material_id) {
      await updateMaterial(formData.material_id, formData)
      ElMessage.success('更新成功')
    } else {
      await createMaterial(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchMaterialList()
  } catch (error) {
    console.error('保存失败', error)
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

// 切换状态
async function handleToggleStatus(row: Material) {
  const newStatus = row.status === '启用' ? '停用' : '启用'
  try {
    await updateMaterial(row.material_id, { status: newStatus })
    ElMessage.success(`${newStatus}成功`)
    fetchMaterialList()
  } catch (error) {
    console.error('操作失败', error)
    ElMessage.error('操作失败')
  }
}

// 删除
async function handleDelete(row: Material) {
  try {
    await ElMessageBox.confirm(`确定删除物料 "${row.material_name}"?`, '删除确认', { type: 'warning' })
    await deleteMaterial(row.material_id)
    ElMessage.success('删除成功')
    fetchMaterialList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
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

// 工具函数
function getCategoryName(code: string) {
  const category = CATEGORY_OPTIONS.find(c => c.value === code)
  return category?.label || code
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
.material-list {
  padding: 16px;

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
