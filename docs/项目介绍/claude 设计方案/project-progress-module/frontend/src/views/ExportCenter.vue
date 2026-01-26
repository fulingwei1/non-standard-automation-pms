<template>
  <div class="export-center-page">
    <header class="page-header">
      <h1>报表中心</h1>
      <p class="subtitle">导出各类统计报表</p>
    </header>

    <!-- 物料报表 -->
    <section class="category-section">
      <h2><span>📦</span> 物料报表</h2>
      <div class="report-cards">
        <div class="report-card" v-for="r in materialReports" :key="r.type" @click="exportReport(r)">
          <span class="card-icon">{{ r.icon }}</span>
          <div class="card-info">
            <h3>{{ r.name }}</h3>
            <p>{{ r.desc }}</p>
          </div>
          <button class="btn-export">导出</button>
        </div>
      </div>
    </section>

    <!-- 项目报表 -->
    <section class="category-section">
      <h2><span>📁</span> 项目报表</h2>
      <div class="report-cards">
        <div class="report-card" v-for="r in projectReports" :key="r.type" @click="exportReport(r)">
          <span class="card-icon">{{ r.icon }}</span>
          <div class="card-info">
            <h3>{{ r.name }}</h3>
            <p>{{ r.desc }}</p>
          </div>
          <button class="btn-export">导出</button>
        </div>
      </div>
    </section>

    <!-- 生产报表 -->
    <section class="category-section">
      <h2><span>🏭</span> 生产报表</h2>
      <div class="report-cards">
        <div class="report-card" v-for="r in productionReports" :key="r.type" @click="exportReport(r)">
          <span class="card-icon">{{ r.icon }}</span>
          <div class="card-info">
            <h3>{{ r.name }}</h3>
            <p>{{ r.desc }}</p>
          </div>
          <button class="btn-export">导出</button>
        </div>
      </div>
    </section>

    <!-- 导出历史 -->
    <section class="history-section">
      <h2><span>📋</span> 导出历史</h2>
      <div class="history-list">
        <div class="history-item" v-for="h in history" :key="h.id">
          <span class="file-icon">📄</span>
          <div class="file-info">
            <span class="file-name">{{ h.name }}</span>
            <span class="file-meta">{{ h.type }} · {{ h.time }} · {{ h.size }}</span>
          </div>
          <button class="btn-download" @click="download(h)">下载</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const materialReports = [
  { type: 'kit_rate', name: '齐套率报表', icon: '📊', desc: '工单物料齐套率统计' },
  { type: 'shortage_alert', name: '缺料预警报表', icon: '⚠️', desc: '缺料预警处理统计' },
  { type: 'supplier_delivery', name: '供应商交期', icon: '🚚', desc: '供应商交期准时率' }
]

const projectReports = [
  { type: 'project_overview', name: '项目总览', icon: '📁', desc: '项目状态及进度汇总' },
  { type: 'project_progress', name: '进度分析', icon: '📈', desc: '计划vs实际进度' },
  { type: 'workload', name: '工时报表', icon: '⏱️', desc: '部门人员工时统计' }
]

const productionReports = [
  { type: 'production', name: '生产统计', icon: '🏭', desc: '工单完成及产能分析' },
  { type: 'quality', name: '质量统计', icon: '✅', desc: '合格率及问题分析' }
]

const history = ref([
  { id: 1, name: '齐套率报表_2025-01.xlsx', type: '齐套率', time: '2025-01-03 14:30', size: '45KB' },
  { id: 2, name: '生产统计_2024-12.xlsx', type: '生产统计', time: '2025-01-02 10:15', size: '128KB' }
])

const exportReport = (report) => {
  const today = new Date().toISOString().split('T')[0]
  const monthStart = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]
  window.open(`/api/v1/export/excel/${report.type}?start_date=${monthStart}&end_date=${today}`, '_blank')
}

const download = (h) => alert(`下载: ${h.name}`)
</script>

<style scoped>
.export-center-page { min-height: 100vh; background: #0f172a; color: white; padding: 24px 32px; }
.page-header { margin-bottom: 32px; }
.page-header h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }

.category-section { margin-bottom: 32px; }
.category-section h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

.report-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.report-card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 16px; border: 1px solid rgba(255,255,255,0.1); cursor: pointer; transition: all 0.2s; }
.report-card:hover { border-color: rgba(99,102,241,0.5); transform: translateY(-2px); }
.card-icon { font-size: 32px; }
.card-info { flex: 1; }
.card-info h3 { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.card-info p { font-size: 13px; color: #94A3B8; }
.btn-export { padding: 8px 16px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; border-radius: 8px; color: white; cursor: pointer; }

.history-section { background: rgba(255,255,255,0.03); border-radius: 16px; padding: 24px; }
.history-section h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.history-list { display: flex; flex-direction: column; gap: 12px; }
.history-item { display: flex; align-items: center; gap: 16px; padding: 16px; background: rgba(255,255,255,0.02); border-radius: 12px; }
.file-icon { font-size: 24px; }
.file-info { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.file-name { font-size: 14px; font-weight: 500; }
.file-meta { font-size: 12px; color: #64748B; }
.btn-download { padding: 6px 16px; background: rgba(99,102,241,0.2); border: none; border-radius: 6px; color: #A5B4FC; cursor: pointer; }
</style>
