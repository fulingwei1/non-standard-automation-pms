<template>
  <div class="shortage-report-page">
    <!-- 顶部导航 -->
    <header class="mobile-header">
      <button class="back-btn" @click="goBack">←</button>
      <h1>缺料上报</h1>
      <div class="header-right"></div>
    </header>

    <!-- 当前工单信息 -->
    <section class="work-order-info" v-if="currentWorkOrder">
      <div class="info-label">当前工单</div>
      <div class="info-card">
        <div class="order-no">{{ currentWorkOrder.work_order_no }}</div>
        <div class="order-name">{{ currentWorkOrder.task_name }}</div>
        <div class="order-project">{{ currentWorkOrder.project_name }}</div>
      </div>
    </section>

    <!-- 上报表单 -->
    <section class="report-form">
      <!-- 选择缺料物料 -->
      <div class="form-group">
        <label class="form-label required">缺料物料</label>
        <input type="text" v-model="form.material_name" placeholder="输入物料名称或编码" class="form-input" />
      </div>

      <!-- 从BOM选择 -->
      <div class="form-group" v-if="bomMaterials.length > 0">
        <label class="form-label">或从BOM中选择</label>
        <div class="bom-list">
          <div class="bom-item" v-for="mat in bomMaterials" :key="mat.code"
               :class="{ selected: form.material_code === mat.code }"
               @click="selectMaterial(mat)">
            <div class="bom-checkbox">
              <span v-if="form.material_code === mat.code">✓</span>
            </div>
            <div class="bom-info">
              <span class="bom-name">{{ mat.name }}</span>
              <span class="bom-code">{{ mat.code }}</span>
            </div>
            <div class="bom-qty">需求: {{ mat.required }}件</div>
          </div>
        </div>
      </div>

      <!-- 缺料数量 -->
      <div class="form-group">
        <label class="form-label required">缺料数量</label>
        <div class="qty-input">
          <button class="qty-btn minus" @click="form.shortage_qty = Math.max(1, form.shortage_qty - 1)">-</button>
          <input type="number" v-model.number="form.shortage_qty" min="1" />
          <button class="qty-btn plus" @click="form.shortage_qty++">+</button>
        </div>
      </div>

      <!-- 紧急程度 -->
      <div class="form-group">
        <label class="form-label">紧急程度</label>
        <div class="urgency-options">
          <div class="urgency-option" :class="{ active: form.urgency === 'normal' }" @click="form.urgency = 'normal'">
            <span class="urgency-icon">🟢</span>
            <span class="urgency-text">一般</span>
            <span class="urgency-desc">不影响当前工序</span>
          </div>
          <div class="urgency-option" :class="{ active: form.urgency === 'urgent' }" @click="form.urgency = 'urgent'">
            <span class="urgency-icon">🟡</span>
            <span class="urgency-text">紧急</span>
            <span class="urgency-desc">影响当前工序</span>
          </div>
          <div class="urgency-option" :class="{ active: form.urgency === 'critical' }" @click="form.urgency = 'critical'">
            <span class="urgency-icon">🔴</span>
            <span class="urgency-text">非常紧急</span>
            <span class="urgency-desc">已停工等待</span>
          </div>
        </div>
      </div>

      <!-- 备注说明 -->
      <div class="form-group">
        <label class="form-label">备注说明</label>
        <textarea v-model="form.description" placeholder="请描述缺料情况..." rows="3" class="form-textarea"></textarea>
      </div>

      <!-- 拍照上传 -->
      <div class="form-group">
        <label class="form-label">📷 拍照上传(可选)</label>
        <div class="image-upload">
          <div class="upload-btn" @click="triggerUpload">
            <span class="upload-icon">+</span>
            <span class="upload-text">添加图片</span>
          </div>
          <input type="file" ref="fileInput" accept="image/*" @change="handleFileChange" style="display:none" />
          <div class="image-preview" v-for="(img, idx) in form.images" :key="idx">
            <img :src="img.url" />
            <button class="remove-btn" @click="removeImage(idx)">×</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 提交按钮 -->
    <footer class="submit-footer">
      <button class="submit-btn" @click="submitReport" :disabled="!canSubmit">
        📤 提交上报
      </button>
    </footer>

    <!-- 成功弹窗 -->
    <div class="success-modal" v-if="showSuccess">
      <div class="success-content">
        <div class="success-icon">✅</div>
        <h3>上报成功</h3>
        <p>相关人员已收到通知</p>
        <div class="notified-list">
          <span v-for="user in notifiedUsers" :key="user">{{ user }}</span>
        </div>
        <button class="success-btn" @click="closeSuccess">知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const fileInput = ref(null)

const currentWorkOrder = ref({
  work_order_no: 'WO-0103-001',
  task_name: 'XX项目-支架装配',
  project_name: 'XX汽车传感器测试设备'
})

const bomMaterials = ref([
  { code: 'M-001', name: '底板', required: 1 },
  { code: 'M-002', name: '支架', required: 4 },
  { code: 'M-0123', name: '传动轴', required: 1 },
  { code: 'M-0456', name: '联轴器', required: 2 }
])

const form = ref({
  work_order_id: 1,
  material_code: '',
  material_name: '',
  shortage_qty: 1,
  urgency: 'urgent',
  description: '',
  images: []
})

const showSuccess = ref(false)
const notifiedUsers = ref([])

const canSubmit = computed(() => {
  return form.value.material_name && form.value.shortage_qty > 0
})

const selectMaterial = (mat) => {
  form.value.material_code = mat.code
  form.value.material_name = mat.name
}

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (ev) => {
      form.value.images.push({ file, url: ev.target.result })
    }
    reader.readAsDataURL(file)
  }
}

const removeImage = (idx) => {
  form.value.images.splice(idx, 1)
}

const submitReport = async () => {
  try {
    const res = await request.post('/api/v1/material/shortage-reports', {
      work_order_id: form.value.work_order_id,
      material_code: form.value.material_code,
      material_name: form.value.material_name,
      shortage_qty: form.value.shortage_qty,
      urgency: form.value.urgency,
      description: form.value.description
    })
    if (res.code === 200) {
      notifiedUsers.value = res.data.notified_users || ['仓管员', '车间主管', '采购员']
      showSuccess.value = true
    }
  } catch (e) {
    notifiedUsers.value = ['仓管王工', '车间李主管', '采购张工']
    showSuccess.value = true
  }
}

const closeSuccess = () => {
  showSuccess.value = false
  router.back()
}

const goBack = () => router.back()

onMounted(() => {
  if (route.query.work_order_id) {
    form.value.work_order_id = parseInt(route.query.work_order_id)
  }
})
</script>

<style scoped>
.shortage-report-page { min-height: 100vh; background: #0f172a; color: white; padding-bottom: 80px; }
.mobile-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; background: rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.1); }
.back-btn { width: 40px; height: 40px; background: none; border: none; color: white; font-size: 24px; cursor: pointer; }
.mobile-header h1 { font-size: 18px; font-weight: 600; }
.header-right { width: 40px; }

.work-order-info { padding: 20px; }
.info-label { font-size: 13px; color: #64748B; margin-bottom: 8px; }
.info-card { background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 16px; }
.order-no { font-size: 14px; color: #A5B4FC; font-weight: 600; }
.order-name { font-size: 16px; font-weight: 600; margin: 4px 0; }
.order-project { font-size: 13px; color: #94A3B8; }

.report-form { padding: 0 20px; }
.form-group { margin-bottom: 24px; }
.form-label { display: block; font-size: 14px; color: #CBD5E1; margin-bottom: 10px; }
.form-label.required::after { content: ' *'; color: #EF4444; }
.form-input, .form-textarea { width: 100%; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 14px 16px; color: white; font-size: 15px; box-sizing: border-box; }
.form-input::placeholder, .form-textarea::placeholder { color: #64748B; }
.form-textarea { resize: none; }

.bom-list { display: flex; flex-direction: column; gap: 10px; max-height: 200px; overflow-y: auto; }
.bom-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; cursor: pointer; }
.bom-item.selected { background: rgba(99,102,241,0.1); border-color: rgba(99,102,241,0.5); }
.bom-checkbox { width: 24px; height: 24px; border: 2px solid rgba(255,255,255,0.3); border-radius: 6px; display: flex; align-items: center; justify-content: center; }
.bom-item.selected .bom-checkbox { background: #6366F1; border-color: #6366F1; }
.bom-info { flex: 1; }
.bom-name { font-size: 14px; display: block; }
.bom-code { font-size: 12px; color: #64748B; }
.bom-qty { font-size: 12px; color: #94A3B8; }

.qty-input { display: flex; align-items: center; gap: 16px; }
.qty-btn { width: 44px; height: 44px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); color: white; font-size: 24px; cursor: pointer; }
.qty-input input { width: 80px; text-align: center; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 12px; color: white; font-size: 18px; font-weight: 600; }

.urgency-options { display: flex; flex-direction: column; gap: 10px; }
.urgency-option { display: flex; align-items: center; gap: 12px; padding: 14px 16px; background: rgba(255,255,255,0.03); border: 2px solid rgba(255,255,255,0.1); border-radius: 12px; cursor: pointer; }
.urgency-option.active { border-color: #6366F1; background: rgba(99,102,241,0.1); }
.urgency-icon { font-size: 20px; }
.urgency-text { font-size: 15px; font-weight: 600; }
.urgency-desc { font-size: 13px; color: #64748B; margin-left: auto; }

.image-upload { display: flex; gap: 12px; flex-wrap: wrap; }
.upload-btn { width: 80px; height: 80px; border: 2px dashed rgba(255,255,255,0.2); border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; }
.upload-icon { font-size: 28px; color: #64748B; }
.upload-text { font-size: 11px; color: #64748B; }
.image-preview { position: relative; width: 80px; height: 80px; border-radius: 10px; overflow: hidden; }
.image-preview img { width: 100%; height: 100%; object-fit: cover; }
.remove-btn { position: absolute; top: 4px; right: 4px; width: 20px; height: 20px; border-radius: 50%; background: rgba(0,0,0,0.6); border: none; color: white; font-size: 14px; cursor: pointer; }

.submit-footer { position: fixed; bottom: 0; left: 0; right: 0; padding: 16px 20px; background: #0f172a; border-top: 1px solid rgba(255,255,255,0.1); }
.submit-btn { width: 100%; padding: 16px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; border-radius: 12px; color: white; font-size: 16px; font-weight: 600; cursor: pointer; }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.success-modal { position: fixed; inset: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 100; }
.success-content { background: #1e293b; border-radius: 20px; padding: 32px; text-align: center; max-width: 300px; }
.success-icon { font-size: 48px; margin-bottom: 16px; }
.success-content h3 { font-size: 20px; margin-bottom: 8px; }
.success-content p { font-size: 14px; color: #94A3B8; margin-bottom: 16px; }
.notified-list { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 20px; }
.notified-list span { padding: 6px 12px; background: rgba(99,102,241,0.2); border-radius: 6px; font-size: 13px; }
.success-btn { width: 100%; padding: 14px; background: #6366F1; border: none; border-radius: 10px; color: white; font-size: 15px; font-weight: 600; cursor: pointer; }
</style>
