# 前端跨部门进度展示实施指南

**文档版本**: 1.0
**创建日期**: 2026-01-07
**目标**: 在前端界面上展示跨部门进度数据

---

## 📋 现状分析

### 当前前端页面情况

| 页面 | 文件路径 | 当前功能 | 是否调用跨部门API |
|------|---------|---------|----------------|
| **PMO驾驶舱** | `frontend/src/pages/PMODashboard.jsx` | 项目概览统计 | ❌ 未调用 |
| **工程师工作台** | `frontend/src/pages/EngineerWorkstation.jsx` | 个人任务管理 | ❌ 未调用 |
| **项目详情** | `frontend/src/pages/ProjectDetail.jsx` | 项目基本信息 | ❌ 未调用 |

### 核心问题

✅ **后端API已完成**：`GET /api/v1/engineers/projects/{project_id}/progress-visibility`
❌ **前端尚未集成**：所有前端页面都未调用此API

---

## 🎯 实施方案

### 方案A：在PMO驾驶舱中添加跨部门进度视图（推荐）

**适用场景**: 项目经理在PMO驾驶舱中查看项目的跨部门进度

**实施步骤**:

#### 1. 修改 `frontend/src/services/api.js`

添加跨部门进度API调用：

```javascript
// frontend/src/services/api.js

export const engineersApi = {
  // ... 其他API ...

  // 获取跨部门进度视图
  getProgressVisibility: (projectId) =>
    apiClient.get(`/engineers/projects/${projectId}/progress-visibility`),
}
```

#### 2. 创建跨部门进度组件

创建新组件 `frontend/src/components/pmo/CrossDepartmentProgress.jsx`：

```jsx
/**
 * 跨部门进度可视化组件
 * 用于展示项目的跨部门进度数据
 */
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, Progress, Badge } from '../ui'
import { Users, TrendingUp, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { engineersApi } from '../../services/api'

export function CrossDepartmentProgress({ projectId }) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await engineersApi.getProgressVisibility(projectId)
        setData(response.data)
      } catch (err) {
        console.error('Failed to fetch cross-department progress:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (projectId) {
      fetchData()
    }
  }, [projectId])

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-white/10 rounded w-1/4" />
            <div className="h-20 bg-white/10 rounded" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-red-400 text-sm">加载失败: {error}</div>
        </CardContent>
      </Card>
    )
  }

  if (!data) return null

  const {
    overall_progress,
    project_health,
    department_progress,
    active_delays
  } = data

  // 健康度颜色
  const healthColors = {
    H1: 'text-emerald-400 bg-emerald-500/10',
    H2: 'text-amber-400 bg-amber-500/10',
    H3: 'text-red-400 bg-red-500/10',
    H4: 'text-slate-400 bg-slate-500/10',
  }

  return (
    <div className="space-y-6">
      {/* 项目整体进度 */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">项目整体进度</h3>
            <Badge className={healthColors[project_health]}>
              {project_health === 'H1' ? '正常' :
               project_health === 'H2' ? '有风险' :
               project_health === 'H3' ? '阻塞' : '已完结'}
            </Badge>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">整体进度</span>
              <span className="text-white font-medium">{overall_progress}%</span>
            </div>
            <Progress value={overall_progress} className="h-3" />
          </div>
        </CardContent>
      </Card>

      {/* 各部门进度统计 */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 mb-6">
            <Users className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">各部门进度</h3>
          </div>

          <div className="space-y-4">
            {department_progress?.map((dept, index) => (
              <motion.div
                key={dept.department}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-4 rounded-lg bg-surface-1/50 border border-border"
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="text-white font-medium">{dept.department}</h4>
                    <p className="text-xs text-slate-400 mt-1">
                      {dept.completed_tasks}/{dept.total_tasks} 任务已完成
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">
                      {dept.average_progress.toFixed(1)}%
                    </div>
                    <div className="text-xs text-slate-400">
                      完成率 {dept.completion_rate.toFixed(0)}%
                    </div>
                  </div>
                </div>

                <Progress value={dept.average_progress} className="h-2 mb-3" />

                {/* 部门成员明细 */}
                {dept.members && Object.keys(dept.members).length > 0 && (
                  <div className="mt-3 pt-3 border-t border-border/50">
                    <p className="text-xs text-slate-400 mb-2">成员进度:</p>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(dept.members).map(([name, member]) => (
                        <div key={name} className="flex items-center justify-between text-xs">
                          <span className="text-slate-300">{member.real_name}</span>
                          <span className="text-white">{member.average_progress.toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 延期任务预警 */}
      {active_delays && active_delays.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <h3 className="text-lg font-semibold text-white">延期任务</h3>
              <Badge className="bg-red-500/10 text-red-400">
                {active_delays.length} 个
              </Badge>
            </div>

            <div className="space-y-3">
              {active_delays.map((task) => (
                <div
                  key={task.task_id}
                  className="p-3 rounded-lg bg-red-500/5 border border-red-500/20"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="text-white font-medium text-sm">
                        {task.task_name}
                      </h4>
                      <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                        <span>{task.assignee} · {task.department}</span>
                        <span>延期 {task.delay_days} 天</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-white">{task.progress}%</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
```

#### 3. 在PMODashboard中集成

修改 `frontend/src/pages/PMODashboard.jsx`：

```jsx
// frontend/src/pages/PMODashboard.jsx
import { CrossDepartmentProgress } from '../components/pmo/CrossDepartmentProgress'

export default function PMODashboard() {
  const [selectedProjectId, setSelectedProjectId] = useState(null)

  // ... 其他代码 ...

  return (
    <div className="space-y-6">
      <PageHeader title="PMO 驾驶舱" description="项目管理部全景视图" />

      {/* 原有的统计卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* ... 统计卡片代码 ... */}
      </div>

      {/* 新增：跨部门进度视图 */}
      <div className="mt-8">
        <div className="mb-4">
          <h2 className="text-xl font-bold text-white mb-2">跨部门进度视图</h2>
          <p className="text-sm text-slate-400">选择项目查看各部门进度</p>
        </div>

        {/* 项目选择器 */}
        <select
          value={selectedProjectId || ''}
          onChange={(e) => setSelectedProjectId(e.target.value ? parseInt(e.target.value) : null)}
          className="mb-4 px-4 py-2 rounded-lg bg-surface-2 border border-border text-white"
        >
          <option value="">选择项目...</option>
          <option value="1">项目1 - BMS老化测试设备</option>
          <option value="2">项目2 - EOL功能测试设备</option>
          <option value="3">项目3 - ICT测试设备</option>
        </select>

        {/* 跨部门进度组件 */}
        {selectedProjectId && (
          <CrossDepartmentProgress projectId={selectedProjectId} />
        )}
      </div>
    </div>
  )
}
```

---

### 方案B：创建独立的跨部门进度查看页面

**适用场景**: 项目经理需要专门的页面查看跨部门进度

#### 1. 创建新页面

创建 `frontend/src/pages/CrossDepartmentProgressPage.jsx`：

```jsx
/**
 * 跨部门进度查看页面
 * 专门用于查看项目的跨部门进度
 */
import { useState } from 'react'
import { PageHeader } from '../components/layout/PageHeader'
import { CrossDepartmentProgress } from '../components/pmo/CrossDepartmentProgress'
import { Card, CardContent } from '../components/ui'

export default function CrossDepartmentProgressPage() {
  const [selectedProjectId, setSelectedProjectId] = useState(1)

  return (
    <div className="space-y-6">
      <PageHeader
        title="跨部门进度视图"
        description="查看项目各部门的实时进度"
      />

      {/* 项目选择器 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <label className="text-sm text-slate-400">选择项目:</label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(parseInt(e.target.value))}
              className="flex-1 px-4 py-2 rounded-lg bg-surface-2 border border-border text-white"
            >
              <option value="1">项目1 - BMS老化测试设备</option>
              <option value="2">项目2 - EOL功能测试设备</option>
              <option value="3">项目3 - ICT测试设备</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* 跨部门进度组件 */}
      <CrossDepartmentProgress projectId={selectedProjectId} />
    </div>
  )
}
```

#### 2. 添加路由

修改 `frontend/src/App.jsx`：

```jsx
// frontend/src/App.jsx
import CrossDepartmentProgressPage from './pages/CrossDepartmentProgressPage'

function App() {
  return (
    <Router>
      <Routes>
        {/* ... 其他路由 ... */}

        <Route
          path="/cross-department-progress"
          element={<CrossDepartmentProgressPage />}
        />
      </Routes>
    </Router>
  )
}
```

#### 3. 添加侧边栏菜单

修改 `frontend/src/components/layout/Sidebar.jsx`：

```jsx
// frontend/src/components/layout/Sidebar.jsx

const menuItems = [
  // ... 其他菜单项 ...

  {
    id: 'cross-dept-progress',
    label: '跨部门进度',
    icon: Users,
    path: '/cross-department-progress',
    badge: null,
  },
]
```

---

## 🎨 界面效果预览

### 展示效果说明

当项目经理在前端页面选择项目后，将看到：

#### 1. **项目整体进度卡片**
```
┌─────────────────────────────────────┐
│ 项目整体进度              [正常] H1 │
│                                     │
│ 整体进度              45.67%       │
│ ████████████░░░░░░░░░░░░░░         │
└─────────────────────────────────────┘
```

#### 2. **各部门进度列表**
```
┌─────────────────────────────────────┐
│ 👥 各部门进度                       │
│                                     │
│ ┌─────────────────────────────────┐│
│ │ 机械部                  52.3%   ││
│ │ 4/10 任务已完成  完成率 40%    ││
│ │ ██████████░░░░░░░░░░            ││
│ │                                 ││
│ │ 成员进度:                       ││
│ │ 张工: 60%    李工: 44.6%       ││
│ └─────────────────────────────────┘│
│                                     │
│ ┌─────────────────────────────────┐│
│ │ 电气部                  41.25%  ││
│ │ 3/8 任务已完成   完成率 37.5%  ││
│ │ ████████░░░░░░░░░░░░            ││
│ │                                 ││
│ │ 成员进度:                       ││
│ │ 王工: 50%    赵工: 32.5%       ││
│ └─────────────────────────────────┘│
│                                     │
│ ┌─────────────────────────────────┐│
│ │ 软件部                  38.33%  ││
│ │ 1/6 任务已完成   完成率 16.67% ││
│ │ ███████░░░░░░░░░░░░░            ││
│ │                                 ││
│ │ 成员进度:                       ││
│ │ 孙工: 46.67%  周工: 30%        ││
│ └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

#### 3. **延期任务预警**
```
┌─────────────────────────────────────┐
│ ⚠️ 延期任务                    [2]  │
│                                     │
│ ┌─────────────────────────────────┐│
│ │ PLC程序开发              65%    ││
│ │ 赵工 · 电气部    延期 2 天     ││
│ └─────────────────────────────────┘│
│                                     │
│ ┌─────────────────────────────────┐│
│ │ 视觉算法优化             40%    ││
│ │ 周工 · 软件部    延期 4 天     ││
│ └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

---

## 🚀 快速实施步骤（最简方案）

如果要快速实现，建议按以下优先级：

### 第1步：添加API调用（5分钟）

```bash
# 编辑 frontend/src/services/api.js
vim frontend/src/services/api.js
```

添加：
```javascript
export const engineersApi = {
  getProgressVisibility: (projectId) =>
    apiClient.get(`/engineers/projects/${projectId}/progress-visibility`),
}
```

### 第2步：创建组件（30分钟）

```bash
# 创建跨部门进度组件
mkdir -p frontend/src/components/pmo
touch frontend/src/components/pmo/CrossDepartmentProgress.jsx
```

复制上面的 `CrossDepartmentProgress.jsx` 代码

### 第3步：集成到现有页面（10分钟）

选择以下任一页面集成：
- **PMODashboard.jsx** - 项目经理看板（推荐）
- **ProjectDetail.jsx** - 项目详情页

在页面中添加：
```jsx
import { CrossDepartmentProgress } from '../components/pmo/CrossDepartmentProgress'

// 在页面中使用
<CrossDepartmentProgress projectId={projectId} />
```

### 第4步：测试（5分钟）

```bash
# 启动前端
cd frontend
npm run dev

# 访问 http://localhost:5173
# 登录后查看PMO驾驶舱或项目详情页
```

---

## 📊 数据流示意图

```
┌──────────────────┐
│  前端页面         │
│  PMODashboard    │
└────────┬─────────┘
         │
         │ 1. 用户选择项目ID
         ▼
┌──────────────────────────────┐
│  CrossDepartmentProgress组件  │
│  - 发起API请求                │
│  - 渲染进度数据               │
└────────┬─────────────────────┘
         │
         │ 2. GET /api/v1/engineers/projects/1/progress-visibility
         ▼
┌──────────────────────────────┐
│  后端API                      │
│  engineers.py:933            │
│  get_project_progress_visibility() │
└────────┬─────────────────────┘
         │
         │ 3. 查询数据库（无部门过滤）
         ▼
┌──────────────────────────────┐
│  数据库                       │
│  - task_unified表            │
│  - users表                   │
│  - projects表                │
└────────┬─────────────────────┘
         │
         │ 4. 返回JSON数据
         ▼
┌──────────────────────────────┐
│  前端展示                     │
│  - 项目整体进度卡片           │
│  - 各部门进度列表             │
│  - 延期任务预警               │
└──────────────────────────────┘
```

---

## ✅ 实施检查清单

### 后端准备（已完成 ✅）
- [x] API端点实现：`GET /api/v1/engineers/projects/{project_id}/progress-visibility`
- [x] 无部门过滤逻辑
- [x] 进度聚合算法
- [x] 健康度计算
- [x] 延期任务识别

### 前端实施（待完成 ⏳）
- [ ] 修改 `frontend/src/services/api.js` 添加API调用
- [ ] 创建 `CrossDepartmentProgress.jsx` 组件
- [ ] 在PMODashboard或ProjectDetail中集成组件
- [ ] （可选）创建独立的跨部门进度页面
- [ ] （可选）在侧边栏添加菜单入口

### 测试验证（待完成 ⏳）
- [ ] 选择项目后能正确加载数据
- [ ] 各部门进度正确显示
- [ ] 进度条动画流畅
- [ ] 延期任务正确标识
- [ ] 健康度颜色正确显示

---

## 🔧 技术栈说明

| 技术 | 用途 | 文件位置 |
|------|------|----------|
| **React** | 前端框架 | `frontend/src/**/*.jsx` |
| **Framer Motion** | 动画库 | 已安装，用于过渡动画 |
| **Tailwind CSS** | 样式 | 已配置，使用 `className` |
| **Axios** | HTTP客户端 | `frontend/src/services/api.js` |
| **React Router** | 路由 | `frontend/src/App.jsx` |

---

## 🎯 预期成果

### 实施前
- ❌ 项目经理无法在前端看到跨部门进度
- ❌ 需要手工查询或导出数据
- ❌ 无实时更新

### 实施后
- ✅ 项目经理在PMO驾驶舱一键查看所有部门进度
- ✅ 自动展示各部门完成情况和人员明细
- ✅ 延期任务自动预警
- ✅ 数据实时更新

---

## 📝 常见问题

### Q1: 前端如何获取项目列表？

**A**: 调用现有的项目API：

```javascript
import { projectApi } from '../services/api'

const fetchProjects = async () => {
  const response = await projectApi.list({ page: 1, page_size: 100 })
  setProjects(response.data.items)
}
```

### Q2: 如何处理API调用失败？

**A**: 组件中已包含错误处理：

```javascript
try {
  const response = await engineersApi.getProgressVisibility(projectId)
  setData(response.data)
} catch (err) {
  console.error('Failed to fetch cross-department progress:', err)
  setError(err.message)
  // 显示友好的错误提示给用户
}
```

### Q3: 数据多久刷新一次？

**A**: 当前实现是组件挂载时加载一次。如需自动刷新：

```javascript
useEffect(() => {
  const fetchData = async () => { /* ... */ }

  fetchData() // 立即加载

  // 每30秒自动刷新
  const interval = setInterval(fetchData, 30000)

  return () => clearInterval(interval)
}, [projectId])
```

### Q4: 如何添加更多维度的统计？

**A**: 后端API已返回 `stage_progress` 和 `assignee_progress`，前端可以添加新的卡片展示：

```jsx
{/* 阶段维度统计 */}
{data.stage_progress && (
  <Card>
    <CardContent className="p-6">
      <h3 className="text-lg font-semibold text-white mb-4">各阶段进度</h3>
      {Object.entries(data.stage_progress).map(([stage, stats]) => (
        <div key={stage} className="mb-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-slate-400">{stage}</span>
            <span className="text-white">{stats.average_progress.toFixed(1)}%</span>
          </div>
          <Progress value={stats.average_progress} className="h-2" />
        </div>
      ))}
    </CardContent>
  </Card>
)}
```

---

## 📚 相关文档

- [CROSS_DEPARTMENT_PROGRESS_VIEWING_GUIDE.md](CROSS_DEPARTMENT_PROGRESS_VIEWING_GUIDE.md) - API使用指南
- [WORK_RESULTS_SHOWCASE.md](WORK_RESULTS_SHOWCASE.md) - 系统整体介绍
- [CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md) - 后端代码审查报告

---

**文档维护**: 如需帮助实施，请联系开发团队
**最后更新**: 2026-01-07
