# 智能缺料预警系统 - 前端文档

**Team 3 - Smart Shortage Alert System Frontend**

## 📋 目录

- [系统概述](#系统概述)
- [技术栈](#技术栈)
- [文件结构](#文件结构)
- [页面说明](#页面说明)
- [组件说明](#组件说明)
- [API 接口](#api-接口)
- [使用指南](#使用指南)

---

## 系统概述

智能缺料预警系统前端，提供缺料预警看板、AI 方案推荐、需求预测、趋势分析等功能。

**核心功能**：
- ✅ 4级预警看板（URGENT/CRITICAL/WARNING/INFO）
- ✅ AI 智能方案推荐（5种处理方案）
- ✅ 需求预测（3种算法：移动平均/指数平滑/线性回归）
- ✅ 缺料趋势分析
- ✅ 根因分析
- ✅ 项目影响分析

---

## 技术栈

- **框架**: React 19 + JSX
- **UI库**: shadcn/ui + Tailwind CSS
- **图表**: Recharts
- **表单**: React Hook Form + Zod
- **路由**: React Router v7
- **HTTP**: Axios

---

## 文件结构

```
frontend/src/pages/shortage/
├── constants.js                    # 常量定义（颜色、级别、类型等）
├── README.md                       # 本文档
│
├── dashboard/                      # 预警看板
│   ├── AlertDashboard.jsx          # 主页面
│   └── components/
│       ├── AlertLevelCards.jsx     # 预警级别统计卡片
│       ├── AlertList.jsx           # 预警列表
│       └── QuickScanButton.jsx     # 快速扫描按钮
│
├── alerts/                         # 预警详情和方案
│   ├── AlertDetail.jsx             # 预警详情页
│   ├── SolutionRecommendation.jsx  # AI方案推荐页
│   └── components/
│       ├── ImpactAnalysis.jsx      # 影响分析组件
│       ├── SolutionCard.jsx        # 方案卡片
│       └── SolutionCompare.jsx     # 方案对比表格
│
├── forecast/                       # 需求预测
│   ├── DemandForecast.jsx          # 主页面
│   └── components/
│       ├── AlgorithmSelector.jsx   # 算法选择器
│       ├── ForecastChart.jsx       # 预测曲线图
│       └── ConfidenceInterval.jsx  # 置信区间和准确率
│
└── analysis/                       # 趋势和根因分析
    ├── TrendAnalysis.jsx           # 缺料趋势分析
    ├── RootCauseAnalysis.jsx       # 根因分析
    ├── ProjectImpactAnalysis.jsx   # 项目影响分析
    └── components/
        ├── TrendLineChart.jsx      # 趋势折线图
        └── RootCauseBarChart.jsx   # 根因柱状图
```

---

## 页面说明

### 1. AlertDashboard (缺料预警看板)

**路由**: `/shortage/dashboard`

**功能**:
- 显示 4 级预警统计卡片
- 快速扫描未来 30 天缺料
- 筛选和搜索预警
- 预警列表展示

**使用**:
```jsx
import AlertDashboard from '@/pages/shortage/dashboard/AlertDashboard';

// 在路由中使用
<Route path="/shortage/dashboard" element={<AlertDashboard />} />
```

---

### 2. AlertDetail (预警详情页)

**路由**: `/shortage/alerts/:id`

**功能**:
- 显示预警基本信息（缺料数量、需求日期等）
- 影响分析（延期天数、成本影响、受影响项目）
- 风险评分展示
- 标记解决功能

**使用**:
```jsx
import AlertDetail from '@/pages/shortage/alerts/AlertDetail';

<Route path="/shortage/alerts/:id" element={<AlertDetail />} />
```

---

### 3. SolutionRecommendation (AI方案推荐)

**路由**: `/shortage/alerts/:id/solutions`

**功能**:
- 显示 AI 生成的 5 种处理方案
- 方案评分（可行性/成本/时间/风险）
- 方案对比表格
- 推荐方案高亮显示

**方案类型**:
1. **URGENT_PURCHASE** - 紧急采购
2. **SUBSTITUTE** - 替代料
3. **TRANSFER** - 项目间调拨
4. **PARTIAL_DELIVERY** - 分批交付
5. **RESCHEDULE** - 生产重排期

---

### 4. DemandForecast (需求预测)

**路由**: `/shortage/forecast`

**功能**:
- 选择预测算法（移动平均/指数平滑/线性回归）
- 配置预测参数（历史周期、预测周期）
- 显示预测曲线图（含 95% 置信区间）
- 显示准确率指标（MAE、MAPE、Accuracy）

**算法说明**:
- **移动平均**: 适用于需求稳定的物料
- **指数平滑** (推荐): 适用于有趋势变化的物料
- **线性回归**: 适用于有明显增长/下降趋势

---

### 5. TrendAnalysis (缺料趋势分析)

**路由**: `/shortage/analysis/trend`

**功能**:
- 总体统计（总预警数、解决率、平均响应时间）
- 按级别分布饼图
- 按状态分布饼图
- 每日趋势折线图
- 日期范围筛选

---

### 6. RootCauseAnalysis (根因分析)

**路由**: `/shortage/analysis/root-cause`

**功能**:
- 缺料原因分类统计
- 成本影响分析
- 改进建议

**根因类型**:
- 需求预测不准
- 供应商延期
- 质量问题退货
- 紧急插单
- 其他

---

### 7. ProjectImpactAnalysis (项目影响分析)

**路由**: `/shortage/analysis/projects`

**功能**:
- 显示所有受影响项目
- 按风险评分排序
- 显示每个项目的延期天数和成本影响
- 显示缺料物料列表

---

## 组件说明

### AlertLevelCards (预警级别卡片)

**Props**:
- `stats`: 统计数据对象 `{ URGENT: 5, CRITICAL: 10, ... }`
- `onLevelClick`: 点击卡片回调函数

**示例**:
```jsx
<AlertLevelCards 
  stats={{ URGENT: 5, CRITICAL: 10, WARNING: 20, INFO: 15 }}
  onLevelClick={(level) => console.log(level)}
/>
```

---

### AlertList (预警列表)

**Props**:
- `alerts`: 预警数组
- `loading`: 加载状态

**示例**:
```jsx
<AlertList 
  alerts={alertsData} 
  loading={false}
/>
```

---

### QuickScanButton (快速扫描按钮)

**Props**:
- `onScanComplete`: 扫描完成回调函数

**示例**:
```jsx
<QuickScanButton 
  onScanComplete={(result) => {
    console.log(`生成 ${result.alerts_generated} 条预警`);
  }}
/>
```

---

### ImpactAnalysis (影响分析)

**Props**:
- `alert`: 预警对象

**示例**:
```jsx
<ImpactAnalysis alert={alertData} />
```

---

### SolutionCard (方案卡片)

**Props**:
- `solution`: 方案对象
- `onClick`: 点击回调函数

**示例**:
```jsx
<SolutionCard 
  solution={solutionData}
  onClick={(solution) => console.log(solution)}
/>
```

---

### ForecastChart (预测曲线图)

**Props**:
- `historicalData`: 历史数据数组 `[{ date, demand }, ...]`
- `forecastData`: 预测数据对象

**示例**:
```jsx
<ForecastChart 
  historicalData={historicalData}
  forecastData={forecastResult}
/>
```

---

## API 接口

### 导入方式

```jsx
import {
  getAlerts,
  getAlertDetail,
  triggerScan,
  getAlertSolutions,
  resolveAlert,
  getForecast,
  getTrendAnalysis,
  getRootCauseAnalysis,
  getProjectImpactAnalysis,
  subscribeNotifications,
} from '@/services/api/shortage';
```

### API 列表

| API 函数 | 方法 | 路径 | 说明 |
|---------|------|------|------|
| `getAlerts(params)` | GET | `/shortage/smart/alerts` | 获取预警列表 |
| `getAlertDetail(id)` | GET | `/shortage/smart/alerts/:id` | 获取预警详情 |
| `triggerScan(data)` | POST | `/shortage/smart/scan` | 触发扫描 |
| `getAlertSolutions(alertId)` | GET | `/shortage/smart/alerts/:id/solutions` | 获取AI方案 |
| `resolveAlert(alertId, data)` | POST | `/shortage/smart/alerts/:id/resolve` | 标记解决 |
| `getForecast(materialId, params)` | GET | `/shortage/smart/forecast/:material_id` | 需求预测 |
| `getTrendAnalysis(params)` | GET | `/shortage/smart/analysis/trend` | 趋势分析 |
| `getRootCauseAnalysis(params)` | GET | `/shortage/smart/analysis/root-cause` | 根因分析 |
| `getProjectImpactAnalysis(params)` | GET | `/shortage/smart/impact/projects` | 项目影响 |
| `subscribeNotifications(data)` | POST | `/shortage/smart/notifications/subscribe` | 订阅通知 |

---

## 使用指南

### 1. 添加路由

在 `frontend/src/routes/` 中添加路由配置：

```jsx
import AlertDashboard from '@/pages/shortage/dashboard/AlertDashboard';
import AlertDetail from '@/pages/shortage/alerts/AlertDetail';
import SolutionRecommendation from '@/pages/shortage/alerts/SolutionRecommendation';
import DemandForecast from '@/pages/shortage/forecast/DemandForecast';
import TrendAnalysis from '@/pages/shortage/analysis/TrendAnalysis';
import RootCauseAnalysis from '@/pages/shortage/analysis/RootCauseAnalysis';
import ProjectImpactAnalysis from '@/pages/shortage/analysis/ProjectImpactAnalysis';

const shortageRoutes = [
  {
    path: '/shortage/dashboard',
    element: <AlertDashboard />,
  },
  {
    path: '/shortage/alerts/:id',
    element: <AlertDetail />,
  },
  {
    path: '/shortage/alerts/:id/solutions',
    element: <SolutionRecommendation />,
  },
  {
    path: '/shortage/forecast',
    element: <DemandForecast />,
  },
  {
    path: '/shortage/analysis/trend',
    element: <TrendAnalysis />,
  },
  {
    path: '/shortage/analysis/root-cause',
    element: <RootCauseAnalysis />,
  },
  {
    path: '/shortage/analysis/projects',
    element: <ProjectImpactAnalysis />,
  },
];
```

---

### 2. 添加导航菜单

```jsx
const navigationItems = [
  {
    title: '智能缺料预警',
    icon: AlertTriangle,
    items: [
      { title: '预警看板', path: '/shortage/dashboard' },
      { title: '需求预测', path: '/shortage/forecast' },
      { title: '趋势分析', path: '/shortage/analysis/trend' },
      { title: '根因分析', path: '/shortage/analysis/root-cause' },
      { title: '项目影响', path: '/shortage/analysis/projects' },
    ],
  },
];
```

---

### 3. 使用常量

```jsx
import { ALERT_LEVELS, ALERT_COLORS, SOLUTION_TYPES } from '@/pages/shortage/constants';

// 获取预警级别配置
const levelConfig = ALERT_LEVELS['URGENT'];
console.log(levelConfig.label); // "紧急"
console.log(levelConfig.color); // "#DC2626"

// 获取方案类型配置
const solutionType = SOLUTION_TYPES['URGENT_PURCHASE'];
console.log(solutionType.label); // "紧急采购"
```

---

### 4. 调用 API

```jsx
import { getAlerts, triggerScan } from '@/services/api/shortage';

// 获取预警列表
const loadAlerts = async () => {
  try {
    const response = await getAlerts({
      alert_level: 'URGENT',
      status: 'PENDING',
      page: 1,
      page_size: 20,
    });
    console.log(response.data.items);
  } catch (error) {
    console.error(error);
  }
};

// 触发扫描
const handleScan = async () => {
  try {
    const response = await triggerScan({ days_ahead: 30 });
    console.log(`生成 ${response.data.alerts_generated} 条预警`);
  } catch (error) {
    console.error(error);
  }
};
```

---

## 颜色规范

```javascript
const ALERT_COLORS = {
  URGENT: '#DC2626',    // 红色
  CRITICAL: '#EA580C',  // 橙色
  WARNING: '#CA8A04',   // 黄色
  INFO: '#2563EB'       // 蓝色
};
```

---

## 验收标准

- [x] 7个主要页面全部完成
- [x] 12+子组件全部完成
- [x] 10个API对接完成
- [x] 响应式设计
- [x] 图表交互流畅
- [x] 组件文档完整

---

## 贡献者

**Team 3 - 智能缺料预警前端开发团队**

---

## 更新日志

### v1.0.0 (2026-02-16)
- ✅ 完成 7 个主要页面开发
- ✅ 完成 12+ 子组件开发
- ✅ 完成 10 个 API 接口集成
- ✅ 完成组件文档
- ✅ 完成常量定义
- ✅ 完成图表集成（Recharts）

---

**文档版本**: v1.0  
**最后更新**: 2026-02-16  
**负责人**: Team 3
