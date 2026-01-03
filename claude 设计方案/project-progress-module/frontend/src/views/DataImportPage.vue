<template>
  <div class="data-import-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>数据导入</span>
          <el-button type="primary" text @click="showHelp = true">
            <el-icon><QuestionFilled /></el-icon>导入说明
          </el-button>
        </div>
      </template>

      <el-steps :active="currentStep" finish-status="success" style="margin-bottom: 30px">
        <el-step title="选择类型" />
        <el-step title="上传文件" />
        <el-step title="数据预览" />
        <el-step title="导入结果" />
      </el-steps>

      <!-- Step 1: 选择导入类型 -->
      <div v-show="currentStep === 0" class="step-content">
        <h3>请选择要导入的数据类型</h3>
        <el-row :gutter="20">
          <el-col :span="8" v-for="template in templates" :key="template.type">
            <div 
              class="import-type-card" 
              :class="{ active: selectedType === template.type }"
              @click="selectType(template.type)"
            >
              <el-icon :size="36"><component :is="template.icon" /></el-icon>
              <h4>{{ template.name }}</h4>
              <p>{{ template.desc }}</p>
              <el-button size="small" text type="primary" @click.stop="downloadTemplate(template.type)">
                <el-icon><Download /></el-icon>下载模板
              </el-button>
            </div>
          </el-col>
        </el-row>
        <div class="step-actions">
          <el-button type="primary" :disabled="!selectedType" @click="nextStep">
            下一步
          </el-button>
        </div>
      </div>

      <!-- Step 2: 上传文件 -->
      <div v-show="currentStep === 1" class="step-content">
        <h3>上传Excel文件</h3>
        <el-upload
          ref="uploadRef"
          class="upload-area"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              只能上传 Excel 文件(.xlsx, .xls)，且不超过10MB
            </div>
          </template>
        </el-upload>

        <el-form :inline="true" style="margin-top: 20px">
          <el-form-item label="工作表">
            <el-input v-model="sheetName" placeholder="默认第一个工作表" style="width: 200px" />
          </el-form-item>
          <el-form-item label="更新已存在数据">
            <el-switch v-model="updateExisting" />
          </el-form-item>
        </el-form>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="primary" :disabled="!selectedFile" @click="previewData">
            预览数据
          </el-button>
        </div>
      </div>

      <!-- Step 3: 数据预览 -->
      <div v-show="currentStep === 2" class="step-content">
        <h3>数据预览</h3>
        <div v-if="previewLoading" class="loading-box">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在解析文件...</span>
        </div>
        <div v-else-if="previewResult">
          <el-alert 
            v-if="previewResult.error_count > 0" 
            type="error" 
            :title="`发现 ${previewResult.error_count} 条数据错误`"
            show-icon
            style="margin-bottom: 16px"
          />
          <el-alert 
            v-else
            type="success" 
            title="数据格式验证通过"
            show-icon
            style="margin-bottom: 16px"
          />

          <div class="preview-info">
            <span>总计 <b>{{ previewResult.total_rows }}</b> 条数据</span>
            <span v-if="previewResult.error_count > 0" style="color: #f56c6c">
              ，其中 <b>{{ previewResult.error_count }}</b> 条有错误
            </span>
          </div>

          <!-- 错误列表 -->
          <el-collapse v-if="previewResult.errors?.length > 0" style="margin: 16px 0">
            <el-collapse-item title="错误详情" name="errors">
              <el-table :data="previewResult.errors" size="small" max-height="200">
                <el-table-column prop="row" label="行号" width="80" />
                <el-table-column prop="field" label="字段" width="120" />
                <el-table-column prop="message" label="错误信息" />
              </el-table>
            </el-collapse-item>
          </el-collapse>

          <!-- 数据预览表格 -->
          <el-table :data="previewResult.preview_data" size="small" max-height="300" border>
            <el-table-column 
              v-for="col in previewResult.columns" 
              :key="col" 
              :prop="col" 
              :label="col"
              min-width="120"
              show-overflow-tooltip
            />
          </el-table>
        </div>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button 
            type="primary" 
            :disabled="previewResult?.error_count > 0"
            :loading="importing"
            @click="doImport"
          >
            {{ importing ? '导入中...' : '开始导入' }}
          </el-button>
        </div>
      </div>

      <!-- Step 4: 导入结果 -->
      <div v-show="currentStep === 3" class="step-content">
        <div class="result-box" :class="importResult?.success ? 'success' : 'error'">
          <el-icon :size="64">
            <CircleCheckFilled v-if="importResult?.success" />
            <CircleCloseFilled v-else />
          </el-icon>
          <h2>{{ importResult?.success ? '导入成功' : '导入失败' }}</h2>
          <div class="result-stats">
            <div class="stat-item">
              <span class="label">总计</span>
              <span class="value">{{ importResult?.total_rows }}</span>
            </div>
            <div class="stat-item success">
              <span class="label">成功</span>
              <span class="value">{{ importResult?.success_count }}</span>
            </div>
            <div class="stat-item error" v-if="importResult?.error_count > 0">
              <span class="label">失败</span>
              <span class="value">{{ importResult?.error_count }}</span>
            </div>
          </div>

          <el-collapse v-if="importResult?.errors?.length > 0" style="margin: 20px 0; text-align: left">
            <el-collapse-item title="失败记录详情">
              <el-table :data="importResult.errors" size="small" max-height="200">
                <el-table-column prop="row" label="行号" width="80" />
                <el-table-column prop="field" label="字段" width="120" />
                <el-table-column prop="message" label="错误信息" />
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </div>

        <div class="step-actions">
          <el-button @click="resetImport">重新导入</el-button>
          <el-button type="primary" @click="$router.push('/projects')">查看数据</el-button>
        </div>
      </div>
    </el-card>

    <!-- 导入说明对话框 -->
    <el-dialog v-model="showHelp" title="导入说明" width="600px">
      <div class="help-content">
        <h4>导入步骤</h4>
        <ol>
          <li>选择要导入的数据类型</li>
          <li>下载对应的导入模板</li>
          <li>按模板格式填写数据</li>
          <li>上传填写好的Excel文件</li>
          <li>预览并确认数据无误</li>
          <li>执行导入</li>
        </ol>

        <h4>注意事项</h4>
        <ul>
          <li>带 * 的列为必填项</li>
          <li>日期格式：YYYY-MM-DD（如 2025-01-15）</li>
          <li>请勿修改表头名称</li>
          <li>示例数据可以删除或覆盖</li>
          <li>导入前请先确保关联数据存在（如导入任务前需先导入项目）</li>
        </ul>

        <h4>数据导入顺序建议</h4>
        <p>部门 → 人员 → 客户 → 项目 → 任务 → 工时</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Folder, User, Clock, List, OfficeBuilding, 
  Download, UploadFilled, Loading, QuestionFilled,
  CircleCheckFilled, CircleCloseFilled
} from '@element-plus/icons-vue'
import request from '@/utils/request'

// 模板类型配置
const templates = [
  { type: 'project', name: '项目导入', icon: 'Folder', desc: '批量导入项目基本信息' },
  { type: 'task', name: '任务导入', icon: 'List', desc: '批量导入WBS任务分解' },
  { type: 'user', name: '人员导入', icon: 'User', desc: '批量导入系统用户' },
  { type: 'timesheet', name: '工时导入', icon: 'Clock', desc: '批量导入工时记录' },
  { type: 'customer', name: '客户导入', icon: 'OfficeBuilding', desc: '批量导入客户信息' },
  { type: 'department', name: '部门导入', icon: 'OfficeBuilding', desc: '批量导入部门结构' },
]

// 状态
const currentStep = ref(0)
const selectedType = ref('')
const selectedFile = ref(null)
const sheetName = ref('')
const updateExisting = ref(false)
const showHelp = ref(false)

// 预览相关
const previewLoading = ref(false)
const previewResult = ref(null)

// 导入相关
const importing = ref(false)
const importResult = ref(null)

const uploadRef = ref(null)

// 选择导入类型
const selectType = (type) => {
  selectedType.value = type
}

// 下载模板
const downloadTemplate = (type) => {
  window.open(`/api/v1/import/templates/${type}`, '_blank')
}

// 文件变化
const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleFileRemove = () => {
  selectedFile.value = null
}

// 步骤导航
const nextStep = () => {
  currentStep.value++
}

const prevStep = () => {
  currentStep.value--
}

// 预览数据
const previewData = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先上传文件')
    return
  }

  previewLoading.value = true
  previewResult.value = null

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    // 先验证
    const validateRes = await request.post(
      `/api/v1/import/validate?import_type=${selectedType.value}&sheet_name=${sheetName.value || ''}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    // 再预览
    const previewRes = await request.post(
      `/api/v1/import/preview?import_type=${selectedType.value}&sheet_name=${sheetName.value || ''}&max_rows=20`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    previewResult.value = {
      ...previewRes.data,
      ...validateRes.data
    }

    currentStep.value = 2
  } catch (e) {
    ElMessage.error(e.message || '预览失败')
  } finally {
    previewLoading.value = false
  }
}

// 执行导入
const doImport = async () => {
  importing.value = true

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const res = await request.post(
      `/api/v1/import/upload?import_type=${selectedType.value}&sheet_name=${sheetName.value || ''}&update_existing=${updateExisting.value}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    importResult.value = res.data
    currentStep.value = 3

    if (res.data.success) {
      ElMessage.success(`成功导入 ${res.data.success_count} 条数据`)
    } else {
      ElMessage.error('部分数据导入失败，请查看详情')
    }
  } catch (e) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    importing.value = false
  }
}

// 重置
const resetImport = () => {
  currentStep.value = 0
  selectedType.value = ''
  selectedFile.value = null
  sheetName.value = ''
  updateExisting.value = false
  previewResult.value = null
  importResult.value = null
  uploadRef.value?.clearFiles()
}
</script>

<style scoped>
.data-import-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-content {
  min-height: 400px;
  padding: 20px;
}

.step-content h3 {
  margin-bottom: 24px;
  color: #333;
}

.import-type-card {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 16px;
}

.import-type-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.import-type-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.import-type-card h4 {
  margin: 12px 0 8px;
  color: #333;
}

.import-type-card p {
  color: #999;
  font-size: 13px;
  margin: 0 0 12px;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
}

.step-actions {
  margin-top: 30px;
  text-align: center;
}

.loading-box {
  text-align: center;
  padding: 60px;
  color: #999;
}

.loading-box .el-icon {
  font-size: 48px;
  color: #409eff;
}

.preview-info {
  margin-bottom: 16px;
  font-size: 14px;
  color: #666;
}

.result-box {
  text-align: center;
  padding: 40px;
}

.result-box.success .el-icon {
  color: #67c23a;
}

.result-box.error .el-icon {
  color: #f56c6c;
}

.result-box h2 {
  margin: 16px 0;
}

.result-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-top: 20px;
}

.stat-item {
  text-align: center;
}

.stat-item .label {
  display: block;
  color: #999;
  font-size: 13px;
}

.stat-item .value {
  display: block;
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.stat-item.success .value {
  color: #67c23a;
}

.stat-item.error .value {
  color: #f56c6c;
}

.help-content h4 {
  margin: 20px 0 10px;
  color: #333;
}

.help-content ol, .help-content ul {
  padding-left: 20px;
  color: #666;
}

.help-content li {
  margin: 8px 0;
}
</style>
