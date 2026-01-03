<template>
  <div class="workload-page">
    <div class="page-header">
      <h2>负荷管理</h2>
      <div class="header-actions">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width: 260px" />
        <el-select v-model="filterDept" placeholder="全部部门" clearable style="width: 120px">
          <el-option label="机械组" value="1" /><el-option label="电气组" value="2" /><el-option label="测试组" value="3" />
        </el-select>
      </div>
    </div>
    
    <!-- 统计概览 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6"><div class="stat-card"><div class="stat-value">{{ teamStats.totalMembers }}</div><div class="stat-label">团队成员</div></div></el-col>
      <el-col :span="6"><div class="stat-card"><div class="stat-value">{{ teamStats.avgLoad }}%</div><div class="stat-label">平均负荷</div></div></el-col>
      <el-col :span="6"><div class="stat-card warning"><div class="stat-value">{{ teamStats.overload }}</div><div class="stat-label">超负荷人数</div></div></el-col>
      <el-col :span="6"><div class="stat-card success"><div class="stat-value">{{ teamStats.available }}</div><div class="stat-label">可用资源</div></div></el-col>
    </el-row>
    
    <el-row :gutter="16">
      <!-- 团队负荷列表 -->
      <el-col :span="16">
        <el-card>
          <template #header><div class="card-header"><span>团队负荷一览</span><el-radio-group v-model="sortBy" size="small"><el-radio-button label="load">按负荷</el-radio-button><el-radio-button label="name">按姓名</el-radio-button></el-radio-group></div></template>
          <el-table :data="sortedMembers" @row-click="viewMemberDetail">
            <el-table-column label="成员" width="150">
              <template #default="{ row }">
                <div class="member-cell"><el-avatar :size="32">{{ row.user_name?.charAt(0) }}</el-avatar><div class="member-info"><span class="name">{{ row.user_name }}</span><span class="dept">{{ row.dept_name }}</span></div></div>
              </template>
            </el-table-column>
            <el-table-column label="角色" width="80"><template #default="{ row }"><el-tag size="small">{{ row.role }}</el-tag></template></el-table-column>
            <el-table-column label="负荷率" width="200">
              <template #default="{ row }">
                <div class="load-cell">
                  <el-progress :percentage="Math.min(row.allocation_rate, 100)" :stroke-width="12" :color="getLoadColor(row.allocation_rate)" :show-text="false" />
                  <span class="load-value" :class="{ overload: row.allocation_rate > 100 }">{{ row.allocation_rate }}%</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="分配工时" width="100"><template #default="{ row }">{{ row.assigned_hours }}h</template></el-table-column>
            <el-table-column label="任务数" width="80"><template #default="{ row }">{{ row.task_count }}</template></el-table-column>
            <el-table-column label="逾期任务" width="80"><template #default="{ row }"><span :class="{ 'text-danger': row.overdue_count > 0 }">{{ row.overdue_count }}</span></template></el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click.stop="viewMemberDetail(row)">详情</el-button>
                <el-button link type="primary" size="small" @click.stop="assignTask(row)">分配任务</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <!-- 负荷热力图 -->
      <el-col :span="8">
        <el-card class="heatmap-card">
          <template #header><span>负荷热力图 (近4周)</span></template>
          <div ref="heatmapChart" style="height: 300px"></div>
        </el-card>
        
        <el-card style="margin-top: 16px">
          <template #header><span>可用资源</span></template>
          <div class="available-list">
            <div v-for="m in availableMembers" :key="m.user_id" class="available-item">
              <div class="member-info"><el-avatar :size="28">{{ m.user_name?.charAt(0) }}</el-avatar><span>{{ m.user_name }}</span></div>
              <div class="available-hours"><span class="hours">{{ m.available_hours }}h</span><span class="label">可用</span></div>
            </div>
            <el-empty v-if="availableMembers.length === 0" description="暂无可用资源" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 成员详情对话框 -->
    <el-dialog v-model="showMemberDetail" :title="currentMember?.user_name + ' - 负荷详情'" width="700px">
      <div v-if="currentMember" class="member-detail">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="姓名">{{ currentMember.user_name }}</el-descriptions-item>
          <el-descriptions-item label="部门">{{ currentMember.dept_name }}</el-descriptions-item>
          <el-descriptions-item label="角色">{{ currentMember.role }}</el-descriptions-item>
          <el-descriptions-item label="分配工时">{{ currentMember.assigned_hours }}h</el-descriptions-item>
          <el-descriptions-item label="标准工时">176h</el-descriptions-item>
          <el-descriptions-item label="负荷率"><span :class="{ 'text-danger': currentMember.allocation_rate > 100 }">{{ currentMember.allocation_rate }}%</span></el-descriptions-item>
        </el-descriptions>
        
        <h4 style="margin: 20px 0 12px">任务分布</h4>
        <el-table :data="memberTasks" size="small">
          <el-table-column prop="project_code" label="项目" width="100" />
          <el-table-column prop="task_name" label="任务名称" min-width="160" />
          <el-table-column prop="plan_hours" label="计划工时" width="80" />
          <el-table-column prop="actual_hours" label="实际工时" width="80" />
          <el-table-column label="进度" width="100"><template #default="{ row }"><el-progress :percentage="row.progress" :stroke-width="6" /></template></el-table-column>
          <el-table-column prop="deadline" label="截止日期" width="100" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const dateRange = ref([])
const filterDept = ref('')
const sortBy = ref('load')
const showMemberDetail = ref(false)
const currentMember = ref(null)
const heatmapChart = ref(null)

const teamMembers = ref([
  { user_id: 1, user_name: '张工', dept_name: '机械组', role: 'ME', assigned_hours: 180, standard_hours: 176, allocation_rate: 102, task_count: 8, overdue_count: 0 },
  { user_id: 2, user_name: '李工', dept_name: '机械组', role: 'ME', assigned_hours: 160, standard_hours: 176, allocation_rate: 91, task_count: 6, overdue_count: 1 },
  { user_id: 3, user_name: '王工', dept_name: '电气组', role: 'EE', assigned_hours: 220, standard_hours: 176, allocation_rate: 125, task_count: 10, overdue_count: 2 },
  { user_id: 4, user_name: '赵工', dept_name: '电气组', role: 'EE', assigned_hours: 140, standard_hours: 176, allocation_rate: 80, task_count: 5, overdue_count: 0 },
  { user_id: 5, user_name: '钱工', dept_name: '测试组', role: 'TE', assigned_hours: 100, standard_hours: 176, allocation_rate: 57, task_count: 4, overdue_count: 0 },
  { user_id: 6, user_name: '孙工', dept_name: '测试组', role: 'TE', assigned_hours: 120, standard_hours: 176, allocation_rate: 68, task_count: 5, overdue_count: 0 }
])

const memberTasks = ref([
  { project_code: 'PRJ-001', task_name: '方案设计', plan_hours: 40, actual_hours: 38, progress: 80, deadline: '2025-01-10' },
  { project_code: 'PRJ-001', task_name: '结构设计', plan_hours: 80, actual_hours: 30, progress: 30, deadline: '2025-01-25' },
  { project_code: 'PRJ-002', task_name: '技术支持', plan_hours: 20, actual_hours: 12, progress: 60, deadline: '2025-01-15' }
])

const teamStats = computed(() => ({
  totalMembers: teamMembers.value.length,
  avgLoad: Math.round(teamMembers.value.reduce((sum, m) => sum + m.allocation_rate, 0) / teamMembers.value.length),
  overload: teamMembers.value.filter(m => m.allocation_rate > 100).length,
  available: teamMembers.value.filter(m => m.allocation_rate < 80).length
}))

const sortedMembers = computed(() => {
  const list = [...teamMembers.value]
  if (sortBy.value === 'load') list.sort((a, b) => b.allocation_rate - a.allocation_rate)
  else list.sort((a, b) => a.user_name.localeCompare(b.user_name))
  return list
})

const availableMembers = computed(() => teamMembers.value.filter(m => m.allocation_rate < 80).map(m => ({ ...m, available_hours: Math.round((1 - m.allocation_rate / 100) * 176) })))

function getLoadColor(rate) { if (rate > 100) return '#ff4d4f'; if (rate > 80) return '#faad14'; return '#52c41a' }
function viewMemberDetail(member) { currentMember.value = member; showMemberDetail.value = true }
function assignTask(member) { ElMessage.info(`为 ${member.user_name} 分配任务`) }

function renderHeatmap() {
  if (!heatmapChart.value) return
  const chart = echarts.init(heatmapChart.value)
  const users = ['张工', '李工', '王工', '赵工', '钱工', '孙工']
  const weeks = ['W01', 'W02', 'W03', 'W04']
  const data = []
  users.forEach((u, i) => weeks.forEach((w, j) => data.push([j, i, Math.round(60 + Math.random() * 60)])))
  
  chart.setOption({
    tooltip: { formatter: p => `${users[p.data[1]]} ${weeks[p.data[0]]}: ${p.data[2]}%` },
    grid: { left: 60, right: 20, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: weeks },
    yAxis: { type: 'category', data: users },
    visualMap: { min: 50, max: 130, calculable: true, orient: 'horizontal', left: 'center', bottom: -5, show: false, inRange: { color: ['#52c41a', '#faad14', '#ff4d4f'] } },
    series: [{ type: 'heatmap', data, label: { show: true, formatter: p => p.data[2] + '%', fontSize: 10 } }]
  })
}

onMounted(() => { nextTick(() => renderHeatmap()) })
</script>

<style lang="scss" scoped>
.workload-page { padding: 20px; background: #f0f2f5; min-height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; h2 { margin: 0; } .header-actions { display: flex; gap: 12px; } }
.stats-row { margin-bottom: 16px; }
.stat-card { padding: 20px; background: #fff; border-radius: 8px; text-align: center; .stat-value { font-size: 32px; font-weight: 600; } .stat-label { font-size: 13px; color: #999; margin-top: 4px; } &.warning .stat-value { color: #faad14; } &.success .stat-value { color: #52c41a; } }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.member-cell { display: flex; align-items: center; gap: 12px; .member-info { display: flex; flex-direction: column; .name { font-size: 14px; } .dept { font-size: 12px; color: #999; } } }
.load-cell { display: flex; align-items: center; gap: 8px; .load-value { width: 50px; text-align: right; font-weight: 500; &.overload { color: #ff4d4f; } } }
.text-danger { color: #ff4d4f; }
.available-list { .available-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f0f0f0; &:last-child { border-bottom: none; } .member-info { display: flex; align-items: center; gap: 8px; } .available-hours { text-align: right; .hours { font-size: 18px; font-weight: 600; color: #52c41a; } .label { font-size: 12px; color: #999; margin-left: 4px; } } } }
</style>
