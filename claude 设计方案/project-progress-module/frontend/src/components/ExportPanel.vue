<template>
  <div class="export-panel">
    <!-- 导出按钮 -->
    <button class="btn-export" @click="showExportModal = true">
      <span class="icon">📥</span>
      <span>导出报表</span>
    </button>

    <!-- 导出弹窗 -->
    <div class="modal-overlay" v-if="showExportModal" @click.self="showExportModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>导出报表</h3>
          <button class="close-btn" @click="showExportModal = false">×</button>
        </div>
        
        <div class="modal-body">
          <!-- 报表类型选择 -->
          <div class="form-group">
            <label>报表类型</label>
            <div class="report-types">
              <div class="type-card" 
                   v-for="type in reportTypes" 
                   :key="type.value"
                   :class="{ active: selectedType === type.value }"
                   @click="selectedType = type.value">
                <span class="type-icon">{{ type.icon }}</span>
                <span class="type-name">{{ type.label }}</span>
              </div>
            </div>
          </div>

          <!-- 日期范围 -->
          <div class="form-group">
            <label>日期范围</label>
            <div class="date-presets">
              <button v-for="preset in datePresets" 
                      :key="preset.value"
                      :class="{ active: selectedPreset === preset.value }"
                      @click="applyDatePreset(preset.value)">
                {{ preset.label }}
              </button>
            </div>
            <div class="date-inputs">
              <input type="date" v-model="dateRange.start" />
              <span>至</span>
              <input type="date" v-model="dateRange.end" />
            </div>
          </div>

          <!-- 筛选条件 -->
          <div class="form-group" v-if="showWorkshopFilter">
            <label>车间</label>
            <select v-model="filters.workshopId">
              <option :value="null">全部车间</option>
              <option v-for="ws in workshops" :key="ws.id" :value="ws.id">
                {{ ws.name }}
              </option>
            </select>
          </div>

          <div class="form-group" v-if="showProjectFilter">
            <label>项目</label>
            <select v-model="filters.projectId">
              <option :value="null">全部项目</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">
                {{ p.name }}
              </option>
            </select>
          </div>

          <div class="form-group" v-if="showSupplierFilter">
            <label>供应商</label>
            <select v-model="filters.supplierId">
              <option :value="null">全部供应商</option>
              <option v-for="s in suppliers" :key="s.id" :value="s.id">
                {{ s.name }}
              </option>
            </select>
          </div>

          <!-- 导出格式 -->
          <div class="form-group">
            <label>导出格式</label>
            <div class="format-options">
              <label class="radio-item">
                <input type="radio" v-model="exportFormat" value="xlsx" />
                <span class="radio-label">
                  <span class="format-icon">📊</span>
                  Excel (.xlsx)
                </span>
              </label>
              <label class="radio-item">
                <input type="radio" v-model="exportFormat" value="pdf" disabled />
                <span class="radio-label disabled">
                  <span class="format-icon">📄</span>
                  PDF (开发中)
                </span>
              </label>
            </div>
          </div>

          <!-- 导出选项 -->
          <div class="form-group">
            <label>导出选项</label>
            <div class="export-options">
              <label class="checkbox-item">
                <input type="checkbox" v-model="exportOptions.includeCharts" />
                <span>包含图表</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="exportOptions.includeSummary" />
                <span>包含汇总</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="exportOptions.includeDetails" />
                <span>包含明细</span>
              </label>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="showExportModal = false">取消</button>
          <button class="btn-confirm" @click="handleExport" :disabled="exporting">
            <span v-if="exporting" class="loading-spinner"></span>
            <span v-else>{{ exporting ? '导出中...' : '确认导出' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 导出进度提示 -->
    <div class="export-toast" v-if="showToast" :class="toastType">
      <span class="toast-icon">{{ toastType === 'success' ? '✓' : toastType === 'error' ? '✗' : '⏳' }}</span>
      <span class="toast-message">{{ toastMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import request from '@/utils/request'

const props = defineProps({
  // 预设报表类型
  defaultType: {
    type: String,
    default: ''
  },
  // 可选报表类型
  availableTypes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['exported'])

// 状态
const showExportModal = ref(false)
const exporting = ref(false)
const showToast = ref(false)
const toastType = ref('info')
const toastMessage = ref('')

// 表单数据
const selectedType = ref(props.defaultType || 'kit_rate')
const selectedPreset = ref('thisMonth')
const exportFormat = ref('xlsx')

const dateRange = reactive({
  start: '',
  end: ''
})

const filters = reactive({
  workshopId: null,
  projectId: null,
  supplierId: null
})

const exportOptions = reactive({
  includeCharts: true,
  includeSummary: true,
  includeDetails: true
})

// 报表类型列表
const allReportTypes = [
  { value: 'kit_rate', label: '齐套率报表', icon: '📊', category: 'material' },
  { value: 'shortage_alert', label: '缺料预警报表', icon: '⚠️', category: 'material' },
  { value: 'supplier_delivery', label: '供应商交期报表', icon: '🚚', category: 'material' },
  { value: 'project_overview', label: '项目总览报表', icon: '📁', category: 'project' },
  { value: 'project_progress', label: '项目进度报表', icon: '📈', category: 'project' },
  { value: 'workload', label: '工时报表', icon: '⏱️', category: 'project' },
  { value: 'production', label: '生产报表', icon: '🏭', category: 'production' },
  { value: 'quality', label: '质量报表', icon: '✅', category: 'production' }
]

const reportTypes = computed(() => {
  if (props.availableTypes.length > 0) {
    return allReportTypes.filter(t => props.availableTypes.includes(t.value))
  }
  return allReportTypes
})

// 日期预设
const datePresets = [
  { value: 'today', label: '今日' },
  { value: 'thisWeek', label: '本周' },
  { value: 'thisMonth', label: '本月' },
  { value: 'lastMonth', label: '上月' },
  { value: 'thisQuarter', label: '本季度' },
  { value: 'thisYear', label: '本年' }
]

// 筛选条件显示逻辑
const showWorkshopFilter = computed(() => 
  ['kit_rate', 'shortage_alert', 'production', 'quality'].includes(selectedType.value)
)

const showProjectFilter = computed(() => 
  ['project_progress', 'workload'].includes(selectedType.value)
)

const showSupplierFilter = computed(() => 
  ['supplier_delivery'].includes(selectedType.value)
)

// 模拟数据
const workshops = ref([
  { id: 1, name: '装配车间' },
  { id: 2, name: '机加车间' },
  { id: 3, name: '调试车间' },
  { id: 4, name: '电气车间' }
])

const projects = ref([
  { id: 1, name: 'XX汽车传感器测试设备' },
  { id: 2, name: 'YY新能源电池检测线' },
  { id: 3, name: 'ZZ医疗器械测试系统' }
])

const suppliers = ref([
  { id: 1, name: '西门子代理' },
  { id: 2, name: 'ZZ自动化' },
  { id: 3, name: 'BB五金' }
])

// 应用日期预设
const applyDatePreset = (preset) => {
  selectedPreset.value = preset
  const today = new Date()
  let start, end
  
  switch (preset) {
    case 'today':
      start = end = today
      break
    case 'thisWeek':
      start = new Date(today)
      start.setDate(today.getDate() - today.getDay() + 1)
      end = new Date(start)
      end.setDate(start.getDate() + 6)
      break
    case 'thisMonth':
      start = new Date(today.getFullYear(), today.getMonth(), 1)
      end = new Date(today.getFullYear(), today.getMonth() + 1, 0)
      break
    case 'lastMonth':
      start = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      end = new Date(today.getFullYear(), today.getMonth(), 0)
      break
    case 'thisQuarter':
      const quarter = Math.floor(today.getMonth() / 3)
      start = new Date(today.getFullYear(), quarter * 3, 1)
      end = new Date(today.getFullYear(), quarter * 3 + 3, 0)
      break
    case 'thisYear':
      start = new Date(today.getFullYear(), 0, 1)
      end = new Date(today.getFullYear(), 11, 31)
      break
  }
  
  dateRange.start = formatDate(start)
  dateRange.end = formatDate(end)
}

const formatDate = (date) => {
  return date.toISOString().split('T')[0]
}

// 初始化日期
applyDatePreset('thisMonth')

// 显示提示
const showExportToast = (type, message, duration = 3000) => {
  toastType.value = type
  toastMessage.value = message
  showToast.value = true
  
  if (duration > 0) {
    setTimeout(() => {
      showToast.value = false
    }, duration)
  }
}

// 导出处理
const handleExport = async () => {
  if (!selectedType.value) {
    showExportToast('error', '请选择报表类型')
    return
  }
  
  if (!dateRange.start || !dateRange.end) {
    showExportToast('error', '请选择日期范围')
    return
  }
  
  exporting.value = true
  showExportToast('info', '正在生成报表，请稍候...', 0)
  
  try {
    // 构建查询参数
    const params = new URLSearchParams({
      start_date: dateRange.start,
      end_date: dateRange.end
    })
    
    if (filters.workshopId) params.append('workshop_id', filters.workshopId)
    if (filters.projectId) params.append('project_id', filters.projectId)
    if (filters.supplierId) params.append('supplier_id', filters.supplierId)
    
    // 调用导出API
    const response = await fetch(
      `/api/v1/export/excel/${selectedType.value}?${params.toString()}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    )
    
    if (!response.ok) {
      throw new Error('导出失败')
    }
    
    // 获取文件名
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = `报表_${dateRange.start}_${dateRange.end}.xlsx`
    if (contentDisposition) {
      const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?([^;\n]+)/i)
      if (match) {
        filename = decodeURIComponent(match[1].replace(/['"]/g, ''))
      }
    }
    
    // 下载文件
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    showExportToast('success', '报表导出成功')
    showExportModal.value = false
    
    emit('exported', {
      type: selectedType.value,
      dateRange: { ...dateRange },
      filters: { ...filters }
    })
    
  } catch (error) {
    console.error('导出失败:', error)
    showExportToast('error', '导出失败，请重试')
  } finally {
    exporting.value = false
  }
}

// 监听默认类型变化
watch(() => props.defaultType, (newVal) => {
  if (newVal) {
    selectedType.value = newVal
  }
})
</script>

<style scoped>
.export-panel {
  position: relative;
}

.btn-export {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #10B981, #059669);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-export:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.btn-export .icon {
  font-size: 16px;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  width: 600px;
  max-height: 90vh;
  background: #1E293B;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #94A3B8;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.modal-body {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #94A3B8;
  margin-bottom: 10px;
}

/* 报表类型选择 */
.report-types {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.type-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.type-card:hover {
  background: rgba(255, 255, 255, 0.1);
}

.type-card.active {
  border-color: #6366F1;
  background: rgba(99, 102, 241, 0.1);
}

.type-icon {
  font-size: 24px;
}

.type-name {
  font-size: 12px;
  color: #E2E8F0;
  text-align: center;
}

/* 日期选择 */
.date-presets {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.date-presets button {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #94A3B8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.date-presets button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.date-presets button.active {
  background: rgba(99, 102, 241, 0.2);
  border-color: #6366F1;
  color: white;
}

.date-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-inputs input {
  flex: 1;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 14px;
}

.date-inputs span {
  color: #64748B;
}

/* 下拉选择 */
.form-group select {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 14px;
}

/* 格式选择 */
.format-options {
  display: flex;
  gap: 16px;
}

.radio-item {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.radio-item input {
  display: none;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid transparent;
  border-radius: 10px;
  color: #E2E8F0;
  transition: all 0.2s;
}

.radio-item input:checked + .radio-label {
  border-color: #6366F1;
  background: rgba(99, 102, 241, 0.1);
}

.radio-label.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.format-icon {
  font-size: 20px;
}

/* 导出选项 */
.export-options {
  display: flex;
  gap: 20px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #E2E8F0;
}

.checkbox-item input {
  width: 18px;
  height: 18px;
  accent-color: #6366F1;
}

/* 底部按钮 */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-cancel {
  padding: 10px 24px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: #94A3B8;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.btn-confirm {
  padding: 10px 24px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-confirm:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 提示消息 */
.export-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: #1E293B;
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  z-index: 1100;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.export-toast.success {
  border-left: 4px solid #10B981;
}

.export-toast.error {
  border-left: 4px solid #EF4444;
}

.export-toast.info {
  border-left: 4px solid #6366F1;
}

.toast-icon {
  font-size: 18px;
}

.export-toast.success .toast-icon { color: #10B981; }
.export-toast.error .toast-icon { color: #EF4444; }
.export-toast.info .toast-icon { color: #6366F1; }

.toast-message {
  color: #E2E8F0;
  font-size: 14px;
}
</style>
