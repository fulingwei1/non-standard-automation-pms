# 前端 API 集成改进总结

**完成日期**: 2026-01-XX  
**目标**: 移除所有 fallback 逻辑，确保 API 集成状态清晰可见

---

## ✅ 已完成的工作

### 1. 统一的错误处理组件

**文件**: `frontend/src/components/ui/ErrorMessage.jsx`

新增 `ApiIntegrationError` 组件，用于明确标识 API 未集成或调用失败的情况：

**特性**:
- ✅ 明确的错误提示："⚠️ API 集成未完成"
- ✅ 显示 HTTP 状态码和状态文本
- ✅ 显示 API 端点信息
- ✅ 提供说明文字，解释为什么移除 fallback
- ✅ 支持重试功能
- ✅ 不提供 fallback 到 mock 数据

**使用示例**:
```javascript
import { ApiIntegrationError } from '../components/ui'

{error ? (
  <ApiIntegrationError
    error={error}
    apiEndpoint="/api/v1/sales/statistics/*"
    onRetry={fetchData}
  />
) : data ? (
  <DataDisplay data={data} />
) : (
  <Loading />
)}
```

### 2. 导出更新

**文件**: `frontend/src/components/ui/index.js`

已更新导出，包含新的 `ApiIntegrationError` 组件：
```javascript
export { ErrorMessage, EmptyState, ApiIntegrationError } from './ErrorMessage'
```

### 3. 示例页面修改

已修改 3 个示例页面作为参考：

#### ✅ SalesReports.jsx（销售报表）

**修改内容**:
- 移除 `useState(mockMonthlySales)` 等 mock 初始值，改为 `useState(null)`
- 移除 catch 中的静默失败逻辑
- 添加错误状态管理
- 使用 `ApiIntegrationError` 组件显示错误
- 添加数据为空和加载中的处理

**关键改动**:
```javascript
// ❌ 之前
const [monthlySales, setMonthlySales] = useState(mockMonthlySales)
catch (err) {
  console.log('Sales reports API unavailable, using mock data')
  // 静默失败，保持 mock 数据
}

// ✅ 之后
const [monthlySales, setMonthlySales] = useState(null)
const [error, setError] = useState(null)
catch (err) {
  console.error('销售报表 API 调用失败:', err)
  setError(err)
  setMonthlySales(null) // 清空数据
}
```

#### ✅ ProductionDashboard.jsx（生产驾驶舱）

**修改内容**:
- 移除 `mockDashboardData` 常量
- 移除 catch 中设置 mock 数据和清除错误的逻辑
- 使用 `ApiIntegrationError` 组件显示错误
- 优化加载和空数据状态处理

**关键改动**:
```javascript
// ❌ 之前
catch (error) {
  setDashboardData(mockDashboardData)
  setError(null) // 清除错误，使用 mock 数据
}

// ✅ 之后
catch (error) {
  console.error('生产驾驶舱 API 调用失败:', error)
  setError(error)
  setDashboardData(null) // 清空数据
}
```

#### ✅ MaterialList.jsx（物料列表）

**修改内容**:
- 移除演示账号的 mock 数据逻辑
- 移除 catch 中的 fallback 逻辑
- 添加错误状态管理
- 使用 `ApiIntegrationError` 组件显示错误
- 优化 `filteredMaterials` 处理 null 数据

**关键改动**:
```javascript
// ❌ 之前
if (isDemoAccount) {
  setMaterials([...mock data...])
} else {
  const res = await materialApi.list(params)
  setMaterials(res.data)
}
catch (error) {
  setMaterials([...mock data...]) // fallback
}

// ✅ 之后
const res = await materialApi.list(params)
setMaterials(res.data)
catch (error) {
  setError(error)
  setMaterials(null) // 清空数据
}
```

### 4. 文档创建

**文件**: `FRONTEND_FALLBACK_PAGES_LIST.md`

创建了完整的清单文档，列出所有有 fallback 逻辑的页面（~60+ 页面），包括：
- 页面名称和文件路径
- Fallback 类型
- 状态（待修改）
- 修改模式和优先级

---

## 📋 标准修改模式

所有页面应遵循以下修改模式：

### 1. 状态初始化

```javascript
// ❌ 之前
const [data, setData] = useState(mockData)

// ✅ 之后
const [data, setData] = useState(null) // 或 []
const [error, setError] = useState(null)
```

### 2. API 调用错误处理

```javascript
// ❌ 之前
try {
  const res = await api.getData()
  setData(res.data)
} catch (error) {
  console.log('API unavailable, using mock data')
  setData(mockData) // fallback
  setError(null) // 清除错误
}

// ✅ 之后
try {
  setError(null)
  const res = await api.getData()
  setData(res.data)
} catch (error) {
  console.error('API 调用失败:', error)
  setError(error)
  setData(null) // 清空数据
}
```

### 3. 渲染逻辑

```javascript
// ✅ 标准模式
import { ApiIntegrationError } from '../components/ui'

// 在组件中
if (error) {
  return (
    <div>
      <PageHeader title="页面标题" />
      <ApiIntegrationError
        error={error}
        apiEndpoint="/api/v1/xxx"
        onRetry={loadData}
      />
    </div>
  )
}

if (loading || !data) {
  return <Loading />
}

if (data.length === 0) {
  return <EmptyState />
}

return <DataDisplay data={data} />
```

---

## 📊 进度统计

- **已修改示例页面**: 3 个
  - ✅ SalesReports.jsx
  - ✅ ProductionDashboard.jsx
  - ✅ MaterialList.jsx

- **待修改页面**: ~60+ 个（见 `FRONTEND_FALLBACK_PAGES_LIST.md`）

---

## 🎯 下一步工作

### 高优先级（P0）
按照示例页面的模式，修改以下核心页面：
1. `PurchaseOrders.jsx` - 采购订单
2. `ProjectBoard.jsx` - 项目看板
3. `AlertCenter.jsx` - 预警中心
4. `GeneralManagerWorkstation.jsx` - 总经理工作台

### 中优先级（P1）
修改其他核心业务模块的页面

### 低优先级（P2）
修改工作台和仪表板类页面

---

## 💡 注意事项

1. **演示账号处理**：如果确实需要支持演示账号，应该在组件顶层明确标识，而不是在 catch 中静默 fallback
2. **错误信息**：确保错误信息清晰，包含 API 端点信息
3. **用户体验**：虽然移除 fallback 会显示错误，但这是必要的，以确保集成状态清晰
4. **数据为空 vs 错误**：区分"数据为空"（空数组）和"API 调用失败"（错误）两种情况

---

## 🔍 验证方法

修改完成后，可以通过以下方式验证：

1. **检查初始状态**：页面加载时不应显示 mock 数据
2. **检查错误处理**：API 失败时应显示 `ApiIntegrationError` 组件
3. **检查控制台**：不应有"使用 mock 数据"的日志（除非是明确的演示模式）
4. **检查代码**：搜索 `setError(null)` 和 `setData(mock` 确保没有遗漏

---

**最后更新**: 2026-01-XX
