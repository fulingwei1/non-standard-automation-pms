# 绩效管理模块集成指南

## 已创建的页面文件

1. ✅ `/frontend/src/pages/PerformanceManagement.jsx` - 绩效管理主页（综合仪表板）
2. ✅ `/frontend/src/pages/PerformanceRanking.jsx` - 绩效排行榜

## 需要在 App.jsx 中添加的代码

### 1. 导入语句 (在文件顶部的 import 区域)

```javascript
import PerformanceManagement from './pages/PerformanceManagement'
import PerformanceRanking from './pages/PerformanceRanking'
```

### 2. 路由配置 (在 <Routes> 标签内)

```javascript
{/* 绩效管理 */}
<Route path="/performance" element={<PerformanceManagement />} />
<Route path="/performance/ranking" element={<PerformanceRanking />} />
```

## 需要在 Sidebar.jsx 中添加的菜单配置

### 方法1: 在 HR角色 的导航组中添加

找到HR或管理层的导航配置，添加：

```javascript
{
  label: '绩效管理',
  items: [
    { name: '绩效概览', path: '/performance', icon: 'Award' },
    { name: '绩效排行榜', path: '/performance/ranking', icon: 'TrendingUp' },
  ],
}
```

### 方法2: 在 chairmanNavGroups 中添加（董事长可查看绩效）

```javascript
{
  label: '绩效管理',
  items: [
    { name: '绩效概览', path: '/performance', icon: 'Award' },
    { name: '绩效排行', path: '/performance/ranking', icon: 'BarChart3' },
  ],
}
```

## 功能特性

### PerformanceManagement 主页面包含：
- 📊 当前考核周期显示
- 📈 绩效统计数据（平均分、优秀人数、完成率）
- ✅ 待办事项列表（评价、自评、申诉）
- 👥 最近绩效结果
- 🏢 部门绩效排行
- 📉 绩效等级分布图

### PerformanceRanking 排行榜包含：
- 🏆 员工绩效 TOP 10
- 🏢 部门绩效排名
- 📊 排名变化趋势
- 🎖️ 金银铜牌标识

## API 集成说明

当前使用 Mock 数据。要连接真实API，需要：

1. 在 `/frontend/src/services/api.js` 中添加：

```javascript
// 绩效管理 API
export const performanceApi = {
  // 获取当前周期
  getCurrentPeriod: () => api.get('/performance/periods/current'),

  // 获取绩效统计
  getStats: (periodId) => api.get(`/performance/stats/${periodId}`),

  // 获取排行榜
  getRanking: (params) => api.get('/performance/ranking', { params }),

  // 获取绩效结果列表
  getResults: (params) => api.get('/performance/results', { params }),

  // 获取部门绩效
  getDepartmentPerformance: (params) => api.get('/performance/departments', { params }),
}
```

2. 在组件中使用：

```javascript
import { performanceApi } from '../services/api'

useEffect(() => {
  const fetchData = async () => {
    try {
      const res = await performanceApi.getCurrentPeriod()
      setCurrentPeriod(res.data)
    } catch (error) {
      console.error('Failed to fetch period:', error)
    }
  }
  fetchData()
}, [])
```

## 后续开发建议

### 优先级 P0（核心功能）
- ✅ 绩效管理主页
- ✅ 绩效排行榜
- ⏳ 绩效结果查看页面（待创建）
- ⏳ 绩效指标配置页面（待创建）

### 优先级 P1（重要功能）
- 绩效评价页面（上级评价、自评）
- 绩效申诉页面
- 周期管理页面

### 优先级 P2（辅助功能）
- 绩效报表导出
- 历史绩效查询
- 绩效趋势图表
- 个人绩效详情页

## 权限配置

需要在 `roleConfig.js` 中为以下角色添加绩效管理权限：

- **HR经理**: 完整绩效管理权限
- **部门经理**: 部门绩效查看和评价权限
- **董事长/总经理**: 全公司绩效查看权限
- **普通员工**: 个人绩效查看权限

## 测试步骤

1. 启动前端开发服务器
2. 登录系统（使用HR或管理员账号）
3. 访问 `/performance` 查看绩效管理主页
4. 访问 `/performance/ranking` 查看排行榜
5. 验证数据显示和交互功能

## 注意事项

- 所有页面都已使用 Framer Motion 动画效果
- UI 风格与系统其他页面保持一致（深色主题）
- 响应式设计，支持移动端查看
- 使用 Tailwind CSS 和自定义组件库
