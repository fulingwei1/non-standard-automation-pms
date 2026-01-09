# 前端页面 Fallback 逻辑清单

**创建日期**: 2026-01-XX  
**目的**: 列出所有使用 Mock 数据作为 fallback 的页面，便于移除 fallback 逻辑，确保 API 集成状态清晰可见

---

## 说明

**Fallback 逻辑的问题**：
- API 调用失败时静默使用 Mock 数据，无法识别页面是否真正集成了 API
- 用户看到的是假数据，但误以为是真实数据
- 无法准确评估 API 集成完成度

**改进方案**：
- 移除所有 fallback 到 Mock 数据的逻辑
- API 失败时使用 `ApiIntegrationError` 组件明确显示错误
- 初始状态使用 `null` 或空数组，而不是 Mock 数据

---

## 有 Fallback 逻辑的页面清单

### 销售管理模块

| 页面 | 文件路径 | Fallback 类型 | 状态 |
|------|---------|--------------|------|
| 销售报表 | `SalesReports.jsx` | catch 中静默失败，保持 mock 初始值 | ⏳ 待修改 |
| 销售工作台 | `SalesWorkstation.jsx` | 使用 `useState(mockStats)` | ⏳ 待修改 |
| 销售总监工作台 | `SalesDirectorWorkstation.jsx` | catch 中使用 mock 数据 | ⏳ 待修改 |
| 销售经理工作台 | `SalesManagerWorkstation.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 销售团队 | `SalesTeam.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 销售漏斗 | `SalesFunnel.jsx` | catch 中 fallback 到 mock | ⏳ 待修改 |

### 生产管理模块

| 页面 | 文件路径 | Fallback 类型 | 状态 |
|------|---------|--------------|------|
| 生产驾驶舱 | `ProductionDashboard.jsx` | catch 中设置 mock 数据，清除错误 | ⏳ 待修改 |
| 生产经理仪表板 | `ProductionManagerDashboard.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 制造总监仪表板 | `ManufacturingDirectorDashboard.jsx` | 使用 mock 数据 | ⏳ 待修改 |

### 采购与物料模块

| 页面 | 文件路径 | Fallback 类型 | 状态 |
|------|---------|--------------|------|
| 物料列表 | `MaterialList.jsx` | catch 中设置 mock 数据 | ⏳ 待修改 |
| 采购订单 | `PurchaseOrders.jsx` | 演示账号使用 mock，catch 中 fallback | ⏳ 待修改 |
| 采购申请列表 | `PurchaseRequestList.jsx` | catch 中使用 mock | ⏳ 待修改 |
| 采购申请详情 | `PurchaseRequestDetail.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 采购订单详情 | `PurchaseOrderDetail.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 从BOM创建采购订单 | `PurchaseOrderFromBOM.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 到货跟踪列表 | `ArrivalTrackingList.jsx` | catch 中使用 mock | ⏳ 待修改 |
| 采购工程师工作台 | `ProcurementEngineerWorkstation.jsx` | catch 中设置 mock，清除错误 | ⏳ 待修改 |
| 采购经理仪表板 | `ProcurementManagerDashboard.jsx` | 使用 mock 数据 | ⏳ 待修改 |

### 项目管理模块

| 页面 | 文件路径 | Fallback 类型 | 状态 |
|------|---------|--------------|------|
| 项目看板 | `ProjectBoard.jsx` | catch 中 fallback 到 mock | ⏳ 待修改 |
| PMO 仪表板 | `PMODashboard.jsx` | catch 中设置 mock 数据 | ⏳ 待修改 |
| 项目评审列表 | `ProjectReviewList.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 排期看板 | `ScheduleBoard.jsx` | 使用 mock 数据 | ⏳ 待修改 |

### 预警与异常模块

| 页面 | 文件路径 | Fallback 类型 | 状态 |
|------|---------|--------------|------|
| 预警中心 | `AlertCenter.jsx` | 演示账号使用 mock，catch 中 fallback | ⏳ 待修改 |
| 预警统计 | `AlertStatistics.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 缺料预警 | `ShortageAlert.jsx` | 使用 mock 数据 | ⏳ 待修改 |

### 成本与财务模块

| 页面 | 文件路径 | Fallback 类型 | 状态 |
|------|---------|--------------|------|
| 成本分析 | `CostAnalysis.jsx` | catch 中设置 mock 数据 | ⏳ 待修改 |
| 预算管理 | `BudgetManagement.jsx` | catch 中设置 mock 数据 | ⏳ 待修改 |
| 财务报表 | `FinancialReports.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 财务经理仪表板 | `FinanceManagerDashboard.jsx` | 使用 mock 数据 | ⏳ 待修改 |

### 工作台（角色）模块

| 页面 | 文件路径 | Fallback 类型 | 状态 |
|------|---------|--------------|------|
| 总经理工作台 | `GeneralManagerWorkstation.jsx` | catch 中设置 mock，清除错误 | ⏳ 待修改 |
| 董事长工作台 | `ChairmanWorkstation.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 执行仪表板 | `ExecutiveDashboard.jsx` | catch 中 fallback | ⏳ 待修改 |
| 工程师工作台 | `EngineerWorkstation.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 工人工作台 | `WorkerWorkstation.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 装配工任务中心 | `AssemblerTaskCenter.jsx` | 使用 `useState(mockAssemblyTasks)` | ⏳ 待修改 |
| 售前工作台 | `PresalesWorkstation.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 售前经理工作台 | `PresalesManagerWorkstation.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 售前任务 | `PresalesTasks.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 业务支持工作台 | `BusinessSupportWorkstation.jsx` | catch 中设置 mock | ⏳ 待修改 |
| 行政经理工作台 | `AdministrativeManagerWorkstation.jsx` | catch 中设置 mock | ⏳ 待修改 |
| 客户服务仪表板 | `CustomerServiceDashboard.jsx` | catch 中设置 mock | ⏳ 待修改 |
| HR 经理仪表板 | `HRManagerDashboard.jsx` | 使用 mock 数据 | ⏳ 待修改 |

### 其他模块

| 页面 | 文件路径 | Fallback 类型 | 状态 |
|------|---------|--------------|------|
| 问题管理 | `IssueManagement.jsx` | catch 中清除错误，使用本地计算 | ⏳ 待修改 |
| 服务分析 | `ServiceAnalytics.jsx` | catch 中 fallback | ⏳ 待修改 |
| 服务工单管理 | `ServiceTicketManagement.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 客户沟通 | `CustomerCommunication.jsx` | 演示账号使用 mock | ⏳ 待修改 |
| 客户满意度 | `CustomerSatisfaction.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 审批中心 | `ApprovalCenter.jsx` | 演示账号使用 mock | ⏳ 待修改 |
| 任务中心 | `TaskCenter.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 通知中心 | `NotificationCenter.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 绩效结果 | `PerformanceResults.jsx` | catch 中静默失败，保持 mock | ⏳ 待修改 |
| 绩效排名 | `PerformanceRanking.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 绩效指标 | `PerformanceIndicators.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 评价任务列表 | `EvaluationTaskList.jsx` | catch 中 fallback 到 mock | ⏳ 待修改 |
| AI 人员匹配 | `AIStaffMatching.jsx` | 使用 `useState(mockStaffingNeeds)` | ⏳ 待修改 |
| 物料分析 | `MaterialAnalysis.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 齐套分析 | `MaterialAnalysis.jsx` | 使用 mock 数据 | ⏳ 待修改 |
| 发票管理 | `InvoiceManagement.jsx` | 使用 mock 数据作为 fallback | ⏳ 待修改 |

---

## 统计

- **总计**: ~60+ 页面有 fallback 逻辑
- **已修改**: 0 页面
- **待修改**: ~60+ 页面

---

## 修改模式

### 标准修改步骤

1. **移除 Mock 数据初始值**
   ```javascript
   // ❌ 之前
   const [data, setData] = useState(mockData)
   
   // ✅ 之后
   const [data, setData] = useState(null) // 或 []
   ```

2. **移除 catch 中的 fallback**
   ```javascript
   // ❌ 之前
   catch (error) {
     console.log('API unavailable, using mock data')
     setData(mockData)
     setError(null) // 清除错误
   }
   
   // ✅ 之后
   catch (error) {
     console.error('API 调用失败:', error)
     setError(error)
     setData(null) // 清空数据
   }
   ```

3. **使用 ApiIntegrationError 组件**
   ```javascript
   import { ApiIntegrationError } from '../components/ui'
   
   // 在渲染中
   {error ? (
     <ApiIntegrationError 
       error={error}
       apiEndpoint="/api/v1/xxx"
       onRetry={loadData}
     />
   ) : data ? (
     <DataDisplay data={data} />
   ) : (
     <Loading />
   )}
   ```

---

## 优先级

### P0 - 高优先级（示例页面）
- ✅ `SalesReports.jsx` - 销售报表
- ✅ `ProductionDashboard.jsx` - 生产驾驶舱
- ✅ `MaterialList.jsx` - 物料列表

### P1 - 核心业务模块
- `PurchaseOrders.jsx` - 采购订单
- `ProjectBoard.jsx` - 项目看板
- `AlertCenter.jsx` - 预警中心
- `GeneralManagerWorkstation.jsx` - 总经理工作台

### P2 - 其他模块
- 其余页面按模块优先级逐步修改

---

## 注意事项

1. **演示账号处理**：如果确实需要支持演示账号，应该在组件顶层明确标识，而不是在 catch 中静默 fallback
2. **错误信息**：确保错误信息清晰，包含 API 端点信息
3. **用户体验**：虽然移除 fallback 会显示错误，但这是必要的，以确保集成状态清晰

---

**最后更新**: 2026-01-XX
