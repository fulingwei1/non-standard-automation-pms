# DataTable 组件使用指南

## 快速开始

```tsx
import { DataTable } from '@/core/components';

<DataTable
  queryKey={['projects']}
  queryFn={(params) => projectApi.listProjects(params)}
  columns={columns}
/>
```

## 完整示例

```tsx
import { DataTable } from '@/core/components';
import { projectApi } from '@/services/api';

const columns = [
  { title: '编码', dataIndex: 'code', key: 'code' },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '状态', dataIndex: 'status', key: 'status' },
];

function ProjectList() {
  return (
    <DataTable
      queryKey={['projects']}
      queryFn={(params) => projectApi.listProjects(params)}
      columns={columns}
      filters={[
        {
          key: 'status',
          label: '状态',
          type: 'select',
          options: [
            { label: '进行中', value: 'ACTIVE' },
            { label: '已完成', value: 'COMPLETED' }
          ]
        },
        {
          key: 'created_at',
          label: '创建日期',
          type: 'dateRange'
        }
      ]}
      keywordFields={['code', 'name']}
      defaultPageSize={20}
    />
  );
}
```

## Props说明

| 属性 | 类型 | 说明 |
|------|------|------|
| queryKey | (string\|number)[] | 查询Key（用于React Query缓存） |
| queryFn | Function | 查询函数 |
| columns | ColumnType[] | 表格列配置 |
| filters | FilterConfig[] | 筛选配置 |
| keywordFields | string[] | 关键词搜索字段 |
| defaultPageSize | number | 每页默认数量 |
| showFilters | boolean | 是否显示筛选面板 |
| showSearch | boolean | 是否显示搜索框 |
| showRefresh | boolean | 是否显示刷新按钮 |
