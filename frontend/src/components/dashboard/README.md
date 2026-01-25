# 统一Dashboard组件使用指南

## 概述

`BaseDashboard` 提供了所有Dashboard页面的统一基类组件，简化Dashboard页面的开发，确保UI一致性和用户体验。

## 特性

- ✅ 统一的数据加载和缓存机制
- ✅ 自动错误处理和重试
- ✅ 加载状态和骨架屏
- ✅ 刷新功能
- ✅ 动画效果
- ✅ 响应式布局

## 快速开始

### 1. 创建Dashboard页面

```jsx
import { BaseDashboard } from '../../components/dashboard';
import { StatCards } from './StatCards';
import { Charts } from './Charts';
import { api } from '../../services/api';

export default function MyDashboard() {
  return (
    <BaseDashboard
      title="我的工作台"
      description="查看我的工作概览和统计数据"
      queryKey={['dashboard', 'my']}
      queryFn={() => api.getMyDashboard()}
      renderContent={(data) => (
        <div className="space-y-6">
          {/* 统计卡片 */}
          <StatCards stats={data.overview} />
          
          {/* 图表 */}
          <Charts charts={data.trends} />
          
          {/* 最近项目 */}
          <RecentItems items={data.recent_items} />
        </div>
      )}
    />
  );
}
```

### 2. 使用自定义操作按钮

```jsx
import { Button } from '../../components/ui/button';
import { Plus } from 'lucide-react';

export default function MyDashboard() {
  return (
    <BaseDashboard
      title="项目管理"
      queryKey={['dashboard', 'projects']}
      queryFn={() => api.getProjectDashboard()}
      actions={
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          新建项目
        </Button>
      }
      renderContent={(data) => (
        // 内容
      )}
    />
  );
}
```

### 3. 配置自动刷新

```jsx
export default function MyDashboard() {
  return (
    <BaseDashboard
      title="实时监控"
      queryKey={['dashboard', 'monitoring']}
      queryFn={() => api.getMonitoringData()}
      refetchInterval={30000} // 每30秒自动刷新
      renderContent={(data) => (
        // 内容
      )}
    />
  );
}
```

## Props参考

### BaseDashboardProps

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `title` | `string` | ✅ | - | Dashboard标题 |
| `description` | `string` | ❌ | - | Dashboard描述 |
| `queryKey` | `Array<string\|number>` | ✅ | - | React Query的查询Key |
| `queryFn` | `Function` | ✅ | - | 数据查询函数，返回Promise |
| `renderContent` | `Function` | ✅ | - | 内容渲染函数，接收data参数 |
| `actions` | `React.ReactNode` | ❌ | - | 额外的操作按钮 |
| `cacheTime` | `number` | ❌ | `300000` | 缓存时间（毫秒），默认5分钟 |
| `enabled` | `boolean` | ❌ | `true` | 是否启用查询 |
| `refetchInterval` | `number` | ❌ | - | 自动刷新间隔（毫秒） |
| `onSuccess` | `Function` | ❌ | - | 查询成功回调 |
| `onError` | `Function` | ❌ | - | 查询失败回调 |
| `className` | `string` | ❌ | - | 自定义样式类名 |
| `showRefresh` | `boolean` | ❌ | `true` | 是否显示刷新按钮 |
| `showError` | `boolean` | ❌ | `true` | 是否显示错误信息 |

## 数据格式

### renderContent接收的data格式

```typescript
interface DashboardData {
  overview: {
    total: number;
    active: number;
    pending: number;
    completed: number;
    // 其他业务特定字段
  };
  stats?: {
    // 统计数据
  };
  trends?: Array<{
    date: string;
    value: number;
  }>;
  distribution?: {
    distribution: Record<string, number>;
    total: number;
    percentages: Record<string, number>;
  };
  recent_items?: Array<{
    id: number;
    // 其他字段
  }>;
  alerts?: Array<{
    id: number;
    // 其他字段
  }>;
  timestamp?: string;
}
```

## 使用示例

### 示例1：简单统计Dashboard

```jsx
import { BaseDashboard } from '../../components/dashboard';
import { StatCard } from '../../components/ui/stat-card';
import { api } from '../../services/api';

export default function StatsDashboard() {
  return (
    <BaseDashboard
      title="统计概览"
      queryKey={['dashboard', 'stats']}
      queryFn={() => api.getStats()}
      renderContent={(data) => (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="总数"
            value={data.overview?.total || 0}
          />
          <StatCard
            title="进行中"
            value={data.overview?.active || 0}
          />
          <StatCard
            title="待处理"
            value={data.overview?.pending || 0}
          />
          <StatCard
            title="已完成"
            value={data.overview?.completed || 0}
          />
        </div>
      )}
    />
  );
}
```

### 示例2：带图表的Dashboard

```jsx
import { BaseDashboard } from '../../components/dashboard';
import { LineChart } from '../../components/ui/charts';
import { api } from '../../services/api';

export default function AnalyticsDashboard() {
  return (
    <BaseDashboard
      title="数据分析"
      queryKey={['dashboard', 'analytics']}
      queryFn={() => api.getAnalytics()}
      renderContent={(data) => (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <LineChart
              title="趋势分析"
              data={data.trends || []}
            />
            <LineChart
              title="分布分析"
              data={data.distribution?.distribution || {}}
            />
          </div>
        </div>
      )}
    />
  );
}
```

### 示例3：带列表的Dashboard

```jsx
import { BaseDashboard } from '../../components/dashboard';
import { DataTable } from '../../components/ui/data-table';
import { api } from '../../services/api';

export default function ListDashboard() {
  return (
    <BaseDashboard
      title="项目列表"
      queryKey={['dashboard', 'projects']}
      queryFn={() => api.getProjects()}
      renderContent={(data) => (
        <div className="space-y-6">
          <StatCards stats={data.overview} />
          <DataTable
            data={data.recent_items || []}
            columns={[
              { key: 'name', label: '名称' },
              { key: 'status', label: '状态' },
              { key: 'created_at', label: '创建时间' },
            ]}
          />
        </div>
      )}
    />
  );
}
```

## 最佳实践

1. **数据格式统一**：确保后端返回的数据格式符合Dashboard的预期结构
2. **错误处理**：在`renderContent`中添加适当的错误边界处理
3. **性能优化**：对于大量数据，考虑使用虚拟滚动或分页
4. **缓存策略**：根据数据更新频率合理设置`cacheTime`
5. **用户体验**：提供清晰的加载状态和错误提示

## 与后端配合

确保后端API返回的数据格式符合前端Dashboard的预期：

```python
# 后端返回格式
{
    "overview": {
        "total": 100,
        "active": 50,
        "pending": 20,
        "completed": 30
    },
    "stats": {
        "by_status": {...},
        "by_stage": {...}
    },
    "trends": [
        {"date": "2026-01-01", "value": 10},
        ...
    ],
    "recent_items": [...],
    "timestamp": "2026-01-25T10:00:00"
}
```
