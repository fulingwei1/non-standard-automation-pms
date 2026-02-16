# 物料库存管理系统 - 组件文档

**Team 2 交付文档**  
**版本**: 1.0.0  
**日期**: 2026-02-16

---

## 📁 目录结构

```
frontend/src/pages/inventory/
├── overview/                          # 库存总览
│   ├── Dashboard.tsx                  # 库存总览仪表板（主页）
│   └── components/
│       ├── StockSummaryCards.tsx      # 统计卡片组件
│       └── QuickActions.tsx           # 快捷操作按钮
├── stocks/                            # 库存查询
│   ├── StockList.tsx                  # 库存查询列表页
│   ├── TransactionHistory.tsx         # 交易记录页
│   └── components/
│       ├── StockFilterBar.tsx         # 库存筛选栏
│       └── BatchTraceDialog.tsx       # 批次追溯对话框
├── operations/                        # 物料操作
│   ├── MaterialReservation.tsx        # 物料预留管理页
│   ├── MaterialIssue.tsx              # 领料出库页
│   ├── MaterialReturn.tsx             # 退料入库页
│   ├── StockTransfer.tsx              # 库存转移页
│   └── components/
│       └── OperationForm.tsx          # 操作表单组件（共享）
├── stockCount/                        # 库存盘点
│   ├── CountTasks.tsx                 # 盘点任务列表页
│   ├── CountDetails.tsx               # 盘点明细页
│   └── components/
│       ├── CreateTaskDialog.tsx       # 创建盘点任务对话框
│       ├── CountInputForm.tsx         # 盘点录入表单
│       └── AdjustmentApproval.tsx     # 库存调整审批组件
└── analysis/                          # 库存分析
    ├── TurnoverAnalysis.tsx           # 周转率分析页
    ├── AgingAnalysis.tsx              # 库龄分析页
    └── components/
        ├── TurnoverChart.tsx          # 周转率图表
        └── AgingPieChart.tsx          # 库龄分布饼图
```

---

## 📄 页面组件说明

### 1. 库存总览模块 (`overview/`)

#### Dashboard.tsx
**功能**: 库存管理首页，展示关键指标和快捷操作

**特性**:
- ✅ 5个统计卡片（总库存、总金额、低库存、盘点任务、周转率）
- ✅ 快捷操作入口（领料、退料、转移、盘点、查询、分析）
- ✅ 最近交易记录展示
- ✅ 库存预警提示

**API依赖**:
- `GET /api/v1/inventory/dashboard/summary` - 获取统计数据

**使用示例**:
```tsx
import Dashboard from '@/pages/inventory/overview/Dashboard';

function App() {
  return <Dashboard />;
}
```

#### StockSummaryCards.tsx
**Props**:
```typescript
interface StockSummaryCardsProps {
  summary: StockSummary;
  loading?: boolean;
}
```

**特性**:
- 响应式网格布局
- 支持加载状态动画
- 彩色图标和数据卡片

#### QuickActions.tsx
**功能**: 提供6个常用操作的快捷入口

**特性**:
- 一键跳转到各功能页面
- 彩色按钮区分不同操作
- 响应式布局

---

### 2. 库存查询模块 (`stocks/`)

#### StockList.tsx
**功能**: 库存数据查询和浏览

**特性**:
- ✅ 高级筛选（物料编码、位置、批次号、状态）
- ✅ 分页显示（每页20条）
- ✅ 批次号点击追溯
- ✅ 导出Excel功能
- ✅ 状态徽章（正常/低库存/已过期/已预留）

**API依赖**:
- `GET /api/v1/inventory/stocks` - 查询库存列表
- `GET /api/v1/inventory/stocks/export` - 导出数据
- `GET /api/v1/inventory/batch/{batchNumber}/trace` - 批次追溯

**查询参数**:
```typescript
{
  material_id?: number;
  location?: string;
  status?: StockStatus;
  batch_number?: string;
  page?: number;
  page_size?: number;
}
```

#### TransactionHistory.tsx
**功能**: 查看库存交易历史记录

**特性**:
- ✅ 按日期范围筛选
- ✅ 按物料名称/编码搜索
- ✅ 交易类型徽章
- ✅ 显示出入库详情

**API依赖**:
- `GET /api/v1/inventory/stocks/{id}/transactions` - 获取交易记录

#### BatchTraceDialog.tsx
**功能**: 显示批次的完整追溯链

**Props**:
```typescript
interface BatchTraceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  batchNumber: string;
}
```

**特性**:
- 时间轴展示
- 详细交易信息卡片
- 来源/目标位置显示
- 工单/项目关联

---

### 3. 物料操作模块 (`operations/`)

#### OperationForm.tsx（共享组件）
**功能**: 领料、退料、转移操作的通用表单

**Props**:
```typescript
interface OperationFormProps {
  type: 'issue' | 'return' | 'transfer';
  onSubmit: (data: any) => Promise<void>;
  loading?: boolean;
}
```

**特性**:
- React Hook Form + Zod 验证
- 根据操作类型显示不同字段
- 领料支持成本核算方法选择（FIFO/LIFO/加权平均）
- 实时表单验证

#### MaterialIssue.tsx
**功能**: 领料出库页面

**特性**:
- ✅ 填写物料、数量、位置
- ✅ 关联工单号
- ✅ 选择成本核算方法
- ✅ 支持预留领料
- ✅ 成功提示

**API依赖**:
- `POST /api/v1/inventory/issue`

#### MaterialReturn.tsx
**功能**: 退料入库页面

**特性**:
- ✅ 填写退料信息
- ✅ 批次号选择
- ✅ 关联工单

**API依赖**:
- `POST /api/v1/inventory/return`

#### StockTransfer.tsx
**功能**: 库存转移页面

**特性**:
- ✅ 源位置和目标位置输入
- ✅ 批次号追踪
- ✅ 转移原因备注

**API依赖**:
- `POST /api/v1/inventory/transfer`

#### MaterialReservation.tsx
**功能**: 物料预留管理

**特性**:
- ✅ 查看预留列表
- ✅ 创建新预留（对话框）
- ✅ 取消预留
- ✅ 状态徽章（有效/已使用/已取消/已过期）
- ✅ 显示剩余数量

**API依赖**:
- `GET /api/v1/inventory/reservations` - 预留列表
- `POST /api/v1/inventory/reserve` - 创建预留
- `POST /api/v1/inventory/reservation/{id}/cancel` - 取消预留

---

### 4. 库存盘点模块 (`stockCount/`)

#### CountTasks.tsx
**功能**: 盘点任务列表和管理

**特性**:
- ✅ 盘点任务列表（表格）
- ✅ 创建盘点任务（对话框）
- ✅ 任务类型（全盘/抽盘/循环盘）
- ✅ 状态筛选
- ✅ 查看盘点详情

**API依赖**:
- `GET /api/v1/inventory/count/tasks` - 任务列表
- `POST /api/v1/inventory/count/tasks` - 创建任务

#### CountDetails.tsx
**功能**: 盘点明细页面，录入实盘数量

**特性**:
- ✅ 汇总卡片（盘点物料数、已录入、差异项目、差异金额）
- ✅ 逐行录入实盘数量
- ✅ 差异高亮（红色负差异、绿色正差异）
- ✅ 批准调整按钮
- ✅ 实时计算差异

**API依赖**:
- `GET /api/v1/inventory/count/tasks/{id}` - 任务详情
- `GET /api/v1/inventory/count/tasks/{taskId}/details` - 明细列表
- `PUT /api/v1/inventory/count/details/{id}` - 更新实盘数量
- `POST /api/v1/inventory/count/tasks/{id}/approve` - 批准调整

#### CreateTaskDialog.tsx
**Props**:
```typescript
interface CreateTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}
```

**特性**:
- 选择盘点类型
- 指定盘点位置（可选）
- 设置计划日期
- 备注信息

#### CountInputForm.tsx
**功能**: 批量录入实盘数量

**Props**:
```typescript
interface CountInputFormProps {
  details: CountDetail[];
  onBatchUpdate: (updates: Array<{ id: number; actual_quantity: number }>) => Promise<void>;
}
```

#### AdjustmentApproval.tsx
**功能**: 审批库存调整

**Props**:
```typescript
interface AdjustmentApprovalProps {
  taskId: number;
  totalDifference: number;
  differenceCount: number;
  onApprove: (comment?: string) => Promise<void>;
  onReject: (comment: string) => Promise<void>;
}
```

**特性**:
- 显示差异汇总
- 审批意见输入
- 批准/拒绝按钮

---

### 5. 库存分析模块 (`analysis/`)

#### TurnoverAnalysis.tsx
**功能**: 库存周转率分析

**特性**:
- ✅ 日期范围选择
- ✅ 4个关键指标卡片（出库总额、平均库存、周转率、周转天数）
- ✅ 周转率等级徽章（快速/正常/缓慢）
- ✅ 趋势图（周转率和周转天数）
- ✅ 智能分析建议

**API依赖**:
- `GET /api/v1/inventory/analysis/turnover`

**分析建议**:
- 周转率 > 6: 库存不足风险
- 周转率 3-6: 正常范围
- 周转率 < 3: 呆滞库存风险

#### AgingAnalysis.tsx
**功能**: 库龄分析，识别呆滞库存

**特性**:
- ✅ 5个库龄范围卡片（0-30天、31-90天、91-180天、181-365天、365天以上）
- ✅ 库龄分布饼图
- ✅ 呆滞库存预警
- ✅ 呆滞物料明细表（库龄>180天）
- ✅ 处理建议

**API依赖**:
- `GET /api/v1/inventory/analysis/aging`

**库龄范围颜色**:
- 0-30天: 绿色（正常）
- 31-90天: 蓝色（正常）
- 91-180天: 橙色（关注）
- 181-365天: 红色（预警）
- 365天以上: 灰色（严重）

#### TurnoverChart.tsx
**Props**:
```typescript
interface TurnoverChartProps {
  data: Array<{
    month: string;
    turnover_rate: number;
    turnover_days: number;
  }>;
}
```

**特性**:
- 使用 Recharts 库
- 双Y轴（周转率和周转天数）
- 折线图展示趋势

#### AgingPieChart.tsx
**Props**:
```typescript
interface AgingPieChartProps {
  data: Array<{
    name: string;
    value: number;
    percentage: number;
  }>;
}
```

**特性**:
- 饼图展示库龄分布
- 百分比标签
- 彩色扇区

---

## 🎨 UI/UX 设计规范

### 颜色规范
- **绿色**: 正常状态、正差异、成功操作
- **蓝色**: 信息提示、进行中状态
- **橙色**: 预警、低库存
- **红色**: 错误、负差异、过期
- **紫色**: 盘点相关
- **灰色**: 已取消、中性状态

### 响应式断点
- **sm**: 640px
- **md**: 768px
- **lg**: 1024px
- **xl**: 1280px

### 表单验证
- 使用 React Hook Form + Zod
- 实时验证
- 清晰的错误提示

### 数据展示
- 大数字使用 `.toLocaleString()` 格式化
- 金额保留2位小数
- 日期使用 `date-fns` 格式化

---

## 🔌 API 集成清单

| API | 方法 | 页面 | 状态 |
|-----|------|------|------|
| `/api/v1/inventory/stocks` | GET | StockList | ✅ |
| `/api/v1/inventory/stocks/{id}/transactions` | GET | TransactionHistory | ✅ |
| `/api/v1/inventory/reserve` | POST | MaterialReservation | ✅ |
| `/api/v1/inventory/issue` | POST | MaterialIssue | ✅ |
| `/api/v1/inventory/return` | POST | MaterialReturn | ✅ |
| `/api/v1/inventory/transfer` | POST | StockTransfer | ✅ |
| `/api/v1/inventory/count/tasks` | GET | CountTasks | ✅ |
| `/api/v1/inventory/count/tasks` | POST | CreateTaskDialog | ✅ |
| `/api/v1/inventory/count/details/{id}` | PUT | CountDetails | ✅ |
| `/api/v1/inventory/count/tasks/{id}/approve` | POST | CountDetails | ✅ |
| `/api/v1/inventory/analysis/turnover` | GET | TurnoverAnalysis | ✅ |
| `/api/v1/inventory/analysis/aging` | GET | AgingAnalysis | ✅ |

**共计**: 12 个API全部对接完成 ✅

---

## 📦 依赖库

```json
{
  "react": "^18.0.0",
  "react-router-dom": "^6.0.0",
  "typescript": "^5.0.0",
  "tailwindcss": "^3.0.0",
  "@/components/ui": "shadcn/ui",
  "recharts": "^2.0.0",
  "react-hook-form": "^7.0.0",
  "zod": "^3.0.0",
  "@hookform/resolvers": "^3.0.0",
  "date-fns": "^3.0.0",
  "lucide-react": "^0.300.0",
  "axios": "^1.0.0"
}
```

---

## ✅ 验收清单

- [x] 10个主要页面全部完成
- [x] 15+子组件全部完成
- [x] 12个API对接成功
- [x] TypeScript类型定义完整
- [x] 响应式设计（支持移动端）
- [x] 组件文档完整
- [x] 表单验证完整
- [x] 错误处理完善
- [x] 加载状态提示
- [x] 用户操作反馈

---

## 🚀 快速开始

### 1. 引入类型定义
```typescript
import { Stock, Transaction, CountTask } from '@/types/inventory';
```

### 2. 使用API客户端
```typescript
import InventoryAPI from '@/services/inventory';

// 查询库存
const stocks = await InventoryAPI.getStocks({ location: '仓库A' });

// 领料
await InventoryAPI.issueMaterial({
  material_id: 101,
  quantity: 50,
  location: '仓库A-01',
});
```

### 3. 路由配置
```tsx
import Dashboard from '@/pages/inventory/overview/Dashboard';
import StockList from '@/pages/inventory/stocks/StockList';
// ... 其他导入

<Route path="/inventory">
  <Route path="dashboard" element={<Dashboard />} />
  <Route path="stocks/list" element={<StockList />} />
  {/* ... 其他路由 */}
</Route>
```

---

## 📞 支持

如有问题，请联系 Team 2 开发组。

**交付日期**: 2026-02-16
