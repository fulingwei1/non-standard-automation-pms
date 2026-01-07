# 采购与物料管理页面 API 集成实现指南

## 概述

本文档提供详细的实现指南，帮助开发人员将采购和物料管理相关页面从 Mock 数据迁移到真实 API 集成。

## 需要集成的页面清单

### 1. PurchaseOrders.jsx - 采购订单列表页

**当前状态**：使用 Mock 数据

**需要集成的 API**：
```javascript
import { purchaseApi } from '../services/api'
import { useApi } from '../hooks/useApi'
import { isPermissionError } from '../utils/errorHandler'
import { toast } from '../components/ui/toast'

// 获取订单列表
const { execute: fetchOrders, loading, error, data } = useApi(
  (params) => purchaseApi.orders.list(params),
  {
    showErrorToast: true,
    onPermissionError: () => {
      toast.error('您没有权限访问采购订单')
      // 可选：重定向到首页
      // navigate('/')
    }
  }
)

// 创建订单
const { execute: createOrder } = useApi(
  (data) => purchaseApi.orders.create(data),
  {
    showSuccessToast: true,
    successMessage: '采购订单创建成功',
    onSuccess: () => {
      // 刷新列表
      fetchOrders(currentParams)
    }
  }
)

// 更新订单
const { execute: updateOrder } = useApi(
  ({ id, data }) => purchaseApi.orders.update(id, data),
  {
    showSuccessToast: true,
    successMessage: '采购订单更新成功'
  }
)

// 审批订单
const { execute: approveOrder } = useApi(
  ({ id, data }) => purchaseApi.orders.approve(id, data),
  {
    showSuccessToast: true,
    successMessage: '采购订单审批成功'
  }
)
```

**实现步骤**：
1. 导入 `purchaseApi` 和 `useApi` hook
2. 替换 `mockPurchaseOrders` 为 API 调用
3. 添加加载状态显示
4. 添加错误处理（特别是权限错误）
5. 实现分页、筛选、搜索功能

**关键代码示例**：
```javascript
// 在组件中
useEffect(() => {
  fetchOrders({
    page: currentPage,
    page_size: pageSize,
    keyword: searchQuery,
    status: statusFilter,
    supplier_id: supplierFilter,
    project_id: projectFilter,
  })
}, [currentPage, pageSize, searchQuery, statusFilter, supplierFilter, projectFilter])

// 处理权限错误
if (error && isPermissionError(error)) {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh]">
      <div className="text-6xl mb-4">🔒</div>
      <h1 className="text-2xl font-semibold text-white mb-2">无权限访问</h1>
      <p className="text-slate-400">您没有权限访问采购订单模块</p>
    </div>
  )
}
```

### 2. PurchaseOrderDetail.jsx - 采购订单详情页

**当前状态**：使用 Mock 数据

**需要集成的 API**：
```javascript
// 获取订单详情
const { execute: fetchOrderDetail, loading, error, data: order } = useApi(
  (id) => purchaseApi.orders.get(id),
  {
    onPermissionError: () => {
      toast.error('您没有权限查看此采购订单')
    }
  }
)

// 获取订单明细
const { execute: fetchOrderItems } = useApi(
  (id) => api.get(`/purchase-orders/${id}/items`),
  {
    onPermissionError: () => {
      toast.error('您没有权限查看订单明细')
    }
  }
)

// 更新订单
const { execute: updateOrder } = useApi(
  ({ id, data }) => purchaseApi.orders.update(id, data),
  {
    showSuccessToast: true,
    successMessage: '订单更新成功',
    onSuccess: () => {
      fetchOrderDetail(orderId)
    }
  }
)

// 审批订单
const { execute: approveOrder } = useApi(
  ({ id, data }) => purchaseApi.orders.approve(id, data),
  {
    showSuccessToast: true,
    successMessage: '订单审批成功',
    onSuccess: () => {
      fetchOrderDetail(orderId)
    }
  }
)
```

**实现步骤**：
1. 从路由参数获取订单 ID
2. 使用 `useParams` 获取 `id`
3. 调用 API 获取订单详情
4. 实现订单状态更新
5. 实现审批流程

### 3. MaterialTracking.jsx - 物料跟踪页

**当前状态**：使用 Mock 数据

**需要集成的 API**：
```javascript
// 获取物料列表
const { execute: fetchMaterials, loading, error, data } = useApi(
  (params) => materialApi.list(params),
  {
    onPermissionError: () => {
      toast.error('您没有权限访问物料管理')
    }
  }
)

// 获取物料详情
const { execute: fetchMaterialDetail } = useApi(
  (id) => materialApi.get(id)
)

// 更新物料信息
const { execute: updateMaterial } = useApi(
  ({ id, data }) => materialApi.update(id, data),
  {
    showSuccessToast: true,
    successMessage: '物料信息更新成功'
  }
)
```

**实现步骤**：
1. 集成物料列表 API
2. 集成物料详情 API
3. 实现物料状态跟踪
4. 实现到货状态更新

### 4. MaterialAnalysis.jsx - 物料分析页

**当前状态**：使用 Mock 数据

**需要集成的 API**：
```javascript
// 获取项目齐套率
const { execute: fetchProjectKitRate } = useApi(
  ({ projectId, calculateBy }) => 
    api.get(`/projects/${projectId}/kit-rate`, {
      params: { calculate_by: calculateBy }
    }),
  {
    onPermissionError: () => {
      toast.error('您没有权限查看齐套分析')
    }
  }
)

// 获取机台齐套率
const { execute: fetchMachineKitRate } = useApi(
  ({ machineId, calculateBy }) =>
    api.get(`/machines/${machineId}/kit-rate`, {
      params: { calculate_by: calculateBy }
    })
)

// 获取机台物料状态
const { execute: fetchMachineMaterialStatus } = useApi(
  (machineId) => api.get(`/machines/${machineId}/material-status`)
)

// 获取项目物料状态
const { execute: fetchProjectMaterialStatus } = useApi(
  (projectId) => api.get(`/projects/${projectId}/material-status`)
)

// 获取齐套看板数据
const { execute: fetchKitRateDashboard } = useApi(
  (params) => api.get('/kit-rate/dashboard', { params })
)
```

**实现步骤**：
1. 集成齐套率计算 API
2. 集成物料状态查询 API
3. 实现数据可视化（图表）
4. 实现实时数据刷新

### 5. ProcurementEngineerWorkstation.jsx - 采购工程师工作台

**当前状态**：使用 Mock 数据

**需要集成的 API**：
```javascript
// 获取采购统计
const { execute: fetchProcurementStats } = useApi(
  () => api.get('/procurement/statistics')
)

// 获取待办事项
const { execute: fetchTodos } = useApi(
  () => api.get('/procurement/todos')
)

// 获取采购订单列表（最近）
const { execute: fetchRecentOrders } = useApi(
  (params) => purchaseApi.orders.list({ ...params, limit: 10 })
)
```

**实现步骤**：
1. 集成统计数据 API
2. 集成待办事项 API
3. 实现快捷操作
4. 实现数据刷新

### 6. ProcurementManagerDashboard.jsx - 采购经理工作台

**当前状态**：使用 Mock 数据

**需要集成的 API**：
```javascript
// 获取管理统计
const { execute: fetchManagementStats } = useApi(
  () => api.get('/procurement/management/statistics')
)

// 获取审批列表
const { execute: fetchApprovals } = useApi(
  (params) => api.get('/procurement/approvals', { params })
)

// 获取供应商统计
const { execute: fetchSupplierStats } = useApi(
  () => api.get('/suppliers/statistics')
)
```

## 通用实现模式

### 1. 权限错误处理模式

```javascript
import { useApi } from '../hooks/useApi'
import { isPermissionError } from '../utils/errorHandler'
import { toast } from '../components/ui/toast'

function ProcurementPage() {
  const { execute, loading, error, data } = useApi(
    (params) => purchaseApi.orders.list(params),
    {
      onPermissionError: (error) => {
        toast.error('您没有权限访问此功能')
        // 可选：记录错误日志
        console.error('Permission denied:', error)
      }
    }
  )

  // 如果发生权限错误，显示无权限页面
  if (error && isPermissionError(error)) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="text-6xl mb-4">🔒</div>
        <h1 className="text-2xl font-semibold text-white mb-2">无权限访问</h1>
        <p className="text-slate-400 mb-4">您没有权限访问此页面</p>
        <Button onClick={() => window.history.back()}>
          返回上一页
        </Button>
      </div>
    )
  }

  // 正常渲染页面内容
  return (
    // ...
  )
}
```

### 2. 加载状态处理模式

```javascript
function ProcurementPage() {
  const { execute, loading, error, data } = useApi(
    (params) => purchaseApi.orders.list(params)
  )

  // 显示加载状态
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  // 显示错误状态
  if (error && !isPermissionError(error)) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h1 className="text-2xl font-semibold text-white mb-2">加载失败</h1>
        <p className="text-slate-400 mb-4">{getErrorMessage(error)}</p>
        <Button onClick={() => execute()}>重试</Button>
      </div>
    )
  }

  // 显示空状态
  if (!data || data.items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="text-6xl mb-4">📦</div>
        <h1 className="text-2xl font-semibold text-white mb-2">暂无数据</h1>
        <p className="text-slate-400">还没有采购订单</p>
      </div>
    )
  }

  // 正常显示数据
  return (
    // ...
  )
}
```

### 3. 分页处理模式

```javascript
function ProcurementPage() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [total, setTotal] = useState(0)

  const { execute: fetchOrders, loading, data } = useApi(
    (params) => purchaseApi.orders.list(params),
    {
      onSuccess: (response) => {
        setTotal(response.total)
      }
    }
  )

  useEffect(() => {
    fetchOrders({
      page,
      page_size: pageSize,
      // 其他筛选参数
    })
  }, [page, pageSize])

  return (
    <div>
      {/* 数据列表 */}
      {data?.items.map(order => (
        // ...
      ))}

      {/* 分页组件 */}
      <Pagination
        current={page}
        pageSize={pageSize}
        total={total}
        onChange={(newPage, newPageSize) => {
          setPage(newPage)
          setPageSize(newPageSize)
        }}
      />
    </div>
  )
}
```

### 4. 筛选和搜索模式

```javascript
function ProcurementPage() {
  const [filters, setFilters] = useState({
    keyword: '',
    status: 'all',
    supplier_id: null,
    project_id: null,
    dateRange: null,
  })

  const { execute: fetchOrders, loading, data } = useApi(
    (params) => purchaseApi.orders.list(params)
  )

  // 防抖搜索
  const debouncedSearch = useMemo(
    () => debounce((keyword) => {
      setFilters(prev => ({ ...prev, keyword }))
    }, 300),
    []
  )

  useEffect(() => {
    fetchOrders({
      page: 1,
      page_size: 20,
      ...filters,
    })
  }, [filters])

  return (
    <div>
      {/* 搜索框 */}
      <Input
        placeholder="搜索订单编号、标题..."
        onChange={(e) => debouncedSearch(e.target.value)}
      />

      {/* 筛选器 */}
      <Select
        value={filters.status}
        onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
      >
        <option value="all">全部状态</option>
        <option value="DRAFT">草稿</option>
        <option value="APPROVED">已审批</option>
        {/* ... */}
      </Select>
    </div>
  )
}
```

## 数据格式转换

### API 响应格式示例

```javascript
// 采购订单列表响应
{
  items: [
    {
      id: 1,
      order_no: "PO-250104-001",
      supplier_name: "XX供应商",
      project_name: "BMS老化测试设备",
      total_amount: 125000.00,
      amount_with_tax: 137500.00,
      required_date: "2025-01-15",
      status: "APPROVED",
      payment_status: "UNPAID",
      created_at: "2025-01-04T10:00:00"
    }
  ],
  total: 100,
  page: 1,
  page_size: 20,
  pages: 5
}
```

### 前端数据格式转换

```javascript
// 将 API 响应转换为前端使用的格式
function transformOrder(order) {
  return {
    id: order.id,
    orderNo: order.order_no,
    supplierName: order.supplier_name,
    projectName: order.project_name,
    totalAmount: order.total_amount,
    amountWithTax: order.amount_with_tax,
    requiredDate: order.required_date,
    status: order.status,
    paymentStatus: order.payment_status,
    createdAt: order.created_at,
    // 添加计算字段
    statusLabel: getStatusLabel(order.status),
    statusColor: getStatusColor(order.status),
    daysLeft: calculateDaysLeft(order.required_date),
  }
}

// 使用
const transformedOrders = data?.items.map(transformOrder) || []
```

## 测试清单

### 功能测试

- [ ] 页面正常加载
- [ ] 数据正确显示
- [ ] 分页功能正常
- [ ] 筛选功能正常
- [ ] 搜索功能正常
- [ ] 创建功能正常
- [ ] 更新功能正常
- [ ] 删除功能正常

### 权限测试

- [ ] 有权限用户能正常访问
- [ ] 无权限用户看到无权限提示
- [ ] 无权限用户无法看到菜单
- [ ] 直接访问 URL 时权限检查生效

### 错误处理测试

- [ ] 网络错误处理
- [ ] 权限错误处理
- [ ] 验证错误处理
- [ ] 服务器错误处理

### 用户体验测试

- [ ] 加载状态显示
- [ ] 空状态显示
- [ ] 错误提示友好
- [ ] 操作反馈及时

## 实施优先级

### 第一阶段（核心功能）

1. **PurchaseOrders.jsx** - 采购订单列表
   - 优先级：最高
   - 预计时间：2-3 天
   - 依赖：无

2. **PurchaseOrderDetail.jsx** - 采购订单详情
   - 优先级：最高
   - 预计时间：2-3 天
   - 依赖：PurchaseOrders.jsx

### 第二阶段（重要功能）

3. **MaterialTracking.jsx** - 物料跟踪
   - 优先级：高
   - 预计时间：2-3 天
   - 依赖：materialApi

4. **MaterialAnalysis.jsx** - 物料分析
   - 优先级：高
   - 预计时间：3-4 天
   - 依赖：kit_rate API

### 第三阶段（辅助功能）

5. **ProcurementEngineerWorkstation.jsx** - 采购工程师工作台
   - 优先级：中
   - 预计时间：2 天
   - 依赖：purchaseApi

6. **ProcurementManagerDashboard.jsx** - 采购经理工作台
   - 优先级：中
   - 预计时间：2 天
   - 依赖：purchaseApi, supplierApi

## 注意事项

1. **权限检查**：所有 API 调用都要处理权限错误
2. **错误处理**：区分不同类型的错误并给出相应提示
3. **加载状态**：所有异步操作都要显示加载状态
4. **数据验证**：前端也要进行基本的数据验证
5. **用户体验**：操作要有及时反馈，错误提示要友好
6. **性能优化**：合理使用缓存，避免重复请求
7. **代码复用**：提取公共逻辑，避免重复代码

## 相关资源

- [API 文档](./API_DOCUMENTATION.md)
- [权限控制文档](./PROCUREMENT_PERMISSION_IMPLEMENTATION.md)
- [错误处理指南](./ERROR_HANDLING_GUIDE.md)
- [前端页面统计](./FRONTEND_PAGES_STATISTICS.md)



