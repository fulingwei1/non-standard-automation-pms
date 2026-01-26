<template>
  <div class="equipment-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-left">
        <h1>设备管理</h1>
        <p class="subtitle">非标设备全生命周期管理</p>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <input type="text" v-model="searchKeyword" placeholder="搜索设备..." />
          <span class="search-icon">🔍</span>
        </div>
        <button class="btn-primary" @click="showCreateModal = true">
          <span>+</span> 新建设备
        </button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <section class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon">🏭</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">设备总数</div>
        </div>
      </div>
      <div class="stat-card designing">
        <div class="stat-icon">📐</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.designing }}</div>
          <div class="stat-label">设计/制造中</div>
        </div>
      </div>
      <div class="stat-card running">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.running }}</div>
          <div class="stat-label">运行中</div>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">⚠️</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.maintenance }}</div>
          <div class="stat-label">维护/故障</div>
        </div>
      </div>
    </section>

    <!-- 筛选器 -->
    <section class="filters">
      <div class="filter-tabs">
        <button :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">全部</button>
        <button :class="{ active: statusFilter === 'in_progress' }" @click="statusFilter = 'in_progress'">制造中</button>
        <button :class="{ active: statusFilter === 'debugging' }" @click="statusFilter = 'debugging'">调试中</button>
        <button :class="{ active: statusFilter === 'running' }" @click="statusFilter = 'running'">运行中</button>
        <button :class="{ active: statusFilter === 'maintenance' }" @click="statusFilter = 'maintenance'">维护中</button>
      </div>
      <div class="filter-selects">
        <select v-model="typeFilter">
          <option value="">全部类型</option>
          <option value="test">测试设备</option>
          <option value="assembly">装配线</option>
          <option value="inspect">检测设备</option>
        </select>
        <select v-model="projectFilter">
          <option value="">全部项目</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
    </section>

    <!-- 设备列表 -->
    <section class="equipment-list">
      <div class="equipment-card" v-for="eq in equipments" :key="eq.id" @click="viewDetail(eq)">
        <div class="card-header">
          <div class="eq-info">
            <span class="eq-no">{{ eq.equipment_no }}</span>
            <span class="eq-status" :class="eq.status">{{ eq.status_label }}</span>
          </div>
          <div class="eq-type">{{ eq.equipment_type }}</div>
        </div>
        
        <h3 class="eq-name">{{ eq.equipment_name }}</h3>
        
        <div class="eq-meta">
          <span class="meta-item">
            <span class="meta-icon">📁</span>
            {{ eq.project_name }}
          </span>
          <span class="meta-item">
            <span class="meta-icon">🏢</span>
            {{ eq.customer_name }}
          </span>
        </div>

        <!-- 进度条(制造中) -->
        <div class="progress-section" v-if="eq.status !== 'running'">
          <div class="progress-header">
            <span>整体进度</span>
            <span class="progress-value">{{ eq.progress }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: eq.progress + '%' }"></div>
          </div>
          <div class="progress-stages">
            <div class="stage" :class="{ done: eq.design_completion === 100 }">
              <span class="stage-dot"></span>
              <span class="stage-name">设计</span>
            </div>
            <div class="stage" :class="{ done: eq.manufacture_completion === 100 }">
              <span class="stage-dot"></span>
              <span class="stage-name">加工</span>
            </div>
            <div class="stage" :class="{ done: eq.assembly_completion === 100 }">
              <span class="stage-dot"></span>
              <span class="stage-name">装配</span>
            </div>
            <div class="stage" :class="{ done: eq.debug_completion === 100 }">
              <span class="stage-dot"></span>
              <span class="stage-name">调试</span>
            </div>
          </div>
        </div>

        <!-- 运行信息(运行中) -->
        <div class="running-info" v-else>
          <div class="info-item">
            <span class="info-label">运行时长</span>
            <span class="info-value">{{ eq.running_hours }}h</span>
          </div>
          <div class="info-item">
            <span class="info-label">上次维护</span>
            <span class="info-value">{{ eq.last_maintenance_date || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">下次维护</span>
            <span class="info-value" :class="{ warning: isMaintenanceDue(eq) }">
              {{ eq.next_maintenance_date || '-' }}
            </span>
          </div>
        </div>

        <div class="card-footer">
          <span class="location">📍 {{ eq.current_location }}</span>
          <div class="actions">
            <button class="btn-icon" @click.stop="viewDetail(eq)">详情</button>
            <button class="btn-icon" @click.stop="showMaintenanceModal(eq)">维护</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 设备详情弹窗 -->
    <div class="modal-overlay" v-if="showDetail" @click.self="showDetail = false">
      <div class="modal-content detail-modal">
        <div class="modal-header">
          <div class="detail-title">
            <h3>{{ currentEquipment?.equipment_name }}</h3>
            <span class="eq-status" :class="currentEquipment?.status">{{ currentEquipment?.status_label }}</span>
          </div>
          <button class="close-btn" @click="showDetail = false">×</button>
        </div>
        
        <div class="modal-body">
          <!-- 标签页 -->
          <div class="detail-tabs">
            <button :class="{ active: detailTab === 'info' }" @click="detailTab = 'info'">基本信息</button>
            <button :class="{ active: detailTab === 'components' }" @click="detailTab = 'components'">部件清单</button>
            <button :class="{ active: detailTab === 'maintenance' }" @click="detailTab = 'maintenance'">维护记录</button>
            <button :class="{ active: detailTab === 'faults' }" @click="detailTab = 'faults'">故障记录</button>
            <button :class="{ active: detailTab === 'documents' }" @click="detailTab = 'documents'">文档附件</button>
          </div>

          <!-- 基本信息 -->
          <div class="tab-content" v-if="detailTab === 'info'">
            <div class="info-grid">
              <div class="info-section">
                <h4>设备信息</h4>
                <div class="info-row"><span>设备编号</span><span>{{ currentEquipment?.equipment_no }}</span></div>
                <div class="info-row"><span>设备类型</span><span>{{ currentEquipment?.equipment_type }}</span></div>
                <div class="info-row"><span>外形尺寸</span><span>3200x2400x2100mm</span></div>
                <div class="info-row"><span>重量</span><span>2500kg</span></div>
                <div class="info-row"><span>功率</span><span>15kW</span></div>
              </div>
              <div class="info-section">
                <h4>项目信息</h4>
                <div class="info-row"><span>所属项目</span><span>{{ currentEquipment?.project_name }}</span></div>
                <div class="info-row"><span>客户</span><span>{{ currentEquipment?.customer_name }}</span></div>
                <div class="info-row"><span>安装地点</span><span>{{ currentEquipment?.current_location }}</span></div>
              </div>
            </div>
            
            <div class="specs-section">
              <h4>技术规格</h4>
              <div class="specs-grid">
                <div class="spec-item"><span>测试工位</span><span>8工位</span></div>
                <div class="spec-item"><span>节拍</span><span>30秒/件</span></div>
                <div class="spec-item"><span>精度</span><span>±0.01mm</span></div>
                <div class="spec-item"><span>电压</span><span>AC380V</span></div>
                <div class="spec-item"><span>气压</span><span>0.5-0.7MPa</span></div>
              </div>
            </div>
          </div>

          <!-- 部件清单 -->
          <div class="tab-content" v-if="detailTab === 'components'">
            <div class="component-tree">
              <div class="tree-item" v-for="comp in components" :key="comp.id">
                <div class="tree-node" @click="comp.expanded = !comp.expanded">
                  <span class="expand-icon">{{ comp.children?.length ? (comp.expanded ? '▼' : '▶') : '•' }}</span>
                  <span class="comp-name">{{ comp.name }}</span>
                  <span class="comp-type">{{ comp.type }}</span>
                  <span class="comp-status" :class="comp.status">{{ comp.status }}</span>
                </div>
                <div class="tree-children" v-if="comp.expanded && comp.children">
                  <div class="tree-child" v-for="child in comp.children" :key="child.id">
                    <span class="child-name">{{ child.name }}</span>
                    <span class="child-qty">x{{ child.quantity }}</span>
                    <span class="child-status" :class="child.status">{{ child.status }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 维护记录 -->
          <div class="tab-content" v-if="detailTab === 'maintenance'">
            <div class="maintenance-list">
              <div class="maintenance-item" v-for="m in maintenanceRecords" :key="m.id">
                <div class="m-header">
                  <span class="m-type" :class="m.maintenance_type">{{ m.maintenance_type_label }}</span>
                  <span class="m-date">{{ m.maintenance_date }}</span>
                </div>
                <div class="m-content">{{ m.description }}</div>
                <div class="m-footer">
                  <span>技术员: {{ m.technician_name }}</span>
                  <span>工时: {{ m.work_hours }}h</span>
                  <span>费用: ¥{{ m.parts_cost + m.labor_cost }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 故障记录 -->
          <div class="tab-content" v-if="detailTab === 'faults'">
            <div class="fault-list">
              <div class="fault-item" v-for="f in faultRecords" :key="f.id">
                <div class="f-header">
                  <span class="f-level" :class="f.fault_level">{{ f.fault_level_label }}</span>
                  <span class="f-type">{{ f.fault_type }}</span>
                  <span class="f-status" :class="f.status">{{ f.status === 'resolved' ? '已解决' : '待处理' }}</span>
                </div>
                <div class="f-desc">{{ f.fault_description }}</div>
                <div class="f-footer">
                  <span>发生时间: {{ f.fault_time }}</span>
                  <span v-if="f.resolution_time">解决时间: {{ f.resolution_time }}</span>
                  <span v-if="f.downtime_hours">停机: {{ f.downtime_hours }}h</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 文档附件 -->
          <div class="tab-content" v-if="detailTab === 'documents'">
            <div class="doc-categories">
              <div class="doc-category" v-for="cat in documentCategories" :key="cat.type">
                <h5>{{ cat.type_label }}</h5>
                <div class="doc-list">
                  <div class="doc-item" v-for="doc in cat.documents" :key="doc.id">
                    <span class="doc-icon">📄</span>
                    <span class="doc-name">{{ doc.name }}</span>
                    <span class="doc-version">{{ doc.version }}</span>
                    <span class="doc-size">{{ doc.size }}</span>
                    <button class="btn-download">下载</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

// 状态
const searchKeyword = ref('')
const statusFilter = ref('all')
const typeFilter = ref('')
const projectFilter = ref('')
const showDetail = ref(false)
const showCreateModal = ref(false)
const currentEquipment = ref(null)
const detailTab = ref('info')

// 统计
const stats = reactive({
  total: 45,
  designing: 18,
  running: 25,
  maintenance: 2
})

// 项目列表
const projects = ref([
  { id: 1, name: 'XX汽车传感器测试设备项目' },
  { id: 2, name: 'YY新能源电池检测线项目' }
])

// 设备列表
const equipments = ref([
  {
    id: 1,
    equipment_no: 'EQ-2025-001',
    equipment_name: 'XX汽车传感器自动测试设备',
    equipment_type: '自动化测试设备',
    project_name: 'XX汽车传感器测试设备项目',
    customer_name: 'XX汽车',
    status: 'debugging',
    status_label: '调试中',
    current_location: '调试车间-工位A3',
    progress: 85,
    design_completion: 100,
    manufacture_completion: 95,
    assembly_completion: 90,
    debug_completion: 60
  },
  {
    id: 2,
    equipment_no: 'EQ-2024-028',
    equipment_name: 'YY电池包EOL测试线',
    equipment_type: '测试产线',
    project_name: 'YY新能源电池检测线项目',
    customer_name: 'YY新能源',
    status: 'running',
    status_label: '运行中',
    current_location: 'YY新能源-生产车间',
    progress: 100,
    running_hours: 2580,
    last_maintenance_date: '2024-12-15',
    next_maintenance_date: '2025-01-15'
  }
])

// 部件
const components = ref([
  { id: 1, name: '机架总成', type: '结构件', status: 'completed', expanded: true,
    children: [
      { id: 11, name: '底座', quantity: 1, status: 'completed' },
      { id: 12, name: '立柱', quantity: 4, status: 'completed' }
    ]
  },
  { id: 2, name: '传动系统', type: '机械系统', status: 'in_progress', expanded: false,
    children: [
      { id: 21, name: '伺服电机', quantity: 6, status: 'arrived' },
      { id: 22, name: '减速机', quantity: 6, status: 'arrived' }
    ]
  }
])

// 维护记录
const maintenanceRecords = ref([
  { id: 1, maintenance_type: 'preventive', maintenance_type_label: '预防性维护',
    maintenance_date: '2024-12-15', description: '季度保养',
    technician_name: '李工', work_hours: 4, parts_cost: 500, labor_cost: 800 }
])

// 故障记录
const faultRecords = ref([
  { id: 1, fault_level: 'moderate', fault_level_label: '中等', fault_type: '机械故障',
    fault_description: 'X轴伺服电机异响', fault_time: '2024-12-20 14:30',
    status: 'resolved', resolution_time: '2024-12-20 18:30', downtime_hours: 4 }
])

// 文档分类
const documentCategories = ref([
  { type: 'design', type_label: '设计文档', documents: [
    { id: 1, name: '总体设计方案.pdf', version: 'V1.2', size: '2.5MB' }
  ]},
  { type: 'drawing', type_label: '图纸', documents: [
    { id: 3, name: '机架装配图.dwg', version: 'V1.0', size: '8.5MB' }
  ]}
])

const isMaintenanceDue = (eq) => {
  if (!eq.next_maintenance_date) return false
  const dueDate = new Date(eq.next_maintenance_date)
  const today = new Date()
  const diffDays = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24))
  return diffDays <= 7
}

const viewDetail = (eq) => {
  currentEquipment.value = eq
  detailTab.value = 'info'
  showDetail.value = true
}

const showMaintenanceModal = (eq) => {
  alert(`维护设备: ${eq.equipment_name}`)
}
</script>

<style scoped>
.equipment-page { min-height: 100vh; background: #0f172a; color: white; padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-header h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.header-actions { display: flex; gap: 16px; align-items: center; }
.search-box { position: relative; }
.search-box input { padding: 10px 16px 10px 40px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; color: white; width: 250px; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); }
.btn-primary { padding: 10px 20px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; border-radius: 10px; color: white; cursor: pointer; display: flex; align-items: center; gap: 8px; }

.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 16px; border: 1px solid rgba(255,255,255,0.1); }
.stat-card.designing { border-color: rgba(99,102,241,0.3); }
.stat-card.running { border-color: rgba(16,185,129,0.3); }
.stat-card.warning { border-color: rgba(245,158,11,0.3); }
.stat-icon { font-size: 28px; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-card.running .stat-value { color: #10B981; }
.stat-card.warning .stat-value { color: #F59E0B; }
.stat-label { font-size: 13px; color: #94A3B8; }

.filters { display: flex; justify-content: space-between; margin-bottom: 20px; }
.filter-tabs { display: flex; gap: 8px; }
.filter-tabs button { padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #94A3B8; cursor: pointer; }
.filter-tabs button.active { background: rgba(99,102,241,0.2); border-color: #6366F1; color: white; }
.filter-selects { display: flex; gap: 12px; }
.filter-selects select { padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; }

.equipment-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.equipment-card { background: rgba(255,255,255,0.03); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1); cursor: pointer; transition: all 0.2s; }
.equipment-card:hover { border-color: rgba(99,102,241,0.5); transform: translateY(-2px); }
.card-header { display: flex; justify-content: space-between; margin-bottom: 12px; }
.eq-info { display: flex; align-items: center; gap: 12px; }
.eq-no { font-size: 14px; color: #94A3B8; }
.eq-status { padding: 4px 10px; border-radius: 6px; font-size: 12px; }
.eq-status.debugging { background: rgba(245,158,11,0.2); color: #F59E0B; }
.eq-status.running { background: rgba(16,185,129,0.2); color: #10B981; }
.eq-status.manufacturing { background: rgba(99,102,241,0.2); color: #A5B4FC; }
.eq-type { font-size: 13px; color: #64748B; }
.eq-name { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.eq-meta { display: flex; gap: 20px; margin-bottom: 16px; }
.meta-item { font-size: 13px; color: #94A3B8; display: flex; align-items: center; gap: 6px; }

.progress-section { margin-bottom: 16px; }
.progress-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; }
.progress-value { color: #6366F1; font-weight: 600; }
.progress-bar { height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6); border-radius: 4px; }
.progress-stages { display: flex; justify-content: space-between; margin-top: 12px; }
.stage { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #64748B; }
.stage.done { color: #10B981; }
.stage-dot { width: 8px; height: 8px; border-radius: 50%; background: #64748B; }
.stage.done .stage-dot { background: #10B981; }

.running-info { display: flex; gap: 20px; margin-bottom: 16px; }
.info-item { flex: 1; background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; }
.info-label { font-size: 12px; color: #64748B; display: block; margin-bottom: 4px; }
.info-value { font-size: 16px; font-weight: 600; }
.info-value.warning { color: #F59E0B; }

.card-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.05); }
.location { font-size: 13px; color: #64748B; }
.actions { display: flex; gap: 8px; }
.btn-icon { padding: 6px 12px; background: rgba(255,255,255,0.05); border: none; border-radius: 6px; color: #94A3B8; cursor: pointer; font-size: 12px; }
.btn-icon:hover { background: rgba(255,255,255,0.1); color: white; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.detail-modal { width: 900px; max-height: 85vh; background: #1E293B; border-radius: 16px; overflow: hidden; }
.modal-header { display: flex; justify-content: space-between; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.detail-title { display: flex; align-items: center; gap: 16px; }
.detail-title h3 { font-size: 18px; }
.close-btn { width: 32px; height: 32px; border: none; background: rgba(255,255,255,0.1); border-radius: 8px; color: #94A3B8; font-size: 20px; cursor: pointer; }
.modal-body { padding: 24px; max-height: 70vh; overflow-y: auto; }

.detail-tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px; }
.detail-tabs button { padding: 8px 16px; background: transparent; border: none; color: #94A3B8; cursor: pointer; border-radius: 6px; }
.detail-tabs button.active { background: rgba(99,102,241,0.2); color: white; }

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
.info-section h4 { font-size: 14px; color: #94A3B8; margin-bottom: 12px; }
.info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; }
.info-row span:first-child { color: #64748B; }

.specs-section h4 { font-size: 14px; color: #94A3B8; margin-bottom: 12px; }
.specs-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
.spec-item { background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; text-align: center; }
.spec-item span:first-child { display: block; font-size: 12px; color: #64748B; margin-bottom: 4px; }
.spec-item span:last-child { font-size: 14px; font-weight: 600; }

.component-tree { background: rgba(0,0,0,0.2); border-radius: 12px; padding: 16px; }
.tree-node { display: flex; align-items: center; gap: 12px; padding: 10px; background: rgba(255,255,255,0.02); border-radius: 8px; margin-bottom: 8px; cursor: pointer; }
.expand-icon { width: 16px; color: #64748B; }
.comp-name { flex: 1; }
.comp-type { font-size: 12px; color: #64748B; }
.comp-status { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.comp-status.completed { background: rgba(16,185,129,0.2); color: #10B981; }
.comp-status.in_progress { background: rgba(245,158,11,0.2); color: #F59E0B; }
.tree-children { margin-left: 28px; }
.tree-child { display: flex; align-items: center; gap: 12px; padding: 8px 10px; font-size: 13px; }
.child-name { flex: 1; color: #94A3B8; }
.child-qty { color: #64748B; }
.child-status { font-size: 11px; padding: 2px 6px; border-radius: 4px; }
.child-status.completed, .child-status.arrived, .child-status.installed { background: rgba(16,185,129,0.2); color: #10B981; }
.child-status.in_transit { background: rgba(99,102,241,0.2); color: #A5B4FC; }

.maintenance-list, .fault-list { display: flex; flex-direction: column; gap: 12px; }
.maintenance-item, .fault-item { background: rgba(255,255,255,0.02); border-radius: 12px; padding: 16px; }
.m-header, .f-header { display: flex; gap: 12px; margin-bottom: 8px; }
.m-type, .f-level { padding: 4px 10px; border-radius: 6px; font-size: 12px; }
.m-type.preventive { background: rgba(16,185,129,0.2); color: #10B981; }
.f-level.moderate { background: rgba(245,158,11,0.2); color: #F59E0B; }
.m-date, .f-type { font-size: 13px; color: #94A3B8; }
.f-status.resolved { color: #10B981; }
.m-content, .f-desc { font-size: 14px; margin-bottom: 8px; }
.m-footer, .f-footer { display: flex; gap: 20px; font-size: 12px; color: #64748B; }

.doc-category { margin-bottom: 20px; }
.doc-category h5 { font-size: 14px; color: #94A3B8; margin-bottom: 12px; }
.doc-list { display: flex; flex-direction: column; gap: 8px; }
.doc-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(255,255,255,0.02); border-radius: 8px; }
.doc-icon { font-size: 20px; }
.doc-name { flex: 1; font-size: 14px; }
.doc-version { font-size: 12px; color: #6366F1; }
.doc-size { font-size: 12px; color: #64748B; }
.btn-download { padding: 6px 12px; background: rgba(99,102,241,0.2); border: none; border-radius: 6px; color: #A5B4FC; cursor: pointer; font-size: 12px; }
</style>
