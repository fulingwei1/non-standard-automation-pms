# Dashboard 统一整合项目

## 🎯 项目目标

将系统中10个独立的Dashboard模块整合到统一的架构中，实现：
- ✅ 统一的API入口和响应格式
- ✅ 易于维护和扩展的适配器架构
- ✅ 向后兼容的渐进式迁移

## ✨ 完成状态

**🎉 100% 完成！所有11个模块已迁移！**

| 模块 | 状态 | 支持角色 |
|------|------|---------|
| 商务支持 | ✅ | business_support, admin |
| 人事管理 | ✅ | hr, admin |
| 生产管理 | ✅ | production, admin |
| PMO | ✅ | pmo, admin |
| 装配齐套 | ✅ | production, procurement, pmo, admin |
| 缺料管理 | ✅ | procurement, production, pmo, admin |
| 售前分析 | ✅ | presales, sales, admin |
| 战略管理 | ✅ | admin, pmo, strategy |
| 管理节律 | ✅ | admin, pmo, management |
| 人员匹配 | ✅ | hr, pmo, admin |
| 齐套率 | ✅ | procurement, production, pmo, admin |

## 📁 项目结构

```
app/
├── schemas/
│   └── dashboard.py                      # 统一Schema定义
├── services/
│   ├── dashboard_adapter.py              # 适配器基类和注册表
│   └── dashboard_adapters/               # 各模块适配器（11个）
│       ├── __init__.py
│       ├── assembly_kit.py
│       ├── business_support.py
│       ├── hr_management.py
│       ├── management_rhythm.py
│       ├── others.py
│       ├── pmo.py
│       ├── presales.py
│       ├── production.py
│       ├── shortage.py
│       └── strategy.py
└── api/v1/endpoints/
    └── dashboard_unified.py              # 统一入口

docs/
├── DASHBOARD_MIGRATION_GUIDE.md          # 迁移指南
└── DASHBOARD_MIGRATION_COMPLETE.md       # 完成总结

scripts/
└── test_dashboard_migration.py           # 测试脚本
```

## 🚀 快速开始

### 1. 运行测试

```bash
# 验证所有适配器是否正确注册
python3 scripts/test_dashboard_migration.py
```

### 2. 启动服务

```bash
# 启动FastAPI服务
uvicorn app.main:app --reload
```

### 3. 测试API

```bash
# 1. 获取PMO角色的dashboard
curl http://localhost:8000/api/v1/dashboard/unified/pmo

# 2. 获取详细数据
curl http://localhost:8000/api/v1/dashboard/unified/pmo/detailed?module_id=business_support

# 3. 列出所有模块
curl http://localhost:8000/api/v1/dashboard/modules

# 4. 按角色过滤模块
curl http://localhost:8000/api/v1/dashboard/modules?role_code=pmo
```

### 4. 访问API文档

打开浏览器访问: http://localhost:8000/docs

在Swagger UI中测试所有端点。

## 📚 API文档

### 端点1: 简化模式

**请求**:
```http
GET /api/v1/dashboard/unified/{role_code}
```

**参数**:
- `role_code`: 角色代码（pmo/admin/production/hr等）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "role_code": "pmo",
    "role_name": "项目管理办公室",
    "stats": [
      {
        "key": "active_projects",
        "label": "活跃项目",
        "value": 42,
        "unit": "个",
        "icon": "project",
        "color": "blue"
      }
    ],
    "widgets": [
      {
        "widget_id": "risk_projects",
        "widget_type": "list",
        "title": "风险项目",
        "data": [...],
        "order": 1,
        "span": 24
      }
    ],
    "last_updated": "2026-01-25T10:30:00",
    "refresh_interval": 300
  }
}
```

### 端点2: 详细模式

**请求**:
```http
GET /api/v1/dashboard/unified/{role_code}/detailed?module_id={module_id}
```

**参数**:
- `role_code`: 角色代码
- `module_id`: 可选，指定模块ID

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "module": "business_support",
      "module_name": "商务支持",
      "summary": {
        "active_contracts_count": 15,
        "pending_amount": 1250000.00
      },
      "details": {
        "urgent_tasks": [...],
        "today_todos": [...]
      },
      "generated_at": "2026-01-25T10:30:00"
    }
  ]
}
```

### 端点3: 模块列表

**请求**:
```http
GET /api/v1/dashboard/modules?role_code={role_code}
```

**参数**:
- `role_code`: 可选，按角色过滤

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "module_id": "business_support",
      "module_name": "商务支持",
      "roles": ["business_support", "admin"],
      "endpoint": "/dashboard/unified/{role_code}/detailed?module_id=business_support",
      "is_active": true
    }
  ]
}
```

## 🎨 前端集成示例

### React示例

```typescript
import { useEffect, useState } from 'react';

function Dashboard({ roleCode }) {
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    fetch(`/api/v1/dashboard/unified/${roleCode}`)
      .then(res => res.json())
      .then(data => setDashboardData(data.data));
  }, [roleCode]);

  return (
    <div>
      {/* 渲染统计卡片 */}
      <div className="stats-grid">
        {dashboardData?.stats.map(stat => (
          <StatCard key={stat.key} {...stat} />
        ))}
      </div>

      {/* 渲染widgets */}
      <div className="widgets-grid">
        {dashboardData?.widgets.map(widget => (
          <Widget key={widget.widget_id} {...widget} />
        ))}
      </div>
    </div>
  );
}
```

### Vue示例

```vue
<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <StatCard
        v-for="stat in dashboardData.stats"
        :key="stat.key"
        v-bind="stat"
      />
    </div>

    <!-- Widgets -->
    <div class="widgets-grid">
      <Widget
        v-for="widget in dashboardData.widgets"
        :key="widget.widget_id"
        v-bind="widget"
      />
    </div>
  </div>
</template>

<script>
export default {
  props: ['roleCode'],
  data() {
    return {
      dashboardData: { stats: [], widgets: [] }
    };
  },
  async mounted() {
    const response = await fetch(`/api/v1/dashboard/unified/${this.roleCode}`);
    const { data } = await response.json();
    this.dashboardData = data;
  }
};
</script>
```

## 🛠️ 开发指南

### 添加新模块

1. 创建适配器文件：

```python
# app/services/dashboard_adapters/my_module.py
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard

@register_dashboard
class MyModuleDashboardAdapter(DashboardAdapter):
    @property
    def module_id(self) -> str:
        return "my_module"

    # ... 实现其他方法
```

2. 在 `__init__.py` 中导入：

```python
from app.services.dashboard_adapters.my_module import MyModuleDashboardAdapter
```

3. 完成！适配器会自动注册。

### 修改现有模块

直接修改对应的适配器文件即可，无需修改其他代码。

## 📖 相关文档

- [详细迁移指南](./docs/DASHBOARD_MIGRATION_GUIDE.md)
- [完成总结](./docs/DASHBOARD_MIGRATION_COMPLETE.md)
- [API文档](http://localhost:8000/docs)

## 🎯 未来计划

- [ ] 前端完整对接
- [ ] 添加缓存机制
- [ ] 支持用户自定义Dashboard
- [ ] 实时数据推送
- [ ] Dashboard配置持久化

## 🙏 贡献

欢迎贡献代码和提出建议！

## 📄 许可

[MIT License](./LICENSE)

---

**项目完成时间**: 2026-01-25
**状态**: ✅ 已完成
**维护者**: 项目团队
