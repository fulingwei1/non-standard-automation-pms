<template>
  <div class="performance-page">
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1>绩效中心</h1>
          <p class="header-subtitle">实时查看个人和团队绩效表现</p>
        </div>
        <div class="header-right">
          <div class="period-selector">
            <select v-model="selectedYear"><option v-for="y in years" :key="y" :value="y">{{ y }}年</option></select>
            <select v-model="selectedMonth"><option v-for="m in 12" :key="m" :value="m">{{ m }}月</option></select>
          </div>
          <button class="btn-primary" @click="refreshData">刷新数据</button>
        </div>
      </div>
      <div class="header-tabs">
        <button class="tab-btn" :class="{ active: activeTab === 'my' }" @click="activeTab = 'my'">我的绩效</button>
        <button class="tab-btn" :class="{ active: activeTab === 'team' }" @click="activeTab = 'team'" v-if="canViewTeam">团队绩效</button>
        <button class="tab-btn" :class="{ active: activeTab === 'project' }" @click="activeTab = 'project'" v-if="canViewProject">项目绩效</button>
        <button class="tab-btn" :class="{ active: activeTab === 'ranking' }" @click="activeTab = 'ranking'" v-if="canViewRanking">排行榜</button>
      </div>
    </header>

    <!-- 我的绩效 -->
    <section class="content-section" v-if="activeTab === 'my' && myPerformance">
      <div class="score-card">
        <div class="score-main">
          <div class="score-circle"><div class="score-value"><span class="value">{{ myPerformance.score.total_score }}</span><span class="label">综合得分</span></div></div>
          <div class="score-info">
            <div class="level-badge" :class="myPerformance.score.level">{{ myPerformance.score.level_text }}</div>
            <div class="rank-info">
              <div class="rank-item"><span class="rank-label">团队排名</span><span class="rank-value">第{{ myPerformance.score.rank_in_team }}名</span></div>
              <div class="rank-item"><span class="rank-label">部门排名</span><span class="rank-value">第{{ myPerformance.score.rank_in_dept }}名</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="dimensions-grid">
        <div class="dimension-card" v-for="dim in dimensions" :key="dim.key">
          <div class="dim-header"><span class="dim-icon">{{ dim.icon }}</span><span class="dim-title">{{ dim.name }}</span></div>
          <div class="dim-score"><span class="score-num">{{ getDimensionScore(dim.key) }}</span><span class="score-max">/100</span></div>
          <div class="dim-progress"><div class="progress-bar" :style="{ width: getDimensionScore(dim.key) + '%', background: dim.color }"></div></div>
        </div>
      </div>

      <div class="section-card">
        <h3>项目贡献</h3>
        <div class="contribution-list">
          <div class="contribution-item" v-for="c in myPerformance.project_contributions" :key="c.project_id">
            <div class="project-info">
              <span class="project-level" :class="'level-' + c.project_level.toLowerCase()">{{ c.project_level }}</span>
              <span class="project-name">{{ c.project_name }}</span>
              <span class="project-role">{{ c.role }}</span>
            </div>
            <div class="contribution-metrics">
              <div class="metric"><span class="metric-value">{{ c.hours_contributed }}h</span><span class="metric-label">工时</span></div>
              <div class="metric"><span class="metric-value">{{ c.tasks_completed }}</span><span class="metric-label">任务</span></div>
              <div class="metric"><span class="metric-value">{{ c.contribution_rate }}%</span><span class="metric-label">贡献</span></div>
              <div class="metric"><span class="metric-value perf">{{ c.performance_in_project }}</span><span class="metric-label">表现</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="feedback-row">
        <div class="feedback-card highlights"><h3>🌟 本期亮点</h3><ul><li v-for="(h, i) in myPerformance.highlights" :key="i">{{ h }}</li></ul></div>
        <div class="feedback-card improvements"><h3>💪 待改进项</h3><ul><li v-for="(imp, i) in myPerformance.improvements" :key="i">{{ imp }}</li></ul></div>
      </div>

      <div class="section-card">
        <h3>绩效趋势</h3>
        <div class="trend-chart">
          <div class="chart-bars">
            <div class="chart-bar" v-for="(t, i) in myPerformance.trends" :key="i">
              <div class="bar-fill" :style="{ height: t.score + '%' }" :class="t.level"><span class="bar-value">{{ t.score }}</span></div>
              <span class="bar-label">{{ t.period.slice(5) }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 团队绩效 -->
    <section class="content-section" v-if="activeTab === 'team' && teamPerformance">
      <div class="team-stats-grid">
        <div class="stat-card"><div class="stat-value">{{ teamPerformance.member_count }}</div><div class="stat-label">团队人数</div></div>
        <div class="stat-card"><div class="stat-value">{{ teamPerformance.avg_score }}</div><div class="stat-label">平均得分</div></div>
        <div class="stat-card"><div class="stat-value">{{ teamPerformance.max_score }}</div><div class="stat-label">最高得分</div></div>
        <div class="stat-card"><div class="stat-value positive">+{{ teamPerformance.vs_last_period }}%</div><div class="stat-label">环比变化</div></div>
      </div>
      <div class="section-card">
        <h3>成员排名</h3>
        <div class="ranking-table">
          <div class="table-row" v-for="m in teamPerformance.members_ranking" :key="m.user_id">
            <span class="col-rank">{{ m.rank }}</span>
            <span class="col-name">{{ m.user_name }}</span>
            <span class="col-score">{{ m.score.toFixed(1) }}</span>
            <span class="col-level" :class="m.level">{{ getLevelText(m.level) }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 排行榜 -->
    <section class="content-section" v-if="activeTab === 'ranking' && rankingData">
      <div class="section-card">
        <h3>{{ rankingData.scope_name }}绩效排行榜</h3>
        <div class="top-three">
          <div class="top-item" v-for="(r, i) in rankingData.ranking.slice(0, 3)" :key="r.user_id" :class="['rank-' + (i+1)]">
            <div class="top-medal">{{ ['🥇', '🥈', '🥉'][i] }}</div>
            <span class="top-name">{{ r.user_name }}</span>
            <span class="top-score">{{ r.score }}</span>
          </div>
        </div>
        <div class="ranking-list">
          <div class="ranking-item" v-for="r in rankingData.ranking.slice(3)" :key="r.user_id">
            <span class="ranking-num">{{ r.rank }}</span>
            <span class="ranking-name">{{ r.user_name }}</span>
            <span class="ranking-dept">{{ r.department }}</span>
            <span class="ranking-score">{{ r.score }}</span>
            <span class="ranking-level" :class="r.level">{{ getLevelText(r.level) }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores'

const userStore = useUserStore()
const activeTab = ref('my')
const selectedYear = ref(new Date().getFullYear())
const selectedMonth = ref(new Date().getMonth() + 1)

const years = computed(() => [2025, 2024, 2023])
const userRole = computed(() => userStore.userInfo?.roleCode || 'engineer')
const canViewTeam = computed(() => ['gm', 'dept_manager', 'team_leader'].includes(userRole.value))
const canViewProject = computed(() => ['gm', 'dept_manager', 'pm'].includes(userRole.value))
const canViewRanking = computed(() => ['gm', 'dept_manager'].includes(userRole.value))

const dimensions = [
  { key: 'workload', name: '工时指标', icon: '⏱️', color: '#6366F1' },
  { key: 'tasks', name: '任务指标', icon: '📋', color: '#F59E0B' },
  { key: 'quality', name: '质量指标', icon: '✅', color: '#10B981' },
  { key: 'collaboration', name: '协作指标', icon: '🤝', color: '#8B5CF6' }
]

const myPerformance = ref({
  score: { total_score: 83.5, level: 'good', level_text: '良好', workload_score: 85, task_score: 82, quality_score: 88, collaboration_score: 78, rank_in_team: 2, rank_in_dept: 5 },
  project_contributions: [
    { project_id: 1, project_name: 'XX自动化测试设备', project_level: 'A', role: '主设计', hours_contributed: 120, tasks_completed: 8, contribution_rate: 35, performance_in_project: '优秀' },
    { project_id: 2, project_name: 'YY产线改造', project_level: 'B', role: '协助', hours_contributed: 45, tasks_completed: 3, contribution_rate: 15, performance_in_project: '良好' }
  ],
  trends: [
    { period: '2024-12', score: 83.5, level: 'good' }, { period: '2024-11', score: 78.3, level: 'qualified' },
    { period: '2024-10', score: 85.1, level: 'good' }, { period: '2024-09', score: 80.2, level: 'good' },
    { period: '2024-08', score: 76.8, level: 'qualified' }, { period: '2024-07', score: 79.5, level: 'qualified' }
  ],
  highlights: ['工时利用率优秀，达到95%以上', '任务按时完成率优秀', '积极支援团队，帮助同事3次'],
  improvements: ['有1个任务逾期，建议加强时间管理']
})

const teamPerformance = ref({
  member_count: 8, avg_score: 82.5, max_score: 92.5, vs_last_period: 3.2,
  members_ranking: [
    { user_id: 1, user_name: '张三', score: 92.5, level: 'excellent', rank: 1 },
    { user_id: 2, user_name: '李四', score: 88.5, level: 'good', rank: 2 },
    { user_id: 3, user_name: '王五', score: 85.2, level: 'good', rank: 3 },
    { user_id: 4, user_name: '赵六', score: 82.0, level: 'good', rank: 4 }
  ]
})

const rankingData = ref({
  scope_name: '研发部',
  ranking: [
    { rank: 1, user_id: 1, user_name: '张三', department: '机械组', score: 92.5, level: 'excellent' },
    { rank: 2, user_id: 5, user_name: '周八', department: '电气组', score: 90.2, level: 'excellent' },
    { rank: 3, user_id: 2, user_name: '李四', department: '电气组', score: 88.5, level: 'good' },
    { rank: 4, user_id: 6, user_name: '吴九', department: '软件组', score: 86.8, level: 'good' },
    { rank: 5, user_id: 3, user_name: '王五', department: '软件组', score: 85.2, level: 'good' },
    { rank: 6, user_id: 7, user_name: '郑十', department: '机械组', score: 82.0, level: 'good' },
    { rank: 7, user_id: 4, user_name: '赵六', department: '测试组', score: 80.5, level: 'good' }
  ]
})

const getDimensionScore = (key) => {
  const map = { workload: 'workload_score', tasks: 'task_score', quality: 'quality_score', collaboration: 'collaboration_score' }
  return myPerformance.value?.score[map[key]] || 0
}

const getLevelText = (level) => {
  const texts = { excellent: '优秀', good: '良好', qualified: '合格', needs_improvement: '待改进' }
  return texts[level] || level
}

const refreshData = () => { console.log('刷新数据') }

onMounted(() => {})
</script>

<style scoped>
.performance-page { min-height: 100vh; background: #F8FAFC; }
.page-header { background: white; border-bottom: 1px solid #E2E8F0; padding: 28px 40px 0; }
.header-content { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.header-content h1 { font-size: 26px; font-weight: 700; color: #0F172A; }
.header-subtitle { font-size: 14px; color: #64748B; margin-top: 4px; }
.header-right { display: flex; gap: 12px; }
.period-selector { display: flex; gap: 8px; }
.period-selector select { padding: 10px 16px; border: 1px solid #E2E8F0; border-radius: 8px; }
.btn-primary { padding: 10px 20px; background: linear-gradient(135deg, #6366F1, #4F46E5); color: white; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; }
.header-tabs { display: flex; gap: 4px; }
.tab-btn { padding: 12px 24px; font-size: 14px; font-weight: 500; color: #64748B; background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; }
.tab-btn.active { color: #6366F1; border-bottom-color: #6366F1; }

.content-section { max-width: 1400px; margin: 0 auto; padding: 32px 40px; }
.score-card { background: white; border-radius: 20px; padding: 32px; margin-bottom: 24px; }
.score-main { display: flex; align-items: center; gap: 48px; }
.score-circle { width: 160px; height: 160px; border-radius: 50%; background: linear-gradient(135deg, #6366F1, #8B5CF6); display: flex; align-items: center; justify-content: center; }
.score-value { text-align: center; color: white; }
.score-value .value { font-size: 48px; font-weight: 700; display: block; }
.score-value .label { font-size: 14px; opacity: 0.9; }
.level-badge { display: inline-block; padding: 8px 20px; border-radius: 20px; font-weight: 600; margin-bottom: 16px; }
.level-badge.excellent { background: #DCFCE7; color: #166534; }
.level-badge.good { background: #EEF2FF; color: #4338CA; }
.level-badge.qualified { background: #FEF3C7; color: #92400E; }
.rank-info { display: flex; gap: 24px; }
.rank-item { display: flex; flex-direction: column; }
.rank-label { font-size: 13px; color: #64748B; }
.rank-value { font-size: 18px; font-weight: 600; color: #0F172A; }

.dimensions-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px; }
.dimension-card { background: white; border-radius: 16px; padding: 24px; }
.dim-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.dim-icon { font-size: 20px; }
.dim-title { font-size: 14px; font-weight: 600; color: #0F172A; }
.dim-score { margin-bottom: 8px; }
.score-num { font-size: 28px; font-weight: 700; color: #0F172A; }
.score-max { font-size: 14px; color: #94A3B8; }
.dim-progress { height: 6px; background: #E2E8F0; border-radius: 3px; overflow: hidden; }
.dim-progress .progress-bar { height: 100%; border-radius: 3px; }

.section-card { background: white; border-radius: 16px; padding: 24px; margin-bottom: 24px; }
.section-card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
.contribution-list { display: flex; flex-direction: column; gap: 12px; }
.contribution-item { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: #F8FAFC; border-radius: 12px; }
.project-info { display: flex; align-items: center; gap: 12px; }
.project-level { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; color: white; }
.project-level.level-a { background: #6366F1; }
.project-level.level-b { background: #F59E0B; }
.project-level.level-c { background: #10B981; }
.project-name { font-weight: 600; }
.project-role { font-size: 12px; color: #64748B; padding: 4px 8px; background: #E2E8F0; border-radius: 4px; }
.contribution-metrics { display: flex; gap: 24px; }
.metric { text-align: center; }
.metric-value { display: block; font-size: 16px; font-weight: 700; color: #0F172A; }
.metric-label { font-size: 11px; color: #64748B; }

.feedback-row { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
.feedback-card { background: white; border-radius: 16px; padding: 24px; }
.feedback-card h3 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.feedback-card ul { list-style: none; padding: 0; margin: 0; }
.feedback-card li { padding: 8px 0; border-bottom: 1px solid #F1F5F9; font-size: 14px; color: #374151; }

.trend-chart { height: 200px; }
.chart-bars { display: flex; justify-content: space-around; align-items: flex-end; height: 100%; padding: 20px 0; }
.chart-bar { display: flex; flex-direction: column; align-items: center; width: 50px; }
.bar-fill { width: 36px; border-radius: 6px 6px 0 0; position: relative; min-height: 20px; display: flex; align-items: flex-start; justify-content: center; }
.bar-fill.excellent { background: #10B981; }
.bar-fill.good { background: #6366F1; }
.bar-fill.qualified { background: #F59E0B; }
.bar-value { font-size: 10px; font-weight: 600; color: white; margin-top: 4px; }
.bar-label { font-size: 11px; color: #64748B; margin-top: 6px; }

.team-stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px; }
.stat-card { background: white; border-radius: 16px; padding: 24px; text-align: center; }
.stat-value { font-size: 32px; font-weight: 700; color: #0F172A; }
.stat-value.positive { color: #10B981; }
.stat-label { font-size: 13px; color: #64748B; margin-top: 4px; }

.ranking-table { display: flex; flex-direction: column; gap: 8px; }
.table-row { display: grid; grid-template-columns: 60px 1fr 100px 100px; padding: 14px 20px; background: #F8FAFC; border-radius: 8px; align-items: center; }
.col-rank { font-weight: 700; color: #6366F1; }
.col-name { font-weight: 600; }
.col-score { font-weight: 600; }
.col-level { padding: 4px 12px; border-radius: 12px; font-size: 12px; text-align: center; }
.col-level.excellent { background: #DCFCE7; color: #166534; }
.col-level.good { background: #EEF2FF; color: #4338CA; }
.col-level.qualified { background: #FEF3C7; color: #92400E; }

.top-three { display: flex; justify-content: center; gap: 40px; padding: 32px 0; }
.top-item { text-align: center; }
.top-item.rank-1 { order: 2; }
.top-item.rank-2 { order: 1; }
.top-item.rank-3 { order: 3; }
.top-medal { font-size: 48px; }
.top-item.rank-1 .top-medal { font-size: 64px; }
.top-name { display: block; font-weight: 600; margin-top: 8px; }
.top-score { font-size: 20px; font-weight: 700; color: #6366F1; }

.ranking-list { margin-top: 24px; }
.ranking-item { display: grid; grid-template-columns: 60px 1fr 120px 80px 80px; padding: 12px 20px; border-bottom: 1px solid #F1F5F9; align-items: center; }
.ranking-num { font-weight: 600; color: #64748B; }
.ranking-name { font-weight: 600; }
.ranking-dept { font-size: 13px; color: #64748B; }
.ranking-score { font-weight: 700; }
.ranking-level { padding: 4px 10px; border-radius: 10px; font-size: 12px; text-align: center; }
.ranking-level.excellent { background: #DCFCE7; color: #166534; }
.ranking-level.good { background: #EEF2FF; color: #4338CA; }
.ranking-level.qualified { background: #FEF3C7; color: #92400E; }

@media (max-width: 1024px) { .dimensions-grid, .team-stats-grid { grid-template-columns: repeat(2, 1fr); } .feedback-row { grid-template-columns: 1fr; } }
@media (max-width: 768px) { .dimensions-grid, .team-stats-grid { grid-template-columns: 1fr; } .score-main { flex-direction: column; } }
</style>
