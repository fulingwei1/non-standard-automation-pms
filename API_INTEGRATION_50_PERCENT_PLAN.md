# API集成度提升至50%+ 优化计划

## 更新日期
2026-01-10

## 当前状况

### 已完成工作（第一轮）
- ✅ 修复了 35+ 个页面
- ✅ 移除了 178处Mock数据引用
- ✅ API集成度从 14% 提升到约 28%
- ✅ 创建了 7 个自动化修复工具
- ✅ 生成了详细的技术文档

### 当前挑战（第二轮）
- ⚠️ 发现 26 个未集成页面（仍在使用Mock或无API）
- ⚠️ 发现 233 个未知状态页面（需要进一步检查）
- ⚠️ 当前 API 集成度：约 28%
- 🎯 目标：50%+（需再提升 22%）

---

## 优化目标

| 阶段 | 集成度 | 需修复页面 | 预计时间 |
|------|--------|------------|----------|
| **当前** | 28% | - | - |
| **第二阶段** | 40% | ~40个 | 2-3小时 |
| **第三阶段** | 50% | ~80个 | 4-5小时 |

---

## 第二阶段优化计划（28% → 40%）

### 1. 高优先级：工作台和仪表板（~15个页面）

**列表**：
1. ChairmanWorkstation.jsx - 董事长工作台
2. EngineerWorkstation.jsx - 工程师工作台
3. SalesManagerWorkstation.jsx - 销售经理工作台
4. FinanceManagerDashboard.jsx - 财务经理仪表板
5. CustomerServiceDashboard.jsx - 客服仪表板
6. ProcurementManagerDashboard.jsx - 采购经理仪表板
7. ProductionManagerDashboard.jsx - 生产经理仪表板
8. ManufacturingDirectorDashboard.jsx - 制造总监仪表板
9. PerformanceManagement.jsx - 绩效管理
10. ProjectBoard.jsx - 项目看板
11. AdminDashboard.jsx - 管理员仪表板
12. AdministrativeManagerWorkstation.jsx - 行政经理工作台
13. SalesDirectorWorkstation.jsx - 销售总监工作台
14. GeneralManagerWorkstation.jsx - 总经理工作台
15. PMODashboard.jsx - PMO仪表板

**优化内容**：
- ✅ 添加 API 导入（如果缺失）
- ✅ 添加 useEffect 数据加载逻辑
- ✅ 添加错误处理和加载状态
- ✅ 移除 Mock 数据定义
- ✅ 使用真实的 API 端点

### 2. 中优先级：功能页面（~25个页面）

**列表**：
16. AlertCenter.jsx - 告警中心
17. ScheduleBoard.jsx - 排程看板
18. TaskCenter.jsx - 任务中心
19. NotificationCenter.jsx - 通知中心
20. ApprovalCenter.jsx - 审批中心
21. MeetingManagement.jsx - 会议管理
22. VehicleManagement.jsx - 车辆管理
23. AttendanceManagement.jsx - 考勤管理
24. LeaveManagement.jsx - 请假管理
25. OvertimeManagement.jsx - 加班管理
26. BudgetManagement.jsx - 预算管理
27. CostAnalysis.jsx - 成本分析
28. CostAccounting.jsx - 成本核算
29. InvoiceManagement.jsx - 发票管理
30. PaymentManagement.jsx - 付款管理
31. PaymentApproval.jsx - 付款审批
32. ContractList.jsx - 合同列表
33. ContractDetail.jsx - 合同详情
34. ContractApproval.jsx - 合同审批
35. DocumentList.jsx - 文档列表
36. KnowledgeBase.jsx - 知识库
37. MaterialList.jsx - 物料列表
38. MaterialAnalysis.jsx - 物料分析
39. SupplierManagement.jsx - 供应商管理
40. ShortageAlert.jsx - 短缺告警

**优化内容**：
- ✅ 添加 API 调用逻辑
- ✅ 添加数据缓存和重新加载
- ✅ 优化用户体验（加载状态、错误提示）

---

## 标准化API集成模式

### 模式1：简单数据加载（单一API）

```jsx
import { useState, useEffect } from 'react'
import { xxxApi } from '../services/api'
import { ApiIntegrationError } from '../components/ui'

export default function XxxPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await xxxApi.list({ page: 1, page_size: 50 })
        const data = response.data?.items || response.data || []
        setData(data)
      } catch (err) {
        console.error('Failed to load data:', err)
        setError(err.response?.data?.detail || err.message || '加载数据失败')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (error && !data) {
    return (
      <ApiIntegrationError
        error={error}
        apiEndpoint="/api/v1/xxx"
        onRetry={() => window.location.reload()}
      />
    )
  }

  if (loading) {
    return <div className="flex justify-center py-8">加载中...</div>
  }

  return (
    <div>
      {/* 页面内容 */}
    </div>
  )
}
```

### 模式2：复杂数据加载（多个API）

```jsx
export default function XxxDashboard() {
  const [stats, setStats] = useState({})
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [statsRes, itemsRes] = await Promise.all([
        xxxApi.getStats(),
        xxxApi.list({ page: 1, page_size: 50 })
      ])

      setStats(statsRes.data || {})
      setItems(itemsRes.data?.items || itemsRes.data || [])
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
      setError(err.response?.data?.detail || err.message || '加载仪表板数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // ... 渲染逻辑
}
```

### 模式3：带搜索和过滤的列表页面

```jsx
export default function XxxListPage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = {
        page: 1,
        page_size: 50,
      }

      if (searchQuery) {
        params.keyword = searchQuery
      }

      if (statusFilter !== 'all') {
        params.status = statusFilter
      }

      const response = await xxxApi.list(params)
      const data = response.data?.items || response.data || []
      setData(data)
    } catch (err) {
      console.error('Failed to load data:', err)
      setError(err.response?.data?.detail || err.message || '加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [searchQuery, statusFilter])

  // ... 渲染逻辑
}
```

---

## 下一步行动

### 立即执行

1. ✅ 运行分析脚本了解当前状况
2. ✅ 创建自动化工具批量添加API集成
3. ✅ 开始第二阶段优化工作
4. ✅ 验证修复效果

### 本周目标

5. ⏭️ 完成 40+ 个页面的 API 集成
6. ⏭️ 提升 API 集成度到 40%
7. ⏭️ 创建完善的自动化工具
8. ⏭️ 生成详细的优化文档

### 本月目标

9. ⏭️ 完成 80+ 个页面的 API 集成
10. ⏭️ 提升 API 集成度到 50%+
11. ⏭️ 优化代码质量和用户体验
12. ⏭️ 完善测试和验证流程

---

**计划完成时间**: 2026-01-10
**计划制定人**: AI Assistant
**项目**: 非标自动化项目管理系统
