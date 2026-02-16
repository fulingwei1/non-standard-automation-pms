# 智能采购管理系统 - 前端组件文档

## 📋 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [目录结构](#目录结构)
- [主要页面](#主要页面)
- [组件说明](#组件说明)
- [API集成](#api集成)
- [使用指南](#使用指南)
- [类型定义](#类型定义)

---

## 项目概述

智能采购管理系统前端界面，实现采购建议管理、供应商绩效评估、订单跟踪、报价比价等核心功能，对接后端10个API接口。

### 核心功能

1. **采购建议管理**
   - 建议列表查看
   - 建议详情展示
   - AI供应商推荐
   - 批准/拒绝建议
   - 建议转订单

2. **供应商绩效管理**
   - 绩效评估展示
   - 触发评估
   - 多维度评分卡
   - 供应商排名

3. **订单管理**
   - 订单跟踪
   - 时间轴展示
   - 收货确认

4. **报价管理**
   - 报价比价
   - 多供应商对比
   - AI推荐分析

---

## 技术栈

- **框架**: React 18 + TypeScript
- **UI组件**: shadcn/ui + Tailwind CSS
- **图表**: Recharts
- **表单**: React Hook Form + Zod
- **HTTP客户端**: Axios
- **路由**: React Router v6

---

## 目录结构

```
frontend/src/pages/purchase/
├── suggestions/                    # 采购建议模块
│   ├── SuggestionsList.tsx        # 建议列表页
│   ├── SuggestionDetail.tsx       # 建议详情页
│   └── components/
│       ├── SupplierRecommendation.tsx  # AI推荐供应商
│       └── ApprovalDialog.tsx          # 批准对话框
├── suppliers/                     # 供应商模块
│   ├── PerformanceManagement.tsx  # 绩效管理页
│   ├── SupplierRanking.tsx        # 供应商排名页
│   └── components/
│       ├── PerformanceScoreCard.tsx    # 绩效评分卡
│       └── RankingTable.tsx            # 排名表格
├── orders/                        # 订单模块
│   ├── OrderTracking.tsx          # 订单跟踪页
│   └── components/
│       └── TrackingTimeline.tsx        # 跟踪时间轴
└── quotations/                    # 报价模块
    ├── QuotationCompare.tsx       # 报价比价页
    └── components/
        └── CompareTable.tsx            # 比价表格

frontend/src/types/purchase/
└── index.ts                       # TypeScript类型定义

frontend/src/services/purchase/
└── purchaseService.ts             # API服务封装
```

---

## 主要页面

### 1. 采购建议列表页 (SuggestionsList.tsx)

**路由**: `/purchase/suggestions`

**功能**:
- 显示所有采购建议
- 支持按状态、紧急程度筛选
- 搜索建议编号、物料
- 批准/拒绝建议
- 查看详情
- 创建订单

**状态管理**:
```typescript
const [suggestions, setSuggestions] = useState<PurchaseSuggestion[]>([]);
const [filters, setFilters] = useState({
  status: '' as SuggestionStatus | '',
  urgency_level: '' as UrgencyLevel | '',
  search: '',
});
```

**主要操作**:
- `loadSuggestions()`: 加载建议列表
- `handleApprove()`: 批准建议
- `handleReject()`: 拒绝建议
- `handleCreateOrder()`: 创建订单

---

### 2. 采购建议详情页 (SuggestionDetail.tsx)

**路由**: `/purchase/suggestions/:id`

**功能**:
- 显示建议详细信息
- 展示AI推荐供应商
- 显示多维度评分雷达图
- 批准建议
- 创建订单

**组件结构**:
```tsx
<SuggestionDetail>
  <Card>基本信息</Card>
  <Card>预估成本</Card>
  <SupplierRecommendation />  {/* AI推荐组件 */}
  <ApprovalDialog />
</SuggestionDetail>
```

---

### 3. 供应商绩效管理页 (PerformanceManagement.tsx)

**路由**: `/purchase/suppliers/performance`

**功能**:
- 查看供应商绩效
- 选择评估期间
- 触发评估
- 展示评分卡片

**评分维度**:
- 准时交货率
- 质量合格率
- 价格竞争力
- 响应速度

---

### 4. 供应商排名页 (SupplierRanking.tsx)

**路由**: `/purchase/suppliers/ranking`

**功能**:
- 查看供应商排名
- 按评估期间筛选
- 显示排名奖牌
- 多维度对比

**排名展示**:
- 前3名高亮显示
- 奖牌图标（金、银、铜）
- 评级颜色编码

---

### 5. 订单跟踪页 (OrderTracking.tsx)

**路由**: `/purchase/orders/:orderId/tracking`

**功能**:
- 显示订单跟踪记录
- 时间轴展示
- 收货确认

**跟踪事件**:
- 下单 (CREATED)
- 确认 (CONFIRMED)
- 发货 (SHIPPED)
- 到货 (RECEIVED)
- 取消 (CANCELLED)

---

### 6. 报价比价页 (QuotationCompare.tsx)

**路由**: `/purchase/quotations/compare`

**功能**:
- 输入物料ID比价
- 显示多个供应商报价
- 标识最低价
- AI推荐供应商
- 显示供应商绩效评级

---

## 组件说明

### SupplierRecommendation.tsx

**用途**: 显示AI推荐的供应商信息和多维度评分

**Props**:
```typescript
interface SupplierRecommendationProps {
  suggestion: PurchaseSuggestion;
}
```

**核心功能**:
- 雷达图展示多维度评分
- 置信度进度条
- 详细评分展示（绩效、价格、交期、历史）

**雷达图数据**:
```typescript
const radarData = [
  { subject: '绩效', value: performance_score, fullMark: 100 },
  { subject: '价格', value: price_score, fullMark: 100 },
  { subject: '交期', value: delivery_score, fullMark: 100 },
  { subject: '历史', value: history_score, fullMark: 100 },
];
```

---

### ApprovalDialog.tsx

**用途**: 采购建议批准对话框

**Props**:
```typescript
interface ApprovalDialogProps {
  open: boolean;
  suggestion: PurchaseSuggestion;
  onClose: () => void;
  onSuccess: () => void;
}
```

**功能**:
- 显示建议详细信息
- 输入审批意见
- 提交批准

---

### PerformanceScoreCard.tsx

**用途**: 供应商绩效评分卡

**Props**:
```typescript
interface PerformanceScoreCardProps {
  performance: SupplierPerformance;
}
```

**展示内容**:
- 评级标识（A+/A/B/C/D）
- 4个关键指标
- 综合评分
- 订单统计

---

### RankingTable.tsx

**用途**: 供应商排名表格

**Props**:
```typescript
interface RankingTableProps {
  rankings: SupplierRanking[];
}
```

**特性**:
- 前3名高亮
- 奖牌图标
- 评级颜色编码

---

### TrackingTimeline.tsx

**用途**: 订单跟踪时间轴

**Props**:
```typescript
interface TrackingTimelineProps {
  events: OrderTrackingEvent[];
}
```

**时间轴元素**:
- 事件图标
- 事件描述
- 时间戳
- 操作人
- 物流信息

---

### CompareTable.tsx

**用途**: 报价比较表格

**Props**:
```typescript
interface CompareTableProps {
  compareData: QuotationCompareResponse;
}
```

**功能**:
- 显示多个供应商报价
- 标识最低价
- 显示AI推荐
- 供应商绩效评级

---

## API集成

### API服务 (purchaseService.ts)

所有API调用通过 `purchaseService` 单例进行：

```typescript
import purchaseService from '@/services/purchase/purchaseService';

// 获取采购建议列表
const suggestions = await purchaseService.getSuggestions({
  status: 'PENDING',
  limit: 20
});

// 批准建议
await purchaseService.approveSuggestion(suggestionId, {
  approved: true,
  review_note: '批准'
});

// 获取供应商绩效
const performance = await purchaseService.getSupplierPerformance(
  supplierId,
  { evaluation_period: '2026-02' }
);
```

### 已对接的API（10个）

| # | 方法 | 路径 | 功能 | 使用页面 |
|---|------|------|------|----------|
| 1 | GET | `/suggestions` | 采购建议列表 | SuggestionsList |
| 2 | POST | `/suggestions/{id}/approve` | 批准建议 | SuggestionsList, SuggestionDetail |
| 3 | POST | `/suggestions/{id}/create-order` | 建议转订单 | SuggestionsList, SuggestionDetail |
| 4 | GET | `/suppliers/{id}/performance` | 供应商绩效 | PerformanceManagement |
| 5 | POST | `/suppliers/{id}/evaluate` | 触发评估 | PerformanceManagement |
| 6 | GET | `/suppliers/ranking` | 供应商排名 | SupplierRanking |
| 7 | POST | `/quotations` | 创建报价 | - |
| 8 | GET | `/quotations/compare` | 比价 | QuotationCompare |
| 9 | GET | `/orders/{id}/tracking` | 订单跟踪 | OrderTracking |
| 10 | POST | `/orders/{id}/receive` | 收货确认 | OrderTracking |

---

## 使用指南

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1/purchase
```

### 3. 启动开发服务器

```bash
npm run dev
```

### 4. 路由配置

在 `App.tsx` 或路由配置文件中添加：

```typescript
import SuggestionsList from '@/pages/purchase/suggestions/SuggestionsList';
import SuggestionDetail from '@/pages/purchase/suggestions/SuggestionDetail';
import PerformanceManagement from '@/pages/purchase/suppliers/PerformanceManagement';
import SupplierRanking from '@/pages/purchase/suppliers/SupplierRanking';
import OrderTracking from '@/pages/purchase/orders/OrderTracking';
import QuotationCompare from '@/pages/purchase/quotations/QuotationCompare';

// 路由配置
<Routes>
  <Route path="/purchase/suggestions" element={<SuggestionsList />} />
  <Route path="/purchase/suggestions/:id" element={<SuggestionDetail />} />
  <Route path="/purchase/suppliers/performance" element={<PerformanceManagement />} />
  <Route path="/purchase/suppliers/ranking" element={<SupplierRanking />} />
  <Route path="/purchase/orders/:orderId/tracking" element={<OrderTracking />} />
  <Route path="/purchase/quotations/compare" element={<QuotationCompare />} />
</Routes>
```

### 5. 认证配置

确保在请求拦截器中正确配置Token：

```typescript
// 在 purchaseService.ts 中已自动配置
// Token从 localStorage 中读取
const token = localStorage.getItem('access_token');
```

---

## 类型定义

### 核心类型

所有类型定义位于 `frontend/src/types/purchase/index.ts`

**主要类型**:

```typescript
// 采购建议
export interface PurchaseSuggestion {
  id: number;
  suggestion_no: string;
  material_id: number;
  material_code: string;
  material_name: string;
  // ... 更多字段
}

// 供应商绩效
export interface SupplierPerformance {
  id: number;
  supplier_id: number;
  supplier_name: string;
  overall_score: number;
  rating: SupplierRating;  // 'A+' | 'A' | 'B' | 'C' | 'D'
  // ... 更多字段
}

// 订单跟踪
export interface OrderTrackingEvent {
  id: number;
  order_id: number;
  event_type: TrackingEventType;
  event_time: string;
  // ... 更多字段
}
```

### 枚举类型

```typescript
export type SuggestionStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'ORDERED';
export type UrgencyLevel = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
export type SupplierRating = 'A+' | 'A' | 'B' | 'C' | 'D';
export type OrderStatus = 'PENDING' | 'CONFIRMED' | 'SHIPPED' | 'RECEIVED' | 'CANCELLED';
```

---

## 样式配置

### 紧急程度颜色

```typescript
const URGENCY_CONFIG = {
  LOW: { color: 'bg-blue-100 text-blue-800', label: '低' },
  NORMAL: { color: 'bg-gray-100 text-gray-800', label: '普通' },
  HIGH: { color: 'bg-yellow-100 text-yellow-800', label: '高' },
  URGENT: { color: 'bg-red-100 text-red-800', label: '紧急' },
};
```

### 供应商评级颜色

```typescript
const RATING_CONFIG = {
  'A+': { color: 'bg-green-600 text-white', label: 'A+', desc: '优秀' },
  'A': { color: 'bg-green-500 text-white', label: 'A', desc: '良好' },
  'B': { color: 'bg-blue-500 text-white', label: 'B', desc: '合格' },
  'C': { color: 'bg-yellow-500 text-white', label: 'C', desc: '一般' },
  'D': { color: 'bg-red-500 text-white', label: 'D', desc: '不合格' },
};
```

---

## 响应式设计

所有页面和组件都采用响应式设计：

```typescript
// 使用 Tailwind CSS 响应式类
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* 手机：1列，平板：2列，桌面：4列 */}
</div>
```

---

## 错误处理

统一的错误处理：

```typescript
try {
  const data = await purchaseService.getSuggestions();
  setSuggestions(data);
} catch (error: any) {
  toast({
    title: '加载失败',
    description: error.response?.data?.detail || '无法加载数据',
    variant: 'destructive',
  });
}
```

---

## 性能优化

1. **懒加载**: 使用 `React.lazy()` 加载页面
2. **分页**: 建议列表支持分页
3. **缓存**: 使用 `useMemo` 缓存计算结果
4. **防抖**: 搜索输入使用防抖

---

## 开发建议

1. **遵循TypeScript类型**: 使用定义的类型，避免 `any`
2. **组件复用**: 提取通用组件
3. **统一样式**: 使用 shadcn/ui 组件
4. **错误处理**: 所有API调用都添加错误处理
5. **加载状态**: 显示加载指示器

---

## 测试

### 单元测试

```bash
npm run test
```

### E2E测试

```bash
npm run test:e2e
```

---

## 构建部署

```bash
# 生产构建
npm run build

# 预览
npm run preview
```

---

## 联系方式

- **项目**: Non-Standard Automation PMS
- **模块**: 智能采购管理前端
- **开发团队**: Team 1

---

**文档版本**: v1.0  
**最后更新**: 2026-02-16
