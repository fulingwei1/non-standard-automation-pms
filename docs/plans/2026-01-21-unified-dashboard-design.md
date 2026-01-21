# 统一工作台设计方案

## 概述

将现有26个角色工作台合并为统一工作台，通过角色权限控制显示内容。

## 设计决策

| 决策点 | 选择 |
|--------|------|
| 首页行为 | 角色自动识别 |
| 多角色处理 | 角色切换器下拉框 |
| 组件保留 | 完整模式（保留所有组件类型） |
| 技术架构 | 组件注册表模式 |

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│  统一工作台 (UnifiedDashboard)                           │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │  角色切换器: [销售工程师 ▼]  当前用户: 张三        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 统计卡片 │ │ 统计卡片 │ │ 统计卡片 │ │ 统计卡片 │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                         │
│  ┌────────────────────┐  ┌────────────────────────┐   │
│  │   待办任务列表      │  │     趋势图表           │   │
│  └────────────────────┘  └────────────────────────┘   │
│                                                         │
│  ┌────────────────────┐  ┌────────────────────────┐   │
│  │   通知/预警        │  │     快捷操作           │   │
│  └────────────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 文件结构

```
frontend/src/pages/UnifiedDashboard/
├── index.jsx                    # 主入口
├── RoleSwitcher.jsx             # 角色切换器
├── DashboardRenderer.jsx        # 动态渲染器
├── config/
│   ├── widgetRegistry.js        # 组件注册表
│   └── roleWidgetConfig.js      # 角色-组件配置
├── widgets/                     # 通用组件
│   ├── StatsCard.jsx
│   ├── TaskList.jsx
│   ├── NotificationPanel.jsx
│   └── ...
└── hooks/
    └── useUnifiedDashboard.js   # 数据管理
```

## 组件注册表

```js
// widgetRegistry.js
export const widgetRegistry = {
  // 通用组件
  'stats-card': { component: StatsCard, category: 'common' },
  'task-list': { component: TaskList, category: 'common' },
  'notification-panel': { component: NotificationPanel, category: 'common' },
  'quick-actions': { component: QuickActions, category: 'common' },
  'recent-items': { component: RecentItems, category: 'common' },

  // 销售组件
  'sales-funnel': { component: SalesFunnel, category: 'sales' },
  'leads-list': { component: LeadsList, category: 'sales' },
  'opportunity-board': { component: OpportunityBoard, category: 'sales' },
  'revenue-chart': { component: RevenueChart, category: 'sales' },
  'customer-list': { component: CustomerList, category: 'sales' },

  // 工程组件
  'project-progress': { component: ProjectProgress, category: 'engineer' },
  'timesheet-summary': { component: TimesheetSummary, category: 'engineer' },
  'ecn-list': { component: EcnList, category: 'engineer' },

  // 生产组件
  'production-board': { component: ProductionBoard, category: 'production' },
  'kit-status': { component: KitStatus, category: 'production' },
  'work-order-list': { component: WorkOrderList, category: 'production' },

  // 管理组件
  'system-health': { component: SystemHealth, category: 'admin' },
  'user-stats': { component: UserStats, category: 'admin' },
  'approval-pending': { component: ApprovalPending, category: 'admin' },
};
```

## 角色配置

```js
// roleWidgetConfig.js
export const roleWidgetConfig = {
  'SALES': {
    label: '销售工程师',
    widgets: [
      { id: 'stats-card', props: { type: 'sales' } },
      { id: 'sales-funnel' },
      { id: 'leads-list' },
      { id: 'task-list' },
      { id: 'notification-panel' },
    ],
    layout: '2-column',
  },

  'ENGINEER': {
    label: '工程师',
    widgets: [
      { id: 'stats-card', props: { type: 'engineer' } },
      { id: 'task-list' },
      { id: 'project-progress' },
      { id: 'timesheet-summary' },
      { id: 'ecn-list' },
    ],
    layout: '2-column',
  },

  'PMO_DIR': {
    label: '项目管理部总监',
    widgets: [
      { id: 'stats-card', props: { type: 'pmo' } },
      { id: 'project-progress' },
      { id: 'task-list' },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
    layout: '2-column',
  },

  'ADMIN': {
    label: '系统管理员',
    widgets: [
      { id: 'stats-card', props: { type: 'admin' } },
      { id: 'system-health' },
      { id: 'user-stats' },
      { id: 'approval-pending' },
      { id: 'notification-panel' },
    ],
    layout: '2-column',
  },

  'PRODUCTION': {
    label: '生产管理',
    widgets: [
      { id: 'stats-card', props: { type: 'production' } },
      { id: 'production-board' },
      { id: 'kit-status' },
      { id: 'work-order-list' },
      { id: 'task-list' },
    ],
    layout: '2-column',
  },

  'DEFAULT': {
    label: '默认',
    widgets: [
      { id: 'stats-card' },
      { id: 'task-list' },
      { id: 'notification-panel' },
    ],
    layout: '2-column',
  },
};
```

## 核心组件实现

### UnifiedDashboard/index.jsx

```jsx
export default function UnifiedDashboard() {
  const { user } = useAuth();
  const [currentRole, setCurrentRole] = useState(null);
  const { widgets, loading } = useUnifiedDashboard(currentRole);

  const userRoles = user?.roles || [];

  useEffect(() => {
    if (userRoles.length > 0 && !currentRole) {
      setCurrentRole(userRoles[0].role_code);
    }
  }, [userRoles]);

  return (
    <div className="unified-dashboard">
      <PageHeader title="工作台">
        <RoleSwitcher
          roles={userRoles}
          currentRole={currentRole}
          onChange={setCurrentRole}
        />
      </PageHeader>

      <DashboardRenderer
        widgets={widgets}
        loading={loading}
      />
    </div>
  );
}
```

### RoleSwitcher.jsx

```jsx
export function RoleSwitcher({ roles, currentRole, onChange }) {
  if (roles.length <= 1) return null;

  return (
    <Select value={currentRole} onValueChange={onChange}>
      <SelectTrigger className="w-48">
        <SelectValue placeholder="选择角色视图" />
      </SelectTrigger>
      <SelectContent>
        {roles.map(role => (
          <SelectItem key={role.role_code} value={role.role_code}>
            {role.role_name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
```

### DashboardRenderer.jsx

```jsx
export function DashboardRenderer({ widgets, loading }) {
  if (loading) return <DashboardSkeleton />;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
      {widgets.map((widget, index) => {
        const WidgetComponent = widgetRegistry[widget.id]?.component;
        if (!WidgetComponent) return null;

        return (
          <div key={widget.id + index} className={widget.className}>
            <WidgetComponent {...widget.props} />
          </div>
        );
      })}
    </div>
  );
}
```

### useUnifiedDashboard.js

```jsx
export function useUnifiedDashboard(roleCode) {
  const [loading, setLoading] = useState(true);
  const [widgetData, setWidgetData] = useState({});

  const roleConfig = roleWidgetConfig[roleCode] || roleWidgetConfig['DEFAULT'];

  useEffect(() => {
    if (!roleCode) return;

    async function loadDashboardData() {
      setLoading(true);
      try {
        const data = await api.get(`/dashboard/${roleCode}`);
        setWidgetData(data);
      } catch (err) {
        console.error('Dashboard load error:', err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, [roleCode]);

  const widgets = roleConfig.widgets.map(w => ({
    ...w,
    props: { ...w.props, data: widgetData[w.id] }
  }));

  return { widgets, loading, roleConfig };
}
```

## 迁移计划

| 阶段 | 动作 | 影响 |
|------|------|------|
| Phase 1 | 创建 UnifiedDashboard | 新增页面 |
| Phase 2 | 菜单改为统一入口 `/dashboard` | 修改 sidebarConfig |
| Phase 3 | 旧工作台路由重定向到新页面 | 兼容旧链接 |
| Phase 4 | 复用旧组件到 widgets/ | 提取复用 |
| Phase 5 | 删除废弃的旧工作台文件 | 清理代码 |

## 路由变更

```jsx
// 旧路由重定向
{ path: "/admin-dashboard", redirect: "/dashboard" },
{ path: "/sales-dashboard", redirect: "/dashboard" },
{ path: "/workstation", redirect: "/dashboard" },
{ path: "/production-dashboard", redirect: "/dashboard" },
{ path: "/procurement-dashboard", redirect: "/dashboard" },
{ path: "/manufacturing-director-dashboard", redirect: "/dashboard" },
{ path: "/production-manager-dashboard", redirect: "/dashboard" },
{ path: "/worker-workstation", redirect: "/dashboard" },
{ path: "/customer-service-dashboard", redirect: "/dashboard" },
{ path: "/finance-manager-dashboard", redirect: "/dashboard" },
{ path: "/hr-manager-dashboard", redirect: "/dashboard" },
{ path: "/presales-dashboard", redirect: "/dashboard" },
{ path: "/business-support", redirect: "/dashboard" },
{ path: "/gm-dashboard", redirect: "/dashboard" },
{ path: "/chairman-dashboard", redirect: "/dashboard" },
{ path: "/executive-dashboard", redirect: "/dashboard" },
// ... 其他旧路由

// 新统一路由
{ path: "/dashboard", element: <UnifiedDashboard /> },
```

## 菜单变更

将 sidebarConfig 中的多个工作台入口合并为一个：

```js
// 原来26个工作台入口
// 改为：
{
  label: "概览",
  items: [
    {
      name: "工作台",
      path: "/dashboard",
      icon: "LayoutDashboard",
      // 无需权限控制，所有人可见，内容按角色动态显示
    },
    // 保留其他非工作台入口...
  ]
}
```

## 待删除文件清单

实施完成后删除：

```
frontend/src/pages/AdminDashboard.jsx
frontend/src/pages/ProductionDashboard.jsx
frontend/src/pages/ProductionManagerDashboard.jsx
frontend/src/pages/OperationDashboard.jsx
frontend/src/pages/SalesManagerWorkstation.jsx
frontend/src/pages/ProcurementEngineerWorkstation.jsx
frontend/src/pages/WorkerWorkstation.jsx
frontend/src/pages/PresalesWorkstation.jsx
frontend/src/pages/BusinessSupportWorkstation.jsx
frontend/src/pages/AdministrativeManagerWorkstation.jsx
frontend/src/pages/SalesWorkstation/
frontend/src/pages/EngineerWorkstation/
frontend/src/pages/CustomerServiceDashboard/
frontend/src/pages/executive-dashboard/
frontend/src/pages/gm-workstation/
frontend/src/pages/SchedulerMonitoringDashboard/
```

## 创建日期

2026-01-21
