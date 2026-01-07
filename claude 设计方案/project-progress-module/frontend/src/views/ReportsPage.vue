<template>
  <div class="reports-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>报表中心</h1>
          <p class="header-subtitle">基于角色视角的智能报表生成</p>
        </div>
        <div class="header-right">
          <div class="role-selector">
            <span class="selector-label">当前视角</span>
            <select v-model="currentRole" class="role-select">
              <option v-for="role in roles" :key="role.code" :value="role.code">
                {{ role.name }} ({{ role.scope }})
              </option>
            </select>
          </div>
        </div>
      </div>
    </header>

    <!-- 报表类型网格 -->
    <section class="report-types-section">
      <h2>选择报表类型</h2>
      <div class="report-types-grid">
        <div class="report-type-card" 
             v-for="report in availableReports" 
             :key="report.code"
             :class="{ selected: selectedReport === report.code }"
             @click="selectReport(report.code)">
          <div class="card-icon" :style="{ background: report.iconBg }">📊</div>
          <h3>{{ report.name }}</h3>
          <p>{{ report.description }}</p>
          <span class="period-badge">{{ report.period }}</span>
        </div>
      </div>
    </section>

    <!-- 报表生成区 -->
    <section class="report-generate-section" v-if="selectedReport">
      <div class="generate-header">
        <h2>{{ selectedReportConfig?.name }}</h2>
        <div class="generate-actions">
          <select v-model="period" class="period-select">
            <option value="weekly">周报</option>
            <option value="monthly">月报</option>
          </select>
          <button class="btn-primary" @click="generateReport" :disabled="loading">
            {{ loading ? '生成中...' : '生成报表' }}
          </button>
        </div>
      </div>

      <!-- 报表内容 -->
      <div class="report-content" v-if="reportData">
        <div class="report-header-card">
          <h2>{{ reportData.title }}</h2>
          <p>{{ reportData.subtitle }} | 角色：{{ currentRoleConfig?.name }} | 范围：{{ reportData.scope_description }}</p>
        </div>

        <!-- 核心指标 -->
        <div class="metrics-grid">
          <div class="metric-card" v-for="metric in reportData.metrics" :key="metric.id">
            <div class="metric-name">{{ metric.name }}</div>
            <div class="metric-value">{{ metric.value }}{{ metric.unit }}</div>
            <div class="metric-status" :class="metric.status">{{ metric.status }}</div>
          </div>
        </div>

        <!-- 预警信息 -->
        <div class="alerts-section" v-if="reportData.alerts?.length">
          <h3>预警信息 ({{ reportData.alerts.length }})</h3>
          <div class="alert-item" v-for="alert in reportData.alerts" :key="alert.id" :class="alert.level">
            <strong>【{{ alert.level }}】{{ alert.title }}</strong>
            <p>{{ alert.description }}</p>
            <div class="alert-actions" v-if="alert.suggested_actions?.length">
              建议：{{ alert.suggested_actions.join('、') }}
            </div>
          </div>
        </div>

        <!-- 建议 -->
        <div class="recommendations-section" v-if="reportData.recommendations?.length">
          <h3>智能建议</h3>
          <div class="rec-item" v-for="rec in reportData.recommendations" :key="rec.id">
            <div class="rec-score">{{ rec.priority_score.toFixed(1) }}</div>
            <div class="rec-content">
              <h4>{{ rec.title }}</h4>
              <p>{{ rec.description }}</p>
              <span>影响: {{ rec.impact }} | 投入: {{ rec.effort }}</span>
            </div>
          </div>
        </div>

        <!-- 导出 -->
        <div class="export-buttons">
          <button @click="exportReport('xlsx')">导出 Excel</button>
          <button @click="exportReport('pdf')">导出 PDF</button>
          <button @click="exportReport('html')">导出 HTML</button>
        </div>
      </div>
    </section>

    <!-- 角色视角对比 -->
    <section class="comparison-section">
      <h2>角色视角对比</h2>
      <p>同一数据在不同角色下的呈现差异</p>
      <div class="comparison-grid">
        <div class="comparison-card" v-for="role in comparisonRoles" :key="role.code">
          <div class="comp-header">
            <div class="comp-avatar" :style="{ background: role.color }">{{ role.avatar }}</div>
            <h4>{{ role.name }}</h4>
          </div>
          <div class="comp-focus">
            <span class="focus-tag" v-for="f in role.focus" :key="f">{{ f }}</span>
          </div>
          <div class="comp-metrics">
            <div v-for="m in role.sampleMetrics" :key="m.name">
              {{ m.name }}: <strong>{{ m.value }}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const currentRole = ref('pm')
const selectedReport = ref('')
const period = ref('weekly')
const loading = ref(false)
const reportData = ref(null)

const roles = [
  { code: 'gm', name: '总经理', scope: '全公司', color: '#6366F1', avatar: '总' },
  { code: 'dept_manager', name: '部门经理', scope: '本部门', color: '#8B5CF6', avatar: '部' },
  { code: 'pm', name: '项目经理', scope: '所负责项目', color: '#F59E0B', avatar: '项' },
  { code: 'te', name: '技术负责人', scope: '技术团队', color: '#10B981', avatar: '技' },
  { code: 'engineer', name: '工程师', scope: '个人任务', color: '#3B82F6', avatar: '工' },
  { code: 'finance', name: '财务', scope: '财务数据', color: '#EC4899', avatar: '财' },
]

const reportTypes = [
  { code: 'project_weekly', name: '项目周报', period: '每周', description: '项目进度、任务、风险汇总', iconBg: '#6366F1', roles: ['gm', 'dept_manager', 'pm', 'te', 'engineer'] },
  { code: 'project_monthly', name: '项目月报', period: '每月', description: '项目月度总结与分析', iconBg: '#8B5CF6', roles: ['gm', 'dept_manager', 'pm', 'te', 'finance'] },
  { code: 'cost_analysis', name: '成本分析', period: '月度', description: '项目成本构成与偏差分析', iconBg: '#10B981', roles: ['gm', 'pm', 'finance'] },
  { code: 'workload_analysis', name: '负荷分析', period: '每周', description: '人员负荷与资源利用率', iconBg: '#F59E0B', roles: ['gm', 'dept_manager', 'pm', 'te'] },
  { code: 'risk_report', name: '风险报告', period: '每周', description: '项目风险识别与预警', iconBg: '#EF4444', roles: ['gm', 'dept_manager', 'pm', 'te'] },
]

const comparisonRoles = [
  { code: 'gm', name: '总经理', avatar: '总', color: '#6366F1', focus: ['经营指标', '战略目标', '重大风险'], sampleMetrics: [{ name: '项目完成率', value: '85%' }, { name: '利润率', value: '18%' }] },
  { code: 'pm', name: '项目经理', avatar: '项', color: '#F59E0B', focus: ['项目进度', '里程碑', '资源协调'], sampleMetrics: [{ name: '任务完成', value: '12/15' }, { name: '进度偏差', value: '+3%' }] },
  { code: 'engineer', name: '工程师', avatar: '工', color: '#3B82F6', focus: ['个人任务', '工时填报', '技能提升'], sampleMetrics: [{ name: '本周任务', value: '5项' }, { name: '工时', value: '42h' }] },
]

const currentRoleConfig = computed(() => roles.find(r => r.code === currentRole.value))
const availableReports = computed(() => reportTypes.filter(r => r.roles.includes(currentRole.value)))
const selectedReportConfig = computed(() => reportTypes.find(r => r.code === selectedReport.value))

const selectReport = (code) => {
  selectedReport.value = code
  reportData.value = null
}

const generateReport = async () => {
  if (!selectedReport.value) return
  loading.value = true
  try {
    const res = await request.post('/api/v1/reports/generate', null, {
      params: { report_type: selectedReport.value, role: currentRole.value, period: period.value }
    })
    if (res.code === 200) {
      reportData.value = res.data
      ElMessage.success('报表生成成功')
    }
  } catch (e) {
    ElMessage.error(e.message || '生成失败')
  } finally {
    loading.value = false
  }
}

const exportReport = (format) => {
  if (!reportData.value) return
  window.open(`/api/v1/reports/export?report_type=${selectedReport.value}&role=${currentRole.value}&format=${format}&period=${period.value}`)
}
</script>

<style scoped>
.reports-page { min-height: 100vh; background: #F8FAFC; padding: 0 0 60px; }
.page-header { background: white; border-bottom: 1px solid #E2E8F0; padding: 24px 40px; }
.header-content { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
.header-content h1 { font-size: 24px; font-weight: 700; color: #0F172A; }
.header-subtitle { font-size: 14px; color: #64748B; margin-top: 4px; }
.role-selector { display: flex; align-items: center; gap: 12px; }
.selector-label { font-size: 13px; color: #64748B; }
.role-select { padding: 10px 16px; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 14px; }

.report-types-section, .report-generate-section, .comparison-section { max-width: 1200px; margin: 32px auto; padding: 0 40px; }
.report-types-section h2, .report-generate-section h2, .comparison-section h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.report-types-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.report-type-card { background: white; border-radius: 12px; padding: 20px; border: 2px solid transparent; cursor: pointer; transition: all 0.2s; }
.report-type-card:hover { border-color: #E2E8F0; transform: translateY(-2px); }
.report-type-card.selected { border-color: #6366F1; background: #F5F5FF; }
.card-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-bottom: 12px; }
.report-type-card h3 { font-size: 15px; font-weight: 600; margin-bottom: 6px; }
.report-type-card p { font-size: 13px; color: #64748B; margin-bottom: 10px; }
.period-badge { font-size: 11px; padding: 4px 8px; background: #F1F5F9; border-radius: 4px; color: #475569; }

.generate-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.generate-actions { display: flex; gap: 12px; }
.period-select { padding: 8px 12px; border: 1px solid #E2E8F0; border-radius: 6px; }
.btn-primary { padding: 10px 20px; background: linear-gradient(135deg, #6366F1, #4F46E5); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.report-header-card { background: linear-gradient(135deg, #6366F1, #4F46E5); border-radius: 12px; padding: 24px; color: white; margin-bottom: 20px; }
.report-header-card h2 { font-size: 20px; margin-bottom: 8px; }
.report-header-card p { opacity: 0.85; font-size: 13px; }

.metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.metric-card { background: white; border-radius: 10px; padding: 16px; border: 1px solid #E2E8F0; }
.metric-name { font-size: 12px; color: #64748B; margin-bottom: 8px; }
.metric-value { font-size: 28px; font-weight: 700; color: #0F172A; }
.metric-status { font-size: 11px; padding: 3px 8px; border-radius: 4px; margin-top: 8px; display: inline-block; }
.metric-status.good { background: #DCFCE7; color: #166534; }
.metric-status.warning { background: #FEF3C7; color: #92400E; }
.metric-status.critical { background: #FEE2E2; color: #991B1B; }
.metric-status.normal { background: #F1F5F9; color: #475569; }

.alerts-section, .recommendations-section { margin-bottom: 24px; }
.alerts-section h3, .recommendations-section h3 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.alert-item { padding: 16px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid; }
.alert-item.high { background: #FEF2F2; border-color: #EF4444; }
.alert-item.medium { background: #FFFBEB; border-color: #F59E0B; }
.alert-item.low { background: #F0FDF4; border-color: #22C55E; }
.alert-item p { font-size: 13px; color: #64748B; margin: 6px 0; }
.alert-actions { font-size: 12px; color: #475569; }

.rec-item { display: flex; gap: 16px; background: white; border-radius: 10px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 10px; }
.rec-score { width: 44px; height: 44px; background: linear-gradient(135deg, #6366F1, #4F46E5); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; }
.rec-content h4 { font-size: 14px; margin-bottom: 4px; }
.rec-content p { font-size: 13px; color: #64748B; margin-bottom: 6px; }
.rec-content span { font-size: 11px; color: #94A3B8; }

.export-buttons { display: flex; gap: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #E2E8F0; }
.export-buttons button { padding: 10px 16px; background: white; border: 1px solid #E2E8F0; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.export-buttons button:hover { background: #F8FAFC; }

.comparison-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px; }
.comparison-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #E2E8F0; }
.comp-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.comp-avatar { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; }
.comp-header h4 { font-size: 15px; font-weight: 600; }
.comp-focus { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.focus-tag { font-size: 11px; padding: 4px 8px; background: #F1F5F9; border-radius: 4px; color: #475569; }
.comp-metrics { font-size: 13px; color: #64748B; }
.comp-metrics div { margin-bottom: 4px; }

@media (max-width: 768px) {
  .page-header, .report-types-section, .report-generate-section, .comparison-section { padding: 0 20px; }
  .header-content { flex-direction: column; gap: 16px; align-items: flex-start; }
  .comparison-grid { grid-template-columns: 1fr; }
}
</style>
